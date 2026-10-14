# ChainSentinel Development Guide

This guide is the operational rulebook for software engineers and AI coding agents working on **ChainSentinel**. Adhere strictly to these principles to maintain codebase stability across development phases.

---

## Core Engineering Principles for AI Agents

All contributors and autonomous AI agents MUST abide by the following 15 rules:

1. **Inspect Existing Code Before Changing It**: Always inspect the relevant codebase files, configurations, and datasets before formulating changes or generating new code.
2. **Never Assume Previous Work Is Missing**: Files and architectures from earlier phases exist and are verified. Do not duplicate or reimplement existing components.
3. **Preserve Working Functionality**: Maintain backward compatibility across all working endpoints and modules. New changes must never break existing features.
4. **Run Existing Tests Before Making Major Changes**: Establish a baseline of passing tests (`pytest backend/tests -v`) prior to introducing alterations.
5. **Run All Tests After Changes**: Every code modification must be verified by running the entire test suite. Never consider a phase complete without executing tests.
6. **Never Delete Tests Just to Make Them Pass**: If a test fails, investigate the underlying discrepancy and fix the implementation or update the test contract deliberately with documented rationale.
7. **Avoid Unnecessary Dependencies**: Do not introduce heavy libraries, external services, or cloud SDKs. Prioritize the standard library and existing lightweight packages.
8. **Keep Detection Logic Explainable**: Maintain deterministic, rule-based algorithms. Avoid black-box machine learning models or probabilistic guesswork. Every alert must articulate *why* it was triggered.
9. **Keep API Contracts Stable**: Maintain existing response schemas and query parameters unless an explicit refactor is required and agreed upon.
10. **Prefer Small Incremental Changes**: Implement features in isolated, logical increments. Never attempt to build an entire phase in a single monolithic edit.
11. **Update `PROJECT_STATE.md` After Completing a Phase**: Record test results, alert counts, and newly available capabilities at the conclusion of every phase.
12. **Update `ARCHITECTURE.md` When Architecture Changes**: Ensure system diagrams, schemas, and component descriptions reflect the real codebase.
13. **Document Known Limitations Instead of Hiding Them**: Be transparent about edge cases, known false positives, or environment constraints.
14. **Do Not Replace Working Implementations**: Do not rewrite functioning modules simply because alternative libraries or design patterns exist.
15. **Do Not Implement Future Phases Prematurely**: Focus exclusively on the scope of the assigned phase. Do not begin downstream frontend or cryptographic tasks ahead of schedule.

---

## Phase Workflow

Every development phase must progress through this 8-step cycle:

```text
Inspect ──► Plan ──► Implement ──► Test ──► Fix ──► Verify ──► Document ──► Checkpoint
```

1. **Inspect**: Read existing code, datasets, and tests related to the objective.
2. **Plan**: Formulate a targeted, minimal implementation strategy respecting existing contracts.
3. **Implement**: Create or edit code cleanly with appropriate types and comments.
4. **Test**: Execute unit and integration tests against real datasets and synthetic edge cases.
5. **Fix**: Address any test failures, warnings, or regressions immediately.
6. **Verify**: Spin up services (FastAPI/Vite) and verify real responses against expected outputs.
7. **Document**: Update `PROJECT_STATE.md` and `ARCHITECTURE.md` with what was created.
8. **Checkpoint**: Report deliverables, test metrics, and wait for human confirmation before proceeding.

---

## Model Handoff Protocol

Multiple AI models (e.g., Claude, Gemini, GPT) and human developers may collaborate on this repository across different turns.

### Source of Truth
The filesystem is the sole source of truth. Do not rely on assumed conversational context from earlier turns.

### Required Reading Order Before Modifying Code:
When taking over a task or initiating a new phase, an AI agent must read files in this exact sequence:
1. `PROJECT_STATE.md` (understand current progress, test counts, and phase status)
2. `ARCHITECTURE.md` (understand technical structure, contracts, and data flows)
3. `DEVELOPMENT_GUIDE.md` (internalize engineering constraints and rules)
4. **Relevant Source Files** (inspect the actual implementations to be extended)
5. **Relevant Test Files** (review existing test coverage and assertions)

---

## Development Environment Quick Reference

### Running Tests
```powershell
# From ChainSentinel root directory:
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### Running Backend API
```powershell
# From ChainSentinel/backend directory:
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
- Interactive Swagger: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### Running Frontend
```powershell
# From ChainSentinel/frontend directory:
npm run dev
```
- Investigation UI: `http://localhost:5173`

---

## Current Status & Next Steps

**Phase 11 is COMPLETE:**
- Backend: 199/199 tests passing.
- Frontend: 0 lint errors, clean production build.
- Live Ethereum JSON-RPC integration operational with resilient public RPC (`https://ethereum-rpc.publicnode.com`) and custom `CHAINSENTINEL_RPC_URL` support.
- Persistent SQLite storage (`backend/data/live_chain.db`) with tables for transactions, processed blocks, and sync state checkpoints.
- Autonomous background polling worker thread with clean start/stop lifecycle.
- Contract creation normalization, reorg detection, memory-bounded sliding window (2hr / 10k txs), and Excel-compatible UTF-8 BOM CSV export.
- UI: Real-time telemetry, live block height badge, on-demand block polling, CSV export, and active monitoring status.
- DEMO mode 100% preserved as the deterministic baseline for reproducible forensics.

**Next Step:**
- Application is fully complete, hardened, and ready for production deployment, live on-chain demonstrations, or hackathon presentation.

