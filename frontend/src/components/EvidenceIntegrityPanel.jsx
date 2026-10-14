import { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Shield,
  RefreshCw,
  Plus,
  Check,
  Copy,
  ChevronDown,
  ChevronRight,
  Hash,
  Clock,
  FileCode
} from 'lucide-react';
import { verifyEvidence, verifyCaseMerkleRoot } from '../api';

export default function EvidenceIntegrityPanel({
  caseId,
  evidenceList = [],
  merkleData = null,
  onRefreshEvidence,
  onOpenAddEvidenceModal
}) {
  // Verification states map: { [evidenceId]: { valid: bool, tampered: bool, loading: bool } }
  const [itemStatuses, setItemStatuses] = useState({});
  const [collectionAudit, setCollectionAudit] = useState(null);
  const [auditingCollection, setAuditingCollection] = useState(false);
  const [auditingAll, setAuditingAll] = useState(false);
  const [expandedItems, setExpandedItems] = useState({});
  const [copiedRoot, setCopiedRoot] = useState(false);

  // Copy Merkle root
  const handleCopyRoot = () => {
    if (merkleData?.merkle_root) {
      navigator.clipboard.writeText(merkleData.merkle_root);
      setCopiedRoot(true);
      setTimeout(() => setCopiedRoot(false), 2000);
    }
  };

  // Toggle item content expansion
  const toggleExpand = (evidenceId) => {
    setExpandedItems((prev) => ({ ...prev, [evidenceId]: !prev[evidenceId] }));
  };

  // Verify single evidence item
  const handleVerifyItem = async (evidenceId) => {
    setItemStatuses((prev) => ({
      ...prev,
      [evidenceId]: { ...prev[evidenceId], loading: true },
    }));

    try {
      const res = await verifyEvidence(evidenceId);
      setItemStatuses((prev) => ({
        ...prev,
        [evidenceId]: {
          valid: res.valid,
          tampered: res.tampered,
          loading: false,
          verifiedAt: new Date().toLocaleTimeString(),
        },
      }));
    } catch (err) {
      console.error('Failed to verify item:', err);
      setItemStatuses((prev) => ({
        ...prev,
        [evidenceId]: { valid: false, tampered: true, loading: false, error: err.message },
      }));
    }
  };

  // Verify all evidence items in sequence
  const handleVerifyAll = async () => {
    if (!evidenceList.length) return;
    setAuditingAll(true);
    for (const item of evidenceList) {
      await handleVerifyItem(item.evidence_id);
    }
    setAuditingAll(false);
  };

  // Audit entire collection against Merkle root
  const handleAuditCollection = async () => {
    if (!caseId || !merkleData?.merkle_root) return;
    setAuditingCollection(true);
    try {
      const res = await verifyCaseMerkleRoot(caseId, merkleData.merkle_root);
      setCollectionAudit(res);
      // Also update item statuses from the audit
      if (res.valid) {
        const updated = {};
        for (const item of evidenceList) {
          updated[item.evidence_id] = { valid: true, tampered: false, loading: false };
        }
        setItemStatuses(updated);
      }
    } catch (err) {
      console.error('Merkle audit failed:', err);
      setCollectionAudit({ valid: false, tampered: true, error: err.message });
    } finally {
      setAuditingCollection(false);
    }
  };

  const verifiedCount = Object.values(itemStatuses).filter((s) => s.valid).length;

  return (
    <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 space-y-5">
      {/* Panel Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h4 className="text-sm font-bold text-white font-mono flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> Evidence Integrity &amp; Merkle Audit
          </h4>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">
            Cryptographic SHA-256 proof chain anchoring investigation artifacts to immutable Merkle roots.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenAddEvidenceModal}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" /> Anchor Evidence
          </button>

          {onRefreshEvidence && (
            <button
              type="button"
              onClick={onRefreshEvidence}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-colors"
              title="Refresh evidence list"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            type="button"
            onClick={handleVerifyAll}
            disabled={auditingAll || !evidenceList.length}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 hover:text-white rounded-lg text-xs font-mono transition-colors flex items-center gap-1.5"
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${auditingAll ? 'animate-spin text-emerald-400' : ''}`} />
            {auditingAll ? 'Auditing...' : 'Verify All'}
          </button>
        </div>
      </div>

      {/* Merkle Root & Summary Metrics Card */}
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Count & Status Metric */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
            Anchored Evidence
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold font-mono text-white">
              {evidenceList.length}
            </span>
            <span className="text-xs font-mono text-slate-500">records</span>
            {evidenceList.length > 0 && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {verifiedCount}/{evidenceList.length} verified
              </span>
            )}
          </div>
        </div>

        {/* Merkle Root Digest */}
        <div className="md:col-span-2 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Hash className="w-3 h-3 text-indigo-400" /> Case Merkle Root (SHA-256)
            </span>
            <button
              type="button"
              onClick={handleCopyRoot}
              disabled={!merkleData?.merkle_root}
              className="text-[10px] font-mono text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              {copiedRoot ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" /> Copied
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" /> Copy Root
                </>
              )}
            </button>
          </div>

          <div className="flex items-center justify-between gap-2 bg-slate-950 p-2 rounded-lg border border-slate-800/80 font-mono text-[11px]">
            <span className="truncate text-indigo-300 font-bold">
              {merkleData?.merkle_root || 'Generating cryptographic root...'}
            </span>
            <button
              type="button"
              onClick={handleAuditCollection}
              disabled={auditingCollection || !evidenceList.length}
              className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded text-[10px] font-bold uppercase transition-all shrink-0"
            >
              {auditingCollection ? 'Auditing Root...' : 'Verify Collection'}
            </button>
          </div>
        </div>
      </div>

      {/* Collection Audit Banner */}
      {collectionAudit && (
        <div
          className={`p-3 rounded-xl border font-mono text-xs flex items-center justify-between ${
            collectionAudit.valid
              ? 'bg-emerald-950/70 border-emerald-700/80 text-emerald-300'
              : 'bg-rose-950/70 border-rose-700/80 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {collectionAudit.valid ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>
              {collectionAudit.valid
                ? `✓ MERKLE ROOT INTEGRITY CONFIRMED: All ${collectionAudit.total_leaves} evidence items match the cryptographic root.`
                : `⚠ TAMPER DETECTED: Merkle root mismatch or compromised evidence record in collection.`}
            </span>
          </div>
          <span className="text-[10px] opacity-75">
            {collectionAudit.verified_at ? new Date(collectionAudit.verified_at).toLocaleTimeString() : ''}
          </span>
        </div>
      )}

      {/* Evidence Items List */}
      <div className="space-y-2">
        <div className="text-[10px] font-mono uppercase text-slate-400 tracking-wider flex items-center justify-between">
          <span>Evidence Artifact Ledger ({evidenceList.length})</span>
          <span>Status</span>
        </div>

        {evidenceList.length === 0 ? (
          <div className="p-6 bg-slate-900/40 border border-slate-800/80 rounded-xl text-center font-mono text-xs text-slate-500 space-y-1">
            <Shield className="w-5 h-5 mx-auto text-slate-600 mb-1" />
            <p className="text-white font-bold">No evidence records anchored yet.</p>
            <p>Click "Anchor Evidence" above to bind transactions or alerts to this case.</p>
          </div>
        ) : (
          evidenceList.map((item) => {
            const status = itemStatuses[item.evidence_id];
            const isExpanded = expandedItems[item.evidence_id];

            return (
              <div
                key={item.evidence_id}
                className="bg-slate-900/70 border border-slate-800 rounded-xl p-3 space-y-2 font-mono text-xs transition-colors hover:border-slate-700"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => toggleExpand(item.evidence_id)}
                      className="text-slate-500 hover:text-white"
                    >
                      {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    </button>

                    <span className="text-indigo-400 font-bold">{item.evidence_id}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">
                      {item.evidence_type}
                    </span>
                    {item.source_ref && (
                      <span className="text-[11px] text-slate-400 truncate max-w-xs">
                        Ref: {item.source_ref}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 justify-end">
                    {/* Verification badge */}
                    {status?.valid ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/60 flex items-center gap-1">
                        <Check className="w-3 h-3" /> VERIFIED
                      </span>
                    ) : status?.tampered ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-700/60 flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" /> TAMPERED
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        ⚪ NOT AUDITED
                      </span>
                    )}

                    <button
                      type="button"
                      onClick={() => handleVerifyItem(item.evidence_id)}
                      disabled={status?.loading}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[10px] transition-colors flex items-center gap-1"
                    >
                      <RefreshCw className={`w-3 h-3 ${status?.loading ? 'animate-spin text-emerald-400' : ''}`} />
                      Verify
                    </button>
                  </div>
                </div>

                {/* Hash and timestamp row */}
                <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60 gap-2">
                  <div className="flex items-center gap-1 text-slate-400 truncate max-w-md">
                    <span className="text-slate-600">SHA-256:</span>
                    <span className="truncate">{item.evidence_hash}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {/* Collapsible Content JSON Payload */}
                {isExpanded && (
                  <div className="pt-2 border-t border-slate-800/80 animate-in fade-in duration-150 space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <FileCode className="w-3 h-3 text-emerald-400" /> Canonical Payload Content
                      </span>
                    </div>
                    <pre className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[10px] text-emerald-300/90 font-mono overflow-x-auto max-h-40">
                      {JSON.stringify(item.content, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
