# ChainSentinel Project State

## Current Status

- **Phase 1 — Project Foundation**: COMPLETE
- **Phase 2 — Synthetic Transaction Dataset & Basic APIs**: COMPLETE
- **Phase 3 — Rule-Based Detection Engine**: COMPLETE
- **Phase 4A — Investigation Case Model, Storage & Core APIs**: COMPLETE
- **Phase 4B — Summary & Graph APIs + Frontend Data Integration**: COMPLETE
- **Phase 4C — Dashboard & Alert Experience Refinement**: COMPLETE
- **Phase 4D — Wallet Investigation & Case Workflow UI**: COMPLETE
- **Phase 4E — Testing, Verification & Checkpoint**: COMPLETE
- **Phase 5 — Cryptographic Evidence Integrity & Merkle Verification**: COMPLETE
- **Phase 6 — Advanced Investigation Workflow**: COMPLETE
- **Phase 7 — Flow Tracer & Path Reconstruction**: COMPLETE
- **Phase 8 — Advanced Analytics & Intelligence**: COMPLETE
- **Phase 9 — Final Integration, Interactive UI Polish & Hackathon Demo Readiness**: COMPLETE
- **Phase 10 — Production Hardening & Real-Time Transaction Readiness**: COMPLETE
- **Phase 11 — Complete Live Ethereum Integration & SQLite Persistence**: COMPLETE

**Current Status**: **Phase 11 Complete — Complete Live Ethereum Integration & SQLite Persistence**

---

## Completed Features

- **Live Ethereum Blockchain Integration & SQLite Persistence (Phase 11)**:
  - `LiveStorage` SQLite Persistence Engine (`backend/providers/storage.py`):
    - Dedicated SQLite relational database (`backend/data/live_chain.db`) with schemas for `live_transactions`, `processed_blocks`, and `sync_state`.
    - Fully indexed for high-throughput queries (`idx_live_tx_timestamp`, `idx_live_tx_block`, `idx_live_tx_from`, `idx_live_tx_to`, `idx_processed_blocks_num`).
    - Thread-safe connection context manager guaranteeing explicit connection closure (`conn.close()` in `finally`), eliminating Windows file-locking regressions.
    - Transaction deduplication via `INSERT OR IGNORE` on primary key `tx_hash`.
    - Sliding-window querying preserving insertion order (`WHERE rowid IN (...) ORDER BY rowid ASC`).
    - Excel-compatible CSV exporter with UTF-8 BOM (`\ufeff`) to prevent character encoding issues in spreadsheet software.
  - `LiveBlockchainProvider` Autonomous Ingestion (`backend/providers/live.py`):
    - Background polling worker running on a daemon thread (`ChainSentinel-LivePollWorker`) polling every 8 seconds (configurable via `CHAINSENTINEL_POLL_INTERVAL`).
    - Auto-recovery and checkpoint restoration: resumes from highest processed block number on restart.
    - Blockchain reorganization detection comparing incoming `parentHash` with previous stored `block_hash`.
    - Contract creation normalization: captures deployment transactions where `to` is `null`/empty, mapping them to `0x0000000000000000000000000000000000000000` with category label `contract_creation`.
    - High-precision Wei-to-ETH conversion, gas calculation, and standardized ISO 8601 UTC timestamps.
    - Dual-tier data model: full transaction history persisted in SQLite, while NetworkX in-memory analysis graph is constrained to an active sliding window (default 2 hours, 10,000 transactions) to prevent memory leaks.
    - Resilient public RPC default (`https://ethereum-rpc.publicnode.com`) with custom override via `CHAINSENTINEL_RPC_URL`.
    - Graceful error tracking (`_last_error`, `_consecutive_errors`, backoff retry).
  - `ProviderManager` Lifecycle & Event Coordination (`backend/providers/manager.py`):
    - Background thread lifecycle management: automatically starts daemon polling on `LIVE` mode and stops it on `DEMO` mode.
    - Real-time listener callback hook notifying `DetectionEngine` to re-index and re-score without restarting the FastAPI server.
    - Zero deceptive fallbacks: returns true on-chain transactions in `LIVE` mode and the 70 synthetic benchmark transactions in `DEMO` mode.
  - New REST API Endpoints:
    - `GET /api/provider/export-csv`: Streams live ingested transactions as an Excel-compatible CSV file with `Content-Disposition: attachment`.
    - `GET /api/provider/check-connection`: Probes the configured JSON-RPC node and reports availability, current block height, and response latency.
  - Frontend Enhancements:
    - 6-second periodic telemetry polling when `LIVE` mode is active.
    - Real-time block height pill (`#<block_number>`) with pulse indicator in the navigation bar.
    - "Poll Block" manual trigger button and "Export CSV" one-click ledger download.
    - Live monitoring status banner on Dashboard explaining active on-chain surveillance and normal AML behavior when 0 alerts are detected.
  - Test Suite: **199 / 199 automated tests passing** (16 new tests in `test_live_integration.py` covering SQLite persistence, contract normalization, reorg detection, deduplication, restart recovery, sliding window, CSV export, and engine integration). Frontend lint: 0 errors; frontend build: clean.

