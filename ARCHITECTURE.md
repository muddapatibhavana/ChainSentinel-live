# ChainSentinel Architecture

## High-Level Architecture

ChainSentinel is structured as a decoupled full-stack platform consisting of a high-performance React forensic user interface and a deterministic Python/FastAPI analytical backend.

```text
┌────────────────────────────────────────────────────────┐
│            React / Vite Frontend (:5173)               │
│  - Forensic Dashboard & Activity Visualizations        │
│  - Cytoscape.js Wallet Graph Interaction               │
│  - Investigation & Evidence Verification Workflows     │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / JSON (via Vite Proxy /api)
                           ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI Backend (:8000)                  │
│  - REST Endpoints (/transactions, /alerts, /graph)     │
│  - In-Memory Response Caching & Pre-warmed Engine      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               Detection Engine Orchestrator            │
│  - Typed Domain Modeling (models.py)                   │
│  - 6 Modular Rule Detectors (NetworkX graph analysis)  │
│  - Flow Tracer & Path Reconstruction (tracer.py)       │
│  - Behavioral Intelligence & Profiler (analytics/)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 Risk Scoring Engine                    │
│  - Additive Pattern Weighting & Severity Thresholds    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│        Pluggable Transaction Provider Layer            │
│  - ProviderManager (Hot-Swappable DEMO / LIVE Mode)   │
│  - SyntheticTransactionProvider (70 Benchmark Txs)     │
│  - LiveBlockchainProvider (Public Ethereum RPC Ingest) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                      Data Layer                        │
│  - CSV Transaction Ledger (backend/data/transactions)  │
│  - Pure-Python Ingestion & Validation (loader.py)      │
│  - Live Ethereum JSON-RPC Feeds (Cloudflare / Custom)  │
└────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
ChainSentinel/
├── PROJECT_STATE.md                  # Persistent memory and phase completion record
├── ARCHITECTURE.md                   # System design, data flow, and technical contracts
├── DEVELOPMENT_GUIDE.md              # Engineering rules and handoff guidelines for AI agents
├── README.md                         # Project introduction and quickstart instructions
├── .gitignore                        # Git exclusion rules for node_modules, venv, and cache
├── frontend/                         # Client application
│   ├── package.json                  # React 19, Cytoscape, Lucide React, Tailwind v4
│   ├── vite.config.js                # Vite build config with backend proxy (:8000)
│   ├── index.html                    # Single-page application root HTML
│   ├── src/
│   │   ├── main.jsx                  # React application entry point
│   │   ├── App.jsx                   # Dark cybersecurity cockpit, tabs, and live data integration
│   │   ├── index.css                 # Tailwind v4 import and custom dark styling
│   │   ├── api/                      # Frontend API client layer (Phase 4B & Phase 10)
│   │   │   ├── client.js             # Universal fetch wrapper with direct/proxy fallback & provider methods
│   │   │   └── index.js              # Re-exports for components
│   │   └── components/
│   │       ├── AddEvidenceModal.jsx         # Modal for anchoring evidence with JSON validation
│   │       ├── AlertDetailModal.jsx         # Full forensic alert drill-down & evidence modal
│   │       ├── AlertsView.jsx               # Interactive alerts explorer with search, severity & pattern filters
│   │       ├── CaseTimeline.jsx             # Chronological investigation audit timeline with filters
│   │       ├── CreateCaseModal.jsx          # Modal for launching investigation cases
│   │       ├── DashboardView.jsx            # Cybersecurity command center with KPI metrics and pattern cards
│   │       ├── EvidenceIntegrityPanel.jsx   # Merkle tree & SHA-256 verification dashboard
│   │       ├── FlowTracerView.jsx           # Flow tracing, path reconstruction & route analysis cockpit (Phase 7)
│   │       ├── GraphViewer.jsx              # Cytoscape.js canvas component with controls, focus glow & path highlighting
│   │       ├── InvestigationsView.jsx       # Case management workspace with 5-step lifecycle & evidence
│   │       └── WalletInvestigationView.jsx  # Wallet deep-dive with risk gauge, graph & transaction ledger
│   └── dist/                         # Verified production bundle build
└── backend/                          # Forensics analytics backend
    ├── requirements.txt              # Backend dependencies (fastapi, uvicorn, networkx, etc.)
    ├── venv/                         # Python 3.12 isolated virtual environment
    ├── main.py                       # FastAPI application, CORS, and REST endpoints
    ├── __init__.py
    ├── providers/                    # Pluggable transaction provider layer (Phase 10)
    │   ├── __init__.py               # Package exports
    │   ├── base.py                   # BaseTransactionProvider abstract interface
    │   ├── synthetic.py              # Synthetic benchmark provider (70 transactions)
    │   ├── live.py                   # Live Ethereum RPC ingestion & normalization provider
    │   └── manager.py                # ProviderManager hot-swap controller & listener hub
    ├── data/                         # Ledger data layer
    │   ├── __init__.py
    │   ├── transactions.csv          # 70 simulated transactions (source of truth)
    │   ├── generate_dataset.py       # Deterministic transaction generator
    │   └── loader.py                 # CSV ingestion and metrics calculator
    ├── detection/                    # Forensic pattern detection engine
    │   ├── __init__.py               # Package exports
    │   ├── models.py                 # Dataclasses: Transaction, Alert, Risk, Summary
    │   ├── config.py                 # Centralized detector thresholds and scoring weights
    │   ├── circular.py               # Directed cycle detection via NetworkX
    │   ├── rapid_movement.py         # Low-latency relay hop tracker
    │   ├── burst.py                  # High-frequency transaction sliding window
    │   ├── fanout.py                 # Smurfing dispersal detector
    │   ├── fanin.py                  # Liquidity aggregation detector
    │   ├── clusters.py               # Dense subgraph / community detector
    │   ├── tracer.py                 # FlowTracer directed path reconstruction engine (Phase 7)
    │   ├── risk.py                   # Additive risk scoring engine
    │   └── engine.py                 # DetectionEngine orchestrator, graph extractor & flow tracer
    ├── investigations/               # Investigation case & timeline workflow (Phases 4 & 6)
    │   ├── __init__.py               # Package exports
    │   ├── models.py                 # InvestigationCase, TimelineEvent & ID generators
    │   └── store.py                  # In-memory case and timeline repository with JSON persistence
    ├── crypto/                       # Cryptographic evidence & Merkle verification (Phase 5)
    │   ├── __init__.py               # Package exports
    │   ├── models.py                 # EvidenceRecord dataclass & ID generator
    │   ├── canonical.py              # Deterministic JSON canonicalization & SHA-256 hashing
    │   ├── merkle.py                 # Binary Merkle tree, odd-leaf balancing & inclusion proofs
    │   └── store.py                  # In-memory evidence store with JSON persistence
    ├── analytics/                    # Advanced Analytics & Behavioral Intelligence (Phase 8)
    │   ├── __init__.py               # Package exports
    │   ├── models.py                 # Profile, classification, correlation & dossier dataclasses
    │   ├── profiler.py               # Deterministic feature extraction & behavioral classification
    │   ├── correlator.py             # Multi-pattern alert correlation & convergence detector
    │   └── intelligence.py           # Unified IntelligenceEngine facade & case dossier compiler
    └── tests/                        # Automated test suite (183 tests passing)
        ├── __init__.py
        ├── test_basic.py             # Phase 1/2 tests (7 tests)
        ├── test_detection.py         # Phase 3 detection tests (56 tests)
        ├── test_flow_tracer.py       # Phase 7 flow tracer & path reconstruction tests (18 tests)
        ├── test_investigations.py    # Phase 4/6 investigation & timeline tests (32 tests)
        ├── test_crypto.py            # Phase 5 cryptographic integrity tests (35 tests)
        ├── test_analytics.py         # Phase 8 analytics & intelligence tests (21 tests)
        └── test_providers.py         # Phase 10 provider & live ingestion tests (14 tests)
```

