"""
ChainSentinel - Risk Scoring Engine

Converts a list of alerts into an explainable risk score and level.

Scoring Logic:
  - Each pattern type has a base weight (see config.RISK_WEIGHTS).
  - For a single wallet, accumulate weights for each unique pattern type
    that appears in its alerts.
  - Map the cumulative score to a severity level using config.RISK_THRESHOLDS.

Score → Level mapping:
  score >= 60  → CRITICAL
  score >= 40  → HIGH
  score >= 20  → MEDIUM
  score <  20  → LOW

This is straightforward additive scoring. No random components.
The weight values and thresholds can be tuned in config.py.
"""

from typing import Dict, List

from .models import Alert, Severity, WalletRiskAssessment
from .config import RISK_WEIGHTS, RISK_THRESHOLDS


def score_to_level(score: int) -> str:
    """Map a numeric risk score to a severity level string."""
    if score >= RISK_THRESHOLDS["CRITICAL"]:
        return Severity.CRITICAL
    if score >= RISK_THRESHOLDS["HIGH"]:
        return Severity.HIGH
    if score >= RISK_THRESHOLDS["MEDIUM"]:
        return Severity.MEDIUM
    return Severity.LOW


def compute_wallet_risk(
    wallet_id: str,
    alerts: List[Alert],
) -> WalletRiskAssessment:
    """
    Given a wallet and all system alerts, compute the wallet's risk profile.
    Only alerts that mention the wallet are included.
    """
    # Filter alerts that involve this wallet
    wallet_alerts = [
        a for a in alerts
        if wallet_id in a.wallets
    ]

    if not wallet_alerts:
        return WalletRiskAssessment(
            wallet_id=wallet_id,
            risk_score=0,
            risk_level=Severity.LOW,
            alert_count=0,
            pattern_types=[],
            alerts=[],
            explanation=f"No suspicious patterns detected for wallet {wallet_id[:10]}...",
        )

    # Accumulate score: one weight per unique pattern type
    seen_patterns = set()
    total_score = 0
    for alert in wallet_alerts:
        if alert.pattern not in seen_patterns:
            total_score += RISK_WEIGHTS.get(alert.pattern, 10)
            seen_patterns.add(alert.pattern)

    risk_level = score_to_level(total_score)
    pattern_list = sorted(seen_patterns)

    # Build human-readable explanation
    pattern_lines = []
    for pattern in pattern_list:
        weight = RISK_WEIGHTS.get(pattern, 10)
        pattern_lines.append(f"  • {pattern.replace('_', ' ').title()} (+{weight} points)")

    explanation = (
        f"Wallet {wallet_id[:10]}... has a risk score of {total_score}/100 "
        f"({risk_level}) based on {len(wallet_alerts)} alert(s) "
        f"covering {len(seen_patterns)} pattern type(s):\n"
        + "\n".join(pattern_lines)
    )

    return WalletRiskAssessment(
        wallet_id=wallet_id,
        risk_score=min(total_score, 100),
        risk_level=risk_level,
        alert_count=len(wallet_alerts),
        pattern_types=pattern_list,
        alerts=[a.to_dict() for a in wallet_alerts],
        explanation=explanation,
    )


def compute_all_wallet_risks(alerts: List[Alert]) -> Dict[str, WalletRiskAssessment]:
    """
    Compute risk assessments for every wallet mentioned in any alert.
    Returns a dict keyed by wallet_id.
    """
    # Collect all unique wallets across all alerts
    all_wallets = set()
    for alert in alerts:
        all_wallets.update(alert.wallets)

    return {
        wallet: compute_wallet_risk(wallet, alerts)
        for wallet in all_wallets
    }
