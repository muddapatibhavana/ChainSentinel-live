"""
ChainSentinel - Phase 5 Cryptographic Evidence & Merkle Verification Tests

Comprehensive test suite verifying:
- Deterministic JSON canonicalization (ordering, primitives, nesting)
- SHA-256 evidence hashing and tamper detection
- EvidenceRecord models and EvidenceStore persistence
- Merkle Tree computation (empty, 1 leaf, 2 leaves, odd leaves, multiple leaves)
- Merkle audit proofs and cryptographic verification
- Full REST API endpoints for evidence creation, retrieval, listing, verification, and Merkle root auditing
"""

import hashlib
import json
import pytest
from starlette.testclient import TestClient

from backend.main import app, DATASET
from backend.investigations.models import InvestigationCase, CaseStatus, generate_case_id
from backend.investigations.store import CASE_STORE
from backend.crypto.models import (
    EvidenceRecord,
    EvidenceType,
    generate_evidence_id,
)
from backend.crypto.canonical import (
    canonicalize,
    hash_data,
    compute_evidence_hash,
    verify_evidence_hash,
)
from backend.crypto.merkle import (
    MerkleTree,
    compute_merkle_root,
    hash_pair,
    EMPTY_MERKLE_ROOT,
)
from backend.crypto.store import EVIDENCE_STORE, EvidenceStore


@pytest.fixture(autouse=True)
def clean_stores():
    """Ensure clean case and evidence stores before and after each test."""
    CASE_STORE.clear()
    EVIDENCE_STORE.clear()
    yield
    CASE_STORE.clear()
    EVIDENCE_STORE.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_case():
    """Create and return a sample investigation case."""
    now_iso = "2026-10-08T12:00:00+00:00"
    target = DATASET[0]["from_wallet"]
    case_id = generate_case_id(target, now_iso)
    case = InvestigationCase(
        case_id=case_id,
        title="Forensic Evidence Test Case",
        target_wallet=target,
        status=CaseStatus.OPEN,
        notes="Testing evidence anchors",
        alert_ids=["ALT-sample-01"],
        related_wallets=[DATASET[0]["to_wallet"]],
        created_at=now_iso,
        updated_at=now_iso,
    )
    return CASE_STORE.create(case)


# ──────────────────────────────────────────────────────────────────
# 1. Canonicalization Tests
# ──────────────────────────────────────────────────────────────────

def test_canonicalize_primitives():
    """Canonicalization handles primitives without whitespace variance."""
    assert canonicalize(123) == "123"
    assert canonicalize("hello") == '"hello"'
    assert canonicalize(True) == "true"
    assert canonicalize(None) == "null"
    assert canonicalize([3, 2, 1]) == "[3,2,1]"


def test_canonicalize_dict_key_ordering():
    """The same logical dictionary with different key insertion orders produces identical canonical string."""
    d1 = {"wallet": "0x123", "amount": 25.5, "status": "CONFIRMED"}
    d2 = {"status": "CONFIRMED", "amount": 25.5, "wallet": "0x123"}
    d3 = {"amount": 25.5, "wallet": "0x123", "status": "CONFIRMED"}

    canon1 = canonicalize(d1)
    canon2 = canonicalize(d2)
    canon3 = canonicalize(d3)

    assert canon1 == canon2 == canon3
    assert canon1 == '{"amount":25.5,"status":"CONFIRMED","wallet":"0x123"}'


def test_canonicalize_nested_structures():
    """Nested dictionaries and lists are recursively key-sorted and whitespace-stripped."""
    nested1 = {
        "outer_b": {"inner_z": 1, "inner_a": 2},
        "outer_a": [{"key_2": "val2", "key_1": "val1"}],
    }
    nested2 = {
        "outer_a": [{"key_1": "val1", "key_2": "val2"}],
        "outer_b": {"inner_a": 2, "inner_z": 1},
    }

    assert canonicalize(nested1) == canonicalize(nested2)