---

## Frontend

The frontend is an investigation cockpit built with:
- **Framework**: React 19 bootstrapped with Vite 8.
- **Styling**: Tailwind CSS v4 using a dark cybersecurity theme (`#0b0f19` background, slate cards, and neon severity badges).
- **API Client Layer (`frontend/src/api/client.js`)**: Universal API client providing clean async methods for all backend endpoints (`getHealth`, `getDatasetInfo`, `getDetectionSummary`, `getAlerts`, `getAlertById`, `getWalletRisk`, `getWalletTransactions`, `getWalletGraph`, `getInvestigations`, `getInvestigationSummary`, `getInvestigationGraph`). Handles automatic relative Vite proxy `/api` routing with graceful direct fallback to `http://127.0.0.1:8000`.
- **Interactive Graph Component (`frontend/src/components/GraphViewer.jsx`)**: Cytoscape.js canvas (`cytoscape@^3.34.3`) rendering live backend nodes and directed edges, with focus node highlight, flagged suspect coloring, transaction amounts, zoom/pan controls, and configurable hop depth traversal.
- **Iconography**: Lucide React (`lucide-react@^1.53.0`) for cybersecurity and system status indicators.
- **Proxying & CORS**: Configured in `vite.config.js` to route all `/api/*` requests directly to `http://127.0.0.1:8000`, with backend CORS enabled for all origins.
- **Frontend Data Flow**:
  `React UI (App.jsx) <──► API Layer (api/client.js) <──► Vite Proxy / CORS <──► FastAPI Backend (:8000) <──► Detection Engine / Case Store`

### Frontend Component Architecture

1. **Root Navigation Shell (`frontend/src/App.jsx`)**:
   - Manages top-level navigation across 5 primary tabs: **Dashboard**, **Alerts**, **Wallet Deep Dive**, **Flow Tracer**, and **Cases**.
   - Maintains cross-view state transitions (e.g. clicking "Investigate" or "Trace Flow" on an alert or case jumps directly to the Wallet Deep Dive, Flow Tracer, or Cases tab with pre-selected identifiers).
   - Real-time backend connectivity check pill indicator (`/health`).
   - Global alert modal and case creation modal state.

2. **Dashboard Command Center (`frontend/src/components/DashboardView.jsx`)**:
   - **KPI Metric Strip**: Real-time counts for Total Alerts (21), High/Critical Alerts (11), Medium Alerts (9), and Low Alerts (1).
   - **Pattern Breakdown Matrix**: 6 pattern detection cards with alert volume, severity breakdown, and pattern descriptions (Circular, Rapid Movement, Burst, Fan-Out, Fan-In, Suspicious Cluster). Clicking any card filters directly into the Alerts view.
   - **Top Threats Feed**: Immediate access to the highest-severity alerts with quick actions to inspect, investigate target wallet, or open case.

