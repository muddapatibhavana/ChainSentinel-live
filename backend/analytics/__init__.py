"""
ChainSentinel - Analytics & Intelligence Package
Phase 8 - Behavioral profiling, alert correlation, and strategic intelligence.
"""

from .models import (
    BehaviorClassification,
    ClassificationType,
    CrossPatternCorrelation,
    InvestigationIntelligence,
    PriorityLevel,
    WalletBehaviorProfile,
    WalletIntelligence,
)
from .profiler import WalletBehaviorProfiler
from .correlator import AlertCorrelator
from .intelligence import IntelligenceEngine

__all__ = [
    "BehaviorClassification",
    "ClassificationType",
    "CrossPatternCorrelation",
    "InvestigationIntelligence",
    "PriorityLevel",
    "WalletBehaviorProfile",
    "WalletIntelligence",
    "WalletBehaviorProfiler",
    "AlertCorrelator",
    "IntelligenceEngine",
]