def test_canonicalize_changed_data_produces_different_string():
    """Modifying content produces a distinct canonical representation."""
    d1 = {"wallet": "0x123", "amount": 25}
    d2 = {"wallet": "0x123", "amount": 26}
    assert canonicalize(d1) != canonicalize(d2)


# ──────────────────────────────────────────────────────────────────
# 2. SHA-256 Hashing & Verification Tests
# ──────────────────────────────────────────────────────────────────

def test_hash_data_deterministic():
    """hash_data produces consistent 64-char lowercase hex digest."""
    d1 = {"b": 2, "a": 1}
    d2 = {"a": 1, "b": 2}

    h1 = hash_data(d1)
    h2 = hash_data(d2)

    assert h1 == h2
    assert len(h1) == 64
    assert h1 == h1.lower()
    # Canonical string is {"a":1,"b":2}
    expected = hashlib.sha256(b'{"a":1,"b":2}').hexdigest()
    assert h1 == expected


def test_hash_data_not_using_builtin_hash():
    """Verification confirms hashlib.sha256 standard digests rather than Python hash()."""
    empty_dict_hash = hash_data({})
    # Canonical string for {} is "{}"
    expected = hashlib.sha256(b"{}").hexdigest()
    assert empty_dict_hash == expected


def test_compute_evidence_hash_deterministic():
    """Evidence hash is identical across key order variations in content and metadata."""
    content1 = {"tx_id": "0xabc", "amount": 100.0}
    content2 = {"amount": 100.0, "tx_id": "0xabc"}
    meta1 = {"analyst": "alice", "confidence": 0.95}
    meta2 = {"confidence": 0.95, "analyst": "alice"}

    h1 = compute_evidence_hash("CASE-1", "TRANSACTION", "0xabc", content1, meta1)
    h2 = compute_evidence_hash("CASE-1", "TRANSACTION", "0xabc", content2, meta2)

    assert h1 == h2


def test_tampered_content_fails_verification():
    """Tampering with evidence content causes verification to fail."""
    content = {"tx_id": "0xabc", "amount": 100.0}
    original_hash = compute_evidence_hash("CASE-1", "TRANSACTION", "0xabc", content)

    # Intact check
    res_intact = verify_evidence_hash(
        stored_hash=original_hash,
        case_id="CASE-1",
        evidence_type="TRANSACTION",
        source_ref="0xabc",
        content=content,
    )
    assert res_intact["valid"] is True
    assert res_intact["tampered"] is False

    # Tampered content
    tampered_content = {"tx_id": "0xabc", "amount": 999.0}
    res_tampered = verify_evidence_hash(
        stored_hash=original_hash,
        case_id="CASE-1",
        evidence_type="TRANSACTION",
        source_ref="0xabc",
        content=tampered_content,
    )
    assert res_tampered["valid"] is False
    assert res_tampered["tampered"] is True
    assert res_tampered["stored_hash"] != res_tampered["computed_hash"]


# ──────────────────────────────────────────────────────────────────
# 3. Evidence Models & Store Unit Tests
# ──────────────────────────────────────────────────────────────────

def test_generate_evidence_id_format():
    """Evidence ID follows 'EVID-<8 hex chars>' convention."""
    eid = generate_evidence_id("CASE-1234", "TRANSACTION", "2026-10-08T12:00:00+00:00")
    assert eid.startswith("EVID-")
    assert len(eid) == 13  # "EVID-" (5) + 8 = 13


def test_generate_evidence_id_uniqueness():
    """Repeated calls produce unique evidence IDs."""
    ids = {generate_evidence_id("CASE-1", "ALERT", "2026-10-08T12:00:00+00:00") for _ in range(50)}
    assert len(ids) == 50