3. **Alerts Explorer (`frontend/src/components/AlertsView.jsx`)**:
   - Filter by severity (`ALL`, `HIGH`, `MEDIUM`, `LOW`) and pattern type.
   - Real-time keyword search across alert descriptions, pattern names, and implicated wallet addresses.
   - Multi-field sorting by severity weight, total transfer amount (ETH), and time window duration.
   - Direct triggers to view forensic evidence or launch an investigation.

4. **Alert Forensic Modal (`frontend/src/components/AlertDetailModal.jsx`)**:
   - Forensic detail inspection dialog showing full narrative explanation, aggregate ETH volume, time window (seconds/minutes), implicated wallet list with role identification, and transaction hashes.
   - Quick forensic action buttons: "Investigate Wallet" (opens deep dive), "View Graph" (loads neighborhood), and "Open Case" (pre-populates case creation modal).

5. **Wallet Deep Dive (`frontend/src/components/WalletInvestigationView.jsx`)**:
   - Address search bar with quick preset scenario buttons (Cycle Origin, Smurfing Hub, Cluster Core, Rapid Hop, Normal Trader).
   - Risk score gauge (0–100) with color-coded severity levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and contributing pattern breakdown.
   - Integrated Cytoscape.js neighborhood graph with 1–3 hop depth selector and auto-fit/zoom controls.
   - Full transaction ledger showing timestamp, direction (`IN` / `OUT`), counterparty wallet, amount (ETH), and category.

6. **Investigation Case Management (`frontend/src/components/InvestigationsView.jsx`)**:
   - Case list with status filtering (`ALL`, `OPEN`, `CLOSED`).
   - Detailed case dossier powered by `GET /investigations/{case_id}/summary` displaying case metadata, resolved alerts, target wallet risk assessment, and related wallet risk profiles.
   - Embedded interactive Cytoscape case graph via `GET /investigations/{case_id}/graph`.
   - **5-Step Case Lifecycle Stepper**: Visual indicator tracking case stages (`1. Opened` ──► `2. Alerts Linked` ──► `3. Evidence Anchored` ──► `4. Merkle Audited` ──► `5. Case Closed`).
   - **Quick Action Evidence Anchoring**: One-click buttons to anchor linked alerts, target wallet risk profiles, or individual transactions directly as cryptographic evidence items.
   - Embedded `EvidenceIntegrityPanel` for SHA-256 and Merkle verification.
   - Embedded `CaseTimeline` for chronological audit trail.
   - In-place editable analyst forensic notes (`PATCH /investigations/{case_id}/notes`).
   - One-click case status toggle (`PATCH /investigations/{case_id}/status`).

7. **Create Case Modal (`frontend/src/components/CreateCaseModal.jsx`)**:
   - Pre-fills target wallet, associated alert IDs, and related counterparty addresses from any view.
   - Validates input and persists cases to the backend (`POST /investigations`).

8. **Interactive Graph Canvas (`frontend/src/components/GraphViewer.jsx`)**:
   - Canvas-based rendering with Cytoscape.js using circular and cose-bilkent layout strategies.
   - Focus node cyan glow, flagged suspect red nodes, counterparty slate nodes, directional arrows, and transfer amount labels.
   - Route path highlighting: distinct styling for origin/source (emerald), destination (purple), path hops (cyan), and background element dimming.
   - Node click inspection, responsive resizing, and full zoom/pan navigation.

9. **Add Evidence Modal (`frontend/src/components/AddEvidenceModal.jsx`)**:
   - Anchors forensic artifacts to the active case (`POST /investigations/{case_id}/evidence`).
   - Supports 6 evidence types: `TRANSACTION`, `ALERT`, `WALLET_RISK`, `ANALYST_NOTE`, `GRAPH_SNAPSHOT`, `CUSTOM`.
   - Live JSON validation editor with formatting helper and analyst contextual description field.

10. **Evidence Integrity Panel (`frontend/src/components/EvidenceIntegrityPanel.jsx`)**:
    - Real-time cryptographic verification interface displaying anchored evidence count, verified ratio, and Merkle root.
    - One-click copy for 64-character hex Merkle roots.
    - Full collection audit against Merkle root (`POST /investigations/{case_id}/evidence/merkle/verify`) with success banner and audited leaf breakdown.
    - Per-item on-demand verification buttons (`GET /evidence/{evidence_id}/verify`) with pass/fail badges.
    - Expandable canonical JSON payload viewer for forensic inspection.

11. **Case Chronology Timeline (`frontend/src/components/CaseTimeline.jsx`)**:
    - Chronological event stream (`GET /investigations/{case_id}/timeline`) reconstructing the lifecycle of the investigation.
    - Distinct event badges: `CASE_CREATED`, `ALERT_LINKED`, `EVIDENCE_ANCHORED`, `INTEGRITY_VERIFIED`, `STATUS_CHANGED`, `NOTES_UPDATED`.
    - Human-readable relative elapsed time plus exact ISO/UTC timestamps.
    - Sort order toggle (`asc` chronological vs `desc` reverse-chronological).

