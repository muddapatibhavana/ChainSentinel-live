/**
 * ChainSentinel - Frontend API Client
 *
 * Connects the React application to the FastAPI backend.
 * Supports relative proxying via Vite (/api) with automatic direct fallback
 * to http://127.0.0.1:8000.
 */

const DIRECT_BASE = 'http://127.0.0.1:8000';

/**
 * Universal JSON request helper with proxy + direct fallback
 */
async function request(endpoint, options = {}) {
  // Construct proxy path: Vite proxies /api to backend and strips /api
  // Special case: /api/info needs /api/api/info to preserve /api in the backend route
  const proxyPath = endpoint.startsWith('/api/')
    ? `/api${endpoint}`
    : `/api${endpoint}`;

  try {
    const res = await fetch(proxyPath, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (res.ok) {
      return await res.json();
    }

    // Parse backend error details if present
    const errBody = await res.json().catch(() => ({}));
    const errMessage = errBody.detail || `HTTP ${res.status}: ${res.statusText}`;
    
    // For 4xx errors returned cleanly by backend (e.g. 404), throw directly
    if (res.status >= 400 && res.status < 500) {
      const err = new Error(errMessage);
      err.status = res.status;
      throw err;
    }
  } catch (err) {
    if (err.status) {
      // It's a clean 4xx from backend, do not retry
      throw err;
    }

    // Network error or 5xx: Try direct fallback to backend
    try {
      const directUrl = `${DIRECT_BASE}${endpoint}`;
      const directRes = await fetch(directUrl, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (directRes.ok) {
        return await directRes.json();
      }

      const directErrBody = await directRes.json().catch(() => ({}));
      const fallbackErr = new Error(directErrBody.detail || `HTTP ${directRes.status}`);
      fallbackErr.status = directRes.status;
      throw fallbackErr;
    } catch (fallbackErr) {
      throw new Error(fallbackErr.message || err.message || 'Failed to connect to ChainSentinel backend');
    }
  }
}

// ──────────────────────────────────────────────────────────────────
// Health & Platform Info
// ──────────────────────────────────────────────────────────────────

export async function getHealth() {
  return request('/health');
}

export async function getDatasetInfo() {
  return request('/api/info');
}

// ──────────────────────────────────────────────────────────────────
// Detection Engine & Alerts
// ──────────────────────────────────────────────────────────────────

export async function getDetectionSummary() {
  return request('/detection/summary');
}

export async function getAlerts({ pattern, severity, wallet, limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (pattern) params.append('pattern', pattern);
  if (severity) params.append('severity', severity);
  if (wallet) params.append('wallet', wallet);
  if (limit) params.append('limit', limit);
  if (offset) params.append('offset', offset);

  const qs = params.toString();
  return request(qs ? `/alerts?${qs}` : '/alerts');
}

export async function getAlertById(alertId) {
  return request(`/alerts/${encodeURIComponent(alertId)}`);
}

// ──────────────────────────────────────────────────────────────────
// Wallet Analytics & Cytoscape Graph
// ──────────────────────────────────────────────────────────────────

export async function getWalletRisk(walletId) {
  return request(`/wallets/${encodeURIComponent(walletId)}/risk`);
}

export async function getWalletTransactions(walletId, limit = 50) {
  return request(`/wallets/${encodeURIComponent(walletId)}/transactions?limit=${limit}`);
}

export async function getWalletGraph(walletId, depth = 2) {
  return request(`/graph/${encodeURIComponent(walletId)}?depth=${depth}`);
}

// ──────────────────────────────────────────────────────────────────
// Investigation Cases (Phase 4)
// ──────────────────────────────────────────────────────────────────

export async function getInvestigations(status = null) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return request(`/investigations${qs}`);
}

export async function getInvestigation(caseId) {
  return request(`/investigations/${encodeURIComponent(caseId)}`);
}

export async function getInvestigationSummary(caseId) {
  return request(`/investigations/${encodeURIComponent(caseId)}/summary`);
}

export async function getInvestigationGraph(caseId, depth = 2) {
  return request(`/investigations/${encodeURIComponent(caseId)}/graph?depth=${depth}`);
}

export async function createInvestigation(data) {
  return request('/investigations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateInvestigationStatus(caseId, status) {
  return request(`/investigations/${encodeURIComponent(caseId)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function updateInvestigationNotes(caseId, notes) {
  return request(`/investigations/${encodeURIComponent(caseId)}/notes`, {
    method: 'PATCH',
    body: JSON.stringify({ notes }),
  });
}

// ──────────────────────────────────────────────────────────────────
// Cryptographic Evidence & Integrity (Phase 5 & 6)
// ──────────────────────────────────────────────────────────────────

export async function getCaseEvidence(caseId) {
  return request(`/investigations/${encodeURIComponent(caseId)}/evidence`);
}

export async function getEvidence(evidenceId) {
  return request(`/evidence/${encodeURIComponent(evidenceId)}`);
}

export async function createCaseEvidence(caseId, data) {
  return request(`/investigations/${encodeURIComponent(caseId)}/evidence`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function verifyEvidence(evidenceId) {
  return request(`/evidence/${encodeURIComponent(evidenceId)}/verify`);
}

export async function getCaseMerkleRoot(caseId) {
  return request(`/investigations/${encodeURIComponent(caseId)}/evidence/merkle`);
}

export async function verifyCaseMerkleRoot(caseId, expectedRoot) {
  return request(`/investigations/${encodeURIComponent(caseId)}/evidence/merkle/verify`, {
    method: 'POST',
    body: JSON.stringify({ expected_root: expectedRoot }),
  });
}

export async function getCaseTimeline(caseId, order = 'asc') {
  return request(`/investigations/${encodeURIComponent(caseId)}/timeline?order=${order}`);
}

export async function traceFlow(source, target = null, maxDepth = 4) {
  let url = `/flow/trace?source=${encodeURIComponent(source)}&max_depth=${maxDepth}`;
  if (target) {
    url += `&target=${encodeURIComponent(target)}`;
  }
  return request(url);
}

export async function getCaseFlow(caseId, target = null, maxDepth = 4) {
  let url = `/investigations/${encodeURIComponent(caseId)}/flow?max_depth=${maxDepth}`;
  if (target) {
    url += `&target=${encodeURIComponent(target)}`;
  }
  return request(url);
}

// ──────────────────────────────────────────────────────────────────
// Advanced Analytics & Intelligence (Phase 8)
// ──────────────────────────────────────────────────────────────────

export async function getAnalyticsSummary() {
  return request('/analytics/summary');
}

export async function getWalletsAnalytics({ limit = 50, offset = 0, classification, priority, min_risk } = {}) {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  if (offset) params.append('offset', offset);
  if (classification) params.append('classification', classification);
  if (priority) params.append('priority', priority);
  if (min_risk !== undefined && min_risk !== null) params.append('min_risk', min_risk);

  const qs = params.toString();
  return request(qs ? `/analytics/wallets?${qs}` : '/analytics/wallets');
}

export async function getWalletIntelligence(walletId) {
  return request(`/analytics/wallet/${encodeURIComponent(walletId)}`);
}

export async function getCorrelations({ severity, wallet } = {}) {
  const params = new URLSearchParams();
  if (severity) params.append('severity', severity);
  if (wallet) params.append('wallet', wallet);

  const qs = params.toString();
  return request(qs ? `/analytics/correlations?${qs}` : '/analytics/correlations');
}

export async function getInvestigationIntelligence(caseId) {
  return request(`/analytics/investigations/${encodeURIComponent(caseId)}`);
}

// ──────────────────────────────────────────────────────────────────
// Transaction Providers & Real-Time Ingestion (Phase 10)
// ──────────────────────────────────────────────────────────────────

export async function getProviderStatus() {
  return request('/api/provider/status');
}

export async function setProviderMode(mode) {
  return request('/api/provider/mode', {
    method: 'POST',
    body: JSON.stringify({ mode }),
  });
}

export async function ingestLiveTransactions(transactions) {
  return request('/api/provider/ingest', {
    method: 'POST',
    body: JSON.stringify({ transactions }),
  });
}

export async function fetchLiveBlock(max_txs = 25) {
  return request('/api/provider/fetch-live', {
    method: 'POST',
    body: JSON.stringify({ max_txs }),
  });
}

export async function checkRpcConnection() {
  return request('/api/provider/check-connection');
}

export async function exportLiveTransactionsCsv() {
  try {
    const res = await fetch('/api/provider/export-csv');
    if (!res.ok) {
      throw new Error(`Export failed: ${res.status}`);
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chainsentinel_live_transactions.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    return { success: true };
  } catch (err) {
    console.error('Failed to export CSV:', err);
    throw err;
  }
}

export async function pauseLiveMonitoring() {
  return request('/api/provider/pause', {
    method: 'POST',
  });
}

export async function resumeLiveMonitoring() {
  return request('/api/provider/resume', {
    method: 'POST',
  });
}