def test_evidence_record_dict_roundtrip():
    """EvidenceRecord serialization to and from dict preserves all fields."""
    rec = EvidenceRecord(
        evidence_id="EVID-11223344",
        case_id="CASE-9999",
        evidence_type=EvidenceType.ALERT,
        source_ref="ALT-circ-01",
        content={"alert_id": "ALT-circ-01", "pattern": "CIRCULAR_TRANSACTION"},
        created_at="2026-10-08T12:00:00+00:00",
        evidence_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        metadata={"tagged_by": "lead_investigator"},
    )
    d = rec.to_dict()
    restored = EvidenceRecord.from_dict(d)
    assert restored.evidence_id == rec.evidence_id
    assert restored.case_id == rec.case_id
    assert restored.content == rec.content
    assert restored.evidence_hash == rec.evidence_hash
    assert restored.metadata == rec.metadata


def test_evidence_store_crud():
    """EvidenceStore handles creation, retrieval, listing, and counting."""
    store = EvidenceStore()
    store.clear()

    rec1 = EvidenceRecord(
        evidence_id="EVID-00000001",
        case_id="CASE-A",
        evidence_type=EvidenceType.TRANSACTION,
        source_ref="0xtx1",
        content={"amount": 10},
        created_at="2026-10-08T10:00:00+00:00",
        evidence_hash="h1",
    )
    rec2 = EvidenceRecord(
        evidence_id="EVID-00000002",
        case_id="CASE-A",
        evidence_type=EvidenceType.ALERT,
        source_ref="ALT-1",
        content={"pattern": "BURST"},
        created_at="2026-10-08T11:00:00+00:00",
        evidence_hash="h2",
    )
    rec3 = EvidenceRecord(
        evidence_id="EVID-00000003",
        case_id="CASE-B",
        evidence_type=EvidenceType.ANALYST_NOTE,
        source_ref="note-1",
        content={"text": "Review complete"},
        created_at="2026-10-08T12:00:00+00:00",
        evidence_hash="h3",
    )

    store.create(rec1)
    store.create(rec2)
    store.create(rec3)

    assert store.count() == 3
    assert store.count_by_case("CASE-A") == 2
    assert store.count_by_case("CASE-B") == 1
    assert store.get("EVID-00000001") == rec1

    # Duplicate ID raises ValueError
    with pytest.raises(ValueError):
        store.create(rec1)

    case_a_recs = store.list_by_case("CASE-A")
    assert len(case_a_recs) == 2
    assert case_a_recs[0].evidence_id == "EVID-00000001"
    assert case_a_recs[1].evidence_id == "EVID-00000002"


def test_evidence_store_verify_in_memory():
    """EvidenceStore verification detects in-memory tampering."""
    store = EvidenceStore()
    store.clear()

    content = {"wallet": "0x123", "risk": 85}
    ehash = compute_evidence_hash("CASE-X", "WALLET_RISK", "0x123", content)
    rec = EvidenceRecord(
        evidence_id="EVID-test-verify",
        case_id="CASE-X",
        evidence_type="WALLET_RISK",
        source_ref="0x123",
        content=content,
        created_at="2026-10-08T12:00:00+00:00",
        evidence_hash=ehash,
    )
    store.create(rec)

    # Intact
    v1 = store.verify("EVID-test-verify")
    assert v1["valid"] is True
    assert v1["tampered"] is False

    # Nonexistent record returns None
    assert store.verify("EVID-nonexistent") is None

    # Simulate malicious modification
    store._records["EVID-test-verify"].content["risk"] = 10
    v2 = store.verify("EVID-test-verify")
    assert v2["valid"] is False
    assert v2["tampered"] is True


# ──────────────────────────────────────────────────────────────────
# 4. Merkle Tree Tests
# ──────────────────────────────────────────────────────────────────

def test_merkle_tree_empty():
    """Empty collection produces canonical empty Merkle root."""
    tree = MerkleTree([])
    assert tree.root == EMPTY_MERKLE_ROOT
    assert compute_merkle_root([]) == EMPTY_MERKLE_ROOT


def test_merkle_tree_single_leaf():
    """Single evidence item produces the leaf hash itself as the root."""
    h = hashlib.sha256(b"leaf1").hexdigest()
    tree = MerkleTree([h])
    assert tree.root == h
    assert compute_merkle_root([h]) == h


