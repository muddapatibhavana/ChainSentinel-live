"""
ChainSentinel - Central Intelligence & Analytics Engine
Phase 8 - Unified intelligence facade combining behavioral profiling,
alert correlation, risk explanation, and investigation-level intelligence.
"""

from typing import Any, Dict, List, Optional

from ..detection.models import Transaction, Alert, Severity
from ..investigations.store import CASE_STORE
from ..crypto.store import EVIDENCE_STORE
from ..crypto.merkle import compute_merkle_root
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


class IntelligenceEngine:
    """
    Central analytical facade for ChainSentinel.
    Provides behavioral analytics, cross-pattern correlations,
    and investigation-level intelligence dossiers.
    """

    def __init__(self, transactions: List[Transaction], detection_engine) -> None:
        self._transactions: List[Transaction] = transactions
        self._detection_engine = detection_engine
        self._profiler = WalletBehaviorProfiler(transactions, detection_engine)
        self._alerts_cache: Optional[List[Alert]] = None
        self._correlator: Optional[AlertCorrelator] = None
        self._profiles_cache: Optional[Dict[str, WalletBehaviorProfile]] = None

    def _get_alerts(self) -> List[Alert]:
        if self._alerts_cache is None:
            self._alerts_cache = self._detection_engine.detect_all()
        return self._alerts_cache

    def _get_correlator(self) -> AlertCorrelator:
        if self._correlator is None:
            self._correlator = AlertCorrelator(self._get_alerts(), self._transactions)
        return self._correlator

    @property
    def known_wallets(self) -> set:
        return self._profiler.all_wallets

    # ------------------------------------------------------------------
    # 1. Wallet Intelligence & Explanation
    # ------------------------------------------------------------------

    def get_wallet_intelligence(self, wallet_id: str) -> Optional[WalletIntelligence]:
        """
        Generate detailed behavioral intelligence and explainable risk context for a wallet.
        """
        if wallet_id not in self.known_wallets:
            return None

        profile = self._profiler.profile_wallet(wallet_id)
        correlator = self._get_correlator()
        correlations = correlator.correlate_for_wallet(wallet_id)

        correlated_patterns = sorted(list(set(
            p for c in correlations for p in c.converging_patterns
        )))

        # Build comprehensive narrative explanation
        primary_signals = list(profile.signals)
        class_names = [c.label for c in profile.classifications]

        if profile.classifications and profile.classifications[0].name != ClassificationType.NORMAL:
            explanation = (
                f"Wallet {wallet_id[:10]}... is evaluated as {profile.investigation_priority} PRIORITY "
                f"with a forensic risk score of {profile.risk_score}/100 ({profile.risk_level}). "
                f"Identified behavioral classifications: {', '.join(class_names)}. "
                f"Total transaction volume is {profile.total_volume:.2f} ETH across {profile.total_tx_count} transfers. "
            )
            if correlations:
                explanation += f"Exhibits {len(correlations)} cross-pattern convergence event(s) across {len(correlated_patterns)} pattern types."
            else:
                explanation += "No multi-pattern topological convergence detected."
        else:
            explanation = (
                f"Wallet {wallet_id[:10]}... demonstrates standard operating activity with a risk score of "
                f"{profile.risk_score}/100 ({profile.risk_level}). Total turnover: {profile.total_volume:.2f} ETH across "
                f"{profile.total_tx_count} transfer(s) with {profile.unique_counterparties_count} counterparty/counterparties."
            )

        return WalletIntelligence(
            wallet_id=wallet_id,
            risk_score=profile.risk_score,
            risk_level=profile.risk_level,
            investigation_priority=profile.investigation_priority,
            behavior_profile=profile,
            classifications=profile.classifications,
            primary_signals=primary_signals,
            correlated_patterns=correlated_patterns,
            correlations=correlations,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # 2. Ranked Wallets Intelligence Listing
    # ------------------------------------------------------------------

    def get_all_wallet_profiles(
        self,
        limit: int = 50,
        offset: int = 0,
        classification: Optional[str] = None,
        priority: Optional[str] = None,
        min_risk: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Return filtered and paginated list of all profiled wallets in the system.
        """
        if self._profiles_cache is None:
            self._profiles_cache = {
                w: self._profiler.profile_wallet(w)
                for w in self.known_wallets
            }

        profiles = list(self._profiles_cache.values())

        # Filtering
        if classification:
            c_upper = classification.upper()
            profiles = [
                p for p in profiles
                if any(c.name == c_upper for c in p.classifications)
            ]

        if priority:
            p_upper = priority.upper()
            profiles = [p for p in profiles if p.investigation_priority == p_upper]

        if min_risk > 0:
            profiles = [p for p in profiles if p.risk_score >= min_risk]

        # Sorting: Priority (CRITICAL > HIGH > MEDIUM > LOW), then risk score, then total volume
        priority_rank = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3,
        }
        profiles.sort(
            key=lambda p: (
                priority_rank.get(p.investigation_priority, 4),
                -p.risk_score,
                -p.total_volume,
            )
        )

        total = len(profiles)
        paginated = profiles[offset: offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "wallets": [p.to_dict() for p in paginated],
        }

    # ------------------------------------------------------------------
    # 3. Cross-Pattern Correlations
    # ------------------------------------------------------------------

    def get_all_correlations(self) -> List[CrossPatternCorrelation]:
        """Return all detected cross-pattern convergence events."""
        return self._get_correlator().correlate_all()

    # ------------------------------------------------------------------
    # 4. Network-Wide Intelligence Summary
    # ------------------------------------------------------------------

    def get_network_summary(self) -> Dict[str, Any]:
        """
        Return global network intelligence indicators, behavioral distribution,
        and high-priority threats.
        """
        if self._profiles_cache is None:
            self._profiles_cache = {
                w: self._profiler.profile_wallet(w)
                for w in self.known_wallets
            }

        profiles = list(self._profiles_cache.values())
        correlations = self.get_all_correlations()

        # Classification counts
        class_counts: Dict[str, int] = {}
        priority_counts: Dict[str, int] = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 0,
            PriorityLevel.MEDIUM: 0,
            PriorityLevel.LOW: 0,
        }

        for p in profiles:
            priority_counts[p.investigation_priority] = priority_counts.get(p.investigation_priority, 0) + 1
            for c in p.classifications:
                class_counts[c.name] = class_counts.get(c.name, 0) + 1

        total_vol = sum(t.amount for t in self._transactions)

        # Top 5 priority wallets
        priority_rank = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3,
        }
        sorted_profiles = sorted(
            profiles,
            key=lambda p: (
                priority_rank.get(p.investigation_priority, 4),
                -p.risk_score,
                -p.total_volume,
            )
        )
        top_wallets = [p.to_dict() for p in sorted_profiles[:5]]

        return {
            "total_wallets": len(self.known_wallets),
            "total_transactions": len(self._transactions),
            "total_volume_eth": round(total_vol, 4),
            "total_correlations": len(correlations),
            "priority_breakdown": priority_counts,
            "classification_breakdown": class_counts,
            "top_priority_wallets": top_wallets,
            "top_correlations": [c.to_dict() for c in correlations[:5]],
        }

    # ------------------------------------------------------------------
    # 5. Investigation-Level Intelligence Dossier
    # ------------------------------------------------------------------

    def get_investigation_intelligence(self, case_id: str) -> Optional[InvestigationIntelligence]:
        """
        Generate strategic intelligence dossier for an investigation case.
        """
        case = CASE_STORE.get(case_id)
        if not case:
            return None

        target_intel = self.get_wallet_intelligence(case.target_wallet)
        if not target_intel:
            return None

        # Related counterparties intelligence
        suspicious_cps: List[Dict[str, Any]] = []
        for rw in case.related_wallets:
            if rw in self.known_wallets:
                rw_intel = self.get_wallet_intelligence(rw)
                if rw_intel and (rw_intel.risk_score >= 20.0 or rw_intel.investigation_priority != PriorityLevel.LOW):
                    suspicious_cps.append({
                        "wallet_id": rw,
                        "risk_score": rw_intel.risk_score,
                        "risk_level": rw_intel.risk_level,
                        "priority": rw_intel.investigation_priority,
                        "classifications": [c.name for c in rw_intel.classifications],
                    })

        # Calculate case transaction volume involving target
        target_in = [t for t in self._transactions if t.to_wallet == case.target_wallet]
        target_out = [t for t in self._transactions if t.from_wallet == case.target_wallet]
        case_vol = sum(t.amount for t in target_in + target_out)

        # Alerts count for case
        case_alerts = [a for a in self._get_alerts() if a.alert_id in case.alert_ids or case.target_wallet in a.wallets]
        alert_count = len(case_alerts)
        high_risk_alerts = sum(1 for a in case_alerts if a.severity in (Severity.HIGH, Severity.CRITICAL))

        dominant_patterns = sorted(list(set(a.pattern for a in case_alerts)))

        # Evidence & Merkle status
        evidence_records = EVIDENCE_STORE.list_by_case(case_id)
        ev_count = len(evidence_records)
        if ev_count > 0:
            merkle_root = compute_merkle_root([ev.evidence_hash for ev in evidence_records])
            ev_status = f"VERIFIED (Root: {merkle_root[:12]}...)"
        else:
            ev_status = "NO_EVIDENCE_ANCHORED"

        # Case Priority calculation
        target_score = target_intel.risk_score
        max_cp_score = max([cp["risk_score"] for cp in suspicious_cps], default=0.0)
        priority_score = min(100.0, 0.6 * target_score + 0.3 * max_cp_score + 10.0 if alert_count >= 2 else 0.5 * target_score)

        if priority_score >= 60.0 or target_intel.investigation_priority == PriorityLevel.CRITICAL:
            priority = PriorityLevel.CRITICAL
        elif priority_score >= 40.0 or target_intel.investigation_priority == PriorityLevel.HIGH:
            priority = PriorityLevel.HIGH
        elif priority_score >= 20.0:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW

        # Executive summary narrative
        class_str = ", ".join([c.label for c in target_intel.classifications])
        pat_str = ", ".join([p.replace('_', ' ').title() for p in dominant_patterns]) if dominant_patterns else "None"
        summary = (
            f"{priority} priority investigation focusing on target wallet {case.target_wallet[:10]}... "
            f"exhibiting {class_str} behaviors. Case spans {case_vol:.2f} ETH across {len(case_alerts)} linked alert(s) "
            f"covering patterns: {pat_str}. Associated with {len(suspicious_cps)} flagged counterparty/counterparties "
            f"and {ev_count} anchored evidence record(s)."
        )

        return InvestigationIntelligence(
            case_id=case_id,
            title=case.title,
            target_wallet=case.target_wallet,
            priority=priority,
            priority_score=priority_score,
            target_risk={
                "score": target_intel.risk_score,
                "level": target_intel.risk_level,
                "explanation": target_intel.explanation,
            },
            target_behavior=target_intel.behavior_profile.to_dict(),
            total_case_volume_eth=case_vol,
            alert_count=alert_count,
            high_risk_alert_count=high_risk_alerts,
            dominant_patterns=dominant_patterns,
            suspicious_counterparties_count=len(suspicious_cps),
            suspicious_counterparties=suspicious_cps,
            correlations=target_intel.correlations,
            evidence_count=ev_count,
            evidence_integrity_status=ev_status,
            executive_summary=summary,
        )
