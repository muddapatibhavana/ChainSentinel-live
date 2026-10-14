"""
ChainSentinel - Transaction Data Loader
Provides robust CSV/SQLite loading and filtering for transaction data.
Designed for maximum portability across all platforms and environments.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

DATA_DIR = Path(__file__).resolve().parent
CSV_PATH = DATA_DIR / "transactions.csv"


def load_transactions(csv_path: Optional[Path] = None) -> List[Dict]:
    """Loads transaction records from CSV into a structured list of dicts."""
    target_path = csv_path or CSV_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Transactions dataset not found at {target_path}")

    records = []
    with open(target_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "tx_id": row["tx_id"],
                "from_wallet": row["from_wallet"],
                "to_wallet": row["to_wallet"],
                "amount": float(row["amount"]),
                "timestamp": row["timestamp"],
                "status": row.get("status", "SUCCESS"),
                "gas_fee": float(row.get("gas_fee", 0.002)),
                "category_label": row.get("category_label", "normal"),
                "description": row.get("description", ""),
            })

    return records


def get_dataset_stats(records: Optional[List[Dict]] = None) -> Dict:
    """Computes summary metrics from transaction records."""
    if records is None:
        records = load_transactions()

    unique_wallets: Set[str] = set()
    total_volume = 0.0
    category_counts: Dict[str, int] = {}

    for tx in records:
        unique_wallets.add(tx["from_wallet"])
        unique_wallets.add(tx["to_wallet"])
        total_volume += tx["amount"]
        cat = tx["category_label"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    timestamps = [tx["timestamp"] for tx in records]
    min_ts = min(timestamps) if timestamps else ""
    max_ts = max(timestamps) if timestamps else ""

    return {
        "total_transactions": len(records),
        "total_wallets": len(unique_wallets),
        "total_volume_eth": round(total_volume, 4),
        "min_timestamp": min_ts,
        "max_timestamp": max_ts,
        "categories_breakdown": category_counts,
    }


if __name__ == "__main__":
    data = load_transactions()
    stats = get_dataset_stats(data)
    print("=== ChainSentinel Dataset Stats ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
