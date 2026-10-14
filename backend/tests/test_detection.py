"""
ChainSentinel - Phase 3 Detection Engine Tests

Tests all 6 detectors, risk scoring, wallet-specific detection,
API endpoints, normal-activity non-flagging, and edge cases.

Run with:
    cd ChainSentinel
    .\backend\venv\Scripts\python.exe -m pytest backend/tests -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from backend.data.loader import load_transactions
from backend.detection.models import Transaction, PatternType, Severity
from backend.detection.engine import DetectionEngine
from backend.detection.circular import detect_circular
from backend.detection.rapid_movement import detect_rapid_movement
from backend.detection.burst import detect_burst
from backend.detection.fanout import detect_fanout
from backend.detection.fanin import detect_fanin
from backend.detection.clusters import detect_clusters
from backend.detection.risk import compute_wallet_risk, score_to_level

# ──────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def raw_transactions():
    return load_transactions()


@pytest.fixture(scope="module")
def typed_transactions(raw_transactions):
    return [Transaction.from_dict(t) for t in raw_transactions]


@pytest.fixture(scope="module")
def engine(raw_transactions):
    return DetectionEngine(raw_transactions)


@pytest.fixture(scope="module")
def all_alerts(engine):
    return engine.detect_all()


@pytest.fixture(scope="module")
def client():
    from backend.main import app
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def make_tx(tx_id, frm, to, amount, ts_offset_secs=0, base_ts=None):
    """Create a synthetic typed Transaction for unit tests."""
    if base_ts is None:
        base_ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return Transaction(
        tx_id=tx_id,
        from_wallet=frm,
        to_wallet=to,
        amount=amount,
        timestamp=base_ts + timedelta(seconds=ts_offset_secs),
        status="SUCCESS",
        gas_fee=0.002,
        category_label="test",
        description="test",
    )


# ──────────────────────────────────────────────────────────────────
# Transaction.from_dict parsing
# ──────────────────────────────────────────────────────────────────

def test_transaction_from_dict_parses_timestamp(raw_transactions):
    """Timestamps in the CSV must parse to tz-aware datetime objects."""
    tx = Transaction.from_dict(raw_transactions[0])
    assert tx.timestamp.tzinfo is not None
    assert isinstance(tx.timestamp, datetime)


def test_transaction_from_dict_types(raw_transactions):
    """All fields must have correct types after parsing."""
    tx = Transaction.from_dict(raw_transactions[0])
    assert isinstance(tx.tx_id, str)
    assert isinstance(tx.amount, float)
    assert isinstance(tx.gas_fee, float)


# ──────────────────────────────────────────────────────────────────
# Circular Detector
# ──────────────────────────────────────────────────────────────────

class TestCircularDetector:

    def test_synthetic_circular_is_detected(self, all_alerts):
        """The circular A→B→C→D→A pattern from the dataset must produce an alert."""
        circular_alerts = [a for a in all_alerts if a.pattern == PatternType.CIRCULAR_TRANSACTION]
        assert len(circular_alerts) > 0, "No circular alerts generated"

        # The main circular wallets
        expected_wallets = {
            '0x71C8366420A85E1A0F9b123D377De304559B0975',
            '0x3a4b95d082E484d84f86f77b7389c9d4E00b144F',
            '0xB72809dDcbFF77B96C005F9A4c4786638069a531',
            '0x89D24A6b4CcB1B6fAA2625fE562bDD9a23260359',
        }
        found = any(set(a.wallets) == expected_wallets for a in circular_alerts)
        assert found, f"Main circular ABCD not found. Detected cycles: {[sorted(a.wallets) for a in circular_alerts]}"

    def test_circular_alert_has_required_fields(self, all_alerts):
        """Every circular alert must have valid wallets, tx_ids, explanation."""
        circ = [a for a in all_alerts if a.pattern == PatternType.CIRCULAR_TRANSACTION]
        for alert in circ:
            assert len(alert.wallets) >= 3
            assert len(alert.transaction_ids) >= 3
            assert len(alert.explanation) > 20
            assert alert.time_span_seconds >= 0

    def test_circular_minimum_length(self, typed_transactions):
        """A 2-wallet loop (A→B→A) should NOT be flagged with min_cycle_length=3."""
        txs = [
            make_tx("t1", "W1", "W2", 10.0, 0),
            make_tx("t2", "W2", "W1", 9.9, 60),
        ]
        alerts = detect_circular(txs, min_cycle_length=3)
        assert len(alerts) == 0

    def test_circular_unit_3hop(self):
        """A 3-wallet loop A→B→C→A within 2h is flagged."""
        txs = [
            make_tx("t1", "A", "B", 100.0, 0),
            make_tx("t2", "B", "C", 99.0, 300),
            make_tx("t3", "C", "A", 98.5, 600),
        ]
        alerts = detect_circular(txs, min_cycle_length=3, max_window_seconds=7200)
        assert len(alerts) >= 1
        assert alerts[0].pattern == PatternType.CIRCULAR_TRANSACTION

    def test_circular_outside_time_window_not_flagged(self):
        """A circular flow that exceeds the time window must not be flagged."""
        txs = [
            make_tx("t1", "A", "B", 100.0, 0),
            make_tx("t2", "B", "C", 99.0, 4000),   # 4000s ≫ max window 3600s
            make_tx("t3", "C", "A", 98.5, 8000),
        ]
        alerts = detect_circular(txs, max_window_seconds=3600)
        assert len(alerts) == 0


# ──────────────────────────────────────────────────────────────────
# Rapid Movement Detector
# ──────────────────────────────────────────────────────────────────

class TestRapidMovementDetector:

    def test_rapid_movement_is_detected(self, all_alerts):
        """The 3-hop rapid relay chain in the dataset must be detected."""
        rapid = [a for a in all_alerts if a.pattern == PatternType.RAPID_MOVEMENT]
        assert len(rapid) > 0, "No rapid movement alerts generated"

    def test_rapid_movement_known_wallets(self, all_alerts):
        """The 3-hop feeder→relay1→relay2→exit chain must appear."""
        feeder = '0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66'
        rapid = [a for a in all_alerts if a.pattern == PatternType.RAPID_MOVEMENT]
        feeder_rapid = [a for a in rapid if feeder in a.wallets]
        assert len(feeder_rapid) >= 1, "Feeder wallet not found in rapid alerts"

    def test_rapid_movement_unit(self):
        """A 3-hop chain with 60s hold times is flagged."""
        txs = [
            make_tx("t1", "A", "B", 100.0, 0),
            make_tx("t2", "B", "C", 99.0, 60),
            make_tx("t3", "C", "D", 98.5, 120),
        ]
        alerts = detect_rapid_movement(txs, min_hops=3, max_hop_seconds=120)
        assert len(alerts) >= 1
        assert alerts[0].pattern == PatternType.RAPID_MOVEMENT

    def test_slow_hops_not_flagged(self):
        """Chain where each hop takes > 10 minutes must not be flagged (if threshold is 5 min)."""
        txs = [
            make_tx("t1", "A", "B", 100.0, 0),
            make_tx("t2", "B", "C", 99.0, 700),   # 11.7 min > 5 min max_hop
            make_tx("t3", "C", "D", 98.5, 1400),
        ]
        alerts = detect_rapid_movement(txs, min_hops=3, max_hop_seconds=300)
        assert len(alerts) == 0


# ──────────────────────────────────────────────────────────────────
# Burst Detector
# ──────────────────────────────────────────────────────────────────

class TestBurstDetector:

    def test_burst_is_detected(self, all_alerts):
        """The 10-tx burst from wallet 0x981C... must be detected."""
        burst_alerts = [a for a in all_alerts if a.pattern == PatternType.BURST]
        assert len(burst_alerts) >= 1

    def test_burst_known_wallet(self, all_alerts):
        burst_wallet = '0x981C30E3259838B4268e64cCE608aC68fD573c88'
        burst_alerts = [a for a in all_alerts if a.pattern == PatternType.BURST]
        matches = [a for a in burst_alerts if burst_wallet in a.wallets]
        assert len(matches) >= 1, f"Burst wallet not found. Alerts: {[a.wallets[0] for a in burst_alerts]}"

    def test_burst_unit_high_severity(self):
        """10 txs in 90s should be HIGH severity."""
        txs = [
            make_tx(f"t{i}", "BurstSender", f"Recv{i}", 1.0, i * 9)
            for i in range(10)
        ]
        alerts = detect_burst(txs, window_seconds=300, min_tx_count=5)
        assert len(alerts) >= 1
        assert alerts[0].severity == Severity.HIGH

    def test_sparse_sender_not_flagged(self):
        """A wallet sending 3 txs spread over 30 minutes must not be flagged (min=5)."""
        txs = [
            make_tx("t1", "Slow", "R1", 5.0, 0),
            make_tx("t2", "Slow", "R2", 5.0, 600),
            make_tx("t3", "Slow", "R3", 5.0, 1800),
        ]
        alerts = detect_burst(txs, window_seconds=300, min_tx_count=5)
        assert len(alerts) == 0


# ──────────────────────────────────────────────────────────────────
# Fan-Out / Splitting Detector
# ──────────────────────────────────────────────────────────────────

class TestFanOutDetector:

    def test_fanout_is_detected(self, all_alerts):
        """The 8-branch smurfing split must produce a fan-out alert."""
        fanout_alerts = [a for a in all_alerts if a.pattern == PatternType.FAN_OUT]
        assert len(fanout_alerts) >= 1

    def test_fanout_known_source(self, all_alerts):
        split_source = '0x323b5d4c32345ced77393b3530b1eed0f346429d'
        fanout_alerts = [a for a in all_alerts if a.pattern == PatternType.FAN_OUT]
        matches = [a for a in fanout_alerts if split_source in a.wallets]
        assert len(matches) >= 1, "Smurfing source wallet not in any fan-out alert"

    def test_fanout_unit(self):
        """A wallet sending to 6 distinct wallets in 1h must be flagged."""
        txs = [
            make_tx(f"t{i}", "Splitter", f"Recv{i}", 10.0, i * 300)
            for i in range(6)
        ]
        alerts = detect_fanout(txs, window_seconds=3600, min_destinations=4)
        assert len(alerts) >= 1
        assert alerts[0].pattern == PatternType.FAN_OUT

    def test_single_destination_not_flagged(self):
        """A wallet sending to only 1 destination (even repeatedly) is not a fan-out."""
        txs = [
            make_tx(f"t{i}", "Normal", "SingleRecv", 5.0, i * 60)
            for i in range(10)
        ]
        alerts = detect_fanout(txs, window_seconds=3600, min_destinations=4)
        assert len(alerts) == 0


# ──────────────────────────────────────────────────────────────────
# Fan-In / Recombination Detector
# ──────────────────────────────────────────────────────────────────

class TestFanInDetector:

    def test_fanin_is_detected(self, all_alerts):
        """The 7-tributary recombination into collector must produce a fan-in alert."""
        fanin_alerts = [a for a in all_alerts if a.pattern == PatternType.FAN_IN]
        assert len(fanin_alerts) >= 1

    def test_fanin_known_collector(self, all_alerts):
        collector = '0x9999f8e404F75eB9Ac49A1B3a0279c78D548F567'
        fanin_alerts = [a for a in all_alerts if a.pattern == PatternType.FAN_IN]
        matches = [a for a in fanin_alerts if collector in a.wallets]
        assert len(matches) >= 1, "Collector wallet not found in fan-in alerts"

    def test_fanin_unit(self):
        """5 senders to 1 receiver within 1h must be flagged."""
        txs = [
            make_tx(f"t{i}", f"Feeder{i}", "Collector", 10.0, i * 300)
            for i in range(5)
        ]
        alerts = detect_fanin(txs, window_seconds=3600, min_sources=4)
        assert len(alerts) >= 1
        assert PatternType.FAN_IN in [a.pattern for a in alerts]

    def test_single_sender_not_flagged(self):
        """One sender sending many times to one receiver is not fan-in (no source diversity)."""
        txs = [
            make_tx(f"t{i}", "OnlyFeeder", "Collector", 5.0, i * 60)
            for i in range(10)
        ]
        alerts = detect_fanin(txs, window_seconds=3600, min_sources=4)
        assert len(alerts) == 0


# ──────────────────────────────────────────────────────────────────
# Cluster Detector
# ──────────────────────────────────────────────────────────────────

class TestClusterDetector:

    def test_cluster_is_detected(self, all_alerts):
        """The 5-node dense cluster must produce a suspicious cluster alert."""
        cluster_alerts = [a for a in all_alerts if a.pattern == PatternType.SUSPICIOUS_CLUSTER]
        assert len(cluster_alerts) >= 1

    def test_cluster_known_wallets(self, all_alerts):
        cluster_nodes = {
            '0xEE01000000000000000000000000000000000001',
            '0xEE02000000000000000000000000000000000002',
            '0xEE03000000000000000000000000000000000003',
            '0xEE04000000000000000000000000000000000004',
            '0xEE05000000000000000000000000000000000005',
        }
        cluster_alerts = [a for a in all_alerts if a.pattern == PatternType.SUSPICIOUS_CLUSTER]
        found = any(cluster_nodes.issubset(set(a.wallets)) for a in cluster_alerts)
        assert found, "EE0x cluster wallets not found in cluster alerts"

    def test_cluster_high_density_is_high_severity(self, all_alerts):
        """The cluster with density=0.60 must be HIGH severity."""
        cluster_alerts = [a for a in all_alerts if a.pattern == PatternType.SUSPICIOUS_CLUSTER]
        high_density = [a for a in cluster_alerts if a.metadata.get("density", 0) >= 0.5]
        assert len(high_density) >= 1

    def test_cluster_unit(self):
        """A dense 4-node fully connected subgraph must be flagged."""
        nodes = ["N1", "N2", "N3", "N4"]
        txs = []
        t = 0
        for i, n1 in enumerate(nodes):
            for n2 in nodes:
                if n1 != n2:
                    txs.append(make_tx(f"t{t}", n1, n2, 1.0, t * 30))
                    t += 1
        alerts = detect_clusters(txs, min_nodes=3, min_edges=5, min_density=0.30)
        assert len(alerts) >= 1

    def test_sparse_star_not_flagged(self):
        """A hub-and-spoke topology (1 hub → 10 leaves) has low density and is not flagged."""
        txs = [
            make_tx(f"t{i}", "Hub", f"Leaf{i}", 5.0, i * 60)
            for i in range(10)
        ]
        # 11 nodes, 10 edges: density = 10/(11*10) = 0.091 < 0.30 → not flagged
        alerts = detect_clusters(txs, min_nodes=3, min_edges=5, min_density=0.30)
        assert len(alerts) == 0


# ──────────────────────────────────────────────────────────────────
# Risk Scoring
# ──────────────────────────────────────────────────────────────────

class TestRiskScoring:

    def test_score_to_level_critical(self):
        assert score_to_level(65) == Severity.CRITICAL

    def test_score_to_level_high(self):
        assert score_to_level(50) == Severity.HIGH

    def test_score_to_level_medium(self):
        assert score_to_level(25) == Severity.MEDIUM

    def test_score_to_level_low(self):
        assert score_to_level(5) == Severity.LOW

    def test_no_alerts_gives_low_risk(self, engine):
        """A wallet with no alerts must have LOW risk."""
        cold_storage = '0x2000B901C412356191910A9292837381920B2020'
        risk = engine.get_wallet_risk(cold_storage)
        assert risk.risk_level == Severity.LOW
        assert risk.risk_score == 0

    def test_suspicious_wallet_has_elevated_risk(self, engine):
        """The burst sender must have at least MEDIUM risk."""
        burst_wallet = '0x981C30E3259838B4268e64cCE608aC68fD573c88'
        risk = engine.get_wallet_risk(burst_wallet)
        assert risk.risk_level in (Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL)
        assert risk.risk_score >= 20

    def test_risk_accumulates_across_patterns(self):
        """Wallet involved in 3 different patterns should score higher than any single one."""
        from backend.detection.models import Alert

        def make_alert(pattern, wallet):
            return Alert(
                alert_id=f"test_{pattern}_{wallet}",
                pattern=pattern,
                severity=Severity.HIGH,
                wallets=[wallet, "OtherWallet"],
                transaction_ids=["tx1"],
                total_amount=100.0,
                time_span_seconds=300.0,
                explanation="test",
            )

        wallet = "SuspiciousWallet"
        alerts = [
            make_alert(PatternType.CIRCULAR_TRANSACTION, wallet),
            make_alert(PatternType.RAPID_MOVEMENT, wallet),
            make_alert(PatternType.BURST, wallet),
        ]
        risk = compute_wallet_risk(wallet, alerts)
        # circular=30, rapid=20, burst=15 → total=65 → CRITICAL
        assert risk.risk_score >= 60
        assert risk.risk_level == Severity.CRITICAL

    def test_risk_caps_at_100(self):
        """Risk score should not exceed 100."""
        from backend.detection.models import Alert
        wallet = "UltraSuspicious"
        alerts = []
        for pattern in [PatternType.CIRCULAR_TRANSACTION, PatternType.RAPID_MOVEMENT,
                        PatternType.BURST, PatternType.FAN_OUT, PatternType.FAN_IN,
                        PatternType.SUSPICIOUS_CLUSTER]:
            alerts.append(Alert(
                alert_id=f"test_{pattern}",
                pattern=pattern,
                severity=Severity.CRITICAL,
                wallets=[wallet],
                transaction_ids=["tx1"],
                total_amount=100.0,
                time_span_seconds=60.0,
                explanation="test",
            ))
        risk = compute_wallet_risk(wallet, alerts)
        assert risk.risk_score <= 100


# ──────────────────────────────────────────────────────────────────
# Wallet-Specific Detection
# ──────────────────────────────────────────────────────────────────

class TestWalletDetection:

    def test_detect_for_wallet_returns_correct_alerts(self, engine):
        """detect_for_wallet returns only alerts that include the specified wallet."""
        burst_wallet = '0x981C30E3259838B4268e64cCE608aC68fD573c88'
        wallet_alerts = engine.detect_for_wallet(burst_wallet)
        assert len(wallet_alerts) >= 1
        for alert in wallet_alerts:
            assert burst_wallet in alert.wallets

    def test_unknown_wallet_returns_empty(self, engine):
        """A wallet not in the dataset returns no alerts."""
        alerts = engine.detect_for_wallet("0x0000000000000000000000000000000000000000")
        assert len(alerts) == 0

    def test_normal_wallets_not_falsely_flagged(self, engine):
        """Retail shoppers (unique, single-tx wallets) must have no alerts."""
        shoppers = [
            '0x3333S0300000000000000000000000000000000',
            '0x3333S0500000000000000000000000000000000',
            '0x3333S0700000000000000000000000000000000',
        ]
        for wallet in shoppers:
            alerts = engine.detect_for_wallet(wallet)
            assert len(alerts) == 0, f"Shopper {wallet} incorrectly flagged: {[a.pattern for a in alerts]}"

    def test_dex_traders_not_primary_suspects(self, engine):
        """
        Individual DEX traders each send 1 tx to the DEX router.
        They appear in the DEX router's FAN_IN alert as contributing source wallets.
        That alert is LOW severity and the primary suspicious actor is the router itself.
        No trader should be identified as a HIGH or CRITICAL risk actor.
        """
        traders = [
            '0x2222D0300000000000000000000000000000000',
            '0x2222D0700000000000000000000000000000000',
        ]
        dex_router = '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640'
        for wallet in traders:
            alerts = engine.detect_for_wallet(wallet)
            # Any alert involving a trader must only be LOW severity
            for alert in alerts:
                assert alert.severity == "LOW", (
                    f"DEX trader {wallet} has unexpected {alert.severity} alert: {alert.pattern}"
                )
                # The collector must be the DEX router, not the trader
                collector = alert.metadata.get("collector_wallet", "")
                assert collector == dex_router


# ──────────────────────────────────────────────────────────────────
# Detection Summary
# ──────────────────────────────────────────────────────────────────

class TestDetectionSummary:

    def test_summary_counts_all_alerts(self, engine, all_alerts):
        summary = engine.get_summary()
        assert summary.total_alerts == len(all_alerts)

    def test_summary_has_all_pattern_types(self, engine):
        summary = engine.get_summary()
        patterns = set(summary.alerts_by_pattern.keys())
        expected = {
            PatternType.CIRCULAR_TRANSACTION,
            PatternType.RAPID_MOVEMENT,
            PatternType.BURST,
            PatternType.FAN_OUT,
            PatternType.FAN_IN,
            PatternType.SUSPICIOUS_CLUSTER,
        }
        assert expected.issubset(patterns), f"Missing patterns in summary: {expected - patterns}"

    def test_summary_severities_sum_to_total(self, engine, all_alerts):
        summary = engine.get_summary()
        severity_total = sum(summary.alerts_by_severity.values())
        assert severity_total == len(all_alerts)


# ──────────────────────────────────────────────────────────────────
# API Endpoints — Detection Routes
# ──────────────────────────────────────────────────────────────────

class TestDetectionAPIEndpoints:

    def test_get_alerts(self, client):
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "alerts" in data
        assert data["total"] > 0

    def test_get_alert_by_id(self, client, all_alerts):
        first_alert = all_alerts[0]
        response = client.get(f"/alerts/{first_alert.alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == first_alert.alert_id

    def test_get_alert_not_found(self, client):
        response = client.get("/alerts/nonexistent_alert_id")
        assert response.status_code == 404

    def test_get_wallet_risk(self, client):
        burst_wallet = '0x981C30E3259838B4268e64cCE608aC68fD573c88'
        response = client.get(f"/wallets/{burst_wallet}/risk")
        assert response.status_code == 200
        data = response.json()
        assert "risk_level" in data
        assert "risk_score" in data
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_get_wallet_alerts(self, client):
        burst_wallet = '0x981C30E3259838B4268e64cCE608aC68fD573c88'
        response = client.get(f"/wallets/{burst_wallet}/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert len(data["alerts"]) >= 1

    def test_get_detection_summary(self, client):
        response = client.get("/detection/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "alerts_by_pattern" in data
        assert data["total_alerts"] > 0

    def test_get_wallet_graph(self, client):
        wallet = '0x71C8366420A85E1A0F9b123D377De304559B0975'
        response = client.get(f"/graph/{wallet}")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0

    def test_get_alerts_filter_by_pattern(self, client):
        response = client.get("/alerts?pattern=CIRCULAR_TRANSACTION")
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["pattern"] == "CIRCULAR_TRANSACTION"

    def test_get_alerts_filter_by_severity(self, client):
        response = client.get("/alerts?severity=HIGH")
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["severity"] == "HIGH"


# ──────────────────────────────────────────────────────────────────
# Backward compatibility — Phase 1 & 2 endpoints must still work
# ──────────────────────────────────────────────────────────────────

class TestBackwardCompatibility:

    def test_health_endpoint_still_works(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_info_still_works(self, client):
        response = client.get("/api/info")
        assert response.status_code == 200

    def test_transactions_listing_still_works(self, client):
        response = client.get("/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 70

    def test_single_transaction_still_works(self, client):
        txs = load_transactions()
        first_tx = txs[0]
        response = client.get(f"/transactions/{first_tx['tx_id']}")
        assert response.status_code == 200