12. **Flow Tracer Cockpit (`frontend/src/components/FlowTracerView.jsx`)**:
    - Dedicated routing analysis workbench for topological fund tracing between arbitrary source/target wallets.
    - Metric strip displaying hop count, total transferred ETH, transit duration, temporal consistency, and deterministic suspicion tier.
    - Integrated Cytoscape visual route canvas with neon path emphasizing source, destination, and intermediate path hops while dimming background elements.
    - Chronological hop-by-hop ledger detailing sender/recipient risk, amount, timestamp, tx hash, and forensic signatures.
    - Downstream discovery view when destination is unspecified, ranking reachable branches by suspicion and value.
    - Direct integration hook to anchor reconstructed flow paths as cryptographic case evidence.

---

## Backend

The backend is built with **FastAPI** (`backend/main.py`), running under **Uvicorn**:
- **Dual-mode Module Imports**: Supports both running directly via `uvicorn main:app` from `backend/` and `uvicorn backend.main:app` from the project root.
- **CORS Configuration**: Wildcard CORS enabled for seamless cross-origin communication.
- **In-Memory Caching**: On startup, transactions are parsed into domain models, the `DetectionEngine` is pre-warmed once, and results are cached in memory for sub-millisecond API response latency.
- **REST Endpoints**:
  - Platform health (`/health`)
  - Ledger discovery (`/api/info`, `/transactions`, `/transactions/{tx_id}`)
  - Detection results (`/alerts`, `/alerts/{alert_id}`, `/detection/summary`)
  - Wallet analytics (`/wallets/{wallet_id}/risk`, `/wallets/{wallet_id}/alerts`, `/wallets/{wallet_id}/transactions`)
  - Topological exploration (`/graph/{wallet_id}`)
  - Investigation cases (`/investigations`, `/investigations/{case_id}`, `/investigations/{case_id}/status`, `/investigations/{case_id}/notes`, `/investigations/{case_id}/summary`, `/investigations/{case_id}/graph`, `/investigations/{case_id}/timeline`)
  - Cryptographic evidence & Merkle verification (`/investigations/{case_id}/evidence`, `/evidence/{evidence_id}`, `/evidence/{evidence_id}/verify`, `/investigations/{case_id}/evidence/merkle`, `/investigations/{case_id}/evidence/merkle/verify`)

---

## Data Layer

The dataset resides in `backend/data/transactions.csv` and is ingested via `backend/data/loader.py`.

### CSV Columns:
1. `tx_id`: Unique 66-character hex hash starting with `0x`.
2. `from_wallet`: Sender address (case-sensitive string).
3. `to_wallet`: Recipient address (case-sensitive string).
4. `amount`: Transaction value in ETH (`float`).
5. `timestamp`: ISO-8601 UTC timestamp string (e.g., `2026-10-08T08:00:00+00:00`).
6. `status`: Transaction execution status (`SUCCESS`).
7. `gas_fee`: Network transaction fee in ETH (`float`).
8. `category_label`: Ground-truth tag (`circular`, `rapid_movement`, `burst`, `split`, `recombination`, `cluster`, `normal`).
9. `description`: Human-readable investigative scenario description.

### Loader Design:
`loader.py` avoids third-party binary compiled dependencies. It parses CSV rows directly using Python's standard `csv.DictReader`, normalizing numerical amounts, timestamps, and computing global volume and category statistics.

---

## Detection Engine

The detection architecture (`backend/detection/`) separates concerns across specialized modules:

1. **`models.py`**:
   - `Transaction`: Typed dataclass representing an immutable blockchain transfer with tz-aware UTC timestamps.
   - `Alert`: Standardized alert object containing `alert_id`, `pattern`, `severity`, `wallets`, `transaction_ids`, `total_amount`, `time_span_seconds`, `explanation`, and `metadata`.
   - `WalletRiskAssessment`: Aggregated profile containing `wallet_id`, `risk_score` (0–100), `risk_level`, `pattern_types`, `alerts`, and narrative `explanation`.
   - `DetectionSummary`: System-level summary of alerts categorized by pattern and severity.
2. **`config.py`**:
   - Central declaration of all time windows, hop limits, thresholds, risk weights, and severity tiers. No magic constants exist in detector logic.
3. **Detectors**:
   - `circular.py`: Constructs NetworkX multigraph, runs elementary cycle enumeration, filters by temporal window ($\le 2$ hours) and path length (3–10 nodes).
   - `rapid_movement.py`: Relational chain-following algorithm tracing rapid passthrough transactions with hold times $\le 300$ seconds.
   - `burst.py`: Sliding-window density evaluation detecting $\ge 5$ transactions in $\le 300$ seconds from a single sender.
   - `fanout.py`: Detects volume dispersal to $\ge 4$ unique destinations within 1 hour, calculating variance ratios to discern batch payroll.
   - `fanin.py`: Detects liquidity aggregation from $\ge 4$ unique sources into a collector within 1 hour.
   - `clusters.py`: Extracts weakly connected components, calculating directed edge density $e / [n(n-1)] \ge 0.30$ to flag mixing networks.
4. **`risk.py`**:
   - Aggregates detected pattern types per wallet using additive weights and maps the resulting score to standardized severity tiers.
5. **`engine.py`**:
   - Coordinates all detectors via `DetectionEngine.detect_all()`.
   - Provides wallet-specific queries via `detect_for_wallet()` and `get_wallet_risk()`.
   - Extracts $k$-hop subgraphs via `get_wallet_graph()` for graph rendering.

---

## Investigation Workflow & Timeline Layer (Phases 4 & 6)

