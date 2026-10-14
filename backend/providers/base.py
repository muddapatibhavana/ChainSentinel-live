"""
ChainSentinel - Base Transaction Provider
Defines the abstract interface and normalization contract for transaction data providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTransactionProvider(ABC):
    """Abstract base class for all transaction providers (Synthetic, Live RPC, Ingestion)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def mode(self) -> str:
        """Provider mode identifier: 'DEMO' or 'LIVE'."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns the operational status, health, and transaction statistics of this provider."""
        pass

    @abstractmethod
    def get_transactions(self) -> List[Dict[str, Any]]:
        """Returns the list of normalized transaction dictionaries."""
        pass

    @abstractmethod
    def normalize_transaction(self, raw_tx: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes a raw transaction payload into ChainSentinel's standard schema."""
        pass
