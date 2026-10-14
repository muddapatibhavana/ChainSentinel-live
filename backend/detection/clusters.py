"""
ChainSentinel - Suspicious Cluster Detector

Logic:
  1. Build a directed transaction graph using NetworkX.
  2. Find weakly connected components (WCC) — groups of wallets linked
     by any directed path.
  3. For each WCC with >= CLUSTER_MIN_NODES nodes and >= CLUSTER_MIN_EDGES
     internal directed edges, compute the edge density.
  4. Flag WCCs where density >= CLUSTER_MIN_EDGE_DENSITY.

  Edge density formula (directed graph):
    density = actual_edges / (n * (n - 1))
    where n = number of nodes, and n*(n-1) is the max possible directed edges.

  Why this avoids false positives:
    - Normal wallets (payroll → employees, traders → DEX) form star-topology
      components with low density (hub sends to many leaves, no cross-links).
    - The suspicious cluster in our dataset has 5 nodes with 12 directed edges.
      Max possible = 5*4 = 20. Density = 12/20 = 0.60 → flagged at HIGH.
    - Payroll hub → 5 employees: 5 edges, 6 nodes, density = 5/(6*5) = 0.17
      → below 0.30 threshold, NOT flagged.
    - DEX router receives from 10 traders: 10 edges, 11 nodes,
      density = 10/(11*10) = 0.09 → NOT flagged.
"""

import hashlib
from typing import Dict, List, Set

import networkx as nx

from .models import Alert, PatternType, Severity, Transaction
from .config import (
    CLUSTER_MIN_NODES,
    CLUSTER_MIN_EDGES,
    CLUSTER_MIN_EDGE_DENSITY,
)


def _make_alert_id(wallets: List[str]) -> str:
    key = "cluster:" + ":".join(sorted(wallets))
    return "alert_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _severity_for_cluster(density: float, node_count: int, edge_count: int) -> str:
    if density >= 0.50 and node_count >= 4:
        return Severity.HIGH
    if density >= 0.30 and edge_count >= 5:
        return Severity.MEDIUM
    return Severity.LOW


def detect_clusters(
    transactions: List[Transaction],
    min_nodes: int = CLUSTER_MIN_NODES,
    min_edges: int = CLUSTER_MIN_EDGES,
    min_density: float = CLUSTER_MIN_EDGE_DENSITY,
) -> List[Alert]:
    """
    Detect suspiciously dense wallet clusters using NetworkX
    weakly connected component analysis and edge density scoring.
    """
    if not transactions:
        return []

    # Build directed graph
    G = nx.DiGraph()
    # Track which transactions link which pairs
    edge_txs: Dict[tuple, List[Transaction]] = {}

    for tx in transactions:
        G.add_edge(tx.from_wallet, tx.to_wallet)
        key = (tx.from_wallet, tx.to_wallet)
        edge_txs.setdefault(key, []).append(tx)

    alerts: List[Alert] = []

    # Analyse each weakly connected component
    for component_nodes in nx.weakly_connected_components(G):
        n = len(component_nodes)
        if n < min_nodes:
            continue

        # Build the subgraph restricted to this component
        subgraph = G.subgraph(component_nodes)
        e = subgraph.number_of_edges()

        if e < min_edges:
            continue

        # Directed density: e / (n * (n-1))
        max_edges = n * (n - 1)
        density = e / max_edges if max_edges > 0 else 0.0

        if density < min_density:
            continue

        # Gather all transactions within this component
        component_txs: List[Transaction] = []
        for u, v in subgraph.edges():
            component_txs.extend(edge_txs.get((u, v), []))

        component_txs.sort(key=lambda t: t.timestamp)
        tx_ids = [tx.tx_id for tx in component_txs]
        total_amount = sum(tx.amount for tx in component_txs)

        wallets = list(component_nodes)
        span = (
            (component_txs[-1].timestamp - component_txs[0].timestamp).total_seconds()
            if len(component_txs) > 1 else 0.0
        )

        severity = _severity_for_cluster(density, n, e)

        explanation = (
            f"A group of {n} wallets has {e} directed transactions among themselves "
            f"(edge density: {density:.2f}, threshold: {min_density:.2f}). "
            f"Total volume circulated: {total_amount:.4f} ETH over "
            f"{span / 60:.1f} minutes. "
            f"This unusually high interconnection density suggests a mixing ring, "
            f"tumbler, or coordinated wash-trading cluster designed to obscure the "
            f"true ownership and movement of funds."
        )

        alerts.append(Alert(
            alert_id=_make_alert_id(wallets),
            pattern=PatternType.SUSPICIOUS_CLUSTER,
            severity=severity,
            wallets=wallets,
            transaction_ids=tx_ids,
            total_amount=total_amount,
            time_span_seconds=span,
            explanation=explanation,
            metadata={
                "node_count": n,
                "edge_count": e,
                "density": round(density, 4),
                "max_possible_edges": max_edges,
            },
        ))

    return alerts
