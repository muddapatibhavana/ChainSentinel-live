"""
ChainSentinel - Synthetic Transaction Provider
Supplies the deterministic 70-transaction synthetic dataset for reliable demo and testing.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from backend.data.loader import load_transactions, get_dataset_stats
    from backend.providers.base import BaseTransactionProvider
except (ImportError, ModuleNotFoundError):
    from data.loader import load_transactions, get_dataset_stats
    from providers.base import BaseTransactionProvider


class SyntheticTransactionProvider(BaseTransactionProvider):
    """Provides pre-generated synthetic forensic transaction data."""

    def __init__(self, csv_path: Optional[Path] = None):
        self._csv_path = csv_path
        self._cached_transactions: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        self._cached_transactions = load_transactions(self._csv_path)

    @property
    def name(self) -> str:
        return "Synthetic Forensic Ledger (Demo)"

    @property
    def mode(self) -> str:
        return "DEMO"

    def get_status(self) -> Dict[str, Any]:
        stats = get_dataset_stats(self._cached_transactions)
        return {
            "mode": self.mode,
            "provider_name": self.name,
            "healthy": True,
            "total_transactions": len(self._cached_transactions),
            "total_wallets": stats.get("total_wallets", 0),
            "total_volume_eth": stats.get("total_volume_eth", 0.0),
            "is_live": False,
            "description": "Deterministic 70-transaction dataset with 6 seeded forensic anomalies.",
        }

    def get_transactions(self) -> List[Dict[str, Any]]:
        return list(self._cached_transactions)

    def normalize_transaction(self, raw_tx: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tx_id": str(raw_tx["tx_id"]),
            "from_wallet": str(raw_tx["from_wallet"]),
            "to_wallet": str(raw_tx["to_wallet"]),
            "amount": float(raw_tx["amount"]),
            "timestamp": str(raw_tx["timestamp"]),
            "status": str(raw_tx.get("status", "SUCCESS")),
            "gas_fee": float(raw_tx.get("gas_fee", 0.002)),
            "category_label": str(raw_tx.get("category_label", "normal")),
            "description": str(raw_tx.get("description", "")),
        }
