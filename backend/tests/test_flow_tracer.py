"""
ChainSentinel - Flow Tracer & Path Reconstruction Tests
Phase 7 automated unit and integration tests.
"""

import pytest
from starlette.testclient import TestClient

from backend.data.loader import load_transactions
from backend.detection.engine import DetectionEngine
from backend.detection.tracer import FlowTracer
from backend.investigations.store import CASE_STORE
from backend.investigations.models import InvestigationCase
from backend.main import app


@pytest.fixture(scope="module")
def dataset_and_engine():
    raw_txs = load_transactions()
    engine = DetectionEngine(raw_txs)
    return raw_txs, engine


@pytest.fixture(scope="module")
def tracer(dataset_and_engine):
    _, engine = dataset_and_engine
    return FlowTracer(engine._transactions, engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests — FlowTracer Core Engine
# ---------------------------------------------------------------------------

def test_direct_path(tracer):
    """Test 1-hop direct path reconstruction."""
    source = "0x71C8366420A85E1A0F9b123D377De304559B0975"
    target = "0x3a4b95d082E484d84f86f77b7389c9d4E00b144F"
    res = tracer.trace_flow(source, target, max_depth=2)

    assert res["path_found"] is True
    assert res["primary_path"] is not None
    assert res["primary_path"]["hops"] == 1
    assert res["primary_path"]["wallets"] == [source, target]
    assert len(res["primary_path"]["hops_detail"]) == 1
    assert res["primary_path"]["total_value"] == 50.0
    assert res["primary_path"]["hops_detail"][0]["amount"] == 50.0


def test_multi_hop_rapid_movement(tracer):
    """Test 3-hop rapid movement path reconstruction with temporal continuity."""
    source = "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    target = "0xDeB94101e4a6eD75d19830Af36691C2817865239"
    res = tracer.trace_flow(source, target, max_depth=4)

    assert res["path_found"] is True
    primary = res["primary_path"]
    assert primary["hops"] == 3
    assert len(primary["wallets"]) == 4
    assert primary["source"] == source
    assert primary["target"] == target
    assert primary["intermediate_wallets"] == [
        "0x42f703B8D4eF128E618EbAee48Ccf0b8Ffa55375",
        "0x7E3523B06C783857500B8e974Ec272bBcEb96E69",
    ]
    # Total volume: 120.0 + 119.8 + 119.5 = 359.3
    assert abs(primary["total_value"] - 359.3) < 0.01
    assert primary["temporal_consistent"] is True
    assert primary["duration_seconds"] <= 1800  # Rapid hops
    assert "RAPID_MOVEMENT" in primary["patterns_encountered"]
    assert primary["path_suspicion_score"] >= 40.0


def test_no_path_disconnected_components(tracer):
    """Test when no directed path connects two wallets."""
    # Rapid feeder to an unrelated E-commerce store receiver
    source = "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    target = "0x3000C888aB110022334455667788990011223344"
    res = tracer.trace_flow(source, target, max_depth=5)

    assert res["path_found"] is False
    assert res["primary_path"] is None
    assert "No directed transaction flow found" in res["explanation"]


def test_nonexistent_source_wallet(tracer):
    """Test error handling when source wallet is not in dataset."""
    res = tracer.trace_flow("0xNONEXISTENT_SOURCE_WALLET", "0xDeB94101e4a6eD75d19830Af36691C2817865239")
    assert res["path_found"] is False
    assert "error" in res
    assert "Source wallet" in res["error"]


def test_nonexistent_target_wallet(tracer):
    """Test error handling when target wallet is not in dataset."""
    source = "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    res = tracer.trace_flow(source, "0xNONEXISTENT_TARGET_WALLET")
    assert res["path_found"] is False
    assert "error" in res
    assert "Target wallet" in res["error"]


def test_source_equals_target_cycle_detected(tracer):
    """Test when source == target on a cyclic flow returns the closed loop."""
    cycle_origin = "0x71C8366420A85E1A0F9b123D377De304559B0975"
    res = tracer.trace_flow(cycle_origin, cycle_origin, max_depth=5)

    assert res["path_found"] is True
    assert res.get("is_cycle") is True
    primary = res["primary_path"]
    assert primary["hops"] == 4
    assert primary["wallets"][0] == cycle_origin
    assert primary["wallets"][-1] == cycle_origin
    assert abs(primary["total_value"] - 197.3) < 0.1
    assert "CIRCULAR_TRANSACTION" in primary["patterns_encountered"] or "CIRCULAR" in primary["patterns_encountered"]


def test_source_equals_target_no_cycle(tracer):
    """Test when source == target on a wallet that has no cyclic outflows."""
    pos_terminal = "0x3000C888aB110022334455667788990011223344"
    res = tracer.trace_flow(pos_terminal, pos_terminal, max_depth=4)

    assert res["path_found"] is True
    assert res.get("is_cycle") is False
    primary = res["primary_path"]
    assert primary["hops"] == 0
    assert primary["total_value"] == 0.0


def test_depth_cutoff_boundary(tracer):
    """Test that max_depth cutoff stops exploration when path is longer."""
    source = "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    target = "0xDeB94101e4a6eD75d19830Af36691C2817865239"

    # Rapid movement path is 3 hops. With max_depth=2, it must not be found.
    res = tracer.trace_flow(source, target, max_depth=2)
    assert res["path_found"] is False
    assert res["primary_path"] is None

    # With max_depth=3, it must be found.
    res_ok = tracer.trace_flow(source, target, max_depth=3)
    assert res_ok["path_found"] is True
    assert res_ok["primary_path"]["hops"] == 3


def test_multiple_paths_and_ranking(tracer):
    """Test dense cluster where multiple paths connect nodes."""
    source = "0xEE01000000000000000000000000000000000001"
    target = "0xEE05000000000000000000000000000000000005"
    res = tracer.trace_flow(source, target, max_depth=4)

    assert res["path_found"] is True
    assert res["primary_path"] is not None
    # Cluster has direct and intermediate links
    assert len(res["primary_path"]["wallets"]) >= 2
    assert "SUSPICIOUS_CLUSTER" in res["primary_path"]["patterns_encountered"] or "CLUSTER" in res["primary_path"]["patterns_encountered"]


def test_downstream_outflow_discovery(tracer):
    """Test discovering downstream flow when target is None."""
    source = "0x323b5d4c32345ced77393b3530b1eed0f346429d"  # Smurfing split hub
    res = tracer.trace_flow(source, target=None, max_depth=2)

    assert res["path_found"] is True
    assert res["total_destinations_discovered"] >= 8
    assert len(res["destinations"]) >= 8
    # All branches should reach 0xCC... wallets
    dest_wallets = [d["destination_wallet"] for d in res["destinations"]]
    assert any("0xCC00000000000000000000000000000000000001" in w for w in dest_wallets)


def test_deterministic_results(tracer):
    """Test that multiple invocations produce identical results."""
    source = "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    target = "0xDeB94101e4a6eD75d19830Af36691C2817865239"

    res1 = tracer.trace_flow(source, target, max_depth=4)
    res2 = tracer.trace_flow(source, target, max_depth=4)

    assert res1["primary_path"]["path_suspicion_score"] == res2["primary_path"]["path_suspicion_score"]
    assert res1["primary_path"]["total_value"] == res2["primary_path"]["total_value"]
    assert res1["primary_path"]["wallets"] == res2["primary_path"]["wallets"]


def test_cytoscape_graph_structure(tracer):
    """Test that Cytoscape graph nodes and edges have proper highlighting flags."""
    source = "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    target = "0xDeB94101e4a6eD75d19830Af36691C2817865239"
    res = tracer.trace_flow(source, target, max_depth=4)

    graph = res["graph"]
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) >= 4

    # Check source and target node flags
    source_node = next(n for n in graph["nodes"] if n["data"]["id"] == source)
    target_node = next(n for n in graph["nodes"] if n["data"]["id"] == target)
    assert source_node["data"]["is_source"] is True
    assert source_node["data"]["is_path"] is True
    assert target_node["data"]["is_target"] is True
    assert target_node["data"]["is_path"] is True

    # Check path edge flags
    path_edges = [e for e in graph["edges"] if e["data"].get("is_path")]
    assert len(path_edges) == 3
    assert all("hop_number" in e["data"] for e in path_edges)