The investigation workflow provides analyst case management, timeline chronology, and auditability on top of the detection and crypto layers:

1. **`models.py` (`backend/investigations/models.py`)**:
   - `InvestigationCase`: Domain dataclass holding `case_id`, `title`, `target_wallet`, `status` (`OPEN` / `CLOSED`), `notes`, `alert_ids`, `related_wallets`, and UTC timestamps (`created_at`, `updated_at`).
   - `InvestigationTimelineEvent`: Domain dataclass holding `event_id`, `case_id`, `event_type` (`CASE_CREATED`, `ALERT_LINKED`, `EVIDENCE_ANCHORED`, `INTEGRITY_VERIFIED`, `STATUS_CHANGED`, `NOTES_UPDATED`), `title`, `description`, `timestamp`, and `metadata`.
   - `generate_case_id()`: Creates deterministic, collision-resistant case IDs (`CASE-<8 hex chars>`).
   - `generate_event_id()`: Creates collision-resistant timeline event IDs (`EVT-<8 hex chars>`).
2. **`store.py` (`backend/investigations/store.py`)**:
   - `InvestigationCaseStore`: In-memory repository with thread-safe dictionary lookup and automatic JSON file persistence (`cases.json`). Automatically records lifecycle audit events when cases are opened, status is changed, or notes are saved.
   - Singleton instance `CASE_STORE` shared across API route handlers.
3. **Forensic Summary Aggregation (`GET /investigations/{case_id}/summary`)**:
   - Assembles a unified forensic dossier: case metadata, resolved alert objects, target wallet risk assessment, target wallet transaction history, and risk assessments for all tagged related wallets in a single query.
4. **Investigation Graph (`GET /investigations/{case_id}/graph`)**:
   - Reuses the Phase 3 NetworkX-based graph traversal engine (`ENGINE.get_wallet_graph`) centered on the case's target wallet, returning Cytoscape.js compatible nodes, edges, flagged wallet highlights, and configurable hop depth (1–3 hops).
5. **Chronological Investigation Timeline (`GET /investigations/{case_id}/timeline`)**:
   - Synthesizes all historical events into a unified, chronological timeline: case creation, alerts linked, evidence anchored, Merkle integrity audits, status transitions, and note updates. Supports ascending/descending temporal sorting.

---

## Cryptographic Evidence & Integrity Layer (Phase 5)

ChainSentinel includes a tamper-evident cryptographic audit layer built on SHA-256 and binary Merkle trees:

```text
Investigation Case
        │
        ▼
Evidence Payload (Transaction, Alert, Wallet Risk, Analyst Finding)
        │
        ▼ (canonical.py)
Sorted-Key Canonical JSON  (whitespace-normalized, ASCII-safe)
        │
        ▼ (hashlib.sha256)
SHA-256 Evidence Hash (bound to EvidenceRecord)
        │
        ▼ (store.py)
Tamper-Evident Evidence Store (in-memory + evidence.json)
        │
        ▼ (merkle.py)
Deterministic Binary Merkle Tree (trailing-duplicate odd leaf balancing)
        │
        ▼
Case Merkle Root & Inclusion Audit Proofs
```

### Components

1. **`models.py` (`backend/crypto/models.py`)**:
   - `EvidenceRecord`: Domain dataclass holding `evidence_id`, `case_id`, `evidence_type` (`TRANSACTION`, `ALERT`, `WALLET_RISK`, `ANALYST_NOTE`, `GRAPH_SNAPSHOT`, `CUSTOM`), `source_ref`, `content`, `created_at`, `evidence_hash`, and `metadata`.
   - `generate_evidence_id()`: Creates collision-resistant IDs (`EVID-<8 hex chars>`) using case ID, evidence type, timestamp, and entropy.
2. **`canonical.py` (`backend/crypto/canonical.py`)**:
   - `canonicalize(data)`: Produces a deterministic, whitespace-normalized, sorted-key JSON string via standard `json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)`. Guarantees identical byte representations regardless of dictionary key insertion order.
   - `hash_data(data)`: Standard SHA-256 digest via Python's `hashlib` (pure standard library, eliminating unsafe non-deterministic Python `hash()`).
   - `compute_evidence_hash()` / `verify_evidence_hash()`: Computes and verifies cryptographic hashes for evidence payloads.
3. **`merkle.py` (`backend/crypto/merkle.py`)**:
   - `MerkleTree`: Binary Merkle tree implementation.
   - **Deterministic Sorting**: Leaf hashes are sorted lexicographically by default, guaranteeing consistent root generation regardless of evidence submission order.
   - **Empty Collections**: Returns canonical digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (SHA-256 of empty bytes `b""`).
   - **Single Leaf**: Returns the leaf hash itself as the root.
   - **Odd-Leaf Balancing**: When any tree layer contains an odd number of nodes (> 1), the final un-paired node is duplicated (paired with itself: `hash_pair(node, node)`), adhering to the Bitcoin/RFC 6962 binary Merkle standard.
   - **Inclusion Proofs**: Generates cryptographic audit paths (`get_proof`) and verifies them (`verify_proof`).
4. **`store.py` (`backend/crypto/store.py`)**:
   - `EvidenceStore`: Thread-safe dictionary repository with JSON file persistence (`evidence.json`).
   - Singleton instance `EVIDENCE_STORE` shared across API route handlers.


## Risk Model

