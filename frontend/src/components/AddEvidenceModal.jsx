import { useState, useEffect } from 'react';
import { ShieldCheck, X, FileText, AlertTriangle, Check } from 'lucide-react';
import { createCaseEvidence } from '../api';

const EVIDENCE_TYPES = [
  { value: 'TRANSACTION', label: 'TRANSACTION (Ledger Transfer)' },
  { value: 'ALERT', label: 'ALERT (Rule-based Detection Alert)' },
  { value: 'WALLET_RISK', label: 'WALLET_RISK (Risk Profile Assessment)' },
  { value: 'ANALYST_NOTE', label: 'ANALYST_NOTE (Investigative Finding)' },
  { value: 'GRAPH_SNAPSHOT', label: 'GRAPH_SNAPSHOT (Topological Graph)' },
  { value: 'CUSTOM', label: 'CUSTOM (External Forensic Artifact)' },
];

export default function AddEvidenceModal({
  isOpen,
  onClose,
  caseId,
  initialEvidenceType = 'TRANSACTION',
  initialSourceRef = '',
  initialContent = {},
  onEvidenceAdded
}) {
  const [evidenceType, setEvidenceType] = useState(initialEvidenceType);
  const [sourceRef, setSourceRef] = useState(initialSourceRef);
  const [contentJson, setContentJson] = useState('');
  const [analystNotes, setAnalystNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setEvidenceType(initialEvidenceType || 'TRANSACTION');
      setSourceRef(initialSourceRef || '');
      setContentJson(
        typeof initialContent === 'object' && Object.keys(initialContent || {}).length > 0
          ? JSON.stringify(initialContent, null, 2)
          : JSON.stringify({ description: 'Forensic evidence item', timestamp: new Date().toISOString() }, null, 2)
      );
      setAnalystNotes('');
      setError(null);
      setSuccess(false);
    }
  }, [isOpen, initialEvidenceType, initialSourceRef, initialContent]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!caseId) {
      setError('No active case selected.');
      return;
    }

    if (!evidenceType) {
      setError('Evidence type is required.');
      return;
    }

    let parsedContent = {};
    try {
      parsedContent = JSON.parse(contentJson);
    } catch {
      setError('Content must be a valid JSON object.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await createCaseEvidence(caseId, {
        evidence_type: evidenceType,
        source_ref: sourceRef.trim(),
        content: parsedContent,
        metadata: {
          analyst_note: analystNotes.trim() || undefined,
          client_timestamp: new Date().toISOString(),
        },
      });

      setSuccess(true);
      setTimeout(() => {
        if (onEvidenceAdded) onEvidenceAdded();
        onClose();
      }, 700);
    } catch (err) {
      console.error('Failed to anchor evidence:', err);
      setError(err.message || 'Failed to cryptographically anchor evidence');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-950/80 border border-emerald-700/60 rounded-xl text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono">Anchor Cryptographic Evidence</h3>
              <p className="text-[11px] text-slate-400 font-mono">
                Case: <span className="text-indigo-400 font-bold">{caseId}</span> &bull; SHA-256 Tamper-evident Record
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto font-mono text-xs flex-1">
          {error && (
            <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
              <Check className="w-4 h-4 shrink-0" />
              <span>Evidence anchored and hashed with SHA-256!</span>
            </div>
          )}

          {/* Evidence Type */}
          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px] uppercase tracking-wider block">
              Evidence Category *
            </label>
            <select
              value={evidenceType}
              onChange={(e) => setEvidenceType(e.target.value)}
              className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-indigo-500 font-mono text-xs"
            >
              {EVIDENCE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {/* Source Reference */}
          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px] uppercase tracking-wider block">
              Source Reference Identifier (Tx Hash, Alert ID, Address)
            </label>
            <input
              type="text"
              value={sourceRef}
              onChange={(e) => setSourceRef(e.target.value)}
              placeholder="e.g. 0x71c8... or ALT-circ-01"
              className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 font-mono text-xs"
            />
          </div>

          {/* Content Payload JSON */}
          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px] uppercase tracking-wider flex items-center justify-between">
              <span>Forensic Data Payload (JSON) *</span>
              <span className="text-[10px] text-slate-500">Deterministically sorted &amp; hashed</span>
            </label>
            <textarea
              rows={6}
              value={contentJson}
              onChange={(e) => setContentJson(e.target.value)}
              className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-emerald-300 font-mono text-[11px] focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          {/* Optional Analyst Note */}
          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px] uppercase tracking-wider block">
              Investigator Context / Attestation
            </label>
            <input
              type="text"
              value={analystNotes}
              onChange={(e) => setAnalystNotes(e.target.value)}
              placeholder="e.g. Verified fund path through hops 1 and 2"
              className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 font-sans text-xs"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-slate-400 hover:text-white rounded-xl text-xs transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-mono font-bold shadow-lg shadow-emerald-600/30 transition-all flex items-center gap-2"
            >
              <FileText className="w-3.5 h-3.5" />
              {submitting ? 'Hashing & Anchoring...' : 'Anchor Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
