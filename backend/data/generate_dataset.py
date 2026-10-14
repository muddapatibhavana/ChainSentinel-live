"""
ChainSentinel - Synthetic Transaction Dataset Generator
Generates realistic simulated blockchain transaction data with both
legitimate activity and deliberate suspicious topologies:
- Circular transactions
- Rapid movement (layering)
- Transaction bursts
- Splitting (fan-out / smurfing)
- Recombination (fan-in / aggregation)
- Suspicious wallet clusters
- Normal legitimate activity (retail, payroll, cold storage, DEX trades)
"""

import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = DATA_DIR / "transactions.csv"


def generate_tx_hash(seed_text: str) -> str:
    """Deterministic 66-character Ethereum transaction hash format: 0x..."""
    h = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return f"0x{h}"


def create_dataset():
    records = []
    base_time = datetime(2026, 10, 8, 8, 0, 0, tzinfo=timezone.utc)

    # =========================================================================
    # 1. CIRCULAR TRANSACTION (A -> B -> C -> D -> A)
    # =========================================================================
    # Origin and destination are identical within 20 mins, high fund retention
    circle_wallets = [
        "0x71C8366420A85E1A0F9b123D377De304559B0975",  # Wallet A (Origin / Target)
        "0x3a4b95d082E484d84f86f77b7389c9d4E00b144F",  # Wallet B
        "0xB72809dDcbFF77B96C005F9A4c4786638069a531",  # Wallet C
        "0x89D24A6b4CcB1B6fAA2625fE562bDD9a23260359",  # Wallet D
    ]
    circle_steps = [
        (circle_wallets[0], circle_wallets[1], 50.0, 0, "Circular Hop 1: Origin to Mule B"),
        (circle_wallets[1], circle_wallets[2], 49.5, 4, "Circular Hop 2: Mule B to Mule C"),
        (circle_wallets[2], circle_wallets[3], 49.1, 10, "Circular Hop 3: Mule C to Mule D"),
        (circle_wallets[3], circle_wallets[0], 48.7, 18, "Circular Hop 4: Mule D back to Origin A"),
    ]

    for i, (frm, to, amt, minute_offset, desc) in enumerate(circle_steps, start=1):
        ts = base_time + timedelta(minutes=minute_offset)
        tx_id = generate_tx_hash(f"circle_{i}_{frm}_{to}_{amt}")
        records.append({
            "tx_id": tx_id,
            "from_wallet": frm,
            "to_wallet": to,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0021,
            "category_label": "circular",
            "description": desc,
        })

    # =========================================================================
    # 2. RAPID MOVEMENT OF FUNDS (High Velocity Layering)
    # =========================================================================
    # Intermediate hops hold funds for under 90 seconds
    rapid_wallets = [
        "0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66",  # Feeder
        "0x42f703B8D4eF128E618EbAee48Ccf0b8Ffa55375",  # Relay 1
        "0x7E3523B06C783857500B8e974Ec272bBcEb96E69",  # Relay 2
        "0xDeB94101e4a6eD75d19830Af36691C2817865239",  # Exit CEX/Cashout
    ]
    rapid_steps = [
        (rapid_wallets[0], rapid_wallets[1], 120.0, 0, "Rapid Flow Hop 1: Feeder to Relay 1"),
        (rapid_wallets[1], rapid_wallets[2], 119.8, 65, "Rapid Flow Hop 2: Relay 1 to Relay 2 (65s hold)"),
        (rapid_wallets[2], rapid_wallets[3], 119.5, 130, "Rapid Flow Hop 3: Relay 2 to Exit (65s hold)"),
    ]
    rapid_start = base_time + timedelta(hours=1, minutes=15)
    for i, (frm, to, amt, sec_offset, desc) in enumerate(rapid_steps, start=1):
        ts = rapid_start + timedelta(seconds=sec_offset)
        tx_id = generate_tx_hash(f"rapid_{i}_{frm}_{to}_{amt}")
        records.append({
            "tx_id": tx_id,
            "from_wallet": frm,
            "to_wallet": to,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0035,
            "category_label": "rapid_movement",
            "description": desc,
        })

    # =========================================================================
    # 3. TRANSACTION BURSTS
    # =========================================================================
    # Wallet fires 10 rapid transactions in under 2 minutes
    burst_sender = "0x981C30E3259838B4268e64cCE608aC68fD573c88"
    burst_targets = [
        f"0xBb0000000000000000000000000000000000{i:04x}" for i in range(1, 11)
    ]
    burst_start = base_time + timedelta(hours=2, minutes=30)
    for i, target in enumerate(burst_targets, start=1):
        ts = burst_start + timedelta(seconds=i * 9)
        amt = round(3.5 + (i * 0.25), 2)
        tx_id = generate_tx_hash(f"burst_{i}_{burst_sender}_{target}")
        records.append({
            "tx_id": tx_id,
            "from_wallet": burst_sender,
            "to_wallet": target,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0018,
            "category_label": "burst",
            "description": f"Burst dispatch #{i} in rapid 90-second batch",
        })

    # =========================================================================
    # 4. SPLITTING (Fan-out / Smurfing)
    # =========================================================================
    # Single source distributes 80 ETH into 8 smaller amounts
    split_source = "0x323b5d4c32345ced77393b3530b1eed0f346429d"
    split_recipients = [
        f"0xCC0000000000000000000000000000000000{i:04x}" for i in range(1, 9)
    ]
    split_start = base_time + timedelta(hours=3, minutes=10)
    for i, recipient in enumerate(split_recipients, start=1):
        ts = split_start + timedelta(minutes=i * 2)
        amt = round(9.75 + (i * 0.05), 2)
        tx_id = generate_tx_hash(f"split_{i}_{split_source}_{recipient}")
        records.append({
            "tx_id": tx_id,
            "from_wallet": split_source,
            "to_wallet": recipient,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0022,
            "category_label": "split",
            "description": f"Smurfing fan-out branch #{i} from master source",
        })

    # =========================================================================
    # 5. RECOMBINATION (Fan-in / Aggregation)
    # =========================================================================
    # 7 disparate feeder wallets aggregate into a single collector
    collector_wallet = "0x9999f8e404F75eB9Ac49A1B3a0279c78D548F567"
    recomb_feeders = [
        f"0xDD0000000000000000000000000000000000{i:04x}" for i in range(1, 8)
    ]
    recomb_start = base_time + timedelta(hours=4, minutes=20)
    for i, feeder in enumerate(recomb_feeders, start=1):
        ts = recomb_start + timedelta(minutes=i * 3)
        amt = round(12.4 + (i * 0.3), 2)
        tx_id = generate_tx_hash(f"recomb_{i}_{feeder}_{collector_wallet}")
        records.append({
            "tx_id": tx_id,
            "from_wallet": feeder,
            "to_wallet": collector_wallet,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0020,
            "category_label": "recombination",
            "description": f"Fan-in tributary #{i} aggregated into collector",
        })

    # =========================================================================
    # 6. SUSPICIOUS WALLET CLUSTER (Dense Interconnected Mixing Ring)
    # =========================================================================
    cluster_nodes = [
        "0xEE01000000000000000000000000000000000001",
        "0xEE02000000000000000000000000000000000002",
        "0xEE03000000000000000000000000000000000003",
        "0xEE04000000000000000000000000000000000004",
        "0xEE05000000000000000000000000000000000005",
    ]
    cluster_transfers = [
        (0, 1, 15.0), (1, 2, 14.5), (2, 3, 14.0), (3, 4, 13.8), (4, 0, 13.5),
        (0, 2, 8.0),  (2, 4, 7.8),  (4, 1, 7.5),  (1, 3, 7.2),  (3, 0, 7.0),
        (1, 0, 4.0),  (3, 2, 3.8),
    ]
    cluster_start = base_time + timedelta(hours=5, minutes=0)
    for i, (src_idx, dst_idx, amt) in enumerate(cluster_transfers, start=1):
        ts = cluster_start + timedelta(minutes=i * 4)
        frm = cluster_nodes[src_idx]
        to = cluster_nodes[dst_idx]
        tx_id = generate_tx_hash(f"cluster_{i}_{frm}_{to}_{amt}")
        records.append({
            "tx_id": tx_id,
            "from_wallet": frm,
            "to_wallet": to,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0025,
            "category_label": "cluster",
            "description": f"Internal dense cluster circulation flow #{i}",
        })

    # =========================================================================
    # 7. NORMAL LEGITIMATE ACTIVITY (DEX, Payroll, Retail, Cold Storage)
    # =========================================================================
    payroll_wallet = "0x1000A892a0d1e38942b0e69F770b09489fDb1010"
    dex_router = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"
    cold_storage = "0x2000B901C412356191910A9292837381920B2020"
    merchant_wallet = "0x3000C888aB110022334455667788990011223344"

    # 7a. Regular Payroll (Periodic, distinct recipients)
    employees = [f"0x1111E{i:02d}00000000000000000000000000000000" for i in range(1, 6)]
    payroll_time = base_time + timedelta(hours=6, minutes=0)
    for i, emp in enumerate(employees, start=1):
        ts = payroll_time + timedelta(minutes=i * 12)
        records.append({
            "tx_id": generate_tx_hash(f"payroll_{i}_{emp}"),
            "from_wallet": payroll_wallet,
            "to_wallet": emp,
            "amount": 4.25,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0015,
            "category_label": "normal",
            "description": f"Corporate payroll compensation disbursement #{i}",
        })

    # 7b. DEX Swaps (Independent users trading via DEX router)
    dex_traders = [f"0x2222D{i:02d}00000000000000000000000000000000" for i in range(1, 11)]
    dex_time = base_time + timedelta(hours=7, minutes=0)
    for i, trader in enumerate(dex_traders, start=1):
        ts = dex_time + timedelta(minutes=i * 15)
        # Random trade between 0.2 and 5.0 ETH
        amt = round(0.5 + (i * 0.45), 2)
        records.append({
            "tx_id": generate_tx_hash(f"dex_{i}_{trader}"),
            "from_wallet": trader,
            "to_wallet": dex_router,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0042,
            "category_label": "normal",
            "description": f"DEX automated market maker liquidity swap #{i}",
        })

    # 7c. Retail Merchant checkouts (Small e-commerce transactions)
    shoppers = [f"0x3333S{i:02d}00000000000000000000000000000000" for i in range(1, 11)]
    merchant_time = base_time + timedelta(hours=9, minutes=0)
    for i, shopper in enumerate(shoppers, start=1):
        ts = merchant_time + timedelta(minutes=i * 18)
        amt = round(0.08 + (i * 0.04), 3)
        records.append({
            "tx_id": generate_tx_hash(f"merchant_{i}_{shopper}"),
            "from_wallet": shopper,
            "to_wallet": merchant_wallet,
            "amount": amt,
            "timestamp": ts.isoformat(),
            "status": "SUCCESS",
            "gas_fee": 0.0011,
            "category_label": "normal",
            "description": f"E-commerce point-of-sale checkout payment #{i}",
        })

    # 7d. Cold Storage Treasury Allocation (One-off large transfer)
    vault_time = base_time + timedelta(hours=12, minutes=0)
    records.append({
        "tx_id": generate_tx_hash("cold_storage_transfer"),
        "from_wallet": payroll_wallet,
        "to_wallet": cold_storage,
        "amount": 250.0,
        "timestamp": vault_time.isoformat(),
        "status": "SUCCESS",
        "gas_fee": 0.0028,
        "category_label": "normal",
        "description": "Quarterly enterprise treasury transfer to multi-sig cold storage vault",
    })

    # Sort all transactions chronologically by timestamp
    records.sort(key=lambda r: r["timestamp"])

    # Write to CSV
    fieldnames = [
        "tx_id",
        "from_wallet",
        "to_wallet",
        "amount",
        "timestamp",
        "status",
        "gas_fee",
        "category_label",
        "description",
    ]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} transactions in: {OUTPUT_CSV}")
    return records


if __name__ == "__main__":
    create_dataset()
