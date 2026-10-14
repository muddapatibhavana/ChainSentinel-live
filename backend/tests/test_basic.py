"""
ChainSentinel - Phase 1 & 2 Verification Tests
Tests backend initialization, dataset loading, and API endpoints.
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app, DATASET, STATS


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ChainSentinel" in data["message"]


def test_dataset_categories_loaded():
    """Verify that all required synthetic transaction topologies exist."""
    categories = {tx["category_label"] for tx in DATASET}
    required = {
        "circular",
        "rapid_movement",
        "burst",
        "split",
        "recombination",
        "cluster",
        "normal",
    }
    assert required.issubset(categories), f"Missing categories: {required - categories}"


def test_circular_transaction_topology():
    """Verify circular pattern has 4 steps and returns to origin."""
    circular_txs = [tx for tx in DATASET if tx["category_label"] == "circular"]
    assert len(circular_txs) == 4
    # First sender should equal last receiver
    assert circular_txs[0]["from_wallet"] == circular_txs[-1]["to_wallet"]


def test_api_info_endpoint(client):
    response = client.get("/api/info")
    assert response.status_code == 200
    info = response.json()
    assert info["total_transactions"] == len(DATASET)
    assert info["total_wallets"] > 0
    assert "categories_breakdown" in info


def test_transactions_listing(client):
    response = client.get("/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(DATASET)
    assert len(data["transactions"]) > 0


def test_transactions_category_filter(client):
    response = client.get("/transactions?category=circular")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    for tx in data["transactions"]:
        assert tx["category_label"] == "circular"


def test_single_transaction_detail(client):
    first_tx = DATASET[0]
    response = client.get(f"/transactions/{first_tx['tx_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["tx_id"] == first_tx["tx_id"]
    assert data["from_wallet"] == first_tx["from_wallet"]
