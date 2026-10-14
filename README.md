# ChainSentinel 🛡️
> Forensic Blockchain Transaction Investigation Platform (MVP)

> [!IMPORTANT]
> ### ⚠️ MANDATORY INSTRUCTION FOR ALL DEVELOPERS & AI AGENTS
> **DO NOT START CODING UNTIL YOU HAVE READ:**
> - [`PROJECT_STATE.md`](PROJECT_STATE.md) — Current state, completed features, metrics, and active phase boundary
> - [`ARCHITECTURE.md`](ARCHITECTURE.md) — System design, data flow, component models, and technical contracts
> - [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) — 15 engineering rules, phase workflow, and model handoff protocol

ChainSentinel is a full-stack blockchain transaction forensics and relationship analysis platform designed for investigators and analysts. It identifies suspicious money laundering topologies (circular flows, rapid movement, transaction bursts, smurfing splits, and mixer clusters) and verifies investigation case evidence using cryptographic hashing (SHA-256) and Merkle Trees.

---

## 📁 Project Structure

```
ChainSentinel/
├── frontend/                     # React + Vite + Tailwind CSS Investigation UI
│   ├── src/
│   │   ├── App.jsx               # Cyber-themed dashboard shell
│   │   ├── index.css             # Tailwind v4 dark cybersecurity styling
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js            # Configured with proxy to FastAPI backend (:8000)
├── backend/                      # Python + FastAPI Forensics Engine
│   ├── data/
│   │   ├── generate_dataset.py   # Synthetic transaction generator
│   │   ├── loader.py             # CSV/ledger loader & statistics
│   │   ├── transactions.csv      # 70 simulated transactions (normal & suspicious)
│   │   └── __init__.py
│   ├── providers/                # Pluggable transaction providers (Phase 10)
│   │   ├── base.py               # Provider abstract contract
│   │   ├── synthetic.py          # Benchmark dataset provider (default demo)
│   │   ├── live.py               # Live Ethereum RPC ingestion & normalization
│   │   ├── manager.py            # Provider manager & state hot-swapper
│   │   └── __init__.py
│   ├── detection/                # Rule-based pattern detection (Phase 3)
│   │   └── __init__.py
│   ├── crypto/                   # SHA-256 & Merkle Tree verification (Phase 5)
│   │   └── __init__.py
│   ├── analytics/                # Behavioral profiling & intelligence (Phase 8)
│   │   └── __init__.py
│   ├── tests/                    # Automated pytest suite (199 tests)
│   │   ├── test_basic.py         # Tests for dataset and API endpoints
│   │   ├── test_providers.py     # Tests for providers and mode switching
│   │   └── test_live_integration.py # Tests for SQLite persistence & live RPC
│   ├── main.py                   # FastAPI application & REST endpoints
│   ├── requirements.txt          # Python dependencies
│   └── venv/                     # Python virtual environment
├── PROJECT_STATE.md              # Project status, completed features, metrics, and phase boundary
├── ARCHITECTURE.md               # System design, data flow, component models, and contracts
├── DEVELOPMENT_GUIDE.md          # 15 engineering rules, phase workflow, and model handoff protocol
├── README.md                     # Documentation & setup instructions
└── .gitignore                    # Project ignore rules
```

---

## 📊 Synthetic Transaction Dataset

The synthetic ledger (`backend/data/transactions.csv`) includes **70 transactions** across **70 wallets** with a realistic mix of legitimate operations and deliberate suspicious forensic topologies:

| Pattern Category | Count | Description |
| :--- | :---: | :--- |
| **Circular** | 4 | A → B → C → D → A fund routing loop retaining ~97% capital |
| **Rapid Movement** | 3 | High-velocity layering across hops with <90s hold times |
| **Burst** | 10 | 10 rapid transactions fired in under 2 minutes from single wallet |
| **Split (Fan-out)** | 8 | Smurfing dispersal of funds into multiple small accounts |
| **Recombination (Fan-in)** | 7 | Multiple feeder wallets aggregating liquidity into a collector |
| **Cluster** | 12 | Dense interconnected mixing ring with circular flow cycles |
| **Normal Legitimate** | 26 | Payroll distributions, DEX liquidity swaps, cold storage, merchant checkouts |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Node.js 18+ (Tested on Node.js v24)
- npm 9+

---

### 1. Backend Setup & Run

Open a terminal in the root directory:

```bash
# Navigate to backend directory
cd ChainSentinel/backend

# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# (Optional: If installing fresh)
pip install -r requirements.txt

# Start the FastAPI development server
uvicorn main:app --reload --port 8000
```

The backend will be available at:
- **API Root / Health**: `http://127.0.0.1:8000/health`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Dataset Summary**: `http://127.0.0.1:8000/api/info`
- **Transaction Explorer**: `http://127.0.0.1:8000/transactions`

---

### 2. Frontend Setup & Run

Open a second terminal:

```bash
# Navigate to frontend directory
cd ChainSentinel/frontend

# (Optional: If installing fresh)
npm install

# Start the Vite development server
npm run dev
```

The frontend will be available at:
- `http://localhost:5173`

The frontend automatically proxies `/api/*` calls to the FastAPI backend running on port 8000.

---

### 3. Running Automated Tests

Run the backend test suite:

```bash
# From ChainSentinel root directory:
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### 3. Running Automated Tests

Run the comprehensive backend test suite:

```bash
# From ChainSentinel root directory:
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