- **Pluggable Transaction Provider Architecture & Real-Time Ingestion (Phase 10)**:
  - `BaseTransactionProvider` (`backend/providers/base.py`): Abstract base contract defining dataset querying, transaction ingestion, and live block fetching.
  - `SyntheticTransactionProvider` (`backend/providers/synthetic.py`): Default, zero-dependency benchmark provider loading the 70 curated forensic transactions (1,200.45 ETH) for 100% reliable deterministic offline demos and automated test runs.
  - `ProviderManager` (`backend/providers/manager.py`): Central controller orchestrating mode switching (`DEMO` vs `LIVE`) and listener registration.
  - Finished Product Branding Cleanup: Removed development-phase branding ("Phase 9", "Hackathon Demo Ready") in favor of production styling ("ChainSentinel", "Blockchain Forensic Intelligence", "Investigation Command Center").

- **React + Vite Frontend (`frontend/`)**: React 19, Vite 8, Tailwind CSS v4, Lucide React icons, Cytoscape.js installed. Development server with backend API proxy (`/api` → `http://127.0.0.1:8000`) and direct fallback. Full frontend API client layer (`frontend/src/api/`) communicating with all backend endpoints. Complete forensic investigation platform across 4 coordinated views:
  - **Dashboard View (`DashboardView.jsx`)**: Cybersecurity command center with live KPI metric strip (21 alerts, 11 high/critical, 9 medium, 1 low), interactive pattern breakdown matrix (6 cards with click-to-filter), top threats feed, and quick forensic jumps.
  - **Alerts Explorer (`AlertsView.jsx` & `AlertDetailModal.jsx`)**: Multi-filter alerts explorer with severity filters (`ALL`, `HIGH`, `MEDIUM`, `LOW`), pattern dropdown, real-time search, sorting by severity/amount/time, and full forensic modal with implicated wallet roles, transaction hashes, and direct "Investigate Wallet" / "Open Case" action buttons.
  - **Wallet Deep Dive (`WalletInvestigationView.jsx`)**: Address search with scenario presets, deterministic risk gauge (0–100) with color-coded levels, contributing pattern breakdown, interactive Cytoscape neighborhood graph with 1–3 hop depth selector, and full inbound/outbound transaction ledger.
  - **Case Management Workspace (`InvestigationsView.jsx`, `CreateCaseModal.jsx`, `AddEvidenceModal.jsx`, `EvidenceIntegrityPanel.jsx`, `CaseTimeline.jsx`)**: Complete investigation case workflow with status filtering (`ALL`, `OPEN`, `CLOSED`), comprehensive case dossier (`GET /investigations/{case_id}/summary`), embedded case graph visualization (`GET /investigations/{case_id}/graph`), inline editable analyst notes (`PATCH /notes`), one-click case status toggle (`PATCH /status`), 5-step lifecycle progress stepper (Opened → Alerts Linked → Evidence Anchored → Merkle Audited → Case Closed), quick "Anchor as Evidence" buttons across alerts and transactions, real-time SHA-256 and Merkle collection audit panel, and unified chronological audit timeline (`GET /investigations/{case_id}/timeline`).
- **FastAPI Backend (`backend/main.py`)**: Asynchronous REST service with CORS enabled for local development, in-memory pre-warmed detection cache, full endpoints for transactions, alerts, risk scores, graphs, investigation cases, cryptographic evidence, and audit timelines.
- **Investigation Workflow Backend (`backend/investigations/`)**:
  - `InvestigationCase` domain model (`case_id`, `title`, `target_wallet`, `status`, `notes`, `alert_ids`, `related_wallets`, timestamps)
  - `InvestigationTimelineEvent` domain model (`event_id`, `case_id`, `event_type`, `title`, `description`, `timestamp`, `metadata`) and `generate_event_id()` generator (`EVT-<8 hex chars>`)
  - `InvestigationCaseStore` singleton (`CASE_STORE`) providing in-memory lookup, event tracking, and JSON file persistence (`cases.json`)
  - Full REST endpoints: create case (`POST /investigations`), list/filter cases (`GET /investigations`), retrieve case (`GET /investigations/{case_id}`), update status (`PATCH /investigations/{case_id}/status`), update analyst notes (`PATCH /investigations/{case_id}/notes`), comprehensive aggregated case summary (`GET /investigations/{case_id}/summary`), investigation graph visualization (`GET /investigations/{case_id}/graph`), and unified chronology timeline (`GET /investigations/{case_id}/timeline`)
- **Cryptographic Evidence & Integrity Layer (`backend/crypto/`)**:
  - `EvidenceRecord` domain model (`evidence_id`, `case_id`, `evidence_type`, `source_ref`, `content`, `created_at`, `evidence_hash`, `metadata`) and `generate_evidence_id` generator (`EVID-<8 hex chars>`).
  - `canonicalize()` deterministic JSON canonicalization function sorting keys at all recursive levels with compact whitespace (`ensure_ascii=True`, `separators=(',', ':')`).
  - `hash_data()` SHA-256 standard hashing via Python `hashlib` (pure standard library, no external crypto packages or non-deterministic Python `hash()`).
  - `compute_evidence_hash()` and `verify_evidence_hash()` for tamper detection and audit verification.
  - `EvidenceStore` singleton (`EVIDENCE_STORE`) with in-memory dict lookup and JSON persistence (`evidence.json`).
  - `MerkleTree` binary tree implementation supporting empty collections (canonical `e3b0c442...`), single leaves, multi-leaf trees, lexicographical leaf sorting for determinism, trailing-duplicate balancing for odd levels (RFC 6962 / Bitcoin standard), and cryptographic inclusion proofs (`get_proof`, `verify_proof`).
  - Full REST APIs:
    - `POST /investigations/{case_id}/evidence` (create and cryptographically anchor evidence)
    - `GET /investigations/{case_id}/evidence` (list case evidence records)
    - `GET /evidence/{evidence_id}` (retrieve single evidence record)
    - `GET /evidence/{evidence_id}/verify` (verify single evidence cryptographic integrity)
    - `GET /investigations/{case_id}/evidence/merkle` (generate case Merkle root)
    - `POST /investigations/{case_id}/evidence/merkle/verify` (verify case evidence collection against expected root)
    - Integrated `evidence_count` into `GET /investigations/{case_id}/summary`
- **Synthetic Transaction Dataset (`backend/data/transactions.csv`)**: 70 transactions across 70 wallets totaling 1,200.45 ETH, containing deliberate examples of 6 suspicious topologies and 4 normal activity patterns.
- **Transaction Loader (`backend/data/loader.py`)**: High-performance dataset loader using Python standard library `csv` and typed records, returning summary metrics without external binary dependencies.
- **Transaction APIs**: `GET /transactions` (with pagination and filtering by category or wallet) and `GET /transactions/{tx_id}`.
- **Detection Engine (`backend/detection/engine.py`)**: `DetectionEngine` orchestrator that converts raw transactions into typed domain models, executes all 6 rule-based detectors, deduplicates alerts, and calculates graph neighbourhoods.
- **Six Rule-Based Detection Patterns**:
  1. `CIRCULAR_TRANSACTION` (directed cycle enumeration with time windows)
  2. `RAPID_MOVEMENT` (hop-by-hop fund forwarding with low hold times)
  3. `TRANSACTION_BURST` (high transaction frequency sliding window)
  4. `FAN_OUT_SPLIT` (smurfing dispersal into multiple accounts)
  5. `FAN_IN_RECOMBINATION` (aggregation from multiple sources into a collector)
  6. `SUSPICIOUS_CLUSTER` (dense interconnected weakly connected components)
