"""
ChainSentinel - Advanced Analytics & Intelligence Tests
Phase 8 automated unit and integration tests.
"""

import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from backend.data.loader import load_transactions
from backend.detection.engine import DetectionEngine
from backend.analytics.models import (
    ClassificationType,
    PriorityLevel,
    BehaviorClassification,
    WalletBehaviorProfile,
    CrossPatternCorrelation,
    WalletIntelligence,
    InvestigationIntelligence,
)
from backend.analytics.profiler import WalletBehaviorProfiler
from backend.analytics.correlator import AlertCorrelator
from backend.analytics.intelligence import IntelligenceEngine
from backend.investigations.store import CASE_STORE
from backend.investigations.models import InvestigationCase
from backend.crypto.store import EVIDENCE_STORE
from backend.crypto.models import EvidenceRecord, EvidenceType
from backend.main import app


@pytest.fixture(scope="module")
def dataset_and_engine():
    raw_txs = load_transactions()
    engine = DetectionEngine(raw_txs)
    return raw_txs, engine


@pytest.fixture(scope="module")
def profiler(dataset_and_engine):
    _, engine = dataset_and_engine
    return WalletBehaviorProfiler(engine._transactions, engine)


@pytest.fixture(scope="module")
def correlator(dataset_and_engine):
    _, engine = dataset_and_engine
    alerts = engine.detect_all()
    return AlertCorrelator(alerts, engine._transactions)


