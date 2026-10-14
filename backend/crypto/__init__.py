"""
ChainSentinel Cryptographic Integrity & Evidence Verification Package (Phase 5)

Exports evidence models, deterministic canonicalization, SHA-256 evidence hashing,
Merkle tree generation & verification, and the singleton EvidenceStore.
"""

from .models import EvidenceRecord, EvidenceType, generate_evidence_id
from .canonical import (
    canonicalize,
    hash_data,
    build_evidence_payload,
    compute_evidence_hash,
    verify_evidence_hash,
)
from .merkle import (
    MerkleTree,
    compute_merkle_root,
    hash_pair,
    EMPTY_MERKLE_ROOT,
)
from .store import EvidenceStore, EVIDENCE_STORE

__all__ = [
    "EvidenceRecord",
    "EvidenceType",
    "generate_evidence_id",
    "canonicalize",
    "hash_data",
    "build_evidence_payload",
    "compute_evidence_hash",
    "verify_evidence_hash",
    "MerkleTree",
    "compute_merkle_root",
    "hash_pair",
    "EMPTY_MERKLE_ROOT",
    "EvidenceStore",
    "EVIDENCE_STORE",
]