def test_merkle_tree_two_leaves():
    """Two leaves combine into hash_pair(leaf0, leaf1)."""
    h_a = hashlib.sha256(b"leafA").hexdigest()
    h_b = hashlib.sha256(b"leafB").hexdigest()

    # Leaves are lexicographically sorted by default
    expected_leaves = sorted([h_a, h_b])
    expected_root = hash_pair(expected_leaves[0], expected_leaves[1])

    tree = MerkleTree([h_a, h_b])
    assert tree.root == expected_root


def test_merkle_tree_odd_number_of_leaves():
    """
    Odd leaf count duplicates the trailing leaf to balance the level (Bitcoin/RFC specification).
    Example with 3 leaves: [L0, L1, L2]
    Level 0 expanded: [L0, L1, L2, L2]
    Level 1: [hash_pair(L0, L1), hash_pair(L2, L2)]
    Root: hash_pair(L0L1, L2L2)
    """
    h1 = hashlib.sha256(b"1").hexdigest()
    h2 = hashlib.sha256(b"2").hexdigest()
    h3 = hashlib.sha256(b"3").hexdigest()

    leaves = sorted([h1, h2, h3])
    expected_p1 = hash_pair(leaves[0], leaves[1])
    expected_p2 = hash_pair(leaves[2], leaves[2])
    expected_root = hash_pair(expected_p1, expected_p2)

    tree = MerkleTree([h1, h2, h3])
    assert tree.root == expected_root
    assert len(tree.levels) == 3


def test_merkle_tree_multiple_leaves_deterministic():
    """Regardless of order passed in, leaves are sorted and produce the identical Merkle root."""
    hashes = [hashlib.sha256(f"item_{i}".encode()).hexdigest() for i in range(7)]

    # Reverse order and shuffled order
    tree1 = MerkleTree(hashes)
    tree2 = MerkleTree(list(reversed(hashes)))
    tree3 = MerkleTree([hashes[3], hashes[0], hashes[6], hashes[1], hashes[4], hashes[2], hashes[5]])

    assert tree1.root == tree2.root == tree3.root


def test_merkle_tree_changed_leaf_changes_root():
    """Altering even a single leaf changes the resulting Merkle root."""
    h1 = hashlib.sha256(b"data_a").hexdigest()
    h2 = hashlib.sha256(b"data_b").hexdigest()
    h3 = hashlib.sha256(b"data_c").hexdigest()

    root_original = compute_merkle_root([h1, h2, h3])

    h3_tampered = hashlib.sha256(b"data_c_tampered").hexdigest()
    root_tampered = compute_merkle_root([h1, h2, h3_tampered])

    assert root_original != root_tampered


def test_merkle_tree_inclusion_proof_and_verification():
    """Cryptographic inclusion proofs succeed for every leaf in both even and odd trees."""
    # Test with 5 leaves (odd)
    hashes = [hashlib.sha256(f"proof_leaf_{i}".encode()).hexdigest() for i in range(5)]
    tree = MerkleTree(hashes)

    for h in tree.leaves:
        proof = tree.get_proof(h)
        assert proof is not None
        # Verify valid proof
        assert MerkleTree.verify_proof(h, proof, tree.root) is True

        # Tampered proof hash fails
        bad_proof = [{"position": step["position"], "hash": "0" * 64} for step in proof]
        assert MerkleTree.verify_proof(h, bad_proof, tree.root) is False

        # Wrong target leaf fails
        assert MerkleTree.verify_proof("1" * 64, proof, tree.root) is False


def test_merkle_tree_proof_for_unknown_leaf():
    """Requesting proof for a hash not in tree returns None."""
    tree = MerkleTree([hashlib.sha256(b"leaf").hexdigest()])
    assert tree.get_proof("f" * 64) is None


# ──────────────────────────────────────────────────────────────────
# 5. REST API Tests
# ──────────────────────────────────────────────────────────────────

