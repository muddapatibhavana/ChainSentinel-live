"""
ChainSentinel - Wallet Behavior Profiler
Phase 8 - Deterministic transaction profiling, behavioral feature extraction,
and explainable classification.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

from ..detection.models import Transaction, Alert, Severity, PatternType
from .models import (
    BehaviorClassification,
    ClassificationType,
    PriorityLevel,
    WalletBehaviorProfile,
)


class WalletBehaviorProfiler:
    """
    Computes deterministic behavioral features and explainable classifications
    for wallets using the transaction ledger and detection results.
    """

    def __init__(self, transactions: List[Transaction], engine=None) -> None:
        self._transactions: List[Transaction] = transactions
        self._engine = engine

        # Build wallet transaction index
        self._wallet_inbound: Dict[str, List[Transaction]] = defaultdict(list)
        self._wallet_outbound: Dict[str, List[Transaction]] = defaultdict(list)
        self._all_wallets: Set[str] = set()

        for tx in self._transactions:
            self._all_wallets.add(tx.from_wallet)
            self._all_wallets.add(tx.to_wallet)
            self._wallet_outbound[tx.from_wallet].append(tx)
            self._wallet_inbound[tx.to_wallet].append(tx)

    @property
    def all_wallets(self) -> Set[str]:
        return self._all_wallets

    def profile_wallet(self, wallet_id: str) -> WalletBehaviorProfile:
        """
        Generate a complete behavioral profile and classifications for a wallet.
        """
        if wallet_id not in self._all_wallets:
            raise ValueError(f"Wallet '{wallet_id}' not found in transaction dataset")

        inbound = self._wallet_inbound.get(wallet_id, [])
        outbound = self._wallet_outbound.get(wallet_id, [])
        all_txs = sorted(inbound + outbound, key=lambda t: t.timestamp)

        in_count = len(inbound)
        out_count = len(outbound)
        total_count = in_count + out_count

        in_vol = sum(t.amount for t in inbound)
        out_vol = sum(t.amount for t in outbound)
        total_vol = in_vol + out_vol
        net_flow = in_vol - out_vol

        in_counterparties = set(t.from_wallet for t in inbound)
        out_counterparties = set(t.to_wallet for t in outbound)
        all_counterparties = in_counterparties | out_counterparties

        avg_value = (total_vol / total_count) if total_count > 0 else 0.0
        largest_value = max([t.amount for t in all_txs], default=0.0)

        first_act = all_txs[0].timestamp if all_txs else None
        last_act = all_txs[-1].timestamp if all_txs else None
        active_span = (last_act - first_act).total_seconds() if (first_act and last_act) else 0.0

        tx_freq = (total_count / (active_span / 3600.0)) if active_span > 60.0 else float(total_count)

        # Alerts and risk for wallet
        wallet_alerts = self._get_wallet_alerts(wallet_id)
        alert_count = len(wallet_alerts)
        high_crit_count = sum(1 for a in wallet_alerts if a.severity in (Severity.HIGH, Severity.CRITICAL))

        risk_score = 0.0
        risk_level = Severity.LOW
        if self._engine:
            risk_assessment = self._engine.get_wallet_risk(wallet_id)
            risk_score = risk_assessment.risk_score
            risk_level = risk_assessment.risk_level

        patterns = set(a.pattern for a in wallet_alerts)
        is_burst = PatternType.BURST in patterns or any(t.category_label == "burst" for t in all_txs)
        is_fan_out = PatternType.FAN_OUT in patterns or (len(out_counterparties) >= 4 and out_count >= 4)
        is_fan_in = PatternType.FAN_IN in patterns or (len(in_counterparties) >= 4 and in_count >= 4)
        is_circular = PatternType.CIRCULAR_TRANSACTION in patterns or any(t.category_label == "circular" for t in all_txs)
        is_rapid = PatternType.RAPID_MOVEMENT in patterns or any(t.category_label == "rapid_movement" for t in all_txs)
        is_cluster = PatternType.SUSPICIOUS_CLUSTER in patterns or any(t.category_label == "cluster" for t in all_txs)

        # Classifications & Explanations
        classifications: List[BehaviorClassification] = []
        signals: List[str] = []

        # 1. Multi-Pattern
        if len(patterns) >= 2:
            pat_names = ", ".join(sorted([p.replace('_', ' ').title() for p in patterns]))
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.MULTI_PATTERN,
                    label="Multi-Pattern Convergence",
                    severity=Severity.CRITICAL if len(patterns) >= 3 else Severity.HIGH,
                    description=f"Wallet participates across {len(patterns)} distinct suspicious topologies ({pat_names}).",
                )
            )
            signals.append(f"Convergence of {len(patterns)} pattern types ({pat_names})")

        # 2. High Risk
        if risk_score >= 40.0 or high_crit_count >= 1:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.HIGH_RISK,
                    label="Elevated Forensic Risk",
                    severity=Severity.CRITICAL if risk_score >= 60.0 else Severity.HIGH,
                    description=f"Associated with {alert_count} alert(s), including {high_crit_count} high/critical alerts (Risk Score: {risk_score}/100).",
                )
            )
            signals.append(f"Risk score of {risk_score}/100 with {high_crit_count} high-severity alert(s)")

        # 3. High Velocity
        if is_rapid:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.HIGH_VELOCITY,
                    label="Rapid Passthrough Velocity",
                    severity=Severity.HIGH,
                    description="Participates in low-latency relay chain forwarding with short holding periods (<300s).",
                )
            )
            signals.append("Rapid forwarding chain participation with tight hold-times")

        # 4. Fan-Out (Smurfing Dispersal)
        if is_fan_out:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.FAN_OUT,
                    label="Fan-Out Dispersal",
                    severity=Severity.HIGH,
                    description=f"Transfers capital outwards across {len(out_counterparties)} unique counterparties in short succession.",
                )
            )
            signals.append(f"Fan-out dispersal to {len(out_counterparties)} recipient addresses")

        # 5. Fan-In (Liquidity Aggregation)
        if is_fan_in:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.FAN_IN,
                    label="Fan-In Aggregator",
                    severity=Severity.HIGH,
                    description=f"Aggregates capital inward from {len(in_counterparties)} distinct tributary feeder addresses.",
                )
            )
            signals.append(f"Fan-in collection from {len(in_counterparties)} distinct feeder sources")

        # 6. Circular Routing
        if is_circular:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.CIRCULAR,
                    label="Circular Routing Loop",
                    severity=Severity.HIGH,
                    description="Participates in closed-loop fund cycling returning liquidity back to origin entity.",
                )
            )
            signals.append("Closed circular transaction loop retaining principal capital")

        # 7. Mixer-like Circulation
        if is_cluster:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.MIXER_LIKE,
                    label="Cluster Mixing Component",
                    severity=Severity.HIGH,
                    description="High-density internal circulation within a tightly interconnected mixing ring.",
                )
            )
            signals.append("Dense internal component circulation indicative of mixing pool")

        # 8. High Volume
        if total_vol >= 100.0:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.HIGH_VOLUME,
                    label="High Volume Throughput",
                    severity=Severity.MEDIUM,
                    description=f"Large capital turnover of {total_vol:.2f} ETH across {total_count} transactions.",
                )
            )
            signals.append(f"Significant cumulative volume of {total_vol:.2f} ETH")

        # 9. Normal Baseline
        if not classifications:
            classifications.append(
                BehaviorClassification(
                    name=ClassificationType.NORMAL,
                    label="Standard Ledger Activity",
                    severity=Severity.LOW,
                    description="Balanced transaction flows with no anomalous topology signatures.",
                )
            )
            signals.append("Normal activity patterns within expected operating thresholds")

        # Determine Investigation Priority
        if risk_score >= 60.0 or len(patterns) >= 3:
            priority = PriorityLevel.CRITICAL
        elif risk_score >= 40.0 or len(patterns) >= 2 or high_crit_count >= 1:
            priority = PriorityLevel.HIGH
        elif risk_score >= 20.0 or total_vol >= 100.0:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW

        return WalletBehaviorProfile(
            wallet_id=wallet_id,
            total_tx_count=total_count,
            inbound_tx_count=in_count,
            outbound_tx_count=out_count,
            inbound_volume=in_vol,
            outbound_volume=out_vol,
            total_volume=total_vol,
            net_flow=net_flow,
            unique_counterparties_count=len(all_counterparties),
            unique_inbound_counterparties_count=len(in_counterparties),
            unique_outbound_counterparties_count=len(out_counterparties),
            avg_tx_value=avg_value,
            largest_tx_value=largest_value,
            first_activity=first_act,
            last_activity=last_act,
            active_time_span_seconds=active_span,
            tx_frequency_per_hour=tx_freq,
            is_burst_participant=is_burst,
            is_fan_out=is_fan_out,
            is_fan_in=is_fan_in,
            is_circular=is_circular,
            is_rapid_movement=is_rapid,
            is_cluster_participant=is_cluster,
            alert_count=alert_count,
            high_critical_alert_count=high_crit_count,
            risk_score=risk_score,
            risk_level=risk_level,
            investigation_priority=priority,
            classifications=classifications,
            signals=signals,
        )

    def _get_wallet_alerts(self, wallet_id: str) -> List[Alert]:
        if self._engine:
            return self._engine.detect_for_wallet(wallet_id)
        return []