@pytest.fixture(scope="module")
def intel_engine(dataset_and_engine):
    _, engine = dataset_and_engine
    return IntelligenceEngine(engine._transactions, engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ===========================================================================
# 1. Unit Tests — WalletBehaviorProfiler
# ===========================================================================

def test_profiler_normal_wallet(profiler):
    """Test profiling a standard retail/shopper wallet with no alerts."""
    shopper_wallet = "0x3333S0100000000000000000000000000000000"
    profile = profiler.profile_wallet(shopper_wallet)

    assert profile.wallet_id == shopper_wallet
    assert profile.total_tx_count > 0
    assert profile.alert_count == 0
    assert profile.risk_score == 0.0
    assert profile.risk_level == "LOW"
    assert profile.investigation_priority == PriorityLevel.LOW
    assert len(profile.classifications) == 1
    assert profile.classifications[0].name == ClassificationType.NORMAL
    assert any("normal activity" in s.lower() for s in profile.signals)


def test_profiler_circular_wallet(profiler):
    """Test profiling a wallet involved in circular transaction mule loops."""
    circular_origin = "0x71C8366420A85E1A0F9b123D377De304559B0975"
    profile = profiler.profile_wallet(circular_origin)

    assert profile.wallet_id == circular_origin
    assert profile.is_circular is True
    assert profile.alert_count > 0
    class_names = [c.name for c in profile.classifications]
    assert ClassificationType.CIRCULAR in class_names
    assert profile.investigation_priority in (PriorityLevel.HIGH, PriorityLevel.CRITICAL)
    assert any("circular" in s.lower() for s in profile.signals)


def test_profiler_cluster_mixing_node(profiler):
    """Test profiling a dense mixing cluster node with multi-pattern convergence."""
    cluster_node = "0xEE01000000000000000000000000000000000001"
    profile = profiler.profile_wallet(cluster_node)

    assert profile.wallet_id == cluster_node
    assert profile.is_cluster_participant is True
    assert profile.investigation_priority == PriorityLevel.CRITICAL
    class_names = [c.name for c in profile.classifications]
    assert ClassificationType.MIXER_LIKE in class_names
    assert ClassificationType.MULTI_PATTERN in class_names
    assert ClassificationType.HIGH_RISK in class_names
    assert profile.risk_score >= 70.0


def test_profiler_burst_wallet(profiler):
    """Test profiling a burst participant wallet."""
    burst_wallet = "0x981C30E3259838B4268e64cCE608aC68fD573c88"
    profile = profiler.profile_wallet(burst_wallet)

    assert profile.wallet_id == burst_wallet
    assert profile.is_burst_participant is True
    assert profile.outbound_tx_count >= 5
    class_names = [c.name for c in profile.classifications]
    assert (
        ClassificationType.HIGH_VELOCITY in class_names
        or ClassificationType.FAN_OUT in class_names
        or ClassificationType.MULTI_PATTERN in class_names
    )


def test_profiler_nonexistent_wallet(profiler):
    """Test profiler gracefully errors on an unknown wallet address."""
    with pytest.raises(ValueError, match="not found"):
        profiler.profile_wallet("0x9999NonExistentAddress000000000000000")


def test_profiler_to_dict(profiler):
    """Test serialization of WalletBehaviorProfile to dictionary."""
    shopper_wallet = "0x3333S0100000000000000000000000000000000"
    profile = profiler.profile_wallet(shopper_wallet)
    data = profile.to_dict()

    assert data["wallet_id"] == shopper_wallet
    assert "total_tx_count" in data
    assert "net_flow" in data
    assert "investigation_priority" in data
    assert isinstance(data["classifications"], list)
    assert isinstance(data["signals"], list)


# ===========================================================================
# 2. Unit Tests — AlertCorrelator
# ===========================================================================

def test_correlator_finds_multi_pattern_convergences(correlator):
    """Test detecting converging alert patterns on the same wallet or entity group."""
    correlations = correlator.correlate_all()
    assert len(correlations) > 0

    # Ensure all correlations have valid schema and distinct patterns
    for c in correlations:
        assert len(c.converging_patterns) >= 2
        assert c.primary_wallet != ""
        assert len(c.participating_wallets) >= 1
        assert c.confidence in ("HIGH", "MEDIUM", "LOW")
        assert c.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert len(c.explanation) > 0


def test_correlator_for_specific_wallet(correlator):
    """Test correlating alerts for a specific suspicious wallet versus a clean wallet."""
    cluster_wallet = "0xEE01000000000000000000000000000000000001"
    cluster_corrs = correlator.correlate_for_wallet(cluster_wallet)
    assert len(cluster_corrs) >= 1
    patterns = cluster_corrs[0].converging_patterns
    assert len(patterns) >= 2

    # Normal wallet has 0 correlations
    clean_wallet = "0x3333S0100000000000000000000000000000000"
    clean_corrs = correlator.correlate_for_wallet(clean_wallet)
    assert len(clean_corrs) == 0


def test_correlator_to_dict(correlator):
    """Test CrossPatternCorrelation to_dict serialization."""
    corrs = correlator.correlate_all()
    first = corrs[0]
    d = first.to_dict()

    assert "correlation_id" in d
    assert "title" in d
    assert "converging_patterns" in d
    assert "confidence" in d
    assert "severity" in d
    assert "explanation" in d


# ===========================================================================
# 3. Unit Tests — IntelligenceEngine
# ===========================================================================

def test_intelligence_engine_wallet_intelligence(intel_engine):
    """Test generating comprehensive WalletIntelligence dossier."""
    wallet_id = "0x71C8366420A85E1A0F9b123D377De304559B0975"
    intel = intel_engine.get_wallet_intelligence(wallet_id)

    assert intel is not None
    assert intel.wallet_id == wallet_id
    assert intel.risk_score > 0
    assert intel.investigation_priority in (PriorityLevel.HIGH, PriorityLevel.CRITICAL)
    assert intel.behavior_profile.wallet_id == wallet_id
    assert len(intel.explanation) > 0
    d = intel.to_dict()
    assert d["wallet_id"] == wallet_id
    assert "behavior_profile" in d
    assert "correlations" in d


def test_intelligence_engine_unknown_wallet(intel_engine):
    """Test generating intelligence for an unknown wallet returns None."""
    res = intel_engine.get_wallet_intelligence("0xUnknownAddressThatDoesNotExist")
    assert res is None


def test_intelligence_engine_get_all_profiles(intel_engine):
    """Test paginated and filtered retrieval of all wallet profiles."""
    all_res = intel_engine.get_all_wallet_profiles(limit=10, offset=0)
    assert all_res["total"] == len(intel_engine.known_wallets)
    assert len(all_res["wallets"]) == 10

    # Filter by priority
    crit_res = intel_engine.get_all_wallet_profiles(priority=PriorityLevel.CRITICAL)
    assert crit_res["total"] > 0
    for w in crit_res["wallets"]:
        assert w["investigation_priority"] == PriorityLevel.CRITICAL

    # Filter by min_risk
    high_risk_res = intel_engine.get_all_wallet_profiles(min_risk=70.0)
    for w in high_risk_res["wallets"]:
        assert w["risk_score"] >= 70.0


def test_intelligence_engine_network_summary(intel_engine):
    """Test global network summary analytics."""
    summary = intel_engine.get_network_summary()

    assert summary["total_wallets"] == 70
    assert summary["total_transactions"] == 70
    assert summary["total_volume_eth"] > 0
    assert summary["total_correlations"] > 0
    assert PriorityLevel.CRITICAL in summary["priority_breakdown"]
    assert ClassificationType.NORMAL in summary["classification_breakdown"]
    assert len(summary["top_priority_wallets"]) <= 5
    assert len(summary["top_correlations"]) <= 5


def test_intelligence_engine_investigation_intelligence(intel_engine):
    """Test investigation case intelligence dossier compilation."""
    # Setup test case in CASE_STORE
    test_target = "0x71C8366420A85E1A0F9b123D377De304559B0975"
    now_iso = datetime.now(timezone.utc).isoformat()
    existing = CASE_STORE.get("CASE-TEST-INTEL-01")
    if existing:
        case = existing
    else:
        case = InvestigationCase(
            case_id="CASE-TEST-INTEL-01",
            title="Test Circular Operation",
            target_wallet=test_target,
            status="OPEN",
            notes="Automated test case",
            alert_ids=["ALT-CIRCULAR-01"],
            related_wallets=["0x3a4b95d082E484d84f86f77b7389c9d4E00b144F"],
            created_at=now_iso,
            updated_at=now_iso,
        )
        CASE_STORE.create(case)

    # Add an evidence record to test Merkle verification inclusion
    if not EVIDENCE_STORE.get("EV-TEST-INTEL-01"):
        ev_record = EvidenceRecord(
            evidence_id="EV-TEST-INTEL-01",
            case_id=case.case_id,
            evidence_type=EvidenceType.WALLET_RISK,
            source_ref=test_target,
            content={"wallet": test_target, "note": "Test profile"},
            created_at=now_iso,
            evidence_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )
        EVIDENCE_STORE.create(ev_record)

    case_intel = intel_engine.get_investigation_intelligence(case.case_id)
    assert case_intel is not None
    assert case_intel.case_id == case.case_id
    assert case_intel.target_wallet == test_target
    assert case_intel.priority in (PriorityLevel.HIGH, PriorityLevel.CRITICAL)
    assert case_intel.priority_score > 0
    assert case_intel.evidence_count >= 1
    assert "VERIFIED" in case_intel.evidence_integrity_status
    assert len(case_intel.executive_summary) > 0

    d = case_intel.to_dict()
    assert d["case_id"] == case.case_id
    assert "target_behavior" in d
    assert "suspicious_counterparties" in d


# ===========================================================================
# 4. Integration Tests — FastAPI REST Endpoints
# ===========================================================================

def test_api_analytics_summary(client):
    """Test GET /analytics/summary."""
    res = client.get("/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_wallets" in data
    assert "total_correlations" in data
    assert "priority_breakdown" in data
    assert "classification_breakdown" in data
    assert "top_priority_wallets" in data


def test_api_analytics_wallets(client):
    """Test GET /analytics/wallets with pagination and filtering."""
    # Base call
    res = client.get("/analytics/wallets?limit=5&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert len(data["wallets"]) == 5

    # Filter by priority
    res_filt = client.get("/analytics/wallets?priority=CRITICAL")
    assert res_filt.status_code == 200
    for w in res_filt.json()["wallets"]:
        assert w["investigation_priority"] == "CRITICAL"

    # Filter by classification
    res_class = client.get("/analytics/wallets?classification=CIRCULAR")
    assert res_class.status_code == 200
    for w in res_class.json()["wallets"]:
        names = [c["name"] for c in w["classifications"]]
        assert "CIRCULAR" in names


def test_api_analytics_wallet_detail(client):
    """Test GET /analytics/wallet/{wallet_id}."""
    valid_id = "0x71C8366420A85E1A0F9b123D377De304559B0975"
    res = client.get(f"/analytics/wallet/{valid_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["wallet_id"] == valid_id
    assert "behavior_profile" in data
    assert "investigation_priority" in data
    assert "explanation" in data


def test_api_analytics_wallet_not_found(client):
    """Test GET /analytics/wallet/{wallet_id} with unknown wallet returns 404."""
    res = client.get("/analytics/wallet/0xNonExistentWalletAddress123456789")
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]


def test_api_analytics_correlations(client):
    """Test GET /analytics/correlations."""
    res = client.get("/analytics/correlations")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "correlations" in data
    assert data["total"] >= 1

    # Filter by severity
    res_crit = client.get("/analytics/correlations?severity=CRITICAL")
    assert res_crit.status_code == 200
    for c in res_crit.json()["correlations"]:
        assert c["severity"] == "CRITICAL"


def test_api_analytics_investigation_intelligence(client):
    """Test GET /analytics/investigations/{case_id}."""
    # First create an investigation case
    create_res = client.post(
        "/investigations",
        json={
            "title": "API Test Intel Case",
            "target_wallet": "0x71C8366420A85E1A0F9b123D377De304559B0975",
            "notes": "Testing intelligence endpoint",
            "alert_ids": [],
            "related_wallets": ["0x3a4b95d082E484d84f86f77b7389c9d4E00b144F"],
        },
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["case_id"]

    res = client.get(f"/analytics/investigations/{case_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == case_id
    assert "executive_summary" in data
    assert "priority_score" in data
    assert "target_behavior" in data


def test_api_analytics_investigation_not_found(client):
    """Test GET /analytics/investigations/{case_id} for nonexistent case returns 404."""
    res = client.get("/analytics/investigations/CASE-NONEXISTENT-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]