The risk model is deterministic, explainable, and transparent for hackathon demonstration:

### Pattern Weights (`config.py`):
```python
RISK_WEIGHTS = {
    "CIRCULAR_TRANSACTION": 30,
    "SUSPICIOUS_CLUSTER":   25,
    "FAN_OUT_SPLIT":        20,
    "FAN_IN_RECOMBINATION": 20,
    "RAPID_MOVEMENT":       20,
    "TRANSACTION_BURST":    15,
}
```

### Severity Tiers:
```python
RISK_THRESHOLDS = {
    "CRITICAL": 60,   # Score >= 60
    "HIGH":     40,   # Score >= 40
    "MEDIUM":   20,   # Score >= 20
    # Score < 20 -> LOW
}
```

**Scoring Invariant**: Each pattern contributes once per wallet regardless of how many individual alerts it generates, preventing duplicate alert penalties. Scores are strictly capped at 100.

---

## Graph Representation

The platform prepares relationship graphs for frontend visualization with Cytoscape.js:

- **Nodes**: Represent wallets. Node data includes `id` (full address), `label` (truncated address), `flagged` (`boolean` indicating if the wallet is implicated in any alert), and `is_focus` (`boolean` indicating the investigator's query target).
- **Edges**: Represent directed transactions. Edge data includes `id` (`tx_id`), `source` (`from_wallet`), `target` (`to_wallet`), `amount` (float), `label` (formatted ETH), and `category`.
- **Extraction**: `DetectionEngine.get_wallet_graph(wallet_id, depth)` performs breadth-first expansion up to `depth` hops (default 2), assembling a clean subgraph containing only relevant interacting nodes.

---

## Data Flow

```text
transactions.csv
      │
      ▼ (read by loader.py)
List[Dict]
      │
      ▼ (instantiated in engine.py)
List[Transaction]
      │
      ├───────────────────────┬───────────────────────┬───────────────────────┐
      ▼                       ▼                       ▼                       ▼
circular.py             rapid_movement.py        burst.py / fanout.py    clusters.py
      │                       │                       │                       │
      └───────────────────────┴───────────────────────┴───────────────────────┘
                                      │
                                      ▼
                                 List[Alert]
                                      │
                                      ▼ (aggregated by risk.py)
                           Dict[wallet_id, WalletRiskAssessment]
                                      │
                                      ▼ (exposed via main.py)
                        FastAPI REST Endpoints
                                      │
                                      ▼ (consumed by React UI)
                           Investigation Dashboard
```

---

## Phase 8 — Advanced Analytics & Behavioral Intelligence Architecture

Phase 8 elevates ChainSentinel from raw pattern detection to explainable, strategic behavioral intelligence.

### 1. Behavioral Profiling Engine (`backend/analytics/profiler.py`)
- **Metric Extraction**: Extracts 20+ deterministic features per wallet: inbound/outbound transaction counts and volume, net flow (accumulator vs distributor), unique counterparty breadth, active time span, transaction frequency (tx/hour), and average/peak transfer sizes.
- **Explainable Taxonomies (9 Behavioral Classifications)**:
  - `NORMAL`: Standard operating baseline with balanced flows and zero alerts.
  - `HIGH_VOLUME`: High-volume treasury transfers (>100 ETH) without malicious topology.
  - `HIGH_VELOCITY`: Rapid passthrough hops forwarding funds with short hold periods (<300s).
  - `FAN_OUT`: Smurfing dispersal distributing funds to multiple downstream destinations.
  - `FAN_IN`: Liquidity consolidation collecting funds from multiple disparate feeders.
  - `CIRCULAR`: Closed routing loops returning capital to the originating entity.
  - `MIXER_LIKE`: High-density reciprocal circulation within tightly interconnected mixing rings.
  - `MULTI_PATTERN`: Simultaneous convergence across >= 2 distinct suspicious topologies.
  - `HIGH_RISK`: Elevated forensic risk scores (>= 60/100) with multiple high/critical alerts.
- **Priority Tiering**: Maps behavioral signatures into deterministic investigation priorities: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Observable Signal Generation**: Synthesizes human-auditable evidence statements for court/analyst review.

### 2. Alert Correlation Engine (`backend/analytics/correlator.py`)
- **Topological Convergence**: Detects multi-pattern intersection where a wallet or tightly coupled entity cluster participates in multiple alert topologies simultaneously.
- **Entity & Temporal Clustering**: Correlates alerts spanning shared wallets and overlapping time windows.
- **Confidence & Severity Scoring**: Assigns deterministic confidence (`HIGH`, `MEDIUM`, `LOW`) and severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) based on pattern count and alert severity.
- **Narrative Explanations**: Generates forensic explanations detailing exactly why the convergence represents an elevated laundering risk.

### 3. Unified Intelligence Facade (`backend/analytics/intelligence.py`)
- **`IntelligenceEngine` Orchestrator**: Singleton uniting the profiler, correlator, `DetectionEngine`, `CASE_STORE`, and `EVIDENCE_STORE`.
- **Wallet Intelligence Dossier**: Complete dossier combining profile metrics, classifications, observable signals, correlated patterns, and risk narrative.
- **Investigation-Level Strategic Dossier**: Executive intelligence brief including strategic priority score (0–100), case-level turnover volume, dominant pattern vectors, suspicious counterparty threat matrix, anchored evidence count, and cryptographic Merkle verification status.

---

