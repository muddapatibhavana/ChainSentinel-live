"""
ChainSentinel - Detection Engine Shared Models
Typed data structures for detectors, alerts, and risk assessments.
All detectors return Alert or DetectionResult objects from this module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Canonical alert pattern identifiers
# ---------------------------------------------------------------------------
class PatternType:
    CIRCULAR_TRANSACTION = "CIRCULAR_TRANSACTION"
    RAPID_MOVEMENT = "RAPID_MOVEMENT"
    BURST = "TRANSACTION_BURST"
    FAN_OUT = "FAN_OUT_SPLIT"
    FAN_IN = "FAN_IN_RECOMBINATION"
    SUSPICIOUS_CLUSTER = "SUSPICIOUS_CLUSTER"


# ---------------------------------------------------------------------------
# Severity levels — ordered LOW < MEDIUM < HIGH < CRITICAL
# ---------------------------------------------------------------------------
class Severity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Transaction:
    """
    Normalised internal representation of a blockchain transaction.
    Created from a raw dict row loaded by data/loader.py.
    """
    tx_id: str
    from_wallet: str
    to_wallet: str
    amount: float
    timestamp: datetime          # always tz-aware UTC
    status: str
    gas_fee: float
    category_label: str
    description: str

    @classmethod
    def from_dict(cls, row: Dict) -> "Transaction":
        """Parse a raw loader dict into a typed Transaction."""
        ts_str = row["timestamp"]
        # Handle ISO 8601 with +00:00 offset
        if ts_str.endswith("+00:00"):
            ts_str = ts_str.replace("+00:00", "+0000")
        ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S%z")
        return cls(
            tx_id=row["tx_id"],
            from_wallet=row["from_wallet"],
            to_wallet=row["to_wallet"],
            amount=float(row["amount"]),
            timestamp=ts,
            status=row.get("status", "SUCCESS"),
            gas_fee=float(row.get("gas_fee", 0.002)),
            category_label=row.get("category_label", "normal"),
            description=row.get("description", ""),
        )

    def to_dict(self) -> Dict:
        return {
            "tx_id": self.tx_id,
            "from_wallet": self.from_wallet,
            "to_wallet": self.to_wallet,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "gas_fee": self.gas_fee,
            "category_label": self.category_label,
            "description": self.description,
        }


@dataclass
class Alert:
    """
    A single suspicious activity alert raised by a detector.
    Contains enough information for the frontend to render an explanation.
    """
    alert_id: str                      # deterministic: sha256(pattern+wallets+txids)
    pattern: str                       # PatternType constant
    severity: str                      # Severity constant
    wallets: List[str]                 # wallets implicated (ordered for paths)
    transaction_ids: List[str]         # tx hashes implicated
    total_amount: float                # total ETH moved through pattern
    time_span_seconds: float           # duration of the pattern window
    explanation: str                   # plain-English explanation for investigators
    metadata: Dict = field(default_factory=dict)  # pattern-specific extra info

    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "pattern": self.pattern,
            "severity": self.severity,
            "wallets": self.wallets,
            "transaction_ids": self.transaction_ids,
            "total_amount": round(self.total_amount, 4),
            "time_span_seconds": round(self.time_span_seconds, 1),
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass
class WalletRiskAssessment:
    """
    Aggregated risk score and alert summary for a single wallet.
    """
    wallet_id: str
    risk_score: int            # 0–100 cumulative score
    risk_level: str            # Severity constant
    alert_count: int
    pattern_types: List[str]
    alerts: List[Dict]
    explanation: str

    def to_dict(self) -> Dict:
        return {
            "wallet_id": self.wallet_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "alert_count": self.alert_count,
            "pattern_types": self.pattern_types,
            "alerts": self.alerts,
            "explanation": self.explanation,
        }


@dataclass
class DetectionSummary:
    """
    Top-level summary returned by DetectionEngine.detect_all().
    """
    total_transactions: int
    total_wallets: int
    total_alerts: int
    alerts_by_pattern: Dict[str, int]
    alerts_by_severity: Dict[str, int]
    alerts: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "total_transactions": self.total_transactions,
            "total_wallets": self.total_wallets,
            "total_alerts": self.total_alerts,
            "alerts_by_pattern": self.alerts_by_pattern,
            "alerts_by_severity": self.alerts_by_severity,
            "alerts": self.alerts,
        }
