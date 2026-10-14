import { AlertTriangle, X, Wallet, FolderPlus, Hash, Compass } from 'lucide-react';

export default function AlertDetailModal({
  alert,
  onClose,
  onInvestigateWallet,
  onViewGraph,
  onTraceFlow,
  onCreateCaseFromAlert
}) {
  if (!alert) return null;

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-purple-950/80 text-purple-300 border-purple-700/60';
      case 'HIGH':
        return 'bg-rose-950/80 text-rose-300 border-rose-700/60';
      case 'MEDIUM':
        return 'bg-amber-950/80 text-amber-300 border-amber-700/60';
      case 'LOW':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const primaryWallet = alert.wallets?.[0] || '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${getSeverityBadge(alert.severity)}`}>
                  {alert.severity}
                </span>
                <span className="text-xs font-mono text-slate-500">#{alert.alert_id}</span>
              </div>
              <h3 className="text-base font-bold text-white mt-0.5">{alert.pattern}</h3>
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

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl">
              <span className="text-[10px] font-mono uppercase text-slate-500 block">Total Volume</span>
              <span className="text-sm font-bold font-mono text-indigo-300">
                {alert.total_amount ? `${alert.total_amount.toFixed(2)} ETH` : 'N/A'}
              </span>
            </div>
            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl">
              <span className="text-[10px] font-mono uppercase text-slate-500 block">Wallets Implicated</span>
              <span className="text-sm font-bold font-mono text-slate-200">
                {alert.wallets?.length || 0} addresses
              </span>
            </div>
            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl">
              <span className="text-[10px] font-mono uppercase text-slate-500 block">Time Span</span>
              <span className="text-sm font-bold font-mono text-slate-200">
                {alert.time_span_seconds ? `${Math.round(alert.time_span_seconds)}s window` : 'Instant'}
              </span>
            </div>
          </div>

          {/* Narrative Explanation */}
          <div>
            <span className="text-[11px] font-mono uppercase text-slate-400 block mb-1.5">
              Forensic Detection Explanation
            </span>
            <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed font-sans">
              {alert.explanation}
            </div>
          </div>

          {/* Implicated Wallets */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-mono uppercase text-slate-400">
                Implicated Wallets ({alert.wallets?.length || 0})
              </span>
              <span className="text-[10px] font-mono text-slate-500">Ordered by topology role</span>
            </div>
            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {alert.wallets?.map((wallet, idx) => (
                <div
                  key={wallet}
                  className="p-2 bg-slate-950/80 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs font-mono"
                >
                  <div className="flex items-center gap-2 truncate mr-3">
                    <span className="text-[10px] text-slate-500 w-4">{idx + 1}.</span>
                    <span className="text-slate-300 truncate">{wallet}</span>
                    {idx === 0 && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold">
                        ORIGIN
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        onInvestigateWallet(wallet);
                        onClose();
                      }}
                      className="px-2 py-1 text-[10px] text-indigo-400 hover:text-white hover:bg-indigo-600 rounded transition-colors"
                    >
                      Investigate
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        onViewGraph(wallet);
                        onClose();
                      }}
                      className="px-2 py-1 text-[10px] text-cyan-400 hover:text-white hover:bg-cyan-600 rounded transition-colors"
                    >
                      Graph
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Associated Transactions */}
          {alert.transaction_ids?.length > 0 && (
            <div>
              <span className="text-[11px] font-mono uppercase text-slate-400 block mb-1.5">
                Associated Transaction Hashes ({alert.transaction_ids.length})
              </span>
              <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                {alert.transaction_ids.map((txId) => (
                  <div
                    key={txId}
                    className="p-1.5 bg-slate-950/50 border border-slate-800/60 rounded text-[11px] font-mono text-slate-400 flex items-center gap-1.5"
                  >
                    <Hash className="w-3 h-3 text-slate-500 shrink-0" />
                    <span className="truncate">{txId}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer Quick Actions */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between shrink-0">
          <div className="text-[11px] font-mono text-slate-500">
            Primary Target: <span className="text-slate-300">{primaryWallet.slice(0, 10)}...</span>
          </div>

          <div className="flex items-center gap-2">
            {onTraceFlow && alert.wallets?.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  const src = alert.wallets[0];
                  const tgt = alert.wallets.length > 1 ? alert.wallets[alert.wallets.length - 1] : '';
                  onTraceFlow(src, tgt);
                  onClose();
                }}
                className="px-3.5 py-1.5 text-xs font-medium text-sky-300 hover:text-white bg-sky-950/70 hover:bg-sky-900 border border-sky-700/60 rounded-xl transition-colors flex items-center gap-1.5 font-mono"
              >
                <Compass className="w-3.5 h-3.5 text-sky-400" /> Trace Flow
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                onCreateCaseFromAlert(alert);
                onClose();
              }}
              className="px-3.5 py-1.5 text-xs font-medium text-indigo-300 hover:text-white bg-indigo-950/70 hover:bg-indigo-900 border border-indigo-700/60 rounded-xl transition-colors flex items-center gap-1.5 font-mono"
            >
              <FolderPlus className="w-3.5 h-3.5" /> Open Case
            </button>
            <button
              type="button"
              onClick={() => {
                onInvestigateWallet(primaryWallet);
                onClose();
              }}
              className="px-4 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-md transition-colors flex items-center gap-1.5 font-mono"
            >
              <Wallet className="w-3.5 h-3.5" /> Full Wallet Deep Dive
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