def test_api_create_evidence_success(client, sample_case):
    """POST /investigations/{case_id}/evidence creates an immutable evidence record (201)."""
    payload = {
        "evidence_type": "TRANSACTION",
        "source_ref": DATASET[0]["tx_id"],
        "content": {
            "tx_id": DATASET[0]["tx_id"],
            "amount": DATASET[0]["amount"],
            "from_wallet": DATASET[0]["from_wallet"],
            "to_wallet": DATASET[0]["to_wallet"],
        },
        "metadata": {"analyst": "investigator_01"},
    }

    res = client.post(f"/investigations/{sample_case.case_id}/evidence", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["case_id"] == sample_case.case_id
    assert data["evidence_type"] == "TRANSACTION"
    assert data["source_ref"] == DATASET[0]["tx_id"]
    assert data["evidence_id"].startswith("EVID-")
    assert len(data["evidence_hash"]) == 64
    assert data["content"]["amount"] == DATASET[0]["amount"]
    assert data["metadata"]["analyst"] == "investigator_01"


def test_api_create_evidence_case_not_found(client):
    """POST /investigations/{case_id}/evidence returns 404 for nonexistent case."""
    res = client.post("/investigations/CASE-nonexistent/evidence", json={
        "evidence_type": "TRANSACTION",
        "source_ref": "0x123",
        "content": {"amount": 10},
    })
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_api_create_evidence_missing_type(client, sample_case):
    """POST /investigations/{case_id}/evidence validates required evidence_type."""
    res = client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "",
        "source_ref": "0x123",
        "content": {"amount": 10},
    })
    assert res.status_code == 400
    assert "evidence_type is required" in res.json()["detail"]


def test_api_list_case_evidence(client, sample_case):
    """GET /investigations/{case_id}/evidence returns all evidence for the case."""
    # Add two evidence items
    client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "ALERT",
        "source_ref": "ALT-1",
        "content": {"pattern": "CIRCULAR_TRANSACTION"},
    })
    client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "WALLET_RISK",
        "source_ref": sample_case.target_wallet,
        "content": {"risk_score": 90},
    })

    res = client.get(f"/investigations/{sample_case.case_id}/evidence")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == sample_case.case_id
    assert data["total"] == 2
    assert len(data["evidence"]) == 2
    types = [e["evidence_type"] for e in data["evidence"]]
    assert "ALERT" in types
    assert "WALLET_RISK" in types


def test_api_list_case_evidence_not_found(client):
    """GET /investigations/{case_id}/evidence returns 404 for nonexistent case."""
    res = client.get("/investigations/CASE-nonexistent/evidence")
    assert res.status_code == 404


def test_api_get_evidence_by_id(client, sample_case):
    """GET /evidence/{evidence_id} retrieves a specific evidence record."""
    create_res = client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "ANALYST_NOTE",
        "source_ref": "analyst-finding-1",
        "content": {"summary": "Cluster ring detected"},
    })
    evidence_id = create_res.json()["evidence_id"]

    res = client.get(f"/evidence/{evidence_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_id"] == evidence_id
    assert data["content"]["summary"] == "Cluster ring detected"


def test_api_get_evidence_not_found(client):
    """GET /evidence/{evidence_id} returns 404 for nonexistent evidence."""
    res = client.get("/evidence/EVID-nonexistent")
    assert res.status_code == 404


def test_api_verify_evidence_intact(client, sample_case):
    """GET /evidence/{evidence_id}/verify returns valid=True and tampered=False."""
    create_res = client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "TRANSACTION",
        "source_ref": "0xtx99",
        "content": {"amount": 50.0},
    })
    evidence_id = create_res.json()["evidence_id"]

    res = client.get(f"/evidence/{evidence_id}/verify")
    assert res.status_code == 200
    data = res.json()

    assert data["evidence_id"] == evidence_id
    assert data["valid"] is True
    assert data["tampered"] is False
    assert data["algorithm"] == "SHA-256"
    assert data["stored_hash"] == data["computed_hash"]