# ---------------------------------------------------------------------------
# Integration Tests — FastAPI Endpoints
# ---------------------------------------------------------------------------

def test_api_flow_trace_success(client):
    """Test GET /flow/trace with valid source and target."""
    resp = client.get(
        "/flow/trace",
        params={
            "source": "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66",
            "target": "0xDeB94101e4a6eD75d19830Af36691C2817865239",
            "max_depth": 4,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path_found"] is True
    assert data["primary_path"]["hops"] == 3
    assert len(data["graph"]["nodes"]) >= 4


def test_api_flow_trace_unspecified_target(client):
    """Test GET /flow/trace without target discovers downstream flows."""
    resp = client.get(
        "/flow/trace",
        params={
            "source": "0x323b5d4c32345ced77393b3530b1eed0f346429d",
            "max_depth": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path_found"] is True
    assert "destinations" in data
    assert len(data["destinations"]) > 0


def test_api_flow_trace_unknown_source_404(client):
    """Test GET /flow/trace returns 404 for unknown source address."""
    resp = client.get(
        "/flow/trace",
        params={"source": "0x9999999999999999999999999999999999999999"},
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_api_flow_trace_invalid_depth_validation(client):
    """Test GET /flow/trace enforces 1 <= max_depth <= 6."""
    resp = client.get(
        "/flow/trace",
        params={
            "source": "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66",
            "max_depth": 10,  # exceeds le=6
        },
    )
    assert resp.status_code == 422


def test_api_case_flow_integration(client):
    """Test GET /investigations/{case_id}/flow anchored to a case."""
    # Create test case
    create_resp = client.post(
        "/investigations",
        json={
            "title": "Rapid Flow Case",
            "target_wallet": "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66",
            "related_wallets": ["0xDeB94101e4a6eD75d19830Af36691C2817865239"],
        },
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["case_id"]

    # Call case flow endpoint without explicit target (should use related_wallets[0])
    resp = client.get(f"/investigations/{case_id}/flow")
    assert resp.status_code == 200
    data = resp.json()
    assert data["path_found"] is True
    assert data["source"] == "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66"
    assert data["target"] == "0xDeB94101e4a6eD75d19830Af36691C2817865239"
    assert data["primary_path"]["hops"] == 3


def test_api_case_flow_unknown_case_404(client):
    """Test GET /investigations/{case_id}/flow returns 404 for nonexistent case."""
    resp = client.get("/investigations/CASE-NONEXISTENT/flow")
    assert resp.status_code == 404
