"""
ChainSentinel - Backend API
FastAPI service providing blockchain forensics endpoints,
transaction exploration, pattern detection, and risk assessment.

Endpoints:
  Phase 1/2 (existing, preserved):
    GET /health
    GET /api/info
    GET /transactions
    GET /transactions/{tx_id}

  Phase 3 (detection engine):
    GET /alerts
    GET /alerts/{alert_id}
    GET /wallets/{wallet_id}/risk
    GET /wallets/{wallet_id}/alerts
    GET /wallets/{wallet_id}/transactions
    GET /graph/{wallet_id}
    GET /detection/summary

  Phase 4A (investigation workflow):
    POST /investigations
    GET  /investigations
    GET  /investigations/{case_id}
    PATCH /investigations/{case_id}/status
    PATCH /investigations/{case_id}/notes

  Phase 4B-1 (investigation summary):
    GET  /investigations/{case_id}/summary

  Phase 4B-2 (investigation graph):
    GET  /investigations/{case_id}/graph

  Phase 5 (evidence integrity & merkle verification):
    POST /investigations/{case_id}/evidence
    GET  /investigations/{case_id}/evidence
    GET  /evidence/{evidence_id}
    GET  /evidence/{evidence_id}/verify
    GET  /investigations/{case_id}/evidence/merkle
    POST /investigations/{case_id}/evidence/merkle/verify

  Phase 6 (advanced investigation workflow):
    GET  /investigations/{case_id}/timeline

  Phase 7 (flow tracer & path reconstruction):
    GET  /flow/trace
    GET  /investigations/{case_id}/flow

  Phase 8 (advanced analytics & intelligence):
    GET  /analytics/wallet/{wallet_id}
    GET  /analytics/wallets
    GET  /analytics/summary
    GET  /analytics/correlations
    GET  /analytics/investigations/{case_id}
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from backend.data.loader import load_transactions, get_dataset_stats
    from backend.detection.engine import DetectionEngine
    from backend.investigations.models import (
        InvestigationCase,
        CaseStatus,
        generate_case_id,
        InvestigationTimelineEvent,
        generate_event_id,
    )
    from backend.investigations.store import CASE_STORE
    from backend.crypto.models import EvidenceRecord, EvidenceType, generate_evidence_id
    from backend.crypto.canonical import compute_evidence_hash, verify_evidence_hash
    from backend.crypto.merkle import MerkleTree, compute_merkle_root
    from backend.crypto.store import EVIDENCE_STORE
    from backend.analytics.intelligence import IntelligenceEngine
    from backend.providers.manager import PROVIDER_MANAGER
except (ImportError, ModuleNotFoundError):
    from data.loader import load_transactions, get_dataset_stats
    from detection.engine import DetectionEngine
    from investigations.models import (
        InvestigationCase,
        CaseStatus,
        generate_case_id,
        InvestigationTimelineEvent,
        generate_event_id,
    )
    from investigations.store import CASE_STORE
    from crypto.models import EvidenceRecord, EvidenceType, generate_evidence_id
    from crypto.canonical import compute_evidence_hash, verify_evidence_hash
    from crypto.merkle import MerkleTree, compute_merkle_root
    from crypto.store import EVIDENCE_STORE
    from analytics.intelligence import IntelligenceEngine
    from providers.manager import PROVIDER_MANAGER


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    PROVIDER_MANAGER.shutdown()


app = FastAPI(
    title="ChainSentinel API",
    description="Forensic investigation and graph analytics API for blockchain transactions",
    version="0.2.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite development and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────
# Application startup — initialize from active transaction provider
# ──────────────────────────────────────────────────────────────────
DATASET = PROVIDER_MANAGER.get_transactions()
STATS = get_dataset_stats(DATASET)
ENGINE = DetectionEngine(DATASET)

# Pre-warm the engine cache at startup (runs all detectors once)
_ALL_ALERTS = ENGINE.detect_all()
_ALERTS_BY_ID = {a.alert_id: a for a in _ALL_ALERTS}

# Initialize Intelligence & Analytics Engine (Phase 8)
INTEL_ENGINE = IntelligenceEngine(ENGINE._transactions, ENGINE)


def _on_provider_dataset_updated():
    """Callback invoked when transactions update or data mode switches."""
    global DATASET, STATS, ENGINE, _ALL_ALERTS, _ALERTS_BY_ID, INTEL_ENGINE
    DATASET = PROVIDER_MANAGER.get_transactions()
    STATS = get_dataset_stats(DATASET)
    ENGINE = DetectionEngine(DATASET)
    _ALL_ALERTS = ENGINE.detect_all()
    _ALERTS_BY_ID = {a.alert_id: a for a in _ALL_ALERTS}
    INTEL_ENGINE = IntelligenceEngine(ENGINE._transactions, ENGINE)


PROVIDER_MANAGER.register_listener(_on_provider_dataset_updated)


# ──────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    data_mode: Optional[str] = "DEMO"
    provider_name: Optional[str] = "Synthetic Forensic Ledger (Demo)"


class CreateInvestigationRequest(BaseModel):
    title: str
    target_wallet: str
    notes: Optional[str] = ""
    alert_ids: Optional[List[str]] = []
    related_wallets: Optional[List[str]] = []


class UpdateCaseStatusRequest(BaseModel):
    status: str


class UpdateCaseNotesRequest(BaseModel):
    notes: str


class CreateEvidenceRequest(BaseModel):
    evidence_type: str
    source_ref: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class VerifyMerkleRootRequest(BaseModel):
    expected_root: str


# ──────────────────────────────────────────────────────────────────
# Phase 1 & 2 Endpoints (preserved, unchanged)
# ──────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint for platform monitoring."""
    return {
        "status": "ok",
        "message": "ChainSentinel Backend Engine Operational",
        "version": "0.2.0",
        "data_mode": PROVIDER_MANAGER.mode,
        "provider_name": PROVIDER_MANAGER.get_active_provider().name,
    }


