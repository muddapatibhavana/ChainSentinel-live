"""
ChainSentinel - Circular Transaction Detector

Logic:
  1. Build a directed graph from all transactions.
  2. Use NetworkX simple_cycles() to enumerate all directed cycles.
  3. Keep only cycles within the configurable length and time window.
  4. For each qualifying cycle, reconstruct the specific transactions involved.
  5. Return an Alert for each detected cycle.

Why this isn't a false-positive machine:
  - We filter by time window: the entire cycle must complete within
    CIRCULAR_MAX_WINDOW_SECONDS.
  - We filter by cycle length: very short (self-loops) and very long
    (spanning unrelated activity) cycles are ignored.
  - A "cycle" requires actual directed edges in the transaction graph,
    not just path reachability.
"""

import hashlib
from typing import List

import networkx as nx

from .models import Alert, PatternType, Severity, Transaction
from .config import (
    CIRCULAR_MAX_WINDOW_SECONDS,
    CIRCULAR_MIN_CYCLE_LENGTH,
    CIRCULAR_MAX_CYCLE_LENGTH,
)


def _make_alert_id(wallets: List[str], tx_ids: List[str]) -> str:
    key = "circular:" + ":".join(sorted(wallets)) + ":" + ":".join(sorted(tx_ids))
    return "alert_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _severity_for_cycle(cycle_length: int, time_span_seconds: float) -> str:
    """
    Longer cycles that complete quickly are more suspicious.
    4-hop cycle closing in <30 min → HIGH; closing in <2h → MEDIUM.
    """
    if cycle_length >= 4 and time_span_seconds <= 3600:
        return Severity.HIGH
    if cycle_length >= 3 and time_span_seconds <= CIRCULAR_MAX_WINDOW_SECONDS:
        return Severity.MEDIUM
    return Severity.LOW


def detect_circular(
    transactions: List[Transaction],
    max_window_seconds: int = CIRCULAR_MAX_WINDOW_SECONDS,
    min_cycle_length: int = CIRCULAR_MIN_CYCLE_LENGTH,
    max_cycle_length: int = CIRCULAR_MAX_CYCLE_LENGTH,
) -> List[Alert]:
    """
    Detect circular transaction flows using directed cycle enumeration.

    Returns one Alert per detected cycle. Cycles sharing edges with an already-
    reported larger cycle are de-duplicated by the engine.
    """
    if not transactions:
        return []

    # Build directed multigraph: wallet → wallet, edge carries tx metadata
    G = nx.MultiDiGraph()
    # tx_lookup: (from_wallet, to_wallet) → list of Transactions (sorted by time)
    edge_txs: dict = {}

    for tx in transactions:
        G.add_edge(tx.from_wallet, tx.to_wallet)
        key = (tx.from_wallet, tx.to_wallet)
        edge_txs.setdefault(key, []).append(tx)

    # Sort each edge list chronologically for time-span calculation
    for key in edge_txs:
        edge_txs[key].sort(key=lambda t: t.timestamp)

    alerts: List[Alert] = []
    seen_cycle_sets: set = set()  # deduplicate identical wallet-set cycles

    # simple_cycles finds all elementary directed cycles
    for cycle in nx.simple_cycles(G):
        length = len(cycle)
        if length < min_cycle_length or length > max_cycle_length:
            continue

        # Frozenset to deduplicate: {A,B,C,D} == {B,C,D,A}
        cycle_key = frozenset(cycle)
        if cycle_key in seen_cycle_sets:
            continue

        # Reconstruct directed edges in cycle order
        edges = [(cycle[i], cycle[(i + 1) % length]) for i in range(length)]

        # For each edge pick the earliest qualifying transaction
        involved_txs: List[Transaction] = []
        valid = True
        for edge in edges:
            if edge not in edge_txs:
                valid = False
                break
            involved_txs.append(edge_txs[edge][0])

        if not valid or not involved_txs:
            continue

        # Sort involved txs by time to compute window
        involved_txs.sort(key=lambda t: t.timestamp)
        first_ts = involved_txs[0].timestamp
        last_ts = involved_txs[-1].timestamp
        span = (last_ts - first_ts).total_seconds()

        if span > max_window_seconds:
            continue

        seen_cycle_sets.add(cycle_key)

        tx_ids = [tx.tx_id for tx in involved_txs]
        total_amount = sum(tx.amount for tx in involved_txs)
        severity = _severity_for_cycle(length, span)

        # Build the readable path string (e.g. "A → B → C → D → A")
        path_str = " → ".join(cycle) + " → " + cycle[0]

        explanation = (
            f"Funds moved through {length} wallets and returned to the originating "
            f"wallet within {span / 60:.1f} minutes. "
            f"Circular flow path: {path_str}. "
            f"Total volume cycled: {total_amount:.4f} ETH. "
            f"This pattern is characteristic of layering in money laundering: "
            f"the funds appear to pass through multiple parties but ultimately "
            f"return to the source, obscuring the true origin."
        )

        alerts.append(Alert(
            alert_id=_make_alert_id(cycle, tx_ids),
            pattern=PatternType.CIRCULAR_TRANSACTION,
            severity=severity,
            wallets=cycle,
            transaction_ids=tx_ids,
            total_amount=total_amount,
            time_span_seconds=span,
            explanation=explanation,
            metadata={
                "cycle_length": length,
                "cycle_path": cycle + [cycle[0]],
                "span_minutes": round(span / 60, 2),
            },
        ))

    return alerts
