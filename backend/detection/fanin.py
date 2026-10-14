"""
ChainSentinel - Fan-In / Recombination Detector

Logic:
  For each receiver wallet, collect all inbound transactions within
  FANIN_WINDOW_SECONDS. If the wallet received from >= FANIN_MIN_SOURCES
  distinct wallets with total amount >= FANIN_MIN_TOTAL_AMOUNT, flag it.

  This is the mirror image of fan-out. Where fan-out disperses,
  fan-in aggregates — the final step of a layering cycle where
  cleaned funds are collected into a single controlled wallet.

  Why this avoids false positives:
    - DEX routers receive from many wallets but are publicly known contracts.
      We do not have a whitelist in this MVP, so the DEX router
      (0x88e6A0c2...) will be flagged at LOW/MEDIUM since it receives
      from 10 traders over 2.25 hours. This is a known limitation noted
      in the report.
    - Merchant wallets receive from shoppers over 2.75 hours (10 txs),
      which falls outside the 1-hour window, so they are NOT flagged.
    - The recombination collector (0x9999f8e4...) receives from 7 feeders
      in 18 minutes → HIGH severity.
"""

import hashlib
from typing import Dict, List

from .models import Alert, PatternType, Severity, Transaction
from .config import (
    FANIN_WINDOW_SECONDS,
    FANIN_MIN_SOURCES,
    FANIN_MIN_TOTAL_AMOUNT,
)


def _make_alert_id(wallet: str, tx_ids: List[str]) -> str:
    key = f"fanin:{wallet}:" + ":".join(sorted(tx_ids))
    return "alert_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _severity_for_fanin(source_count: int, total_amount: float, span_seconds: float) -> str:
    if source_count >= 6 and span_seconds <= 3600:
        return Severity.HIGH
    if source_count >= 4 and total_amount >= 20.0:
        return Severity.MEDIUM
    return Severity.LOW


def detect_fanin(
    transactions: List[Transaction],
    window_seconds: int = FANIN_WINDOW_SECONDS,
    min_sources: int = FANIN_MIN_SOURCES,
    min_total_amount: float = FANIN_MIN_TOTAL_AMOUNT,
) -> List[Alert]:
    """
    Detect fan-in / recombination patterns where many wallets
    channel funds into a single collector wallet within a short window.
    """
    if not transactions:
        return []

    # Group inbound by receiver, sorted chronologically
    inbound: Dict[str, List[Transaction]] = {}
    for tx in transactions:
        inbound.setdefault(tx.to_wallet, []).append(tx)

    for wallet in inbound:
        inbound[wallet].sort(key=lambda t: t.timestamp)

    alerts: List[Alert] = []

    for wallet, txs in inbound.items():
        # Sliding window: find window with most unique sources
        best_window: List[Transaction] = []

        for i, anchor_tx in enumerate(txs):
            window: List[Transaction] = [anchor_tx]
            for j in range(i + 1, len(txs)):
                delta = (txs[j].timestamp - anchor_tx.timestamp).total_seconds()
                if delta <= window_seconds:
                    window.append(txs[j])
                else:
                    break

            unique_sources_in_window = {tx.from_wallet for tx in window}
            best_sources = {tx.from_wallet for tx in best_window} if best_window else set()

            if len(unique_sources_in_window) > len(best_sources):
                best_window = window

        if not best_window:
            continue

        unique_sources = {tx.from_wallet for tx in best_window}
        if len(unique_sources) < min_sources:
            continue

        total_amount = sum(tx.amount for tx in best_window)
        if total_amount < min_total_amount:
            continue

        tx_ids = [tx.tx_id for tx in best_window]
        span = (best_window[-1].timestamp - best_window[0].timestamp).total_seconds()
        severity = _severity_for_fanin(len(unique_sources), total_amount, span)

        explanation = (
            f"Wallet {wallet[:10]}... received {total_amount:.4f} ETH from "
            f"{len(unique_sources)} distinct wallets within "
            f"{span / 60:.1f} minutes. "
            f"This fan-in (recombination) pattern is the aggregation phase of a "
            f"layering scheme: previously dispersed or obfuscated funds are "
            f"channelled back into a single controlled address for consolidation "
            f"before final extraction or use."
        )

        alerts.append(Alert(
            alert_id=_make_alert_id(wallet, tx_ids),
            pattern=PatternType.FAN_IN,
            severity=severity,
            wallets=[wallet] + list(unique_sources),
            transaction_ids=tx_ids,
            total_amount=total_amount,
            time_span_seconds=span,
            explanation=explanation,
            metadata={
                "collector_wallet": wallet,
                "source_count": len(unique_sources),
                "window_seconds": window_seconds,
            },
        ))

    return alerts
