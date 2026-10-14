"""
ChainSentinel - Transaction Burst Detector

Logic:
  For each unique sender wallet, sort its outgoing transactions by time.
  Use a sliding window of BURST_WINDOW_SECONDS.
  If the wallet sends >= BURST_MIN_TX_COUNT transactions within that window,
  flag the burst.

  We take the maximum-density window per wallet (greedy left-anchor approach):
  start at each tx, find how many subsequent txs fall within the window.

  Why this avoids false positives:
    - Requires a minimum count (5 by default), so a wallet with 2-3 fast
      transactions is not flagged.
    - Normal payroll wallets send 5 txs over 48 minutes — well outside
      the 5-minute window.
    - DEX traders each make 1 transaction — not flagged.
    - The burst sender in our dataset makes 10 txs in 81 seconds → flagged.
"""

import hashlib
from typing import Dict, List

from .models import Alert, PatternType, Severity, Transaction
from .config import BURST_WINDOW_SECONDS, BURST_MIN_TX_COUNT


def _make_alert_id(wallet: str, tx_ids: List[str]) -> str:
    key = f"burst:{wallet}:" + ":".join(sorted(tx_ids))
    return "alert_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _severity_for_burst(count: int, window_seconds: float) -> str:
    if count >= 10 and window_seconds <= 120:
        return Severity.HIGH
    if count >= 7 and window_seconds <= 300:
        return Severity.MEDIUM
    if count >= 5:
        return Severity.MEDIUM
    return Severity.LOW


def detect_burst(
    transactions: List[Transaction],
    window_seconds: int = BURST_WINDOW_SECONDS,
    min_tx_count: int = BURST_MIN_TX_COUNT,
) -> List[Alert]:
    """
    Detect unusual transaction frequency bursts from a single wallet
    within a configurable sliding time window.
    """
    if not transactions:
        return []

    # Group outbound transactions by sender wallet, sorted by time
    outbound: Dict[str, List[Transaction]] = {}
    for tx in transactions:
        outbound.setdefault(tx.from_wallet, []).append(tx)

    for wallet in outbound:
        outbound[wallet].sort(key=lambda t: t.timestamp)

    alerts: List[Alert] = []

    for wallet, txs in outbound.items():
        if len(txs) < min_tx_count:
            continue

        best_window: List[Transaction] = []

        # Sliding window: anchor at each tx, expand right while within window
        for i, anchor_tx in enumerate(txs):
            window: List[Transaction] = [anchor_tx]
            for j in range(i + 1, len(txs)):
                delta = (txs[j].timestamp - anchor_tx.timestamp).total_seconds()
                if delta <= window_seconds:
                    window.append(txs[j])
                else:
                    break

            if len(window) > len(best_window):
                best_window = window

        if len(best_window) < min_tx_count:
            continue

        tx_ids = [tx.tx_id for tx in best_window]
        total_amount = sum(tx.amount for tx in best_window)
        span = (best_window[-1].timestamp - best_window[0].timestamp).total_seconds()
        dest_wallets = list({tx.to_wallet for tx in best_window})
        severity = _severity_for_burst(len(best_window), span)

        explanation = (
            f"Wallet {wallet[:10]}... sent {len(best_window)} transactions within "
            f"{span:.0f} seconds ({span / 60:.1f} minutes), dispatching "
            f"{total_amount:.4f} ETH to {len(dest_wallets)} different addresses. "
            f"This unusually high transaction frequency is characteristic of "
            f"automated dispersal scripts used in smurfing and layering operations."
        )

        alerts.append(Alert(
            alert_id=_make_alert_id(wallet, tx_ids),
            pattern=PatternType.BURST,
            severity=severity,
            wallets=[wallet] + dest_wallets,
            transaction_ids=tx_ids,
            total_amount=total_amount,
            time_span_seconds=span,
            explanation=explanation,
            metadata={
                "source_wallet": wallet,
                "tx_count": len(best_window),
                "destination_count": len(dest_wallets),
                "window_seconds": window_seconds,
            },
        ))

    return alerts