@app.get("/api/info")
def dataset_info():
    """Returns dataset summary statistics and category breakdown."""
    return STATS


@app.get("/transactions")
def list_transactions(
    category: Optional[str] = Query(None, description="Filter by category (e.g., circular, burst, normal)"),
    wallet: Optional[str] = Query(None, description="Filter by wallet address (from or to)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retrieve simulated blockchain transactions with filtering options."""
    txs = DATASET

    if category:
        txs = [t for t in txs if t["category_label"].lower() == category.lower()]

    if wallet:
        target = wallet.lower()
        txs = [t for t in txs if t["from_wallet"].lower() == target or t["to_wallet"].lower() == target]

    total = len(txs)
    paginated = txs[offset: offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "transactions": paginated,
    }


@app.get("/transactions/{tx_id}")
def get_transaction(tx_id: str):
    """Retrieve single transaction details by transaction hash."""
    target_id = tx_id.lower()
    for tx in DATASET:
        if tx["tx_id"].lower() == target_id:
            return tx

    raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found")


# ──────────────────────────────────────────────────────────────────
# Phase 3 Endpoints — Detection Engine
# ──────────────────────────────────────────────────────────────────

@app.get("/alerts")
def list_alerts(
    pattern: Optional[str] = Query(None, description="Filter by pattern type (e.g., CIRCULAR_TRANSACTION)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    wallet: Optional[str] = Query(None, description="Filter alerts containing this wallet"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all detected suspicious activity alerts.
    Supports filtering by pattern type, severity level, and wallet address.
    """
    alerts = _ALL_ALERTS

    if pattern:
        alerts = [a for a in alerts if a.pattern.upper() == pattern.upper()]

    if severity:
        alerts = [a for a in alerts if a.severity.upper() == severity.upper()]

    if wallet:
        alerts = [a for a in alerts if wallet in a.wallets]

    total = len(alerts)
    paginated = alerts[offset: offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "alerts": [a.to_dict() for a in paginated],
    }


@app.get("/alerts/{alert_id}")
def get_alert(alert_id: str):
    """Retrieve a single alert by its unique alert_id."""
    for alert in _ALL_ALERTS:
        if alert.alert_id == alert_id:
            return alert.to_dict()
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@app.get("/wallets/{wallet_id}/risk")
def get_wallet_risk(wallet_id: str):
    """
    Return the risk assessment (score, level, pattern types) for a wallet.
    Score is computed from the additive weight of all detected pattern types.
    """
    risk = ENGINE.get_wallet_risk(wallet_id)
    return risk.to_dict()


@app.get("/wallets/{wallet_id}/alerts")
def get_wallet_alerts(wallet_id: str):
    """Return all alerts that involve the specified wallet address."""
    alerts = ENGINE.detect_for_wallet(wallet_id)
    return {
        "wallet_id": wallet_id,
        "total": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


@app.get("/wallets/{wallet_id}/transactions")
def get_wallet_transactions(
    wallet_id: str,
    limit: int = Query(50, ge=1, le=200),
):
    """Return all transactions (inbound + outbound) for a wallet."""
    txs = [
        t for t in DATASET
        if t["from_wallet"] == wallet_id or t["to_wallet"] == wallet_id
    ]
    return {
        "wallet_id": wallet_id,
        "total": len(txs),
        "transactions": txs[:limit],
    }


@app.get("/graph/{wallet_id}")
def get_wallet_graph(
    wallet_id: str,
    depth: int = Query(2, ge=1, le=3, description="Hop depth for graph expansion"),
):
    """
    Return Cytoscape-compatible graph data (nodes + edges) for a wallet
    and its neighbourhood up to `depth` hops.
    """
    return ENGINE.get_wallet_graph(wallet_id, depth=depth)


@app.get("/detection/summary")
def get_detection_summary():
    """
    Return a high-level summary of all detection results:
    total alerts, breakdown by pattern and severity.
    """
    summary = ENGINE.get_summary()
    return summary.to_dict()


# ──────────────────────────────────────────────────────────────────
# Phase 4A Endpoints — Investigation Workflow
# ──────────────────────────────────────────────────────────────────

@app.post("/investigations", status_code=201)
def create_investigation(payload: CreateInvestigationRequest):
    """
    Create a new investigation case.
    Validates required fields, generates a unique deterministic case ID,
    and stores the case in the investigation repository.
    """
    title = payload.title.strip() if payload.title else ""
    target_wallet = payload.target_wallet.strip() if payload.target_wallet else ""

    if not title:
        raise HTTPException(status_code=400, detail="title cannot be empty")
    if not target_wallet:
        raise HTTPException(status_code=400, detail="target_wallet cannot be empty")

    now_iso = datetime.now(timezone.utc).isoformat()
    case_id = generate_case_id(target_wallet, now_iso)

    case = InvestigationCase(
        case_id=case_id,
        title=title,
        target_wallet=target_wallet,
        status=CaseStatus.OPEN,
        notes=payload.notes.strip() if payload.notes else "",
        alert_ids=payload.alert_ids or [],
        related_wallets=payload.related_wallets or [],
        created_at=now_iso,
        updated_at=now_iso,
    )

    try:
        saved_case = CASE_STORE.create(case)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return saved_case.to_dict()


@app.get("/investigations")
def list_investigations(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, CLOSED)"),
):
    """
    List all investigation cases, ordered newest first.
    Optionally filter by status.
    """
    cases = CASE_STORE.list_all()
    if status:
        norm_status = status.strip().upper()
        cases = [c for c in cases if c.status == norm_status]

    return {
        "total": len(cases),
        "investigations": [c.to_dict() for c in cases],
    }


@app.get("/investigations/{case_id}")
def get_investigation(case_id: str):
    """Retrieve details for a single investigation case by its case_id."""
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")
    return case.to_dict()


@app.patch("/investigations/{case_id}/status")
def update_investigation_status(case_id: str, payload: UpdateCaseStatusRequest):
    """Update the status of an investigation case (OPEN or CLOSED)."""
    norm_status = payload.status.strip().upper() if payload.status else ""
    if norm_status not in (CaseStatus.OPEN, CaseStatus.CLOSED):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Status must be OPEN or CLOSED.",
        )

    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    updated = CASE_STORE.update_status(case_id, norm_status)
    return updated.to_dict()


@app.patch("/investigations/{case_id}/notes")
def update_investigation_notes(case_id: str, payload: UpdateCaseNotesRequest):
    """Update analyst notes for an investigation case."""
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    updated = CASE_STORE.update_notes(case_id, payload.notes)
    return updated.to_dict()


@app.get("/investigations/{case_id}/summary")
def get_investigation_summary(case_id: str):
    """
    Retrieve comprehensive forensic investigation summary for a case.
    Aggregates case metadata, resolved alert objects, target wallet risk assessment,
    inbound and outbound transactions for the target wallet, and risk assessments
    for any tagged related wallets.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    target_risk = ENGINE.get_wallet_risk(case.target_wallet).to_dict()

    resolved_alerts = [
        _ALERTS_BY_ID[aid].to_dict()
        for aid in case.alert_ids
        if aid in _ALERTS_BY_ID
    ]

    wallet_txs = [
        t for t in DATASET
        if t["from_wallet"] == case.target_wallet or t["to_wallet"] == case.target_wallet
    ]

    related_risks = {
        wallet_addr: ENGINE.get_wallet_risk(wallet_addr).to_dict()
        for wallet_addr in case.related_wallets
    }

    return {
        "case": case.to_dict(),
        "target_wallet_risk": target_risk,
        "resolved_alerts": resolved_alerts,
        "wallet_transactions": wallet_txs,
        "related_wallet_risks": related_risks,
        "evidence_count": EVIDENCE_STORE.count_by_case(case_id),
    }


@app.get("/investigations/{case_id}/graph")
def get_investigation_graph(
    case_id: str,
    depth: int = Query(2, ge=1, le=3, description="Hop depth for graph expansion"),
):
    """
    Return Cytoscape-compatible graph data (nodes + edges) for an investigation case,
    centered around the case's target_wallet up to `depth` hops.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    graph_data = ENGINE.get_wallet_graph(case.target_wallet, depth=depth)
    return {
        "case_id": case.case_id,
        "target_wallet": case.target_wallet,
        **graph_data,
    }


# ──────────────────────────────────────────────────────────────────
# Phase 5 Endpoints — Cryptographic Evidence & Integrity Verification
# ──────────────────────────────────────────────────────────────────

@app.post("/investigations/{case_id}/evidence", status_code=201)
def create_case_evidence(case_id: str, payload: CreateEvidenceRequest):
    """
    Create and cryptographically anchor an evidence record for an investigation case.
    Validates case existence, canonicalizes payload, calculates SHA-256 digest,
    and stores in the tamper-evident repository.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    ev_type = payload.evidence_type.strip().upper() if payload.evidence_type else ""
    if not ev_type:
        raise HTTPException(status_code=400, detail="evidence_type is required")

    source_ref = payload.source_ref.strip() if payload.source_ref else ""
    now_iso = datetime.now(timezone.utc).isoformat()
    evidence_id = generate_evidence_id(case_id, ev_type, now_iso)
    meta = payload.metadata or {}

    evidence_hash = compute_evidence_hash(
        case_id=case_id,
        evidence_type=ev_type,
        source_ref=source_ref,
        content=payload.content,
        metadata=meta,
    )

    record = EvidenceRecord(
        evidence_id=evidence_id,
        case_id=case_id,
        evidence_type=ev_type,
        source_ref=source_ref,
        content=payload.content,
        created_at=now_iso,
        evidence_hash=evidence_hash,
        metadata=meta,
    )

    try:
        saved = EVIDENCE_STORE.create(record)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Log timeline event to case store
    evt = InvestigationTimelineEvent(
        event_id=generate_event_id(case_id, "EVIDENCE_ANCHORED", now_iso),
        case_id=case_id,
        event_type="EVIDENCE_ANCHORED",
        title=f"Evidence Anchored ({ev_type})",
        description=f"Cryptographically hashed evidence record {saved.evidence_id} added with source ref '{source_ref}'.",
        timestamp=now_iso,
        actor="Evidence Engine",
        metadata={
            "evidence_id": saved.evidence_id,
            "evidence_type": ev_type,
            "source_ref": source_ref,
            "evidence_hash": saved.evidence_hash,
        },
    )
    CASE_STORE.add_event(evt)

    return saved.to_dict()


@app.get("/investigations/{case_id}/evidence")
def list_case_evidence(case_id: str):
    """List all cryptographic evidence records bound to an investigation case."""
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    records = EVIDENCE_STORE.list_by_case(case_id)
    return {
        "case_id": case_id,
        "total": len(records),
        "evidence": [r.to_dict() for r in records],
    }


@app.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: str):
    """Retrieve an evidence record by its unique evidence ID."""
    record = EVIDENCE_STORE.get(evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evidence record '{evidence_id}' not found")
    return record.to_dict()


@app.get("/evidence/{evidence_id}/verify")
def verify_evidence(evidence_id: str):
    """
    Verify the cryptographic integrity of an evidence record.
    Re-canonicalizes stored content and checks against the recorded SHA-256 digest.
    """
    record = EVIDENCE_STORE.get(evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evidence record '{evidence_id}' not found")

    result = EVIDENCE_STORE.verify(evidence_id)
    result["algorithm"] = "SHA-256"
    result["verified_at"] = datetime.now(timezone.utc).isoformat()
    return result


@app.get("/investigations/{case_id}/evidence/merkle")
def get_case_merkle_root(case_id: str):
    """
    Generate and retrieve the Merkle root and audit parameters for an
    investigation's complete evidence collection.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    records = EVIDENCE_STORE.list_by_case(case_id)
    leaf_hashes = [r.evidence_hash for r in records]
    tree = MerkleTree(leaf_hashes)

    return {
        "case_id": case_id,
        "total_leaves": len(leaf_hashes),
        "leaf_hashes": tree.leaves,
        "merkle_root": tree.root,
        "odd_leaf_handling": "trailing_duplicate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/investigations/{case_id}/evidence/merkle/verify")
def verify_case_merkle_root(case_id: str, payload: VerifyMerkleRootRequest):
    """
    Verify an investigation's current evidence collection against an expected Merkle root.
    Also audits all individual leaves for tamper detection.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    records = EVIDENCE_STORE.list_by_case(case_id)
    leaf_hashes = [r.evidence_hash for r in records]
    tree = MerkleTree(leaf_hashes)

    # Audit each individual leaf
    intact_count = 0
    tampered_count = 0
    for r in records:
        v = EVIDENCE_STORE.verify(r.evidence_id)
        if v and v.get("valid"):
            intact_count += 1
        else:
            tampered_count += 1

    expected_norm = payload.expected_root.strip().lower()
    computed_norm = tree.root.lower()
    root_match = (expected_norm == computed_norm)
    valid = root_match and (tampered_count == 0)

    # Log audit event to case store
    now_iso = datetime.now(timezone.utc).isoformat()
    evt = InvestigationTimelineEvent(
        event_id=generate_event_id(case_id, "INTEGRITY_VERIFIED", now_iso),
        case_id=case_id,
        event_type="INTEGRITY_VERIFIED",
        title="Merkle Integrity Audit Executed",
        description=f"Collection integrity audited against Merkle root. Status: {'VERIFIED INTACT' if valid else 'COMPROMISED'} ({intact_count}/{len(records)} leaves intact).",
        timestamp=now_iso,
        actor="Integrity Engine",
        metadata={
            "valid": valid,
            "root_match": root_match,
            "intact_leaves_count": intact_count,
            "total_leaves": len(records),
        },
    )
    CASE_STORE.add_event(evt)

    return {
        "case_id": case_id,
        "expected_root": payload.expected_root,
        "computed_root": tree.root,
        "root_match": root_match,
        "valid": valid,
        "tampered": not valid,
        "total_leaves": len(records),
        "intact_leaves_count": intact_count,
        "tampered_leaves_count": tampered_count,
        "verified_at": now_iso,
    }


# ──────────────────────────────────────────────────────────────────
# Phase 6 Endpoints — Advanced Investigation Workflow & Timeline
# ──────────────────────────────────────────────────────────────────

@app.get("/investigations/{case_id}/timeline")
def get_investigation_timeline(
    case_id: str,
    order: str = Query("asc", description="Sort order: 'asc' (chronological) or 'desc'"),
):
    """
    Return the complete, chronological audit timeline for an investigation case.
    Synthesizes events from case creation, alert linkages, evidence anchors,
    status transitions, analyst notes updates, and Merkle integrity audits.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    events = list(CASE_STORE.get_events(case_id))

    # Ensure baseline creation event exists
    has_creation = any(e.event_type == "CASE_CREATED" for e in events)
    if not has_creation:
        events.append(InvestigationTimelineEvent(
            event_id=generate_event_id(case_id, "CASE_CREATED", case.created_at),
            case_id=case_id,
            event_type="CASE_CREATED",
            title="Investigation Opened",
            description=f"Formal case initialized for target wallet {case.target_wallet} with {len(case.alert_ids)} linked alert(s).",
            timestamp=case.created_at,
            actor="Lead Investigator",
            metadata={"target_wallet": case.target_wallet, "alert_ids": case.alert_ids},
        ))

    # Ensure all evidence records from the store are represented
    existing_evidence_ids = {
        e.metadata.get("evidence_id")
        for e in events
        if e.event_type == "EVIDENCE_ANCHORED" and "evidence_id" in e.metadata
    }
    for ev in EVIDENCE_STORE.list_by_case(case_id):
        if ev.evidence_id not in existing_evidence_ids:
            events.append(InvestigationTimelineEvent(
                event_id=generate_event_id(case_id, "EVIDENCE_ANCHORED", ev.created_at),
                case_id=case_id,
                event_type="EVIDENCE_ANCHORED",
                title=f"Evidence Anchored ({ev.evidence_type})",
                description=f"Cryptographically hashed evidence record {ev.evidence_id} added (source: '{ev.source_ref}', SHA-256: {ev.evidence_hash[:16]}...).",
                timestamp=ev.created_at,
                actor="Evidence Engine",
                metadata={
                    "evidence_id": ev.evidence_id,
                    "evidence_type": ev.evidence_type,
                    "source_ref": ev.source_ref,
                    "evidence_hash": ev.evidence_hash,
                },
            ))

    reverse = (order.lower() == "desc")
    sorted_events = sorted(events, key=lambda e: (e.timestamp, e.event_id), reverse=reverse)

    return {
        "case_id": case_id,
        "total": len(sorted_events),
        "events": [e.to_dict() for e in sorted_events],
    }


# ──────────────────────────────────────────────────────────────────
# Phase 7 Endpoints — Flow Tracer & Path Reconstruction
# ──────────────────────────────────────────────────────────────────

@app.get("/flow/trace")
def trace_transaction_flow(
    source: str = Query(..., description="Source origin wallet address"),
    target: Optional[str] = Query(None, description="Optional target destination wallet address"),
    max_depth: int = Query(4, ge=1, le=6, description="Maximum traversal depth (1-6 hops)"),
):
    """
    Trace directed transaction flow and reconstruct paths between wallets.
    Returns path metrics, hop-by-hop transactions, suspicion score,
    and Cytoscape-formatted graph elements with highlighting flags.
    If target is not specified, discovers all reachable downstream destinations.
    """
    source_clean = source.strip()
    target_clean = target.strip() if target else None

    # Validate that wallets exist in transaction dataset
    all_wallets = set(t["from_wallet"] for t in DATASET) | set(t["to_wallet"] for t in DATASET)
    if source_clean not in all_wallets:
        raise HTTPException(
            status_code=404,
            detail=f"Source wallet '{source_clean}' does not exist in transaction dataset",
        )
    if target_clean and target_clean not in all_wallets:
        raise HTTPException(
            status_code=404,
            detail=f"Target wallet '{target_clean}' does not exist in transaction dataset",
        )

    return ENGINE.trace_flow(source=source_clean, target=target_clean, max_depth=max_depth)


@app.get("/investigations/{case_id}/flow")
def trace_case_flow(
    case_id: str,
    target: Optional[str] = Query(None, description="Optional destination wallet (defaults to first related wallet if available)"),
    max_depth: int = Query(4, ge=1, le=6, description="Maximum traversal depth (1-6 hops)"),
):
    """
    Execute flow trace anchored to an investigation case's target wallet.
    Allows investigating fund flow between the case's target wallet and related entities.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{case_id}' not found")

    target_wallet = target.strip() if target else None
    if not target_wallet and case.related_wallets:
        target_wallet = case.related_wallets[0]

    all_wallets = set(t["from_wallet"] for t in DATASET) | set(t["to_wallet"] for t in DATASET)
    if case.target_wallet not in all_wallets:
        raise HTTPException(
            status_code=404,
            detail=f"Case target wallet '{case.target_wallet}' does not exist in transaction dataset",
        )

    return ENGINE.trace_flow(source=case.target_wallet, target=target_wallet, max_depth=max_depth)


# ──────────────────────────────────────────────────────────────────
# Phase 8 Endpoints — Advanced Analytics & Intelligence
# ──────────────────────────────────────────────────────────────────

@app.get("/analytics/wallet/{wallet_id}")
def get_wallet_intelligence(wallet_id: str):
    """
    Retrieve comprehensive behavioral profile, explainable risk assessment,
    observable forensic signals, and multi-pattern correlations for a wallet.
    """
    clean_id = wallet_id.strip()
    intel = INTEL_ENGINE.get_wallet_intelligence(clean_id)
    if not intel:
        raise HTTPException(
            status_code=404,
            detail=f"Wallet '{clean_id}' does not exist in transaction dataset",
        )
    return intel.to_dict()


@app.get("/analytics/wallets")
def list_wallets_analytics(
    limit: int = Query(50, ge=1, le=200, description="Page size limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    classification: Optional[str] = Query(None, description="Filter by classification, e.g. NORMAL, CIRCULAR, HIGH_RISK"),
    priority: Optional[str] = Query(None, description="Filter by priority, e.g. LOW, MEDIUM, HIGH, CRITICAL"),
    min_risk: float = Query(0.0, ge=0.0, le=100.0, description="Minimum risk score"),
):
    """
    Retrieve ranked and paginated list of behavioral profiles for all wallets in the system.
    Supports filtering by behavioral classification, investigation priority, and minimum risk score.
    """
    return INTEL_ENGINE.get_all_wallet_profiles(
        limit=limit,
        offset=offset,
        classification=classification,
        priority=priority,
        min_risk=min_risk,
    )


@app.get("/analytics/summary")
def get_analytics_summary():
    """
    Retrieve global network intelligence summary including behavioral classification breakdown,
    priority distribution, cross-pattern correlations count, and top priority targets.
    """
    return INTEL_ENGINE.get_network_summary()


@app.get("/analytics/correlations")
def list_correlations(
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    wallet: Optional[str] = Query(None, description="Filter correlations involving this wallet"),
):
    """
    Retrieve all multi-pattern correlation events where distinct suspicious topologies converge
    on the same wallet, entity cluster, or time window.
    """
    correlations = INTEL_ENGINE.get_all_correlations()
    if severity:
        sev_upper = severity.upper()
        correlations = [c for c in correlations if c.severity == sev_upper]
    if wallet:
        w_clean = wallet.strip()
        correlations = [
            c for c in correlations
            if c.primary_wallet == w_clean or w_clean in c.participating_wallets
        ]
    return {
        "total": len(correlations),
        "correlations": [c.to_dict() for c in correlations],
    }


@app.get("/analytics/investigations/{case_id}")
def get_investigation_intelligence(case_id: str):
    """
    Generate an executive-level strategic intelligence dossier for an investigation case,
    including priority score, target behavioral analysis, counterparty risk matrix,
    cross-pattern convergence events, and cryptographic Merkle integrity status.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation case '{case_id}' not found",
        )

    intel = INTEL_ENGINE.get_investigation_intelligence(case_id)
    if not intel:
        raise HTTPException(
            status_code=404,
            detail=f"Intelligence dossier could not be compiled for case '{case_id}' (target wallet may not exist in ledger)",
        )
    return intel.to_dict()


# ──────────────────────────────────────────────────────────────────
# Phase 10: Pluggable Transaction Providers & Real-Time Ingestion
# ──────────────────────────────────────────────────────────────────

class SwitchModeRequest(BaseModel):
    mode: str


class IngestTransactionsRequest(BaseModel):
    transactions: List[Dict[str, Any]]


class FetchLiveBlockRequest(BaseModel):
    max_txs: Optional[int] = 25


@app.get("/api/provider/status")
def get_provider_status():
    """Returns the operational status of the active transaction provider and data mode."""
    return PROVIDER_MANAGER.get_status()


@app.post("/api/provider/mode")
def set_provider_mode(req: SwitchModeRequest):
    """
    Switches the active transaction data mode between 'DEMO' (synthetic ledger)
    and 'LIVE' (real-time blockchain ingestion / public RPC).
    """
    try:
        return PROVIDER_MANAGER.switch_mode(req.mode)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


class MonitoringControlRequest(BaseModel):
    active: bool


@app.post("/api/provider/pause")
def pause_live_monitoring():
    """Pauses automatic background block polling while preserving live dataset and LIVE mode."""
    return PROVIDER_MANAGER.pause_monitoring()


@app.post("/api/provider/resume")
def resume_live_monitoring():
    """Resumes automatic background block polling for live Ethereum transactions."""
    return PROVIDER_MANAGER.resume_monitoring()


@app.post("/api/provider/monitoring")
def control_live_monitoring(req: MonitoringControlRequest):
    """Controls automatic background block polling (active=True or active=False)."""
    if req.active:
        return PROVIDER_MANAGER.resume_monitoring()
    return PROVIDER_MANAGER.pause_monitoring()


@app.post("/api/provider/ingest")
def ingest_live_transactions(req: IngestTransactionsRequest):
    """
    Ingests live external blockchain transactions, normalizes them into ChainSentinel
    schema, and updates detection models and risk scores in real-time.
    """
    if not req.transactions:
        raise HTTPException(status_code=400, detail="Transactions array cannot be empty")
    return PROVIDER_MANAGER.ingest_live_transactions(req.transactions)


@app.post("/api/provider/fetch-live")
def fetch_live_blockchain_block(req: Optional[FetchLiveBlockRequest] = None):
    """
    Polls the configured public Ethereum JSON-RPC endpoint for latest block transactions,
    normalizes them, and ingests them into the live feed.
    """
    max_txs = req.max_txs if req and req.max_txs else 25
    return PROVIDER_MANAGER.fetch_live_block(max_txs=max_txs)


@app.get("/api/provider/check-connection")
def check_rpc_connection():
    """
    Probes the active Ethereum JSON-RPC provider to test network connectivity
    and return current block height.
    """
    return PROVIDER_MANAGER.live_provider.check_connection()


@app.get("/api/provider/export-csv")
def export_live_transactions_csv():
    """
    Exports all persisted live Ethereum blockchain transactions from SQLite
    to an Excel-compatible CSV file with UTF-8 BOM encoding.
    """
    csv_content = PROVIDER_MANAGER.export_live_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="chainsentinel_live_transactions.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )






