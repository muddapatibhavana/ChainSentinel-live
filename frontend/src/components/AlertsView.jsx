import { useState, useMemo } from 'react';
import {
  AlertTriangle,
  Search,
  ArrowUpDown,
  Wallet,
  ArrowUpRight,
  Eye,
  X,
  Compass
} from 'lucide-react';

const PATTERNS = [
  'ALL',
  'CIRCULAR_TRANSACTION',
  'RAPID_MOVEMENT',
  'TRANSACTION_BURST',
  'FAN_OUT_SPLIT',
  'FAN_IN_RECOMBINATION',
  'SUSPICIOUS_CLUSTER',
];

export default function AlertsView({
  alerts,
  onSelectAlert,
  onInvestigateWallet,
  onTraceFlow,
  initialPatternFilter = 'ALL'
}) {
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [patternFilter, setPatternFilter] = useState(initialPatternFilter);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('severity'); // 'severity' | 'amount' | 'time'

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

  const filteredAndSortedAlerts = useMemo(() => {
    return alerts
      .filter((a) => {
        const matchesSeverity = severityFilter === 'ALL' || a.severity === severityFilter;
        const matchesPattern = patternFilter === 'ALL' || a.pattern === patternFilter;
        const query = searchQuery.trim().toLowerCase();
        const matchesQuery =
          !query ||
          a.pattern.toLowerCase().includes(query) ||
          a.alert_id.toLowerCase().includes(query) ||
          a.explanation.toLowerCase().includes(query) ||
          a.wallets?.some((w) => w.toLowerCase().includes(query));
        return matchesSeverity && matchesPattern && matchesQuery;
      })
      .sort((a, b) => {
        if (sortBy === 'severity') {
          const rank = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
          return (rank[a.severity] ?? 4) - (rank[b.severity] ?? 4);
        }
        if (sortBy === 'amount') {
          return (b.total_amount || 0) - (a.total_amount || 0);
        }
        if (sortBy === 'time') {
          return (a.time_span_seconds || 0) - (b.time_span_seconds || 0);
        }
        return 0;
      });
  }, [alerts, severityFilter, patternFilter, searchQuery, sortBy]);

  const clearFilters = () => {
    setSeverityFilter('ALL');
    setPatternFilter('ALL');
    setSearchQuery('');
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters Toolbar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4.5 space-y-3.5 shadow-lg">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by ID, pattern, wallet address, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono transition-colors"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-2.5 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Sort Controls */}
          <div className="flex items-center gap-2 w-full md:w-auto justify-end">
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" /> Sort:
            </span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
            >
              <option value="severity">Severity (High to Low)</option>
              <option value="amount">Volume (Highest First)</option>
              <option value="time">Time Window (Fastest First)</option>
            </select>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
          {/* Severity Pills */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-mono text-slate-400 mr-1 uppercase">Severity:</span>
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                type="button"
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 text-xs font-mono rounded-lg border transition-all ${
                  severityFilter === sev
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                    : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white hover:border-slate-700'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Pattern Dropdown */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-mono text-slate-400 mr-1 uppercase">Pattern:</span>
            <select
              value={patternFilter}
              onChange={(e) => setPatternFilter(e.target.value)}
              className="bg-slate-950/80 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono focus:outline-none focus:border-indigo-500"
            >
              {PATTERNS.map((p) => (
                <option key={p} value={p}>
                  {p === 'ALL' ? 'All Patterns' : p}
                </option>
              ))}
            </select>

            {(severityFilter !== 'ALL' || patternFilter !== 'ALL' || searchQuery) && (
              <button
                type="button"
                onClick={clearFilters}
                className="text-xs text-rose-400 hover:text-rose-300 underline font-mono ml-2"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
        <span>
          Showing <strong className="text-white">{filteredAndSortedAlerts.length}</strong> of{' '}
          <strong className="text-white">{alerts.length}</strong> detected alerts
        </span>
      </div>

      {/* Alerts Grid / Cards */}
      {filteredAndSortedAlerts.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-16 text-center text-slate-500 font-mono text-xs space-y-2">
          <AlertTriangle className="w-8 h-8 mx-auto text-slate-600 mb-2" />
          <p className="text-sm font-bold text-slate-300">No alerts match the active filters.</p>
          <p>Try clearing your search query or selecting "ALL" severity/patterns.</p>
          <button
            type="button"
            onClick={clearFilters}
            className="mt-3 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs"
          >
            Clear All Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredAndSortedAlerts.map((alert) => {
            const isCritical = alert.severity === 'CRITICAL';
            const isHigh = alert.severity === 'HIGH';
            const cardBorderClass = isCritical
              ? 'border-purple-600/70 glow-critical'
              : isHigh
              ? 'border-rose-600/60 glow-high'
              : 'border-slate-800/80';

            return (
              <div
                key={alert.alert_id}
                onClick={() => onSelectAlert(alert)}
                className={`glass-card rounded-xl p-4.5 cursor-pointer transition-all flex flex-col justify-between group space-y-3 ${cardBorderClass}`}
              >
                <div className="space-y-2">
                  {/* Header row */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 truncate">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold shrink-0 ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs font-mono font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                        {alert.pattern}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-indigo-300 font-bold shrink-0">
                      {alert.total_amount ? `${alert.total_amount.toFixed(2)} ETH` : 'N/A'}
                    </span>
                  </div>

                  {/* Explanation */}
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {alert.explanation}
                  </p>

                  {/* Wallets Snippet */}
                  <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400 pt-1">
                    <Wallet className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span className="truncate">
                      Origin: <span className="text-slate-300">{alert.wallets?.[0]?.slice(0, 10)}...</span>
                    </span>
                    <span>&bull;</span>
                    <span className="shrink-0">{alert.wallets?.length} wallets</span>
                  </div>
                </div>

                {/* Bottom bar with action buttons */}
                <div className="pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
                  <span className="text-[10px] text-slate-500">#{alert.alert_id}</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectAlert(alert);
                      }}
                      className="px-2 py-1 text-[11px] font-medium text-slate-300 hover:text-white bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg transition-colors flex items-center gap-1"
                    >
                      <Eye className="w-3 h-3" /> Inspect
                    </button>
                    {onTraceFlow && alert.wallets?.length > 0 && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          const src = alert.wallets[0];
                          const tgt = alert.wallets.length > 1 ? alert.wallets[alert.wallets.length - 1] : '';
                          onTraceFlow(src, tgt);
                        }}
                        className="px-2 py-1 text-[11px] font-medium text-sky-300 hover:text-white bg-sky-950/70 hover:bg-sky-900 border border-sky-800/80 rounded-lg transition-colors flex items-center gap-1"
                        title="Trace Fund Flow"
                      >
                        <Compass className="w-3 h-3 text-sky-400" /> Flow
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onInvestigateWallet(alert.wallets?.[0]);
                      }}
                      className="px-2.5 py-1 text-[11px] font-medium text-indigo-300 hover:text-white bg-indigo-950/70 hover:bg-indigo-600 border border-indigo-800/80 rounded-lg transition-colors flex items-center gap-1"
                    >
                      Investigate <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
