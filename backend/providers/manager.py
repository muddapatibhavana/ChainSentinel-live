"""
ChainSentinel - Transaction Provider Manager
Phase 11 - Coordinates synthetic demo data and real-time blockchain ingestion.
Provides hot-switching, background worker lifecycle management, and engine
update notification callbacks.
"""

import os
from typing import Any, Callable, Dict, List, Optional

try:
    from backend.providers.base import BaseTransactionProvider
    from backend.providers.synthetic import SyntheticTransactionProvider
    from backend.providers.live import LiveBlockchainProvider
except (ImportError, ModuleNotFoundError):
    from providers.base import BaseTransactionProvider
    from providers.synthetic import SyntheticTransactionProvider
    from providers.live import LiveBlockchainProvider


class ProviderManager:
    """Singleton manager controlling active data mode (DEMO vs LIVE) and transaction feeds."""

    MODE_DEMO = "DEMO"
    MODE_LIVE = "LIVE"

    def __init__(self):
        initial_mode = os.getenv("CHAINSENTINEL_DATA_MODE", self.MODE_DEMO).upper()
        self._mode = self.MODE_LIVE if initial_mode == self.MODE_LIVE else self.MODE_DEMO
        self._synthetic = SyntheticTransactionProvider()
        self._live = LiveBlockchainProvider()
        self._update_listeners: List[Callable[[], None]] = []

        # Connect live provider's new data callback to notify listeners
        self._live.set_on_new_data_callback(self._on_live_data_updated)

        # If starting in LIVE mode, start the polling thread
        if self._mode == self.MODE_LIVE:
            self._live.start_polling()

    def _on_live_data_updated(self) -> None:
        """Invoked when newly ingested live transactions update the in-memory window."""
        if self._mode == self.MODE_LIVE:
            self._notify_listeners()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def synthetic_provider(self) -> SyntheticTransactionProvider:
        return self._synthetic

    @property
    def live_provider(self) -> LiveBlockchainProvider:
        return self._live

    def register_listener(self, callback: Callable[[], None]) -> None:
        """Registers a callback hook invoked when transaction dataset changes or mode switches."""
        if callback not in self._update_listeners:
            self._update_listeners.append(callback)

    def _notify_listeners(self) -> None:
        for cb in self._update_listeners:
            try:
                cb()
            except Exception as err:
                print(f"[ProviderManager] Listener notification error: {err}")

    def get_active_provider(self) -> BaseTransactionProvider:
        """Returns the currently active transaction provider instance."""
        if self._mode == self.MODE_LIVE:
            return self._live
        return self._synthetic

    def get_transactions(self) -> List[Dict[str, Any]]:
        """Returns transactions from the active provider without deceptive fallbacks."""
        if self._mode == self.MODE_LIVE:
            return self._live.get_transactions()
        return self._synthetic.get_transactions()

    def switch_mode(self, new_mode: str) -> Dict[str, Any]:
        """Switches the active provider between DEMO and LIVE, managing worker threads cleanly."""
        target = new_mode.upper().strip()
        if target not in (self.MODE_DEMO, self.MODE_LIVE):
            raise ValueError(f"Invalid mode '{new_mode}'. Expected 'DEMO' or 'LIVE'.")

        if self._mode != target:
            if target == self.MODE_LIVE:
                self._mode = self.MODE_LIVE
                self._live.start_polling()
            else:
                self._live.stop_polling()
                self._mode = self.MODE_DEMO

            self._notify_listeners()

        return self.get_status()

    def ingest_live_transactions(self, raw_txs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingests raw transactions into the live provider and refreshes analytical models."""
        added = self._live.ingest_batch(raw_txs)
        live_count = len(self._live.get_transactions())
        return {
            "ingested_count": len(added),
            "total_live_transactions": live_count,
            "active_window_transactions": live_count,
            "total_persisted_transactions": self._live.get_status()["total_transactions"],
            "active_mode": self._mode,
        }

    def fetch_live_block(self, max_txs: int = 25) -> Dict[str, Any]:
        """Polls public RPC for latest block and normalizes transactions into the live feed."""
        added = self._live.fetch_latest_block_transactions(max_txs=max_txs)
        status = self._live.get_status()
        live_count = len(self._live.get_transactions())
        return {
            "fetched_count": len(added),
            "total_live_transactions": live_count,
            "active_window_transactions": live_count,
            "total_persisted_transactions": status["total_transactions"],
            "latest_block_number": status.get("latest_block_number"),
            "last_error": status.get("last_error"),
            "active_mode": self._mode,
            "mode": self._mode,
            "is_polling": self._live.is_polling(),
            "is_monitoring": self._live.is_polling(),
        }

    def pause_monitoring(self) -> Dict[str, Any]:
        """
        Pauses automatic background block polling while remaining in LIVE mode.
        Preserves all collected SQLite data and in-memory analytics.
        """
        self._live.stop_polling()
        return self.get_status()

    def resume_monitoring(self) -> Dict[str, Any]:
        """
        Resumes automatic background block polling if currently in LIVE mode.
        Avoids creating duplicate background workers.
        """
        if self._mode == self.MODE_LIVE:
            self._live.start_polling()
        return self.get_status()

    def export_live_csv(self, filepath: Optional[str] = None) -> str:
        """Exports all persisted live transactions to an Excel-friendly CSV string or file."""
        return self._live.export_csv(filepath)

    def shutdown(self) -> None:
        """Gracefully shuts down background polling workers."""
        self._live.stop_polling()

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of both providers and active mode configuration."""
        active_provider = self.get_active_provider()
        live_status = self._live.get_status()
        synthetic_status = self._synthetic.get_status()
        is_polling = self._live.is_polling()

        return {
            "mode": self._mode,
            "active_mode": self._mode,
            "is_live_active": self._mode == self.MODE_LIVE,
            "is_polling": is_polling,
            "is_monitoring": is_polling,
            "monitoring_status": "ACTIVE" if is_polling else "PAUSED",
            "active_provider_name": active_provider.name,
            "synthetic_status": synthetic_status,
            "live_status": live_status,
            "active_transaction_count": len(self.get_transactions()),
            "latest_block_number": live_status.get("latest_block_number"),
            "last_error": live_status.get("last_error"),
            "live_supported": True,
        }


# Global singleton instance
PROVIDER_MANAGER = ProviderManager()
