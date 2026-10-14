"""
ChainSentinel - Analytics & Intelligence Domain Models
Phase 8 - Behavioral profiling, classification, cross-pattern correlation,
and investigation-level intelligence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class ClassificationType:
    NORMAL = "NORMAL"
    HIGH_VOLUME = "HIGH_VOLUME"
    HIGH_VELOCITY = "HIGH_VELOCITY"
    FAN_OUT = "FAN_OUT"
    FAN_IN = "FAN_IN"
    CIRCULAR = "CIRCULAR"
    MIXER_LIKE = "MIXER_LIKE"
    MULTI_PATTERN = "MULTI_PATTERN"
    HIGH_RISK = "HIGH_RISK"


class PriorityLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class BehaviorClassification:
    """An explainable behavioral tag assigned to a wallet based on observed activity."""
    name: str                       # ClassificationType constant
    label: str                      # Human-readable title
    severity: str                   # LOW | MEDIUM | HIGH | CRITICAL
    description: str                # Plain-English explanation of why it was assigned

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class WalletBehaviorProfile:
    """Comprehensive behavioral metrics calculated from a wallet's transaction history."""
    wallet_id: str
    total_tx_count: int
    inbound_tx_count: int
    outbound_tx_count: int
    inbound_volume: float
    outbound_volume: float
    total_volume: float
    net_flow: float
    unique_counterparties_count: int
    unique_inbound_counterparties_count: int
    unique_outbound_counterparties_count: int
    avg_tx_value: float
    largest_tx_value: float
    first_activity: Optional[datetime]
    last_activity: Optional[datetime]
    active_time_span_seconds: float
    tx_frequency_per_hour: float
    is_burst_participant: bool
    is_fan_out: bool
    is_fan_in: bool
    is_circular: bool
    is_rapid_movement: bool
    is_cluster_participant: bool
    alert_count: int
    high_critical_alert_count: int
    risk_score: float
    risk_level: str
    investigation_priority: str
    classifications: List[BehaviorClassification] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "total_tx_count": self.total_tx_count,
            "inbound_tx_count": self.inbound_tx_count,
            "outbound_tx_count": self.outbound_tx_count,
            "inbound_volume": round(self.inbound_volume, 4),
            "outbound_volume": round(self.outbound_volume, 4),
            "total_volume": round(self.total_volume, 4),
            "net_flow": round(self.net_flow, 4),
            "unique_counterparties_count": self.unique_counterparties_count,
            "unique_inbound_counterparties_count": self.unique_inbound_counterparties_count,
            "unique_outbound_counterparties_count": self.unique_outbound_counterparties_count,
            "avg_tx_value": round(self.avg_tx_value, 4),
            "largest_tx_value": round(self.largest_tx_value, 4),
            "first_activity": self.first_activity.isoformat() if self.first_activity else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "active_time_span_seconds": round(self.active_time_span_seconds, 1),
            "tx_frequency_per_hour": round(self.tx_frequency_per_hour, 2),
            "is_burst_participant": self.is_burst_participant,
            "is_fan_out": self.is_fan_out,
            "is_fan_in": self.is_fan_in,
            "is_circular": self.is_circular,
            "is_rapid_movement": self.is_rapid_movement,
            "is_cluster_participant": self.is_cluster_participant,
            "alert_count": self.alert_count,
            "high_critical_alert_count": self.high_critical_alert_count,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "investigation_priority": self.investigation_priority,
            "classifications": [c.to_dict() for c in self.classifications],
            "signals": self.signals,
        }


@dataclass
class CrossPatternCorrelation:
    """Correlation event where multiple suspicious patterns or signals converge."""
    correlation_id: str
    title: str
    primary_wallet: str
    converging_patterns: List[str]
    alert_ids: List[str]
    time_window_seconds: float
    confidence: str                 # HIGH | MEDIUM | LOW
    severity: str                   # CRITICAL | HIGH | MEDIUM | LOW
    participating_wallets: List[str]
    total_volume_eth: float
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "title": self.title,
            "primary_wallet": self.primary_wallet,
            "converging_patterns": self.converging_patterns,
            "alert_ids": self.alert_ids,
            "time_window_seconds": round(self.time_window_seconds, 1),
            "confidence": self.confidence,
            "severity": self.severity,
            "participating_wallets": self.participating_wallets,
            "total_volume_eth": round(self.total_volume_eth, 4),
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass
class WalletIntelligence:
    """Comprehensive intelligence package for a single wallet."""
    wallet_id: str
    risk_score: float
    risk_level: str
    investigation_priority: str
    behavior_profile: WalletBehaviorProfile
    classifications: List[BehaviorClassification]
    primary_signals: List[str]
    correlated_patterns: List[str]
    correlations: List[CrossPatternCorrelation]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "investigation_priority": self.investigation_priority,
            "behavior_profile": self.behavior_profile.to_dict(),
            "classifications": [c.to_dict() for c in self.classifications],
            "primary_signals": self.primary_signals,
            "correlated_patterns": self.correlated_patterns,
            "correlations": [c.to_dict() for c in self.correlations],
            "explanation": self.explanation,
        }


@dataclass
class InvestigationIntelligence:
    """Investigation-level strategic intelligence dossier."""
    case_id: str
    title: str
    target_wallet: str
    priority: str
    priority_score: float
    target_risk: Dict[str, Any]
    target_behavior: Dict[str, Any]
    total_case_volume_eth: float
    alert_count: int
    high_risk_alert_count: int
    dominant_patterns: List[str]
    suspicious_counterparties_count: int
    suspicious_counterparties: List[Dict[str, Any]]
    correlations: List[CrossPatternCorrelation]
    evidence_count: int
    evidence_integrity_status: str
    executive_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "target_wallet": self.target_wallet,
            "priority": self.priority,
            "priority_score": round(self.priority_score, 1),
            "target_risk": self.target_risk,
            "target_behavior": self.target_behavior,
            "total_case_volume_eth": round(self.total_case_volume_eth, 4),
            "alert_count": self.alert_count,
            "high_risk_alert_count": self.high_risk_alert_count,
            "dominant_patterns": self.dominant_patterns,
            "suspicious_counterparties_count": self.suspicious_counterparties_count,
            "suspicious_counterparties": self.suspicious_counterparties,
            "correlations": [c.to_dict() for c in self.correlations],
            "evidence_count": self.evidence_count,
            "evidence_integrity_status": self.evidence_integrity_status,
            "executive_summary": self.executive_summary,
        }
