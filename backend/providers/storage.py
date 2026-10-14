"""
ChainSentinel - SQLite Persistent Storage for Live Ethereum Transactions
Phase 11 - Thread-safe SQLite storage for real on-chain transactions,
processed blocks, checkpoint state, and Excel-compatible CSV exports.
"""

import os
import sqlite3
import csv
import io
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "live_chain.db"


class LiveStorage:
    """Manages SQLite persistence for live blockchain transactions and sync state."""

    def __init__(self, db_path: Optional[Path] = None):
        env_path = os.getenv("CHAINSENTINEL_DB_PATH")
        if env_path:
            self._db_path = Path(env_path).resolve()
        elif db_path:
            self._db_path = Path(db_path).resolve()
        else:
            self._db_path = DEFAULT_DB_PATH

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @property
    def db_path(self) -> Path:
        return self._db_path

    @contextmanager
    def _connection(self):
        """Yields an SQLite connection and guarantees immediate closure upon exit."""
        conn = sqlite3.connect(str(self._db_path), timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initializes tables and indexes if they do not already exist."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS live_transactions (
                    tx_hash TEXT PRIMARY KEY,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    amount_eth REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'SUCCESS',
                    gas_fee REAL DEFAULT 0.0,
                    category_label TEXT DEFAULT 'live_transfer',
                    description TEXT DEFAULT '',
                    block_number INTEGER,
                    block_hash TEXT,
                    receipt_status TEXT DEFAULT 'SUCCESS',
                    ingested_at TEXT NOT NULL
                );
            """)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_live_tx_block ON live_transactions(block_number);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_live_tx_time ON live_transactions(timestamp);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_live_tx_from ON live_transactions(from_address);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_live_tx_to ON live_transactions(to_address);")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS processed_blocks (
                    block_number INTEGER PRIMARY KEY,
                    block_hash TEXT NOT NULL,
                    parent_hash TEXT,
                    timestamp INTEGER,
                    tx_count INTEGER DEFAULT 0,
                    processed_at TEXT NOT NULL
                );
            """)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_proc_blocks_num ON processed_blocks(block_number);")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.commit()

    # ──────────────────────────────────────────────────────────────────
    # Transactions Persistence & Querying
    # ──────────────────────────────────────────────────────────────────

    def save_transactions(self, tx_list: List[Dict[str, Any]]) -> int:
        """
        Batch inserts normalized transactions into SQLite, ignoring duplicates.
        Returns the number of newly inserted transactions.
        """
        if not tx_list:
            return 0

        now_iso = datetime.now(timezone.utc).isoformat()
        records_to_insert = []
        for tx in tx_list:
            tx_hash = tx.get("tx_id") or tx.get("tx_hash") or tx.get("hash")
            if not tx_hash:
                continue
            from_addr = tx.get("from_wallet") or tx.get("from_address") or tx.get("from") or ""
            to_addr = tx.get("to_wallet") or tx.get("to_address") or tx.get("to") or "0x0000000000000000000000000000000000000000"
            amount = float(tx.get("amount") or tx.get("amount_eth") or 0.0)
            timestamp = str(tx.get("timestamp") or now_iso)
            status = str(tx.get("status") or "SUCCESS")
            gas_fee = float(tx.get("gas_fee") or 0.0)
            cat = str(tx.get("category_label") or "live_transfer")
            desc = str(tx.get("description") or "")
            block_num = tx.get("block_number")
            block_hash = tx.get("block_hash")
            receipt_status = str(tx.get("receipt_status") or status)
            ingested_at = str(tx.get("ingested_at") or now_iso)

            records_to_insert.append((
                str(tx_hash),
                str(from_addr).lower(),
                str(to_addr).lower(),
                amount,
                timestamp,
                status,
                gas_fee,
                cat,
                desc,
                int(block_num) if block_num is not None else None,
                str(block_hash) if block_hash else None,
                receipt_status,
                ingested_at
            ))

        if not records_to_insert:
            return 0

        with self._connection() as conn:
            cur = conn.cursor()
            cur.executemany("""
                INSERT OR IGNORE INTO live_transactions (
                    tx_hash, from_address, to_address, amount_eth, timestamp,
                    status, gas_fee, category_label, description,
                    block_number, block_hash, receipt_status, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records_to_insert)
            inserted_count = cur.rowcount
            conn.commit()

        return inserted_count

    def _row_to_tx_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Converts an SQLite row into a normalized ChainSentinel transaction dict."""
        return {
            "tx_id": row["tx_hash"],
            "tx_hash": row["tx_hash"],
            "from_wallet": row["from_address"],
            "from_address": row["from_address"],
            "to_wallet": row["to_address"],
            "to_address": row["to_address"],
            "amount": float(row["amount_eth"]),
            "amount_eth": float(row["amount_eth"]),
            "timestamp": row["timestamp"],
            "status": row["status"],
            "gas_fee": float(row["gas_fee"]),
            "category_label": row["category_label"],
            "description": row["description"],
            "block_number": row["block_number"],
            "block_hash": row["block_hash"],
            "receipt_status": row["receipt_status"],
            "ingested_at": row["ingested_at"],
        }

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single transaction by hash."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM live_transactions WHERE tx_hash = ? LIMIT 1", (str(tx_hash),))
            row = cur.fetchone()
            if row:
                return self._row_to_tx_dict(row)
        return None

    def get_all_transactions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns transactions ordered by insertion order ascending."""
        query = "SELECT * FROM live_transactions ORDER BY rowid ASC"
        params: Tuple = ()
        if limit:
            query += " LIMIT ?"
            params = (int(limit),)

        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [self._row_to_tx_dict(r) for r in rows]

    def get_sliding_window_transactions(self, max_count: int = 10000) -> List[Dict[str, Any]]:
        """
        Returns recent transactions for in-memory graph detection, capped at max_count.
        Preserves insertion order (oldest first).
        """
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM live_transactions
                WHERE rowid IN (
                    SELECT rowid FROM live_transactions
                    ORDER BY rowid DESC
                    LIMIT ?
                )
                ORDER BY rowid ASC
            """, (int(max_count),))
            rows = cur.fetchall()
            return [self._row_to_tx_dict(r) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Computes aggregate metrics from persistent live storage."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) as total_txs,
                    COALESCE(SUM(amount_eth), 0.0) as total_vol,
                    MIN(timestamp) as min_ts,
                    MAX(timestamp) as max_ts
                FROM live_transactions
            """)
            row = cur.fetchone()

            # Unique wallets
            cur.execute("""
                SELECT COUNT(DISTINCT addr) as wallet_count FROM (
                    SELECT from_address AS addr FROM live_transactions
                    UNION
                    SELECT to_address AS addr FROM live_transactions
                )
            """)
            w_row = cur.fetchone()

            # Latest block
            cur.execute("SELECT MAX(block_number) as max_block FROM processed_blocks")
            b_row = cur.fetchone()

        return {
            "total_transactions": row["total_txs"] if row else 0,
            "total_volume_eth": round(row["total_vol"] if row else 0.0, 4),
            "total_wallets": w_row["wallet_count"] if w_row else 0,
            "min_timestamp": row["min_ts"] if row else None,
            "max_timestamp": row["max_ts"] if row else None,
            "latest_block_number": b_row["max_block"] if b_row else None,
        }

    # ──────────────────────────────────────────────────────────────────
    # Processed Blocks Tracking
    # ──────────────────────────────────────────────────────────────────

    def record_processed_block(
        self,
        block_number: int,
        block_hash: str,
        parent_hash: Optional[str] = None,
        timestamp: Optional[int] = None,
        tx_count: int = 0
    ) -> None:
        """Records a successfully processed block."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO processed_blocks (
                    block_number, block_hash, parent_hash, timestamp, tx_count, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (int(block_number), str(block_hash), str(parent_hash or ""), timestamp, tx_count, now_iso))
            conn.commit()

    def is_block_processed(self, block_number: int) -> bool:
        """Checks if a block has already been processed."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM processed_blocks WHERE block_number = ? LIMIT 1", (int(block_number),))
            return cur.fetchone() is not None

    def get_latest_processed_block(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent processed block record."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM processed_blocks ORDER BY block_number DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                return {
                    "block_number": row["block_number"],
                    "block_hash": row["block_hash"],
                    "parent_hash": row["parent_hash"],
                    "timestamp": row["timestamp"],
                    "tx_count": row["tx_count"],
                    "processed_at": row["processed_at"],
                }
        return None

    def get_block_by_number(self, block_number: int) -> Optional[Dict[str, Any]]:
        """Retrieves a processed block by its number."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM processed_blocks WHERE block_number = ? LIMIT 1", (int(block_number),))
            row = cur.fetchone()
            if row:
                return {
                    "block_number": row["block_number"],
                    "block_hash": row["block_hash"],
                    "parent_hash": row["parent_hash"],
                    "timestamp": row["timestamp"],
                    "tx_count": row["tx_count"],
                    "processed_at": row["processed_at"],
                }
        return None

    def get_processed_blocks_count(self) -> int:
        """Returns the count of processed blocks."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM processed_blocks")
            return cur.fetchone()[0]

    # ──────────────────────────────────────────────────────────────────
    # Sync State Key-Value Store
    # ──────────────────────────────────────────────────────────────────

    def set_sync_state(self, key: str, value: str) -> None:
        """Sets a sync state string value."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO sync_state (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (str(key), str(value), now_iso))
            conn.commit()

    def get_sync_state(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a sync state string value."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM sync_state WHERE key = ? LIMIT 1", (str(key),))
            row = cur.fetchone()
            if row:
                return row["value"]
        return default

    # ──────────────────────────────────────────────────────────────────
    # Excel-Compatible CSV Export
    # ──────────────────────────────────────────────────────────────────

    def export_to_csv(self, target_filepath: Optional[str] = None) -> str:
        """
        Exports all persisted live transactions to an Excel-friendly CSV string or file.
        Uses UTF-8 with BOM for clean opening in Microsoft Excel.
        """
        txs = self.get_all_transactions()
        headers = [
            "tx_hash",
            "from_address",
            "to_address",
            "amount_eth",
            "timestamp",
            "block_number",
            "gas_fee",
            "status",
            "category_label",
            "description",
            "ingested_at"
        ]

        output = io.StringIO()
        # Add UTF-8 BOM so Excel opens non-ASCII and symbols accurately
        output.write('\ufeff')
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(headers)

        for tx in txs:
            writer.writerow([
                tx["tx_hash"],
                tx["from_address"],
                tx["to_address"],
                tx["amount_eth"],
                tx["timestamp"],
                tx["block_number"] if tx["block_number"] is not None else "",
                tx["gas_fee"],
                tx["status"],
                tx["category_label"],
                tx["description"],
                tx["ingested_at"]
            ])

        csv_content = output.getvalue()

        if target_filepath:
            out_path = Path(target_filepath).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, mode="w", encoding="utf-8-sig", newline="") as f:
                f.write(csv_content.lstrip('\ufeff'))  # utf-8-sig will write BOM automatically

        return csv_content

    def clear_all_data(self) -> None:
        """Clears all live tables (used for testing resets)."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM live_transactions;")
            cur.execute("DELETE FROM processed_blocks;")
            cur.execute("DELETE FROM sync_state;")
            conn.commit()
