
# ChainSentinel 🛡️
### Blockchain Transaction Forensics & Investigation Platform

**Detect suspicious transaction patterns. Trace wallet relationships. Preserve verifiable digital evidence.**

ChainSentinel is a full-stack blockchain transaction investigation platform built to help analysts explore transaction flows, identify suspicious financial patterns, investigate wallet relationships, and verify the integrity of investigation evidence.

The platform combines a React-based investigation dashboard with a Python/FastAPI backend, graph-based transaction analysis, explainable risk indicators, Ethereum JSON-RPC ingestion, SQLite persistence, and cryptographic evidence verification.

> **Project status:** Minimum Viable Product (MVP). Features and deployment readiness should be assessed against the current implementation. Suspicious-pattern alerts are investigative indicators, not proof of money laundering, criminal activity, or common wallet ownership.

---

## 📌 Table of Contents

- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Transaction Detection](#-transaction-detection)
- [Synthetic Transaction Dataset](#-synthetic-transaction-dataset)
- [Live Ethereum Integration](#-live-ethereum-integration)
- [Evidence Integrity](#-evidence-integrity)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Running Automated Tests](#-running-automated-tests)
- [API Reference](#-api-reference)
- [Roadmap](#-roadmap)
- [Limitations and Verification Notes](#-limitations-and-verification-notes)
- [Development Guidelines](#-development-guidelines)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 The Problem

Public blockchains provide transparent transaction records, but investigating those records can be challenging.

- Large transaction volumes make manual analysis difficult.
- Funds can move through multiple wallets in complex patterns.
- Suspicious transactions may be hidden within otherwise legitimate activity.
- Connections between wallets do not necessarily establish common ownership.
- Investigation evidence must remain consistent and independently verifiable.
- Analysts need understandable alerts rather than unexplained risk scores.

ChainSentinel aims to make blockchain transaction analysis more structured, explainable, and suitable for forensic investigation workflows.

## 💡 Our Solution

ChainSentinel transforms transaction records into an investigation workflow.

1. **Ingest:** Load a synthetic transaction dataset or retrieve blockchain data through an Ethereum JSON-RPC provider.
2. **Analyze:** Examine transaction relationships, timing, movement patterns, and wallet behavior.
3. **Detect:** Identify patterns that may warrant further investigation.
4. **Investigate:** Explore wallets, transaction paths, alerts, and related evidence.
5. **Preserve:** Record investigation evidence and calculate cryptographic integrity values.
6. **Verify:** Use SHA-256 digests and Merkle Tree verification to identify changes to recorded evidence.

The platform supports both a reproducible offline demonstration and a live-data ingestion mode.

---

## ✨ Key Features

### 1. Transaction Pattern Detection

Analyze transaction graphs to identify suspicious topologies, including:

- Circular fund flows
- Rapid movement across multiple wallets
- Transaction bursts
- Fan-out dispersal patterns
- Fan-in aggregation patterns
- Dense, interconnected wallet clusters

### 2. Wallet Investigation and Flow Tracing

- Explore relationships between wallets.
- Reconstruct multi-hop transaction paths.
- Examine the timing and direction of fund movements.
- Investigate downstream transaction relationships.
- View graph-based relationships and investigation context.

A transaction relationship is not, by itself, proof that two wallets belong to the same person or organization.

### 3. Risk Analysis and Behavioral Intelligence

- Deterministic risk scoring and severity aggregation.
- Behavioral wallet profiling.
- Explainable wallet classifications.
- Cross-pattern alert correlation.
- Investigation-oriented summaries and intelligence endpoints.

**Verification note:** Confirm that the current implementation exposes all documented classifications, scores, and intelligence endpoints before relying on these capabilities in a demonstration.

### 4. Investigation Case Management

- Create and manage investigation cases.
- Associate evidence with cases.
- Examine case summaries and timelines.
- Track investigation activity and chronology.
- Review related transaction graphs and findings.

### 5. Cryptographic Evidence Integrity

- Canonicalize evidence representations.
- Calculate SHA-256 digests.
- Construct Merkle Trees.
- Verify recorded evidence against cryptographic integrity values.
- Support investigation evidence auditing.

Cryptographic verification helps detect changes to covered data. It does not independently prove that the original data was accurate or that an investigation conclusion was correct.

### 6. Live Ethereum Data Ingestion

- Retrieve transaction data through an Ethereum JSON-RPC provider.
- Normalize ingested transaction records.
- Poll for new blockchain data.
- Persist live-ingestion records in SQLite.
- Support on-demand block polling and CSV export.
- Detect certain blockchain reorganization conditions.

See [Live Ethereum Integration](#-live-ethereum-integration) for details and verification notes.

### 7. Investigation Dashboard

The React frontend organizes investigation workflows into views for dashboards, alerts, wallet investigations, transaction flows, cases, and evidence integrity.

**Screenshots and demo:** Add verified screenshots of the dashboard, alert investigation, wallet flow tracing, and evidence integrity views here. Include a public demo URL if one is available.

- **Repository:** https://github.com/muddapatibhavana/ChainSentinel-live
- **Live demo:** Not provided; add a URL if deployed.
- **Demo video:** Not provided; add a link if available.

---

## 🏗️ System Architecture

ChainSentinel separates the investigation interface, backend API, transaction ingestion, analysis engine, and evidence storage.

```text
                ┌─────────────────────────┐
                │  React + Vite Frontend  │
                │ Investigation Dashboard│
                └────────────┬────────────┘
                             │ HTTP / REST
                             ▼
                ┌─────────────────────────┐
                │    FastAPI Backend      │
                │ API & Workflow Services │
                └────────────┬────────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
      ┌────────────┐  ┌─────────────┐  ┌──────────────┐
      │ Transaction│  │ Detection & │  │ Investigation│
      │ Providers  │  │  Analytics  │  │   Services  │
      └─────┬──────┘  └─────────────┘  └──────┬───────┘
            │                                  │
      ┌─────┴──────────┐                ┌──────▼───────┐
      ▼                ▼                │ Evidence &   │
 Synthetic Dataset  Ethereum RPC        │ Audit Data   │
                       │                └──────┬───────┘
                       ▼                       ▼
                 SQLite Storage         SHA-256 / Merkle
```

The diagram represents the documented logical architecture. Confirm the exact runtime connections and storage responsibilities in the current codebase.

### Backend Modules

| Module | Responsibility |
|---|---|
| `backend/main.py` | FastAPI application and REST endpoints |
| `backend/data/` | Synthetic dataset generation, loading, and statistics |
| `backend/providers/` | Transaction-provider abstractions, synthetic data, live ingestion, and provider management |
| `backend/detection/` | Transaction topology detection and risk analysis |
| `backend/analytics/` | Behavioral profiling, intelligence, and alert correlation |
| `backend/crypto/` | Evidence canonicalization, hashing, and Merkle Tree operations |
| `backend/investigations/` | Investigation models and storage |
| `backend/tests/` | Automated backend tests |

---

## 🧰 Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Styling | Tailwind CSS v4, custom CSS |
| Backend | Python, FastAPI |
| API documentation | OpenAPI, Swagger UI |
| Transaction analysis | NetworkX and graph-based analysis, where used by the implementation |
| Blockchain integration | Ethereum JSON-RPC |
| Persistence | SQLite |
| Evidence integrity | SHA-256, Merkle Trees |
| Testing | pytest |
| Package management | npm, pip |

**Verification note:** Check `frontend/package.json` and `backend/requirements.txt` to confirm the exact dependency versions and installed libraries.

---

## 🔎 Transaction Detection

ChainSentinel's documented detection engine analyzes transaction relationships and identifies patterns that may require further investigation.

| Pattern | Description |
|---|---|
| Circular flows | Detect directed transaction paths that return to an earlier wallet. |
| Rapid movement | Identify funds moving across multiple hops with short holding intervals. |
| Bursts | Identify unusually concentrated transaction activity within a time window. |
| Fan-out / split | Detect one wallet dispersing funds to multiple destinations. |
| Fan-in / recombination | Detect multiple wallets sending funds to a common destination. |
| Clusters | Identify densely connected transaction relationships that may warrant investigation. |

### Explainable Investigation Signals

Detection findings can help investigators ask more focused questions:

- Which wallets participate in the pattern?
- What transaction sequence connects them?
- How quickly do funds move between addresses?
- Are multiple detection patterns present in the same transaction graph?
- What evidence supports the alert?
- Does the available information justify further investigation?

Detection thresholds and risk scores are analytical heuristics. They should not be treated as proof of illicit activity.

---

## 📊 Synthetic Transaction Dataset

The documented demonstration dataset is located at:

`backend/data/transactions.csv`

The README's existing dataset description reports **70 transactions across 70 wallets**.

| Pattern category | Reported count | Description |
|---|---:|---|
| Circular | 4 | Transactions associated with circular fund-routing patterns |
| Rapid movement | 3 | Multi-hop movements with short holding intervals |
| Burst | 10 | Concentrated transaction activity |
| Fan-out / split | 8 | Dispersal of funds across multiple destinations |
| Fan-in / recombination | 7 | Aggregation of funds from multiple sources |
| Cluster | 12 | Dense interconnected transaction relationships |
| Normal / legitimate | 26 | Simulated payroll, DEX, cold-storage, and merchant activity |
| **Total** | **70** | **Reported transaction count** |

These are the counts documented for the benchmark dataset. Re-run the dataset generator or inspect the CSV before relying on the counts in a presentation.

The dataset is intended for controlled demonstrations and testing. Synthetic records must not be represented as real blockchain transactions.

---

## ⛓️ Live Ethereum Integration

ChainSentinel documents two transaction-provider modes.

### DEMO Mode

The default demonstration mode is designed to use the bundled synthetic dataset.

- Works without an Ethereum network connection.
- Supports reproducible demonstration data.
- Allows transaction detection and investigation workflows to be demonstrated independently of live RPC availability.

The original project documentation reports 21 alerts across six topologies. Verify this figure against the current dataset and detection configuration.

### LIVE Mode

The live provider is designed to retrieve Ethereum blockchain data through JSON-RPC.

#### Documented capabilities

- **RPC endpoint:** `https://ethereum-rpc.publicnode.com`
- **Configuration:** `CHAINSENTINEL_RPC_URL`
- **Polling interval:** Default documented interval of 8 seconds, configurable through `CHAINSENTINEL_POLL_INTERVAL`.
- **Background polling:** A worker named `ChainSentinel-LivePollWorker` is documented.
- **Persistence:** SQLite database at `backend/data/live_chain.db`.
- **In-memory analysis window:** Documented defaults of the latest two hours or 10,000 transactions.
- **On-demand ingestion:** A documented “Poll Block” interface action.
- **CSV export:** A documented `GET /api/provider/export-csv` endpoint.
- **Reorganization checks:** Detection of certain parent-hash mismatches.

These values describe the documented design and should be checked against the current implementation.

### Configure an RPC Endpoint

The application documentation describes the following environment variables:

```text
CHAINSENTINEL_RPC_URL=https://ethereum-rpc.publicnode.com
CHAINSENTINEL_POLL_INTERVAL=8
```

Set them in your local environment or an appropriately configured environment file, depending on how the backend loads configuration.

Do not commit API keys, provider credentials, or other secrets to GitHub.

### Live Mode Considerations

- Public RPC providers may impose rate limits or experience downtime.
- Live ingestion depends on external network availability.
- A polling interval does not guarantee that every transaction will be ingested.
- Reorganization handling should be tested against realistic chain changes.
- Historical ingestion, restart recovery, and deduplication should be verified with integration tests.
- A sliding-window analysis view may not contain the entire historical ledger.

**Production-readiness warning:** The existence of a live provider does not by itself establish production readiness. Reliability, backpressure, RPC failure handling, persistence recovery, monitoring, and chain-reorganization behavior should be tested before production deployment.

---

## 🔐 Evidence Integrity

ChainSentinel documents a cryptographic evidence workflow based on SHA-256 and Merkle Trees.

### SHA-256

SHA-256 generates a fixed-length digest from input data. When the same canonical data is hashed using the same process, the digest should be identical.

### Merkle Trees

A Merkle Tree organizes hashes into a tree structure whose root digest summarizes the included data. Changing covered data should change the resulting root, subject to the correctness of the implementation and hash construction.

### Investigation Use

The documented workflow includes:

1. Canonicalize evidence data.
2. Calculate evidence digests.
3. Build or update the Merkle Tree.
4. Record the resulting integrity information.
5. Verify the evidence against the recorded values.
6. Flag discrepancies for investigation.

Cryptographic hashes provide integrity checks, not proof of source authenticity, legal admissibility, or correctness of the underlying transaction interpretation. Those require additional controls and appropriate procedures.

---

## 📁 Project Structure

```text
ChainSentinel/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js
│   │   │   └── index.js
│   │   ├── assets/
│   │   ├── components/
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── backend/
│   ├── analytics/
│   ├── crypto/
│   ├── data/
│   │   ├── generate_dataset.py
│   │   ├── loader.py
│   │   └── transactions.csv
│   ├── detection/
│   ├── investigations/
│   ├── providers/
│   │   ├── base.py
│   │   ├── live.py
│   │   ├── manager.py
│   │   ├── storage.py
│   │   └── synthetic.py
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
│
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── DEVELOPMENT_GUIDE.md
└── PROJECT_STATE.md
```

This is a representative view of the documented repository. Some files and subdirectories may be omitted for readability. Virtual environments, caches, local databases, and generated artifacts should generally be excluded from version control unless the project specifically requires them.

---

## 🚀 Getting Started

### Prerequisites

Install the following software:

- Python 3.10 or later; the original project documentation reports testing on Python 3.12.
- Node.js 18 or later; the original documentation reports testing on Node.js v24.
- npm 9 or later.
- Git.

Check your installed versions:

```cmd
python --version
node --version
npm --version
git --version
```

### 1. Clone the Repository

Open CMD or a terminal and run:

```cmd
git clone https://github.com/muddapatibhavana/ChainSentinel-live.git
cd ChainSentinel-live
```

### 2. Set Up the Backend

From the repository root, run:

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the FastAPI server:

```cmd
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open.

If `python` is not recognized on Windows, try `py` instead.

### 3. Set Up the Frontend

Open a **second terminal** in the repository root.

Run:

```cmd
cd frontend
npm install
npm run dev
```

Open the local development URL printed by Vite, normally:

`http://localhost:5173`

The documented frontend configuration proxies `/api/*` requests to the FastAPI backend on port 8000. Confirm the proxy configuration in `frontend/vite.config.js`.

### 4. Explore the API

With the backend running, open:

| Resource | URL |
|---|---|
| Health endpoint | `http://127.0.0.1:8000/health` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| Dataset summary | `http://127.0.0.1:8000/api/info` |
| Transaction explorer | `http://127.0.0.1:8000/transactions` |

These routes are documented in the project README. If a route returns 404, check the current route definitions in `backend/main.py`.

### 5. Stop the Servers

Press `Ctrl + C` in each terminal running a development server.

---

## 🧪 Running Automated Tests

The project documentation reports **199 backend tests**. Treat this as a documented count, not a verified current test result, until the suite has been run successfully.

From the repository root, activate the backend virtual environment if needed and run:

```cmd
cd backend
.venv\Scripts\activate
python -m pytest tests -v
```

Alternatively, from the repository root, if pytest is installed in your active Python environment:

```cmd
python -m pytest backend/tests -v
```

The documented test coverage includes:

- Health checks and API endpoints.
- Synthetic dataset structure and integrity.
- Transaction-provider behavior and mode switching.
- Circular, rapid movement, burst, split, recombination, and cluster detection.
- Risk scoring and severity aggregation.
- Investigation case management, graphs, summaries, and timelines.
- SHA-256 evidence digests and Merkle Tree audits.
- Multi-hop flow tracing and path reconstruction.
- Behavioral profiling and alert correlation.
- Live transaction normalization and RPC integration.
- SQLite persistence, indexing, and deduplication.
- Contract creation normalization.
- Blockchain reorganization detection.
- In-memory sliding-window capacity and time-based pruning.
- Checkpoint restoration after server restarts.
- CSV export with a UTF-8 byte-order mark (BOM).

### Test Reporting

When reporting test results, include:

- The actual number of tests collected and passed.
- The Python version and environment used.
- Whether live RPC integration tests were skipped or executed.
- Any failures, warnings, or external-network dependencies.

Do not claim that all tests pass until the current test suite confirms it.

---

## 🔌 API Reference

The FastAPI application documents its endpoints through Swagger UI:

`http://127.0.0.1:8000/docs`

Documented endpoint examples include:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check |
| `GET /api/info` | Dataset or platform information |
| `GET /transactions` | Transaction exploration |
| `GET /api/provider/export-csv` | CSV export of provider data |

Other documented API areas include detection, risk analysis, wallet intelligence, flow tracing, investigation cases, evidence integrity, and provider management.

**Verification note:** This is a list of documented endpoint examples, not a complete endpoint inventory. Inspect the FastAPI route definitions or Swagger UI for the current methods, parameters, response schemas, and authentication requirements.

---

## 🗺️ Roadmap & Development Phases

The following phases reflect the progression documented in the original project README.

| Phase | Focus |
|---|---|
| 1 | Project structure and tooling |
| 2 | Synthetic transaction dataset and loading |
| 3 | Rule-based transaction pattern detection |
| 4 | Forensic investigation platform and UI workflows |
| 5 | Cryptographic evidence integrity and Merkle Tree verification |
| 6 | Advanced investigation workflow and case chronology |
| 7 | Flow tracing and path reconstruction |
| 8 | Behavioral analytics and intelligence |
| 9 | UI integration, polish, and demonstration readiness |
| 10 | Provider abstraction and live-ingestion readiness |
| 11 | Live Ethereum integration and SQLite persistence |

The original documentation describes Phase 11 as covering background polling, persistent storage, reorganization checks, contract normalization, sliding-window analysis, and CSV export.

Refer to `PROJECT_STATE.md` for the current phase boundary and active work. A phase listed here should not automatically be interpreted as independently audited or production-ready.

---

## ⚠️ Limitations and Verification Notes

ChainSentinel is an investigation-support MVP. Before relying on it for real-world investigations, consider the following:

1. **Detection is heuristic.** Transaction patterns can have legitimate explanations and require contextual analysis.
2. **Wallet ownership is not inferred from connectivity alone.** A graph edge does not establish common ownership or attribution.
3. **Synthetic data is not real evidence.** Clearly distinguish demo transactions from records obtained from the Ethereum network.
4. **Live ingestion requires validation.** Test RPC failures, rate limits, missing records, reorganization behavior, and restart recovery.
5. **Cryptographic integrity has limits.** Hashes verify covered data against a reference; they do not independently authenticate the original source.
6. **Performance claims require benchmarks.** Measure throughput, latency, memory use, and scalability before publishing performance figures.
7. **Security requires review.** Validate authentication, authorization, secret handling, input validation, logging, and deployment settings before exposing the service publicly.

### Items to Verify Before a Hackathon Demo

- [ ] The current test suite passes and the reported test count is accurate.
- [ ] The synthetic dataset contains the documented number of transactions and wallets.
- [ ] The reported number of alerts and detected topologies matches actual output.
- [ ] DEMO mode works without a network connection.
- [ ] LIVE mode successfully ingests and normalizes current Ethereum data.
- [ ] SQLite persistence and restart recovery work as documented.
- [ ] CSV export produces the expected records and encoding.
- [ ] Evidence verification detects a controlled modification to covered data.
- [ ] Every documented API route exists and returns the expected response.
- [ ] No API keys, credentials, private data, or local environment files are committed.
- [ ] The repository's dependency files and setup instructions are up to date.

---

## 📚 Development Guidelines

Before modifying the project, read the following documents:

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — Current project state, completed features, metrics, and active phase boundary.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — System design, data flow, component models, and technical contracts.
- [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) — Engineering rules, phase workflow, and model handoff protocol.

These documents provide the intended development constraints and help maintain consistency across project changes.

### Suggested Contribution Workflow

1. Read the project state and architecture documents.
2. Identify the relevant module and its existing tests.
3. Make a focused change consistent with the documented contracts.
4. Add or update automated tests.
5. Run the relevant test suite.
6. Review the Git diff for accidental secrets, generated files, and unrelated modifications.
7. Commit the change with a descriptive message.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

When proposing a change:

- Describe the problem being addressed.
- Explain the intended behavior.
- Include relevant test results.
- Document any configuration changes.
- Avoid committing credentials, private datasets, or machine-specific files.

Please follow the development rules in `DEVELOPMENT_GUIDE.md`.

---

## 📄 License

No license is specified here.

**Before publishing a license**, choose one that reflects how you want others to use, modify, and redistribute the project. Until then, do not assume that the repository grants permission to reuse its code.

---

## 👥 Project

**ChainSentinel — Blockchain Transaction Forensics & Investigation Platform**

Repository: https://github.com/muddapatibhavana/ChainSentinel-live

Built as a blockchain investigation MVP to explore transaction patterns, wallet relationships, and cryptographic evidence integrity.