def test_api_verify_evidence_tampered(client, sample_case):
    """Modifying evidence content triggers tampered=True in verification endpoint."""
    create_res = client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "TRANSACTION",
        "source_ref": "0xtx99",
        "content": {"amount": 50.0},
    })
    evidence_id = create_res.json()["evidence_id"]

    # Directly mutate content in the store to simulate database or memory tampering
    EVIDENCE_STORE._records[evidence_id].content["amount"] = 99999.0

    res = client.get(f"/evidence/{evidence_id}/verify")
    assert res.status_code == 200
    data = res.json()

    assert data["evidence_id"] == evidence_id
    assert data["valid"] is False
    assert data["tampered"] is True
    assert data["stored_hash"] != data["computed_hash"]


def test_api_get_case_merkle_root_empty(client, sample_case):
    """GET /investigations/{case_id}/evidence/merkle returns canonical empty root when no evidence added."""
    res = client.get(f"/investigations/{sample_case.case_id}/evidence/merkle")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == sample_case.case_id
    assert data["total_leaves"] == 0
    assert data["merkle_root"] == EMPTY_MERKLE_ROOT
    assert data["odd_leaf_handling"] == "trailing_duplicate"


def test_api_get_case_merkle_root_with_leaves(client, sample_case):
    """GET /investigations/{case_id}/evidence/merkle calculates tree from case evidence."""
    # Add 3 evidence items
    for i in range(3):
        client.post(f"/investigations/{sample_case.case_id}/evidence", json={
            "evidence_type": "TRANSACTION",
            "source_ref": f"0xtx_{i}",
            "content": {"idx": i, "val": i * 10},
        })

    res = client.get(f"/investigations/{sample_case.case_id}/evidence/merkle")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == sample_case.case_id
    assert data["total_leaves"] == 3
    assert len(data["leaf_hashes"]) == 3
    assert len(data["merkle_root"]) == 64


def test_api_verify_case_merkle_root_success(client, sample_case):
    """POST /investigations/{case_id}/evidence/merkle/verify validates matching expected root."""
    for i in range(2):
        client.post(f"/investigations/{sample_case.case_id}/evidence", json={
            "evidence_type": "ALERT",
            "source_ref": f"ALT-{i}",
            "content": {"alert_idx": i},
        })

    # Fetch root
    root_res = client.get(f"/investigations/{sample_case.case_id}/evidence/merkle")
    current_root = root_res.json()["merkle_root"]

    # Verify against correct root
    res = client.post(
        f"/investigations/{sample_case.case_id}/evidence/merkle/verify",
        json={"expected_root": current_root},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == sample_case.case_id
    assert data["valid"] is True
    assert data["root_match"] is True
    assert data["tampered"] is False
    assert data["total_leaves"] == 2
    assert data["intact_leaves_count"] == 2
    assert data["tampered_leaves_count"] == 0


def test_api_verify_case_merkle_root_mismatch(client, sample_case):
    """POST /investigations/{case_id}/evidence/merkle/verify flags mismatched expected root."""
    client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "ALERT",
        "source_ref": "ALT-0",
        "content": {"val": 1},
    })

    res = client.post(
        f"/investigations/{sample_case.case_id}/evidence/merkle/verify",
        json={"expected_root": "0" * 64},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["valid"] is False
    assert data["root_match"] is False
    assert data["tampered"] is True


def test_api_investigation_summary_includes_evidence_count(client, sample_case):
    """GET /investigations/{case_id}/summary enriches response with evidence_count."""
    # Initially 0
    res1 = client.get(f"/investigations/{sample_case.case_id}/summary")
    assert res1.status_code == 200
    assert res1.json()["evidence_count"] == 0

    # Add evidence
    client.post(f"/investigations/{sample_case.case_id}/evidence", json={
        "evidence_type": "TRANSACTION",
        "source_ref": "0x123",
        "content": {"amt": 10},
    })

    res2 = client.get(f"/investigations/{sample_case.case_id}/summary")
    assert res2.status_code == 200
    assert res2.json()["evidence_count"] == 1
