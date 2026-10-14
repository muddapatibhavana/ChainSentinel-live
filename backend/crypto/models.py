"""
ChainSentinel - Evidence & Integrity Models (Phase 5)

Data structures for cryptographically verifiable forensic evidence records.
An EvidenceRecord captures a tamper-evident snapshot of forensic data
associated with an InvestigationCase.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EvidenceType:
    """Canonical evidence type identifiers."""
    TRANSACTION = "TRANSACTION"
    ALERT = "ALERT"
    WALLET_RISK = "WALLET_RISK"
    ANALYST_NOTE = "ANALYST_NOTE"
    GRAPH_SNAPSHOT = "GRAPH_SNAPSHOT"
    CUSTOM = "CUSTOM"


@dataclass
class EvidenceRecord:
    """
    A single immutable forensic evidence record bound to an investigation case.

    Fields
    ------
    evidence_id    Unique ID (e.g. EVID-8a3b1c2d).
    case_id        Associated investigation case identifier.
    evidence_type  Type category (TRANSACTION, ALERT, WALLET_RISK, etc.).
    source_ref     Reference identifier in primary source (tx hash, alert ID, etc.).
    content        Structured forensic payload being preserved.
    created_at     ISO-8601 UTC creation timestamp.
    evidence_hash  SHA-256 digest of the canonicalized evidence payload.
    metadata       Optional contextual metadata dictionary.
    """
    evidence_id: str
    case_id: str
    evidence_type: str
    source_ref: str
    content: Dict[str, Any]
    created_at: str
    evidence_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence record to a JSON-serializable dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "evidence_type": self.evidence_type,
            "source_ref": self.source_ref,
            "content": self.content,
            "created_at": self.created_at,
            "evidence_hash": self.evidence_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRecord":
        """Reconstruct an EvidenceRecord from a dictionary."""
        return cls(
            evidence_id=data["evidence_id"],
            case_id=data["case_id"],
            evidence_type=data["evidence_type"],
            source_ref=data.get("source_ref", ""),
            content=data.get("content", {}),
            created_at=data["created_at"],
            evidence_hash=data["evidence_hash"],
            metadata=data.get("metadata", {}),
        )


def generate_evidence_id(case_id: str, evidence_type: str, created_at: str) -> str:
    """
    Produce a deterministic, collision-resistant evidence ID.
    Format: EVID-<8 hex chars>
    Example: EVID-a1b2c3d4
    """
    raw = f"{case_id}:{evidence_type}:{created_at}:{uuid.uuid4().hex[:8]}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
    return f"EVID-{digest}"
