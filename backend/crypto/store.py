"""
ChainSentinel - Evidence Store (Phase 5)

In-memory store for forensic evidence records with optional JSON file persistence.
Maintains tamper-evident records associated with investigation cases.
Follows the same singleton and persistence pattern as InvestigationCaseStore.
"""

import json
import os
from typing import Dict, List, Optional

try:
    from backend.crypto.models import EvidenceRecord
    from backend.crypto.canonical import verify_evidence_hash
except (ImportError, ModuleNotFoundError):
    from .models import EvidenceRecord
    from .canonical import verify_evidence_hash

# Path for optional JSON persistence, relative to this file's directory
_STORE_FILE = os.path.join(os.path.dirname(__file__), "evidence.json")


class EvidenceStore:
    """
    In-memory dictionary store for EvidenceRecord entities with disk persistence.
    Thread-safe for single-worker Uvicorn (MVP pattern).
    """

    def __init__(self) -> None:
        self._records: Dict[str, EvidenceRecord] = {}
        self._load_from_disk()

    # ──────────────────────────────────────────────────────────────
    # CRUD Operations
    # ──────────────────────────────────────────────────────────────

    def create(self, record: EvidenceRecord) -> EvidenceRecord:
        """
        Store a new evidence record.
        Raises ValueError if evidence_id already exists.
        """
        if record.evidence_id in self._records:
            raise ValueError(f"Evidence {record.evidence_id} already exists.")
        self._records[record.evidence_id] = record
        self._save_to_disk()
        return record

    def get(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """Return evidence record by ID or None if not found."""
        return self._records.get(evidence_id)

    def list_by_case(self, case_id: str) -> List[EvidenceRecord]:
        """
        Return all evidence records belonging to a case,
        ordered chronologically by created_at.
        """
        return sorted(
            [r for r in self._records.values() if r.case_id == case_id],
            key=lambda r: (r.created_at, r.evidence_id),
        )

    def list_all(self) -> List[EvidenceRecord]:
        """Return all evidence records across all cases."""
        return sorted(
            self._records.values(),
            key=lambda r: (r.created_at, r.evidence_id),
        )

    def count(self) -> int:
        """Return total evidence count in the store."""
        return len(self._records)

    def count_by_case(self, case_id: str) -> int:
        """Return count of evidence records bound to a specific case."""
        return sum(1 for r in self._records.values() if r.case_id == case_id)

    def verify(self, evidence_id: str) -> Optional[Dict]:
        """
        Verify the integrity of a stored evidence record.
        Returns verification result dictionary or None if record does not exist.
        """
        record = self.get(evidence_id)
        if record is None:
            return None

        result = verify_evidence_hash(
            stored_hash=record.evidence_hash,
            case_id=record.case_id,
            evidence_type=record.evidence_type,
            source_ref=record.source_ref,
            content=record.content,
            metadata=record.metadata,
        )
        result["evidence_id"] = record.evidence_id
        result["case_id"] = record.case_id
        return result

    def clear(self) -> None:
        """Reset the store in-memory and delete persistence file (for test isolation)."""
        self._records.clear()
        if os.path.exists(_STORE_FILE):
            try:
                os.remove(_STORE_FILE)
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────

    def _save_to_disk(self) -> None:
        """Persist current records to JSON file."""
        try:
            data = [r.to_dict() for r in self._records.values()]
            with open(_STORE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # persistence failure is non-fatal for MVP

    def _load_from_disk(self) -> None:
        """Load evidence records from JSON file if it exists."""
        if not os.path.exists(_STORE_FILE):
            return
        try:
            with open(_STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                record = EvidenceRecord.from_dict(item)
                self._records[record.evidence_id] = record
        except Exception:
            self._records = {}


# ──────────────────────────────────────────────────────────────────
# Module-level singleton — import this everywhere
# ──────────────────────────────────────────────────────────────────
EVIDENCE_STORE = EvidenceStore()
