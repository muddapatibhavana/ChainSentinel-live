"""
ChainSentinel - Central Detection Engine

This is the single entry point for all detection logic.
The engine orchestrates all detectors and produces a unified alert list.

Usage:
    engine = DetectionEngine(transactions)
    all_alerts = engine.detect_all()
    wallet_alerts = engine.detect_for_wallet("0xABC...")
    risk = engine.get_wallet_risk("0xABC...")
    summary = engine.get_summary()
"""

from typing import Dict, List, Optional

from .models import (
    Alert,
    DetectionSummary,
    Transaction,
    WalletRiskAssessment,
)
from .circular import detect_circular
from .rapid_movement import detect_rapid_movement
from .burst import detect_burst
from .fanout import detect_fanout
from .fanin import detect_fanin
from .clusters import detect_clusters
from .risk import compute_wallet_risk, compute_all_wallet_risks


class DetectionEngine:
    """
    Orchestrates all rule-based detectors and caches results in memory.
    Create one instance per backend startup and reuse it.
    """

    def __init__(self, raw_transactions: List[Dict]) -> None:
        """
        Accept raw transaction dicts from data/loader.py
        and convert them to typed Transaction objects.
        """
        self._raw = raw_transactions
        self._transactions: List[Transaction] = [
            Transaction.from_dict(row) for row in raw_transactions
        ]
        self._alerts: Optional[List[Alert]] = None
        self._wallet_risks: Optional[Dict[str, WalletRiskAssessment]] = None

    # ------------------------------------------------------------------
    # Core detection
    # ------------------------------------------------------------------

    def detect_all(self) -> List[Alert]:
        """
        Run every detector and return the de-duplicated, merged alert list.
        Results are cached — calling this multiple times is free.
        """
        if self._alerts is not None:
            return self._alerts

        all_alerts: List[Alert] = []

        all_alerts.extend(detect_circular(self._transactions))
        all_alerts.extend(detect_rapid_movement(self._transactions))
        all_alerts.extend(detect_burst(self._transactions))
        all_alerts.extend(detect_fanout(self._transactions))
        all_alerts.extend(detect_fanin(self._transactions))
        all_alerts.extend(detect_clusters(self._transactions))

        # Deduplicate by alert_id (safety net)
        seen_ids: set = set()
        deduped: List[Alert] = []
        for alert in all_alerts:
            if alert.alert_id not in seen_ids:
                seen_ids.add(alert.alert_id)
                deduped.append(alert)

        # Sort by severity (CRITICAL first), then by time_span (shortest first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        deduped.sort(key=lambda a: (severity_order.get(a.severity, 4), a.time_span_seconds))

        self._alerts = deduped
        return self._alerts

    def detect_for_wallet(self, wallet_id: str) -> List[Alert]:
        """
        Return all alerts that involve the specified wallet address.
        Case-sensitive match (blockchain addresses are case-sensitive checksums).
        """
        return [
            alert for alert in self.detect_all()
            if wallet_id in alert.wallets
        ]

    # ------------------------------------------------------------------
    # Risk scoring
    # ------------------------------------------------------------------

    def get_wallet_risk(self, wallet_id: str) -> WalletRiskAssessment:
        """Compute or retrieve cached risk assessment for a specific wallet."""
        risks = self._get_all_risks()
        if wallet_id in risks:
            return risks[wallet_id]
        # Wallet exists but has no alerts → return clean LOW assessment
        return compute_wallet_risk(wallet_id, [])

    def _get_all_risks(self) -> Dict[str, WalletRiskAssessment]:
        if self._wallet_risks is None:
            self._wallet_risks = compute_all_wallet_risks(self.detect_all())
        return self._wallet_risks

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> DetectionSummary:
        """Return a high-level summary of all detection results."""
        alerts = self.detect_all()

        alerts_by_pattern: Dict[str, int] = {}
        alerts_by_severity: Dict[str, int] = {}
        all_wallets: set = set()

        for alert in alerts:
            alerts_by_pattern[alert.pattern] = alerts_by_pattern.get(alert.pattern, 0) + 1
            alerts_by_severity[alert.severity] = alerts_by_severity.get(alert.severity, 0) + 1
            all_wallets.update(alert.wallets)

        return DetectionSummary(
            total_transactions=len(self._transactions),
            total_wallets=len(
                set(t.from_wallet for t in self._transactions)
                | set(t.to_wallet for t in self._transactions)
            ),
            total_alerts=len(alerts),
            alerts_by_pattern=alerts_by_pattern,
            alerts_by_severity=alerts_by_severity,
            alerts=[a.to_dict() for a in alerts],
        )

    # ------------------------------------------------------------------
    # Graph data for frontend Cytoscape (Phase 6)
    # ------------------------------------------------------------------

    def get_wallet_graph(self, wallet_id: str, depth: int = 2) -> Dict:
        """
        Return Cytoscape-compatible node/edge data for a wallet subgraph.
        Includes transactions within `depth` hops from wallet_id.
        """
        if depth < 1:
            depth = 1

        visited_wallets: set = {wallet_id}
        frontier: set = {wallet_id}

        txs_in_graph: List[Transaction] = []

        for _ in range(depth):
            next_frontier: set = set()
            for tx in self._transactions:
                if tx.from_wallet in frontier or tx.to_wallet in frontier:
                    txs_in_graph.append(tx)
                    next_frontier.add(tx.from_wallet)
                    next_frontier.add(tx.to_wallet)
            frontier = next_frontier - visited_wallets
            visited_wallets |= next_frontier

        # Deduplicate transactions
        seen_txs: set = set()
        unique_txs: List[Transaction] = []
        for tx in txs_in_graph:
            if tx.tx_id not in seen_txs:
                seen_txs.add(tx.tx_id)
                unique_txs.append(tx)

        # Get alerts for all wallets in graph for coloring
        all_alerts = self.detect_all()
        flagged_wallets: set = set()
        for alert in all_alerts:
            for w in alert.wallets:
                if w in visited_wallets:
                    flagged_wallets.add(w)

        nodes = [
            {
                "data": {
                    "id": w,
                    "label": w[:8] + "...",
                    "flagged": w in flagged_wallets,
                    "is_focus": w == wallet_id,
                }
            }
            for w in visited_wallets
        ]

        edges = [
            {
                "data": {
                    "id": tx.tx_id,
                    "source": tx.from_wallet,
                    "target": tx.to_wallet,
                    "amount": tx.amount,
                    "timestamp": tx.timestamp.isoformat(),
                    "label": f"{tx.amount:.2f} ETH",
                    "category": tx.category_label,
                }
            }
            for tx in unique_txs
        ]

        return {
            "wallet_id": wallet_id,
            "nodes": nodes,
            "edges": edges,
            "flagged_wallets": list(flagged_wallets),
        }

    # ------------------------------------------------------------------
    # Flow Tracing & Path Reconstruction (Phase 7)
    # ------------------------------------------------------------------

    def trace_flow(
        self,
        source: str,
        target: Optional[str] = None,
        max_depth: int = 4,
    ) -> Dict:
        """
        Execute flow tracing and path reconstruction from source to target
        (or discover downstream flows if target is None).
        """
        if not hasattr(self, "_tracer") or self._tracer is None:
            from .tracer import FlowTracer
            self._tracer = FlowTracer(self._transactions, self)
        return self._tracer.trace_flow(source, target, max_depth=max_depth)
