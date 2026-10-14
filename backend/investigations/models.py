"""
ChainSentinel - Investigation Case Models

Data structures for the investigation workflow.
An InvestigationCase captures an investigator's working hypothesis
about a suspicious wallet or transaction cluster.

These models are intentionally simple for MVP: plain Python dataclasses
serialisable to/from dicts. No ORM needed; the store layer handles persistence.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


class CaseStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class InvestigationCase:
    """
    A single investigation case opened by an analyst.

    Fields
    ------
    case_id         Deterministic short ID derived from target_wallet + created_at.
    title           Short, human-readable case title.
    target_wallet   Primary wallet under investigation (the anchor address).
    status          CaseStatus.OPEN or CaseStatus.CLOSED.
    notes           Free-text analyst observations.
    alert_ids       Alert IDs imported into this case from the detection engine.
    related_wallets Additional wallets the investigator has tagged.
    created_at      ISO-8601 UTC creation timestamp.
    updated_at      ISO-8601 UTC last-modified timestamp.
    """
    case_id: str
    title: str
    target_wallet: str
    status: str                       # CaseStatus constant
    notes: str
    alert_ids: List[str]              # alert_ids from detection engine
    related_wallets: List[str]        # additional tagged wallets
    created_at: str                   # ISO-8601 UTC
    updated_at: str                   # ISO-8601 UTC

    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "target_wallet": self.target_wallet,
            "status": self.status,
            "notes": self.notes,
            "alert_ids": self.alert_ids,
            "related_wallets": self.related_wallets,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "InvestigationCase":
        return cls(
            case_id=data["case_id"],
            title=data["title"],
            target_wallet=data["target_wallet"],
            status=data.get("status", CaseStatus.OPEN),
            notes=data.get("notes", ""),
            alert_ids=data.get("alert_ids", []),
            related_wallets=data.get("related_wallets", []),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


def generate_case_id(target_wallet: str, created_at: str) -> str:
    """
    Produce a short case ID from the target wallet + timestamp + entropy.
    Format: CASE-<8 hex chars>
    Example: CASE-3f7a91b2
    """
    raw = f"{target_wallet}:{created_at}:{uuid.uuid4().hex[:8]}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:8]
    return f"CASE-{digest}"


@dataclass
class InvestigationTimelineEvent:
    """
    A single chronological audit event in an investigation case lifecycle.
    """
    event_id: str
    case_id: str
    event_type: str        # e.g. CASE_CREATED, STATUS_CHANGED, NOTES_UPDATED, EVIDENCE_ANCHORED, INTEGRITY_VERIFIED
    title: str
    description: str
    timestamp: str         # ISO-8601 UTC
    actor: str             # e.g. "Analyst", "Integrity Engine"
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "case_id": self.case_id,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "InvestigationTimelineEvent":
        return cls(
            event_id=data["event_id"],
            case_id=data["case_id"],
            event_type=data["event_type"],
            title=data["title"],
            description=data["description"],
            timestamp=data["timestamp"],
            actor=data.get("actor", "Analyst"),
            metadata=data.get("metadata", {}),
        )


def generate_event_id(case_id: str, event_type: str, timestamp: str) -> str:
    """
    Produce a deterministic event ID.
    Format: EVT-<8 hex chars>
    """
    raw = f"{case_id}:{event_type}:{timestamp}:{uuid.uuid4().hex[:8]}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:8]
    return f"EVT-{digest}"

