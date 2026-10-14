"""
ChainSentinel - Rapid Movement Detector

Logic:
  For each wallet W, look at all inbound transactions.
  When W receives funds, check if W re-sends a similar amount within
  RAPID_MAX_HOP_SECONDS. If this forms a chain of >= RAPID_MIN_HOPS
  consecutive relays, flag it.

  Chain construction:
    - Start at any transaction.
    - At each step, find a subsequent transaction from to_wallet within
      the hop time limit.
    - Continue until the chain breaks or exceeds max length.

  Why this avoids false positives:
    - We require a minimum chain length (3 hops by default).
    - Each hop must be from the *receiver* of the prior hop.
    - The hop time limit (5 minutes by default) filters normal activity
      where wallets just happen to be active on the same day.
"""

import hashlib
from typing import Dict, List, Set

from .models import Alert, PatternType, Severity, Transaction
from .config import (
    RAPID_MIN_HOPS,
    RAPID_MAX_HOP_SECONDS,
    RAPID_CHAIN_WINDOW_SECONDS,
)


def _make_alert_id(tx_ids: List[str]) -> str:
    key = "rapid:" + ":".join(tx_ids)
    return "alert_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _severity_for_rapid(hop_count: int, avg_hold_seconds: float) -> str:
    if hop_count >= 4 and avg_hold_seconds < 120:
        return Severity.HIGH
    if hop_count >= 3 and avg_hold_seconds < 300:
        return Severity.MEDIUM
    return Severity.LOW


def detect_rapid_movement(
    transactions: List[Transaction],
    min_hops: int = RAPID_MIN_HOPS,
    max_hop_seconds: int = RAPID_MAX_HOP_SECONDS,
    chain_window_seconds: int = RAPID_CHAIN_WINDOW_SECONDS,
) -> List[Alert]:
    """
    Detect rapid fund-relay chains where each intermediate wallet
    quickly re-forwards received funds to the next hop.
    """
    if not transactions:
        return []

    # Sort all txs by timestamp
    sorted_txs = sorted(transactions, key=lambda t: t.timestamp)

    # Index: for each wallet, all outbound transactions (sorted by time)
    outbound: Dict[str, List[Transaction]] = {}
    for tx in sorted_txs:
        outbound.setdefault(tx.from_wallet, []).append(tx)

    alerts: List[Alert] = []
    # Track tx_ids already used in a reported chain to avoid duplicate alerts
    reported_tx_sets: List[Set[str]] = []

    for seed_tx in sorted_txs:
        # Try to grow a chain starting from seed_tx
        chain: List[Transaction] = [seed_tx]

        while True:
            current_tx = chain[-1]
            relay_wallet = current_tx.to_wallet
            current_time = current_tx.timestamp

            # Find the first outbound tx from relay_wallet within hop window
            next_tx = None
            for candidate in outbound.get(relay_wallet, []):
                delta = (candidate.timestamp - current_time).total_seconds()
                if 0 < delta <= max_hop_seconds:
                    next_tx = candidate
                    break

            if next_tx is None:
                break
            chain.append(next_tx)

        if len(chain) < min_hops:
            continue

        # Check total window
        total_span = (chain[-1].timestamp - chain[0].timestamp).total_seconds()
        if total_span > chain_window_seconds:
            continue

        tx_ids = [tx.tx_id for tx in chain]
        tx_id_set = set(tx_ids)

        # Deduplicate: skip if this chain is a subset of an already-reported one
        already_reported = any(tx_id_set.issubset(existing) for existing in reported_tx_sets)
        if already_reported:
            continue

        reported_tx_sets.append(tx_id_set)

        wallets = [chain[0].from_wallet] + [tx.to_wallet for tx in chain]
        hold_times = [
            (chain[i + 1].timestamp - chain[i].timestamp).total_seconds()
            for i in range(len(chain) - 1)
        ]
        avg_hold = sum(hold_times) / len(hold_times) if hold_times else 0
        total_amount = sum(tx.amount for tx in chain)
        severity = _severity_for_rapid(len(chain), avg_hold)

        wallet_path = " → ".join(wallets)
        explanation = (
            f"Funds moved through {len(chain)} consecutive hops in "
            f"{total_span:.0f} seconds (avg {avg_hold:.0f}s per hop). "
            f"Relay path: {wallet_path}. "
            f"Each intermediate wallet received and re-forwarded funds almost "
            f"immediately, a classic layering technique to obscure the original "
            f"source of funds."
        )

        alerts.append(Alert(
            alert_id=_make_alert_id(tx_ids),
            pattern=PatternType.RAPID_MOVEMENT,
            severity=severity,
            wallets=wallets,
            transaction_ids=tx_ids,
            total_amount=total_amount,
            time_span_seconds=total_span,
            explanation=explanation,
            metadata={
                "hop_count": len(chain),
                "avg_hold_seconds": round(avg_hold, 1),
                "hold_times_seconds": [round(h, 1) for h in hold_times],
                "relay_path": wallets,
            },
        ))

    return alerts
