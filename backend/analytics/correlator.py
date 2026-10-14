"""
ChainSentinel - Cross-Pattern Alert Correlator
Phase 8 - Identifies multi-pattern convergence, shared-entity intersections,
and temporal correlation clusters across detection alerts.
"""

import hashlib
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from ..detection.models import Alert, Severity, Transaction
from .models import CrossPatternCorrelation


class AlertCorrelator:
    """
    Correlates individual alerts into coherent multi-pattern intelligence events.
    Deterministic, explainable, and rule-grounded.
    """

    def __init__(self, alerts: List[Alert], transactions: List[Transaction] = None) -> None:
        self._alerts: List[Alert] = alerts
        self._transactions: List[Transaction] = transactions or []
        self._tx_map: Dict[str, Transaction] = {t.tx_id: t for t in self._transactions}

    def correlate_all(self) -> List[CrossPatternCorrelation]:
        """
        Scan all alerts and produce deduplicated cross-pattern correlation records.
        """
        correlations: List[CrossPatternCorrelation] = []

        # 1. Wallet Convergence: Wallets that appear across multiple pattern types
        wallet_to_alerts: Dict[str, List[Alert]] = defaultdict(list)
        for alert in self._alerts:
            for w in alert.wallets:
                wallet_to_alerts[w].append(alert)

        seen_correlation_keys: Set[str] = set()

        for wallet, w_alerts in wallet_to_alerts.items():
            patterns = set(a.pattern for a in w_alerts)
            if len(patterns) >= 2:
                # Deduplicate alerts
                unique_alerts = []
                seen_ids = set()
                for a in w_alerts:
                    if a.alert_id not in seen_ids:
                        seen_ids.add(a.alert_id)
                        unique_alerts.append(a)

                sorted_patterns = sorted(patterns)
                corr_key = f"wallet_convergence:{wallet}:{':'.join(sorted_patterns)}"
                if corr_key in seen_correlation_keys:
                    continue
                seen_correlation_keys.add(corr_key)

                # Participating wallets and total volume
                all_wallets = set()
                total_vol = 0.0
                time_spans = []
                for a in unique_alerts:
                    all_wallets.update(a.wallets)
                    total_vol += a.total_amount
                    time_spans.append(a.time_span_seconds)

                max_time_span = max(time_spans) if time_spans else 3600.0

                # Determine severity & confidence
                severities = set(a.severity for a in unique_alerts)
                if Severity.CRITICAL in severities or len(patterns) >= 3:
                    severity = Severity.CRITICAL
                    confidence = "HIGH"
                elif Severity.HIGH in severities or len(patterns) >= 2:
                    severity = Severity.HIGH
                    confidence = "HIGH"
                else:
                    severity = Severity.MEDIUM
                    confidence = "MEDIUM"

                readable_patterns = [p.replace('_', ' ').title() for p in sorted_patterns]
                pat_str = ", ".join(readable_patterns)
                duration_min = round(max_time_span / 60.0, 1)

                explanation = (
                    f"{len(patterns)} distinct suspicious topologies ({pat_str}) converge on wallet "
                    f"{wallet[:10]}... across {len(unique_alerts)} alert(s) within a {duration_min}-minute time frame."
                )

                corr_id = "corr_" + hashlib.sha256(corr_key.encode()).hexdigest()[:16]

                title = f"Multi-Pattern Convergence: {readable_patterns[0]} & {readable_patterns[1]}"
                if len(readable_patterns) > 2:
                    title += f" (+{len(readable_patterns) - 2} more)"

                correlations.append(
                    CrossPatternCorrelation(
                        correlation_id=corr_id,
                        title=title,
                        primary_wallet=wallet,
                        converging_patterns=sorted_patterns,
                        alert_ids=[a.alert_id for a in unique_alerts],
                        time_window_seconds=max_time_span,
                        confidence=confidence,
                        severity=severity,
                        participating_wallets=sorted(list(all_wallets)),
                        total_volume_eth=total_vol,
                        explanation=explanation,
                        metadata={
                            "correlation_type": "WALLET_CONVERGENCE",
                            "alert_count": len(unique_alerts),
                            "pattern_count": len(patterns),
                        },
                    )
                )

        # Sort correlations by severity (CRITICAL first), then pattern count descending, then volume
        sev_rank = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        correlations.sort(
            key=lambda c: (
                sev_rank.get(c.severity, 4),
                -len(c.converging_patterns),
                -c.total_volume_eth,
            )
        )

        return correlations

    def correlate_for_wallet(self, wallet_id: str) -> List[CrossPatternCorrelation]:
        """Return all correlations where the wallet is the primary focus or a participant."""
        all_corrs = self.correlate_all()
        return [
            c for c in all_corrs
            if c.primary_wallet == wallet_id or wallet_id in c.participating_wallets
        ]
