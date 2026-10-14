"""
ChainSentinel - Canonicalization & SHA-256 Evidence Hashing (Phase 5)

Deterministic JSON canonicalization and SHA-256 hash generation for evidence integrity.
Guarantees that semantically identical evidence produces identical byte streams and digests,
regardless of dictionary key insertion order or formatting differences.
"""

import hashlib
import json
from typing import Any, Dict, Optional


def canonicalize(data: Any) -> str:
    """
    Produce a deterministic, whitespace-normalized, sorted-keys JSON string.
    Ensures identical logical structures produce identical byte streams across platforms.

    Parameters
    ----------
    data : Any JSON-serializable Python data structure (dict, list, str, int, float, bool, None)

    Returns
    -------
    Deterministic canonical JSON string.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def hash_data(data: Any) -> str:
    """
    Compute the SHA-256 hex digest of the canonicalized data representation.

    Parameters
    ----------
    data : Any JSON-serializable structure

    Returns
    -------
    64-character lowercase hexadecimal SHA-256 digest.
    """
    canonical_bytes = canonicalize(data).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def build_evidence_payload(
    case_id: str,
    evidence_type: str,
    source_ref: str,
    content: Any,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Construct the canonical evidence payload dictionary.
    Keys are strictly defined to guarantee standard forensic hashing.
    """
    return {
        "case_id": case_id,
        "content": content,
        "evidence_type": evidence_type,
        "metadata": metadata or {},
        "source_ref": source_ref,
    }


def compute_evidence_hash(
    case_id: str,
    evidence_type: str,
    source_ref: str,
    content: Any,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Compute the SHA-256 digest of an evidence record payload.
    """
    payload = build_evidence_payload(
        case_id=case_id,
        evidence_type=evidence_type,
        source_ref=source_ref,
        content=content,
        metadata=metadata,
    )
    return hash_data(payload)


def verify_evidence_hash(
    stored_hash: str,
    case_id: str,
    evidence_type: str,
    source_ref: str,
    content: Any,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Verify whether the current evidence content matches the recorded SHA-256 hash.

    Returns
    -------
    Dict containing verification boolean flags and computed vs stored digests.
    """
    computed = compute_evidence_hash(
        case_id=case_id,
        evidence_type=evidence_type,
        source_ref=source_ref,
        content=content,
        metadata=metadata,
    )
    is_valid = (computed.lower() == stored_hash.lower())
    return {
        "valid": is_valid,
        "tampered": not is_valid,
        "stored_hash": stored_hash,
        "computed_hash": computed,
    }
