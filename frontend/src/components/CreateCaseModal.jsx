import { useState, useEffect } from 'react';
import { FolderLock, X, AlertCircle } from 'lucide-react';

export default function CreateCaseModal({
  isOpen,
  onClose,
  initialTargetWallet = '',
  initialAlertId = '',
  initialRelatedWallets = [],
  onCaseCreated
}) {
  const [title, setTitle] = useState('');
  const [targetWallet, setTargetWallet] = useState('');
  const [notes, setNotes] = useState('');
  const [alertIdsInput, setAlertIdsInput] = useState('');
  const [relatedWalletsInput, setRelatedWalletsInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setTargetWallet(initialTargetWallet || '');
      setTitle(initialTargetWallet ? `Investigation: ${initialTargetWallet.slice(0, 10)}...` : '');
      setNotes('');
      setAlertIdsInput(initialAlertId ? initialAlertId : '');
      setRelatedWalletsInput(initialRelatedWallets?.length ? initialRelatedWallets.join(', ') : '');
      setError(null);
    }
  }, [isOpen, initialTargetWallet, initialAlertId, initialRelatedWallets]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Case title is required.');
      return;
    }
    if (!targetWallet.trim()) {
      setError('Target wallet address is required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const alertIds = alertIdsInput
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const relatedWallets = relatedWalletsInput
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    try {
      await onCaseCreated({
        title: title.trim(),
        target_wallet: targetWallet.trim(),
        notes: notes.trim(),
        alert_ids: alertIds,
        related_wallets: relatedWallets,
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create case');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
              <FolderLock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Create Investigation Case</h3>
              <p className="text-xs text-slate-400">Open a formal forensic investigation dossier</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 text-xs text-rose-300 bg-rose-950/50 border border-rose-800/80 rounded-xl">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Case Title <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Circular Routing Ring Analysis"
              className="w-full px-3.5 py-2 text-xs text-white bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 font-sans"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Target Wallet Address <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={targetWallet}
              onChange={(e) => setTargetWallet(e.target.value)}
              placeholder="0x..."
              className="w-full px-3.5 py-2 text-xs text-white bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Initial Analyst Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record preliminary hypothesis, pattern observations, or priority level..."
              className="w-full px-3.5 py-2 text-xs text-white bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 font-sans resize-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                Linked Alert IDs (comma separated)
              </label>
              <input
                type="text"
                value={alertIdsInput}
                onChange={(e) => setAlertIdsInput(e.target.value)}
                placeholder="alert_circ_01, ..."
                className="w-full px-3 py-1.5 text-xs text-white bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1">
                Related Wallets (comma separated)
              </label>
              <input
                type="text"
                value={relatedWalletsInput}
                onChange={(e) => setRelatedWalletsInput(e.target.value)}
                placeholder="0xabc..., 0xdef..."
                className="w-full px-3 py-1.5 text-xs text-white bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              {submitting ? 'Creating Case...' : 'Create Case'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