## Architectural Decisions

1. **Rule-Based Deterministic Algorithms instead of ML**:
   For an MVP and hackathon judging, explainability is paramount. Deterministic graph and sliding-window rules yield clear explanations ("Funds moved through 4 wallets and returned in 18 minutes") rather than opaque black-box neural scores.
2. **Synthetic Realistic Dataset instead of Live Blockchain APIs**:
   Live blockchain RPC nodes are rate-limited, slow, and unpredictable during demonstrations. A pre-seeded synthetic dataset guarantees instantaneous responses and reliable reproduction of all 6 suspicious topologies.
3. **Pure-Python Data Ingestion over Pandas**:
   In Windows environments with Application Control (WDAC) policies, compiled binary C-extensions (such as `pandas._libs.hashing.pyd`) can be blocked from running in desktop folders. The system uses Python's standard library `csv` and pure-Python `networkx`, eliminating fragile binary `.dll`/`.pyd` execution risks.
4. **NetworkX for Topology Analysis**:
   NetworkX is a battle-tested, pure-Python graph analytics library that supports directed cycle enumeration (`simple_cycles`), connected components (`weakly_connected_components`), and subgraph density metrics.
5. **FastAPI for Asynchronous Forensics Services**:
   Provides automatic OpenAPI documentation (`/docs`), strong Pydantic typing, high throughput, and zero configuration for CORS.
6. **Cytoscape.js for Graph Visualizations**:
   Cytoscape.js is the gold standard for high-performance canvas-based network graph visualization, supporting custom node badges, edge weights, and path highlighting.
7. **Cryptographic Integrity & Merkle Preservation (Phase 5 & 6)**:
   Deterministic canonical JSON serialization, SHA-256 standard digests, and RFC 6962-compliant binary Merkle trees anchor case evidence into tamper-evident proofs.
8. **Explainable Behavioral Intelligence over Black-Box Scoring (Phase 8)**:
   Behavioral profiling uses explicit, inspectable criteria (flow balance, counterparty breadth, velocity, loop topology) allowing forensic investigators to defend their conclusions under regulatory and legal examination.
9. **Pluggable Transaction Provider Architecture with Deterministic Fallback (Phase 10)**:
   Separating transaction ingestion behind `BaseTransactionProvider` and `ProviderManager` allows seamless transition between synthetic benchmark scenarios and live blockchain RPC nodes. By defaulting to `SyntheticTransactionProvider`, the application guarantees 100% demo uptime and deterministic test repeatability without network flakiness.

---

## Phase 10 — Pluggable Transaction Provider & Real-Time Ingestion Architecture

### 1. Architectural Motivation
Prior to Phase 10, the system read statically from `backend/data/transactions.csv`. In Phase 10, the data access layer was refactored into a modular provider interface to allow:
- Zero-downtime hot-swapping between pre-baked benchmark scenarios (`DEMO`) and live on-chain feeds (`LIVE`).
- Direct JSON batch ingestion from external telemetry systems or microservices.
- Polling of live Ethereum blocks via standard Ethereum JSON-RPC without introducing heavy web3 dependencies.

### 2. Provider Abstraction Contract (`backend/providers/base.py`)
All transaction providers adhere to `BaseTransactionProvider`:
- `get_transactions() -> List[Transaction]`: Returns the current dataset of typed transactions.
- `get_transaction(tx_id: str) -> Optional[Transaction]`: O(1) single transaction lookup.
- `ingest(raw_txs: List[Dict[str, Any]]) -> int`: Ingests and normalizes external transaction payloads into active memory.
- `fetch_live(max_txs: int) -> Dict[str, Any]`: Queries the active blockchain RPC endpoint for block transfers.
- `count() -> int`: Returns current record count.

### 3. Concrete Providers
- **`SyntheticTransactionProvider` (`backend/providers/synthetic.py`)**: Loads the 70 benchmark forensic transactions (1,200.45 ETH) from `backend/data/transactions.csv`. Provides an immutable baseline for deterministic demonstration of all 6 suspicious topologies.
- **`LiveBlockchainProvider` (`backend/providers/live.py`)**:
  - Connects to Ethereum public RPC (defaulting to Cloudflare public node `https://cloudflare-eth.com`, configurable via `CHAINSENTINEL_RPC_URL`).
  - Implements lightweight, non-blocking JSON-RPC `eth_getBlockByNumber("latest", true)` requests using standard Python `urllib.request`.
  - Normalizes hex values (e.g., `value`, `gasPrice`) into standard decimal ETH floats and unix timestamps.
  - Dynamically appends transactions to an in-memory ledger with deduplication.

### 4. Provider Manager & Engine Synchronization (`backend/providers/manager.py`)
`ProviderManager` acts as the single entry point for the backend application:
- Coordinates active mode (`DEMO` vs `LIVE`).
- Manages an observer subscription pattern (`register_listener(callback)`).
- When a mode change or dynamic ingestion occurs, the registered callback rebuilds the `DetectionEngine` and `IntelligenceEngine` cache in memory, ensuring immediate synchronization across all downstream endpoints (`/alerts`, `/wallets/*`, `/graph/*`, `/flow/*`, `/analytics/*`).

---

## Phase 11 — Live Ethereum Integration, SQLite Persistence & Sliding Window Architecture

### 1. Dual-Tier Data Architecture: Persistent SQLite vs In-Memory Graph

