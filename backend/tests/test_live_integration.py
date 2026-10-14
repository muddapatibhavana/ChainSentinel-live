"""
ChainSentinel - Phase 11 Live Ethereum Integration Test Suite
Comprehensive tests verifying SQLite persistence, normalization of contract creations,
reorg detection, sliding-window pruning, checkpoint recovery, background polling,
CSV export, and detection engine integration without external network calls.
"""

import os
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from starlette.testclient import TestClient

from backend.main import app
from backend.providers.live import LiveBlockchainProvider
from backend.providers.storage import LiveStorage
from backend.providers.manager import ProviderManager, PROVIDER_MANAGER
from backend.detection.engine import DetectionEngine


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_storage():
    """Provides a fresh isolated SQLite storage in a temporary directory."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_file = Path(tmp_dir) / "test_live_chain.db"
        storage = LiveStorage(db_path=db_file)
        yield storage


@pytest.fixture(autouse=True)
def clean_manager_state():
    """Ensure every test leaves the global manager in DEMO mode."""
    yield
    PROVIDER_MANAGER.switch_mode("DEMO")
    PROVIDER_MANAGER.live_provider.clear_live_transactions()


class TestLiveStorage:
    """Verifies SQLite storage operations, constraints, and Excel-compatible CSV exports."""

    def test_storage_init_and_tables(self, temp_storage):
        assert temp_storage.db_path.exists()
        stats = temp_storage.get_stats()
        assert stats["total_transactions"] == 0
        assert stats["total_wallets"] == 0

    def test_storage_save_and_deduplicate(self, temp_storage):
        txs = [
            {
                "tx_id": "0xABC1",
                "from_wallet": "0x1111",
                "to_wallet": "0x2222",
                "amount": 2.5,
                "timestamp": "2026-10-10T10:00:00+00:00",
                "block_number": 100,
            },
            {
                "tx_id": "0xABC2",
                "from_wallet": "0x2222",
                "to_wallet": "0x3333",
                "amount": 1.5,
                "timestamp": "2026-10-10T10:01:00+00:00",
                "block_number": 100,
            },
        ]
        inserted = temp_storage.save_transactions(txs)
        assert inserted == 2
        assert temp_storage.get_stats()["total_transactions"] == 2

        # Duplicate insertion
        inserted_dup = temp_storage.save_transactions(txs)
        assert inserted_dup == 0
        assert temp_storage.get_stats()["total_transactions"] == 2

    def test_storage_sliding_window_query(self, temp_storage):
        for i in range(10):
            temp_storage.save_transactions([{
                "tx_id": f"0xTX_{i}",
                "from_wallet": "0xA",
                "to_wallet": "0xB",
                "amount": float(i + 1),
                "timestamp": f"2026-10-10T10:{i:02d}:00+00:00",
                "block_number": 1000 + i,
            }])

        window = temp_storage.get_sliding_window_transactions(max_count=5)
        assert len(window) == 5
        # Oldest in window should be 0xTX_5
        assert window[0]["tx_id"] == "0xTX_5"
        assert window[-1]["tx_id"] == "0xTX_9"

    def test_storage_csv_export_format(self, temp_storage):
        temp_storage.save_transactions([{
            "tx_id": "0xCSV_TEST",
            "from_wallet": "0xAlice",
            "to_wallet": "0xBob",
            "amount": 10.75,
            "timestamp": "2026-10-10T10:30:00+00:00",
            "block_number": 500,
            "gas_fee": 0.003,
            "status": "SUCCESS",
            "category_label": "live_transfer",
            "description": "Test Transfer",
        }])

        csv_str = temp_storage.export_to_csv()
        assert "tx_hash,from_address,to_address,amount_eth" in csv_str
        assert "0xCSV_TEST" in csv_str
        assert "10.75" in csv_str
        assert csv_str.startswith("\ufeff")  # Excel BOM present

    def test_processed_blocks_and_checkpoint(self, temp_storage):
        assert temp_storage.is_block_processed(200) is False
        temp_storage.record_processed_block(
            block_number=200,
            block_hash="0xBLOCK200HASH",
            parent_hash="0xBLOCK199HASH",
            timestamp=1700000000,
            tx_count=45,
        )
        assert temp_storage.is_block_processed(200) is True
        latest = temp_storage.get_latest_processed_block()
        assert latest is not None
        assert latest["block_number"] == 200
        assert latest["block_hash"] == "0xBLOCK200HASH"


class TestLiveBlockchainProviderLogic:
    """Verifies normalization, reorg detection, capacity pruning, and restart recovery."""

    def test_contract_creation_normalization(self, temp_storage):
        prov = LiveBlockchainProvider(storage=temp_storage)
        raw_contract_tx = {
            "hash": "0xCONTRACT_DEPLOY_HASH",
            "from": "0xDEVELOPER_WALLET",
            "to": None,  # Contract creation has null 'to'
            "value": "0x0",
            "gas": "0x100000",
            "gasPrice": "0x3b9aca00",
            "blockNumber": "0x64",
            "blockHash": "0xBHASH",
            "block_timestamp": "2026-10-10T12:00:00+00:00",
        }
        normalized = prov.normalize_transaction(raw_contract_tx)
        assert normalized["tx_id"] == "0xCONTRACT_DEPLOY_HASH"
        assert normalized["from_wallet"] == "0xdeveloper_wallet"
        assert normalized["to_wallet"] == "0x0000000000000000000000000000000000000000"
        assert normalized["category_label"] == "contract_creation"
        assert normalized["amount"] == 0.0

    def test_reorganization_detection(self, temp_storage):
        prov = LiveBlockchainProvider(storage=temp_storage)
        # Record block 10
        temp_storage.record_processed_block(
            block_number=10,
            block_hash="0xCANONICAL_HASH_10",
            parent_hash="0xHASH_9",
            timestamp=1700000000,
            tx_count=5,
        )

        # Mock incoming block 11 whose parent is NOT 0xCANONICAL_HASH_10 (Reorg!)
        mock_block_11 = {
            "number": "0xb",  # 11
            "hash": "0xNEW_HASH_11",
            "parentHash": "0xREORG_ALTERNATIVE_HASH_10",  # Mismatch!
            "timestamp": "0x65432100",
            "transactions": [
                {
                    "hash": "0xTX_REORG_1",
                    "from": "0xUSER1",
                    "to": "0xUSER2",
                    "value": "0xde0b6b3a7640000",
                    "gas": "0x5208",
                    "gasPrice": "0x4a817c800",
                }
            ],
        }

        with patch.object(prov, "_rpc_call", return_value=mock_block_11):
            prov.fetch_block_by_number(11)

        status = prov.get_status()
        assert status["last_reorg_info"] is not None
        assert status["last_reorg_info"]["block_number"] == 11
        assert status["last_reorg_info"]["expected_parent"] == "0xCANONICAL_HASH_10"

    def test_sliding_window_pruning(self, temp_storage):
        # Set small capacity limit of 3
        prov = LiveBlockchainProvider(storage=temp_storage, window_capacity=3)
        txs = [
            {"tx_id": f"0xWIN_{i}", "from_wallet": "0xA", "to_wallet": "0xB", "amount": 1.0}
            for i in range(5)
        ]
        prov.ingest_batch(txs)

        # Active sliding window should be capped at 3
        active_txs = prov.get_transactions()
        assert len(active_txs) == 3
        assert [t["tx_id"] for t in active_txs] == ["0xWIN_2", "0xWIN_3", "0xWIN_4"]

        # But SQLite retains all 5!
        assert temp_storage.get_stats()["total_transactions"] == 5

    def test_checkpoint_persistence_restart_recovery(self, temp_storage):
        # First instance ingests data
        prov1 = LiveBlockchainProvider(storage=temp_storage)
        prov1.ingest_batch([
            {"tx_id": "0xSAVED_1", "from_wallet": "0xAAA", "to_wallet": "0xBBB", "amount": 5.0},
            {"tx_id": "0xSAVED_2", "from_wallet": "0xBBB", "to_wallet": "0xCCC", "amount": 4.5},
        ])
        temp_storage.record_processed_block(block_number=5000, block_hash="0xBHASH5000")

        # Simulate backend restart: create a new provider instance pointing to same storage
        prov2 = LiveBlockchainProvider(storage=temp_storage)
        status2 = prov2.get_status()
        assert status2["total_transactions"] == 2
        assert status2["latest_block_number"] == 5000
        assert len(prov2.get_transactions()) == 2
        assert prov2.get_transactions()[0]["tx_id"] == "0xSAVED_1"

    def test_provider_failure_and_retry_behavior(self, temp_storage):
        prov = LiveBlockchainProvider(storage=temp_storage)
        with patch.object(prov, "_rpc_call", side_effect=urllib.error.URLError("Connection refused")):
            res = prov.fetch_latest_block_transactions()
            assert res == []

        status = prov.get_status()
        assert status["healthy"] is False
        assert "Connection refused" in status["last_error"]
        assert status["consecutive_errors"] == 1

    def test_background_worker_start_stop(self, temp_storage):
        prov = LiveBlockchainProvider(storage=temp_storage, poll_interval=1.0)
        assert prov.is_polling() is False
        prov.start_polling()
        assert prov.is_polling() is True
        # Second call does not duplicate
        prov.start_polling()
        assert prov.is_polling() is True
        prov.stop_polling()
        assert prov.is_polling() is False


class TestProviderManagerAndAPIs:
    """Verifies manager mode switching and new Phase 11 REST endpoints."""

    def test_demo_live_mode_switching_preserves_sqlite(self):
        mgr = ProviderManager()
        assert mgr.mode == "DEMO"

        # Switch to LIVE (preventing async poll during test assertion)
        with patch.object(mgr.live_provider, "fetch_latest_block_transactions", return_value=[]):
            mgr.switch_mode("LIVE")
            assert mgr.mode == "LIVE"
            assert mgr.live_provider.is_polling() is True

            # Ingest a live transaction
            mgr.ingest_live_transactions([
                {"tx_id": "0xPERSIST_TX", "from_wallet": "0x111", "to_wallet": "0x222", "amount": 7.0}
            ])
            assert len(mgr.get_transactions()) == 1

            # Switch to DEMO
            mgr.switch_mode("DEMO")
            assert mgr.mode == "DEMO"
            assert mgr.live_provider.is_polling() is False
            assert len(mgr.get_transactions()) == 70  # Synthetic restored

            # Switch back to LIVE -> previous live tx is still there!
            mgr.switch_mode("LIVE")
            assert mgr.mode == "LIVE"
            assert len(mgr.get_transactions()) == 1
            assert mgr.get_transactions()[0]["tx_id"] == "0xPERSIST_TX"
            mgr.switch_mode("DEMO")

    def test_export_csv_endpoint(self, client):
        resp = client.get("/api/provider/export-csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "attachment; filename=" in resp.headers["content-disposition"]
        assert "tx_hash,from_address,to_address,amount_eth" in resp.text

    def test_check_connection_endpoint(self, client):
        with patch.object(PROVIDER_MANAGER.live_provider, "_rpc_call", return_value="0x1234"):
            resp = client.get("/api/provider/check-connection")
            assert resp.status_code == 200
            data = resp.json()
            assert data["connected"] is True
            assert data["current_block"] == int("0x1234", 16)


class TestDetectionEngineWithLiveTransfers:
    """Verifies that live ingested transactions flow cleanly into DetectionEngine."""

    def test_benign_live_transfers_yield_zero_false_alerts(self):
        # Ordinary disjoint live transfers
        live_transfers = [
            {
                "tx_id": "0xLIVETX_1",
                "from_wallet": "0xAlice",
                "to_wallet": "0xBob",
                "amount": 1.5,
                "timestamp": "2026-10-10T10:00:00+00:00",
                "status": "SUCCESS",
                "gas_fee": 0.002,
                "category_label": "live_transfer",
                "description": "Benign Transfer",
            },
            {
                "tx_id": "0xLIVETX_2",
                "from_wallet": "0xCarol",
                "to_wallet": "0xDave",
                "amount": 2.0,
                "timestamp": "2026-10-10T10:02:00+00:00",
                "status": "SUCCESS",
                "gas_fee": 0.002,
                "category_label": "live_transfer",
                "description": "Benign Transfer",
            },
        ]

        engine = DetectionEngine(live_transfers)
        alerts = engine.detect_all()
        # Normal transfers must not trigger false alarms
        assert len(alerts) == 0

        # Graph should still work properly for Alice
        graph = engine.get_wallet_graph("0xAlice", depth=1)
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) == 1

    def test_anomalous_live_transfers_detects_cycle(self):
        # A deliberate cycle of transfers on chain
        cycle_transfers = [
            {
                "tx_id": "0xCYCLE_1",
                "from_wallet": "0xW1",
                "to_wallet": "0xW2",
                "amount": 10.0,
                "timestamp": "2026-10-10T10:00:00+00:00",
                "status": "SUCCESS",
                "gas_fee": 0.002,
                "category_label": "live_transfer",
                "description": "Hop 1",
            },
            {
                "tx_id": "0xCYCLE_2",
                "from_wallet": "0xW2",
                "to_wallet": "0xW3",
                "amount": 9.8,
                "timestamp": "2026-10-10T10:05:00+00:00",
                "status": "SUCCESS",
                "gas_fee": 0.002,
                "category_label": "live_transfer",
                "description": "Hop 2",
            },
            {
                "tx_id": "0xCYCLE_3",
                "from_wallet": "0xW3",
                "to_wallet": "0xW1",
                "amount": 9.6,
                "timestamp": "2026-10-10T10:10:00+00:00",
                "status": "SUCCESS",
                "gas_fee": 0.002,
                "category_label": "live_transfer",
                "description": "Hop 3",
            },
        ]

        engine = DetectionEngine(cycle_transfers)
        alerts = engine.detect_all()
        assert len(alerts) >= 1
        patterns = [a.pattern for a in alerts]
        assert "CIRCULAR_TRANSACTION" in patterns