All 199 automated tests verify:
- Health check, platform statistics, and transaction provider endpoints
- Synthetic dataset topological integrity
- Six modular graph detection algorithms (Circular, Rapid, Burst, Split, Recomb, Cluster)
- Deterministic risk scoring and severity aggregation
- Investigation case management, summaries, graphs, and audit timelines
- Cryptographic evidence canonicalization, SHA-256 digests, and Merkle tree audits
- Multi-hop directed flow tracer and path reconstruction
- Behavioral wallet profiling, 9 explainable classifications, and cross-pattern alert correlation
- Pluggable provider abstraction, live transaction normalization, and public RPC polling
- SQLite relational persistence, schema indexing, and deduplication
- Contract creation normalization (`to = null` -> `0x00...00`)
- Blockchain reorganization detection (`parentHash` mismatch)
- In-memory sliding-window pruning (capacity & time window)
- Checkpoint restoration from SQLite upon server restarts
- Excel-compatible CSV stream generation with UTF-8 BOM

---

## ⚡ Live Ethereum Integration & SQLite Persistence (Phase 11)

ChainSentinel features a production-ready live Ethereum ingestion engine while maintaining 100% deterministic offline demo capability:

1. **`DEMO` Mode (Default)**: Loads the deterministic 70-transaction benchmark dataset (`backend/data/transactions.csv`). Guarantees 100% offline uptime, reproducible alerts (21 alerts across 6 topologies), and zero network dependency.
2. **`LIVE` Mode**: Connects to the Ethereum blockchain via JSON-RPC:
   - **Zero-Config Public RPC**: Defaults to `https://ethereum-rpc.publicnode.com`. Override via environment variable `CHAINSENTINEL_RPC_URL` (e.g., Alchemy, Infura, or custom node).
   - **Autonomous Background Polling**: A dedicated background daemon thread (`ChainSentinel-LivePollWorker`) polls the canonical chain every 8 seconds (`CHAINSENTINEL_POLL_INTERVAL`).
   - **Persistent SQLite Storage**: Ingests all historical transactions into `backend/data/live_chain.db`. Persists across server restarts.
   - **Dual-Tier Sliding Window**: Retains a bounded window (default: last 2 hours or 10,000 transactions) in memory for sub-second NetworkX graph analysis and AML pattern matching without memory bloat.
   - **Reorganization Detection**: Automatically flags chain reorganizations when incoming `parentHash` mismatches previous recorded block height.
   - **Excel-Compatible CSV Export**: Click "Export CSV" in the navigation bar (or call `GET /api/provider/export-csv`) to download an audit-ready ledger with UTF-8 BOM encoding.
   - **Manual Poll Trigger**: Click "Poll Block" in the navigation bar to immediately ingest the latest Ethereum block on demand.

---

## 💻 Beginner-Friendly Windows PowerShell Run Guide

### Terminal 1 — Start the Backend
```powershell
cd "c:\Users\C-SQUARE\Desktop\Hackathons\TechHorizen 2.0\ChainSentinel\backend"
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Terminal 2 — Start the Frontend
```powershell
cd "c:\Users\C-SQUARE\Desktop\Hackathons\TechHorizen 2.0\ChainSentinel\frontend"
npm run dev
```

### Open in Browser
Visit **`http://localhost:5173`** in your browser.

### Stop Servers
In each PowerShell terminal, press **`Ctrl + C`** and type `Y` if prompted.

---

## 🗺️ Roadmap & Phases

- [x] **Phase 1**: Project Structure & Tooling (React + Vite + Tailwind, Python + FastAPI)
- [x] **Phase 2**: Synthetic Transaction Dataset (7 topologies, CSV loader, summary analytics)
- [x] **Phase 3**: Rule-Based Detection Engine (Circular, Rapid, Burst, Split, Recomb, Cluster algorithms)
- [x] **Phase 4**: Forensic Investigation Platform & UI Workflows (Case model, summary/graph APIs, forensic dashboard, alerts explorer, wallet deep-dive, case dossiers)
- [x] **Phase 5**: Cryptographic Evidence Integrity & Merkle Tree Verification (Canonical JSON, SHA-256 digests, Merkle root audits, tamper detection APIs)
- [x] **Phase 6**: Advanced Investigation Workflow (End-to-end flow: Alert → Wallet Deep Dive → Case Dossier → Evidence Anchoring → Merkle Audit → Investigation Chronology Timeline → Closure)
- [x] **Phase 7**: Flow Tracer & Path Reconstruction (Multi-hop path routing, temporal consistency, deterministic suspicion scoring, Cytoscape path visual highlighting, downstream discovery)
- [x] **Phase 8**: Advanced Analytics & Intelligence (Behavioral profiling, 9 explainable classifications, multi-pattern alert correlation, executive strategic dossiers, 5 REST endpoints, frontend intelligence visualizations)
- [x] **Phase 9**: Final Integration, Interactive UI Polish & Hackathon Demo Readiness (Dark cinematic cyber command center aesthetics, forensic workflow pipeline stepper, smooth Cytoscape animations & halo glows, glassmorphism cards, cross-view seamless navigation)
- [x] **Phase 10**: Production Hardening & Real-Time Ingestion Readiness (Pluggable provider layer, Ethereum JSON-RPC polling, dynamic transaction ingestion, navbar mode switcher, 183 tests passing)
- [x] **Phase 11**: Complete Live Ethereum Integration & SQLite Persistence (Autonomous daemon polling, SQLite storage, reorg detection, contract normalization, sliding window, CSV export, 199 tests passing)