In production blockchain intelligence, raw transaction throughput is unbounded, whereas in-memory graph topologies (NetworkX directed graphs) must remain memory-efficient and performant for sub-second path reconstruction and cycle detection.

Phase 11 introduces a decoupled dual-tier architecture:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Ethereum Mainnet JSON-RPC Node                       │
│              (https://ethereum-rpc.publicnode.com)                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ eth_getBlockByNumber (latest)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│         LiveBlockchainProvider (Daemon Poller Thread)                  │
│  - Contract Creation Normalization (to=0x00...00, contract_creation)   │
│  - Reorganization Detection (parentHash mismatch validation)           │
│  - Wei-to-ETH Floating Point Conversion & Timestamp Parsing            │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌─────────────────────────────────────┐   ┌──────────────────────────────┐
│ Tier 1: Persistent SQLite Database  │   │ Tier 2: In-Memory Window     │
│   (backend/data/live_chain.db)      │   │   (NetworkX Detection Graph) │
│ - live_transactions (Full Ledger)   │   │ - Bounded Sliding Window     │
│ - processed_blocks (Reorg History)  │   │   (Max 10k txs / 2.0 hours)  │
│ - sync_state (Checkpoint Height)    │   │ - Zero Memory Growth Leaks   │
│ - Export to Excel-BOM CSV           │   │ - Pre-warmed on Startup      │
└─────────────────────────────────────┘   └──────────────┬───────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────┐
                                          │ Engine Hot-Reload Broadcast  │
                                          │ - Re-indexes Graph & Alerts  │
                                          │ - Instant UI Metric Updates  │
                                          └──────────────────────────────┘
```

### 2. SQLite Storage Schema (`backend/providers/storage.py`)

The persistent storage engine utilizes SQLite3 (`backend/data/live_chain.db`) with zero external binary dependencies:

- **`live_transactions` Table**:
  - `tx_hash` (TEXT PRIMARY KEY): Hexadecimal 32-byte transaction hash.
  - `from_address` (TEXT NOT NULL) & `to_address` (TEXT NOT NULL): Standardized lowercase Ethereum addresses.
  - `amount_eth` (REAL NOT NULL): Converted Ether amount.
  - `timestamp` (TEXT NOT NULL): ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SS+00:00`).
  - `block_number` (INTEGER NOT NULL): Canonical Ethereum block height.
  - `gas_fee` (REAL NOT NULL): Cumulative gas fee in ETH (`gas * gasPrice`).
  - `status` (TEXT): Receipt execution status (`SUCCESS` / `FAILED`).
  - `category_label` (TEXT): Classification tag (`live_transfer`, `contract_creation`).
  - `description` (TEXT): Human-readable activity summary.
  - **Indexes**: `idx_live_tx_timestamp`, `idx_live_tx_block`, `idx_live_tx_from`, `idx_live_tx_to`.

- **`processed_blocks` Table**:
  - `block_number` (INTEGER PRIMARY KEY)
  - `block_hash` (TEXT UNIQUE NOT NULL)
  - `parent_hash` (TEXT NOT NULL)
  - `timestamp` (INTEGER NOT NULL)
  - `tx_count` (INTEGER NOT NULL)
  - `processed_at` (TEXT NOT NULL)

- **`sync_state` Table**:
  - Key-value metadata table recording `latest_processed_block` and `last_sync_timestamp` for instant checkpoint restoration on service restart.

### 3. Concurrency Safety & Windows File-Locking Prevention

To eliminate Windows `[WinError 32]` file handle locks (which occur when SQLite connections remain open across threads or during test directory cleanup), `LiveStorage` encapsulates database connections inside a strict Python generator context manager:

```python
@contextmanager
def _get_connection(self):
    conn = sqlite3.connect(self._db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

This guarantees that SQLite handles are immediately released upon statement completion, even under abnormal process termination or exceptions.

### 4. Background Polling Daemon Lifecycle

- When `ProviderManager.switch_mode("LIVE")` is invoked, it instantiates and starts `ChainSentinel-LivePollWorker` as a daemon background thread (`threading.Thread(daemon=True)`).
- The thread continuously polls the next block every 8 seconds (`CHAINSENTINEL_POLL_INTERVAL`), catching network disconnects gracefully with exponential backoff and error tracking (`_consecutive_errors`).
- When switching back to `DEMO`, `ProviderManager.switch_mode("DEMO")` sets a thread-safe stop event (`_stop_event.set()`), joins the worker thread cleanly, and restores the synthetic dataset.

### 5. Blockchain Reorganization Detection

When processing block $N$, the provider queries the previous block record $N-1$ from SQLite:
- If `incoming_block.parentHash != previous_block.block_hash`, a chain reorganization is detected.
- The provider logs a warning, flags the metadata status, updates `sync_state`, and records `last_reorg_info` for investigator visibility.

### 6. Excel-Compatible CSV Exporter

The `LiveStorage.export_to_csv()` engine streams ingested transactions directly into standard CSV format with a UTF-8 Byte Order Mark (`\ufeff`) prepended to the stream:
- Prevents character corruption in Microsoft Excel on Windows.
- Exposes standard forensic columns (`tx_hash`, `from_address`, `to_address`, `amount_eth`, `timestamp`, `block_number`, `gas_fee`, `status`, `category_label`, `description`).
- Available via `GET /api/provider/export-csv` with browser download attachment headers.