- **Risk Scoring (`backend/detection/risk.py`)**: Deterministic additive scoring model with configurable weights and thresholds, mapping scores to `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- **Wallet Risk Analysis**: `GET /wallets/{wallet_id}/risk` providing score (0–100), severity level, and itemized pattern explanations.
- **Wallet Alert Analysis**: `GET /wallets/{wallet_id}/alerts` returning all alerts mentioning a specific wallet.
- **Wallet Transactions**: `GET /wallets/{wallet_id}/transactions` returning all inbound and outbound transactions for a wallet.
- **Graph API**: `GET /graph/{wallet_id}?depth=2` returning Cytoscape-formatted nodes and directed edges with flagging metadata.
- **Flow Tracer & Path Reconstruction Engine (`backend/detection/tracer.py`)**:
  - Directed simple path search with bounded traversal depth (1 to 6 hops).
  - Transaction-aware path reconstruction with temporal consistency analysis ($W_1 \to W_2 \to \dots \to W_k$).
  - Closed circular loop detection when source == target.
  - Downstream outflow discovery when target is unspecified.
  - Deterministic path suspicion scoring (0–100) combining peak wallet risk, average risk, pattern involvement, and velocity bonuses.
  - Cytoscape-formatted graph generation with source, target, and hop-indexed path highlighting flags.
- **Flow Tracer Frontend Interface (`frontend/src/components/FlowTracerView.jsx`)**:
  - Dedicated cybersecurity command-center view with origin/destination wallet inputs, depth selector, swap action, and demo presets.
  - Reconstructed path banner with hop count, total ETH volume, transit duration, and suspicion tier badges.
  - Visual route canvas with neon path emphasizing source (emerald), destination (purple), path hops (cyan), and non-path dimming.
  - Chronological hop-by-hop ledger detailing sender/recipient risk, amount, timestamp, tx hash, and forensic signatures.
  - Direct integration to anchor reconstructed flow paths as cryptographic case evidence.
- **Advanced Analytics & Behavioral Intelligence (`backend/analytics/`)**:
  - `WalletBehaviorProfiler` deterministic feature extraction calculating turnover volumes, net flow, counterparty breadths, transaction velocity, holding durations, and active spans.
  - 9 explainable behavioral classifications: `NORMAL`, `HIGH_VOLUME`, `HIGH_VELOCITY`, `FAN_OUT`, `FAN_IN`, `CIRCULAR`, `MIXER_LIKE`, `MULTI_PATTERN`, and `HIGH_RISK`.
  - `AlertCorrelator` deterministic cross-pattern convergence engine identifying multi-topology convergence events (e.g. Circular + Rapid Movement + Mixing Ring on identical entity clusters) with confidence rating and plain-English narratives.
  - `IntelligenceEngine` central facade providing wallet-level intelligence dossiers, ranked and filtered multi-criteria wallet profiling, global network summary metrics, and executive-level strategic case dossiers with priority scoring, counterparty threat matrices, and Merkle status integration.
- **Final Integration, Interactive UI Polish & Hackathon Demo Readiness (Phase 9)**:
  - Dark cinematic cyber command center aesthetics: custom subtle cyber background grid, glassmorphism card utilities (`.glass-panel`, `.glass-card`), restrained threat severity glows (`.glow-critical`, `.glow-high`, `.glow-indigo`, `.glow-emerald`, `.glow-cyan`), smooth cubic-bezier transitions.
  - Interactive Forensic Workflow Pipeline Bar in `App.jsx`: 4-step progressive lifecycle stepper (`1. Alert Triage -> 2. Wallet Deep Dive -> 3. Flow Tracer -> 4. Case Dossier & Cryptographic Audit`) with active tracking and instant cross-view navigation.
  - Interactive Cytoscape graph enhancements (`GraphViewer.jsx`): smooth easing animation on node tap centering, smooth zoom and fit transitions (`cy.animate`), enhanced node halo styling for source (emerald), destination (purple), path hops (sky blue), and flagged nodes (rose), and cursor pointer on hover.
  - Alerts view polish (`AlertsView.jsx`): glass-card elevation, glowing severity borders on Critical/High alerts, direct one-click "Trace Flow" action button into Flow Tracer, "Inspect" modal, and "Investigate" deep dive.
  - Dashboard view polish (`DashboardView.jsx`): glass-card KPI widgets, pulsing priority indicators, fixed tab navigation to cases workspace.
  - Investigations view polish (`InvestigationsView.jsx`): enhanced 5-step lifecycle stepper with distinct visual completed/active states.
- **Automated Tests (`backend/tests/`)**: 169 automated pytest unit and integration tests covering data loading, topology verification, all detectors, edge cases, risk scoring, REST endpoints, investigation workflow, timeline chronology, cryptographic evidence integrity, flow path reconstruction, and advanced analytics/intelligence (100% passing).

---

## Detection Results (Phase 3 on Synthetic Dataset)

- **Test Suite**: **63 / 63 tests passing** (7 from Phase 1/2 + 56 added in Phase 3).
- **Total Alerts Detected**: **21 alerts**

### Pattern Breakdown:
- `CIRCULAR_TRANSACTION`: **12 alerts**
- `FAN_OUT_SPLIT`: **3 alerts**
- `RAPID_MOVEMENT`: **2 alerts**
- `FAN_IN_RECOMBINATION`: **2 alerts**
- `TRANSACTION_BURST`: **1 alert**
- `SUSPICIOUS_CLUSTER`: **1 alert**
- **Total**: **21 alerts**

### Severity Breakdown:
- `HIGH`: **11 alerts**
- `MEDIUM`: **9 alerts**
- `LOW`: **1 alert**
- **Total**: **21 alerts**

---

## Detection Patterns

### 1. `CIRCULAR_TRANSACTION`
- **Algorithm**: Builds a directed MultiDiGraph via NetworkX and applies `nx.simple_cycles()` to find closed loops of transactions.
- **Constraints**: Cycle length between 3 and 10 wallets (`CIRCULAR_MIN_CYCLE_LENGTH` to `CIRCULAR_MAX_CYCLE_LENGTH`), completing within 7,200 seconds (2 hours).
- **Forensic Context**: Layering technique where capital is routed through intermediary mule wallets before returning to the originator to obfuscate fund ownership.

### 2. `RAPID_MOVEMENT`
- **Algorithm**: Follows consecutive transaction chains where recipient wallet $W_i$ forwards funds to $W_{i+1}$ within a tight time delta.
- **Constraints**: Minimum chain length of 3 hops (`RAPID_MIN_HOPS`), maximum inter-hop hold time of 300 seconds / 5 minutes (`RAPID_MAX_HOP_SECONDS`), total chain window of 3,600 seconds.
- **Forensic Context**: Rapid layering / passthrough accounts used to quickly move stolen funds across multiple hops before law enforcement can freeze balances.

### 3. `TRANSACTION_BURST`
- **Algorithm**: Chronological sliding window per sender wallet to measure outbound transaction density.
- **Constraints**: Minimum 5 transactions (`BURST_MIN_TX_COUNT`) within a 300-second / 5-minute sliding window (`BURST_WINDOW_SECONDS`).
- **Forensic Context**: Automated programmatic disbursement or dusting attacks using high-speed script execution.

### 4. `FAN_OUT_SPLIT`
- **Algorithm**: Sliding window analysis of single source distributing funds to many distinct destination wallets.
- **Constraints**: Minimum 4 distinct destinations (`FANOUT_MIN_DESTINATIONS`), minimum 5.0 ETH total amount (`FANOUT_MIN_TOTAL_AMOUNT`), within 3,600 seconds (`FANOUT_WINDOW_SECONDS`). Includes coefficient of variation heuristic on amounts to flag potential automated payroll.
- **Forensic Context**: Smurfing / structuring technique breaking large balances into smaller increments below standard reporting thresholds.

### 5. `FAN_IN_RECOMBINATION`
- **Algorithm**: Sliding window analysis of multiple disparate feeder wallets depositing into a single collector wallet.
- **Constraints**: Minimum 4 distinct source wallets (`FANIN_MIN_SOURCES`), minimum 5.0 ETH total amount (`FANIN_MIN_TOTAL_AMOUNT`), within 3,600 seconds (`FANIN_WINDOW_SECONDS`).
- **Forensic Context**: Liquidity consolidation phase where smurfed or washed funds are gathered back into an operator-controlled collector wallet.

### 6. `SUSPICIOUS_CLUSTER`
- **Algorithm**: Evaluates weakly connected components (WCC) in the directed graph with edge density calculation ($e / [n(n-1)]$).
- **Constraints**: Minimum 3 nodes (`CLUSTER_MIN_NODES`), minimum 5 directed edges (`CLUSTER_MIN_EDGES`), and edge density $\ge 0.30$ (`CLUSTER_MIN_EDGE_DENSITY`).
- **Forensic Context**: Tightly knit mixing rings or wash-trading networks where participants circulate funds reciprocally with no outside economic purpose.

---

## Risk Scoring

Defined in `backend/detection/config.py` and implemented in `backend/detection/risk.py`:

### Pattern Weights:
- `CIRCULAR_TRANSACTION`: **+30 points**
- `SUSPICIOUS_CLUSTER`: **+25 points**
- `FAN_OUT_SPLIT`: **+20 points**
- `FAN_IN_RECOMBINATION`: **+20 points**
- `RAPID_MOVEMENT`: **+20 points**
- `TRANSACTION_BURST`: **+15 points**

### Aggregation Rules:
- Scores are additive per unique pattern type implicated with a wallet (maximum score capped at 100).
- If a wallet is clean (no associated alerts), its score is 0.

### Score to Level Mapping:
- **`CRITICAL`**: Score $\ge 60$
- **`HIGH`**: Score $\ge 40$
- **`MEDIUM`**: Score $\ge 20$
- **`LOW`**: Score $< 20$

---

## Current API Endpoints

| Method | Path | Query / Path Parameters | Description & Return Format |
|---|---|---|---|
| `GET` | `/health` | None | Operational status and API version (`{"status": "ok", ...}`) |
| `GET` | `/api/info` | None | Dataset metrics, wallet counts, volume, and category stats |
| `GET` | `/transactions` | `category`, `wallet`, `limit` (default 100), `offset` (default 0) | Paginated list of transactions with metadata and descriptions |
| `GET` | `/transactions/{tx_id}` | `tx_id` (hash string) | Detailed view of single transaction; returns 404 if missing |
| `GET` | `/alerts` | `pattern`, `severity`, `wallet`, `limit`, `offset` | List of detected alerts with forensic explanations, implicated wallets, and tx IDs |
| `GET` | `/alerts/{alert_id}` | `alert_id` (string) | Details of a single alert by ID; returns 404 if missing |
| `GET` | `/wallets/{wallet_id}/risk` | `wallet_id` (address string) | Wallet risk score (0-100), severity level (`LOW` to `CRITICAL`), and pattern explanations |
| `GET` | `/wallets/{wallet_id}/alerts` | `wallet_id` (address string) | List of alerts implicating the specified wallet |
| `GET` | `/wallets/{wallet_id}/transactions`| `wallet_id`, `limit` (default 50) | Inbound and outbound transactions for the specified wallet |
| `GET` | `/graph/{wallet_id}` | `wallet_id`, `depth` (1-3, default 2) | Subgraph JSON formatted for Cytoscape.js (`nodes`, `edges`, `flagged_wallets`) |
| `GET` | `/detection/summary` | None | Aggregate metrics: `total_alerts`, `alerts_by_pattern`, `alerts_by_severity` |
| `POST` | `/investigations` | Body: `title`, `target_wallet`, optional `notes`, `alert_ids`, `related_wallets` | Create an investigation case (201 Created); returns case object |
| `GET` | `/investigations` | `status` (optional: `OPEN`, `CLOSED`) | List all investigation cases (newest first); returns array and total |
| `GET` | `/investigations/{case_id}` | `case_id` (string) | Retrieve investigation case by ID; returns 404 if not found |
| `PATCH` | `/investigations/{case_id}/status` | Body: `status` (`OPEN` or `CLOSED`) | Update investigation case status; returns updated case object |
| `PATCH` | `/investigations/{case_id}/notes` | Body: `notes` (string) | Update investigation case notes; returns updated case object |
| `GET` | `/investigations/{case_id}/summary` | `case_id` (string) | Comprehensive forensic investigation summary (case, target risk, resolved alerts, transactions, related risks, evidence_count) |
| `GET` | `/investigations/{case_id}/graph` | `case_id` (string), `depth` (1-3, default 2) | Cytoscape graph data centered on case target wallet (reusing Phase 3 graph engine) |
| `GET` | `/investigations/{case_id}/timeline` | `case_id` (string), `order` (`asc` or `desc`, default `asc`) | Chronological audit timeline synthesizing case lifecycle, linked alerts, evidence, verification, and analyst notes |
| `POST` | `/investigations/{case_id}/evidence` | Body: `evidence_type`, `source_ref`, `content`, optional `metadata` | Cryptographically anchor evidence record (201 Created); computes canonical SHA-256 hash |
| `GET` | `/investigations/{case_id}/evidence` | `case_id` (string) | List all evidence records bound to a case; returns array and total |
| `GET` | `/evidence/{evidence_id}` | `evidence_id` (string) | Retrieve single evidence record by ID; returns 404 if not found |
| `GET` | `/evidence/{evidence_id}/verify` | `evidence_id` (string) | Cryptographic verification of evidence payload against stored SHA-256 digest |
| `GET` | `/investigations/{case_id}/evidence/merkle` | `case_id` (string) | Calculate and return Merkle root and audit leaves for case evidence collection |
| `POST` | `/investigations/{case_id}/evidence/merkle/verify` | Body: `expected_root` (string) | Verify case evidence collection against expected Merkle root and audit individual leaves |
| `GET` | `/flow/trace` | `source` (required address), `target` (optional address), `max_depth` (1-6, default 4) | Reconstruct directed transaction flow path(s) between wallets or discover downstream flow network; returns path metrics, hops detail, suspicion score, and Cytoscape graph |
| `GET` | `/investigations/{case_id}/flow` | `case_id` (string), `target` (optional address), `max_depth` (1-6, default 4) | Reconstruct fund flow anchored to an investigation case's target wallet and linked entities |
| `GET` | `/analytics/wallet/{wallet_id}` | `wallet_id` (address string) | Retrieve comprehensive behavioral profile, explainable risk assessment, observable signals, and cross-pattern correlations |
| `GET` | `/analytics/wallets` | `limit`, `offset`, `classification`, `priority`, `min_risk` | Paginated and ranked behavioral profiles for all wallets in the network |
| `GET` | `/analytics/summary` | None | Network-wide intelligence summary: classification breakdown, priority distribution, top correlations, and top targets |
| `GET` | `/analytics/correlations` | `severity` (optional), `wallet` (optional) | Cross-pattern correlation convergence events where distinct suspicious topologies intersect |
| `GET` | `/analytics/investigations/{case_id}` | `case_id` (string) | Executive strategic intelligence dossier for investigation case with priority score, target behavior, counterparty threat matrix, and Merkle status |
| `GET` | `/api/provider/status` | None | Returns active data mode (`DEMO` / `LIVE`), provider description, and total transactions loaded |
| `POST` | `/api/provider/mode` | Body: `mode` (`DEMO` or `LIVE`) | Hot-swaps data provider mode, resets engine state, and broadcasts reload listeners |
| `POST` | `/api/provider/ingest` | Body: `transactions` (list of raw or normalized tx dicts) | Dynamically ingest batch transactions into active provider and re-evaluates detections |
| `POST` | `/api/provider/fetch-live` | Body: optional `max_txs` (default 25) | Poll latest block transactions from Ethereum RPC into live memory and recalculates graph |

---

## Known Limitations

1. **Synthetic Wallet Addresses with 'S' Characters**:
   Addresses such as `0x3333S0100000000000000000000000000000000` contain the character `S` (non-hexadecimal). These are intentional synthetic identifiers created for retail shopper simulation. The entire platform treats wallet addresses strictly as opaque case-sensitive strings. Do not enforce strict hex decoding on addresses.
2. **DEX Router Generates Low-Severity Fan-In**:
   The Uniswap DEX Router address (`0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`) receives transactions from multiple independent traders within 1 hour. This triggers a `FAN_IN_RECOMBINATION` alert at `LOW` severity. In the MVP this is documented behavior. In future iterations, a verified public contract whitelist can be introduced.
3. **Cluster Generates Sub-Cycles in Circular Detection**:
   The 5-node mixing ring (`0xEE01...` through `0xEE05...`) features 12 interconnected transfers, resulting in multiple sub-cycles detected by `CIRCULAR_TRANSACTION` alongside the primary `SUSPICIOUS_CLUSTER` alert. This is mathematically accurate for cyclic subgraphs and must not be suppressed without a dedicated cycle subsumption rule.
4. **Merkle Tree Odd-Leaf Handling Specification**:
   When any binary tree level contains an odd number of nodes (> 1), the final un-paired node is duplicated (paired with itself: `hash_pair(node, node)`) to balance the tree layer. This adheres to the Bitcoin/RFC 6962 binary Merkle standard and guarantees deterministic, replayable root calculation.

> **CRITICAL RULE**: These limitations are known characteristics of the current deterministic rule-based algorithms and cryptographic standards. They must NOT be silently altered, bypassed, or removed.

---

## Current Phase

- **Current Status**: **Phase 10 Complete** (Phase 10: Final Hardening + Real-Time Transaction Readiness: pluggable provider layer with Synthetic benchmark and Live Ethereum JSON-RPC ingestion, hot-swapping provider manager, UI DEMO/LIVE switcher, production branding cleanup, 183 backend tests passing, 0 frontend lint errors, clean production build)
- **Next Task**: **Project Complete / Production Deployment Ready**

> **IMPORTANT RULE**: This file must be updated at the end of each completed phase to maintain persistent project context.


