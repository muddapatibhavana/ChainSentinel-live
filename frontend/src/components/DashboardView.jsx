import { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  Layers,
  ChevronRight,
  ArrowUpRight,
  FolderLock,
  GitMerge,
  Radar,
  Zap
} from 'lucide-react';
import { getAnalyticsSummary } from '../api';

const PATTERN_DESCRIPTIONS = {
  CIRCULAR_TRANSACTION: 'Directed cycle loops routing funds across mule intermediaries to obscure ownership.',
  RAPID_MOVEMENT: 'High-velocity passthrough hops forwarding funds within seconds to evade freezes.',
  TRANSACTION_BURST: 'Rapid programmatic transaction storms indicating automated distribution.',
  FAN_OUT_SPLIT: 'Smurfing dispersal of large balances across multiple smaller accounts.',
  FAN_IN_RECOMBINATION: 'Liquidity consolidation funneling disparate feeder wallets into one collector.',
  SUSPICIOUS_CLUSTER: 'Dense mixing ring networks with reciprocal transfers and no external utility.',
};

const CLASSIFICATION_LABELS = {
  NORMAL: 'Standard Operating',
  HIGH_VOLUME: 'High Volume Treasury',
  HIGH_VELOCITY: 'Rapid Passthrough',
  FAN_OUT: 'Dispersal Fan-Out',
  FAN_IN: 'Consolidation Fan-In',
  CIRCULAR: 'Circular Cycle Loop',
  MIXER_LIKE: 'Cluster Mixing Node',
  MULTI_PATTERN: 'Multi-Pattern Convergence',
  HIGH_RISK: 'High Forensic Risk',
};

const CLASSIFICATION_COLORS = {
  NORMAL: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
  HIGH_VOLUME: 'bg-sky-950/80 text-sky-300 border-sky-700/60',
  HIGH_VELOCITY: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
  FAN_OUT: 'bg-orange-950/80 text-orange-300 border-orange-700/60',
  FAN_IN: 'bg-indigo-950/80 text-indigo-300 border-indigo-700/60',
  CIRCULAR: 'bg-pink-950/80 text-pink-300 border-pink-700/60',
  MIXER_LIKE: 'bg-purple-950/80 text-purple-300 border-purple-700/60',
  MULTI_PATTERN: 'bg-fuchsia-950/80 text-fuchsia-300 border-fuchsia-700/60',
  HIGH_RISK: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
};

export default function DashboardView({
  dataMode = 'DEMO',
  providerInfo = null,
  summary,
  datasetInfo,
  alerts,
  onSelectAlert,
  onInvestigateWallet,
  onNavigateTab
}) {
  const [intelSummary, setIntelSummary] = useState(null);

  useEffect(() => {
    let active = true;
    getAnalyticsSummary()
      .then((data) => {
        if (active) setIntelSummary(data);
      })
      .catch((err) => {
        console.error('Failed to load analytics summary:', err);
      });
    return () => {
      active = false;
    };
  }, []);

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

  const highPriorityAlerts = alerts
    .filter(a => a.severity === 'HIGH' || a.severity === 'CRITICAL')
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Hero / Executive Command Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono mb-2">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              <span>Real-Time Forensic Engine Active &bull; Behavioral Intelligence Layer</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Forensic Intelligence Command Center
            </h2>
            <p className="text-slate-400 text-xs max-w-2xl mt-1 leading-relaxed">
              Deterministic graph topology detection and explainable behavioral profiling monitoring blockchain ledger flows. Identifies smurfing splits, circular mule loops, rapid passthrough chains, and multi-pattern convergence.
            </p>
          </div>

          {datasetInfo && (
            <div className="flex items-center gap-4 bg-slate-950/80 border border-slate-800/80 rounded-xl px-4 py-3 text-xs font-mono shrink-0 shadow-lg">
              <div>
                <div className="text-[11px] text-slate-500">Indexed Volume</div>
                <div className="text-indigo-300 font-bold text-sm">{datasetInfo.total_volume_eth?.toFixed(2)} ETH</div>
              </div>
              <div className="w-px h-8 bg-slate-800" />
              <div>
                <div className="text-[11px] text-slate-500">Tracked Wallets</div>
                <div className="text-slate-200 font-bold text-sm">{datasetInfo.total_wallets}</div>
              </div>
              <div className="w-px h-8 bg-slate-800" />
              <div>
                <div className="text-[11px] text-slate-500">Ledger Transfers</div>
                <div className="text-slate-200 font-bold text-sm">{datasetInfo.total_transactions}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Live Mode Telemetry Banner */}
      {dataMode === 'LIVE' && (
        <div className={`bg-slate-900/80 border rounded-xl px-4 py-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono shadow-md ${
          providerInfo?.is_polling === false ? 'border-amber-500/40' : 'border-emerald-500/30 glow-emerald'
        }`}>
          <div className="flex items-center gap-2.5">
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${
              providerInfo?.is_polling === false ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'
            }`} />
            <div>
              <span className={`font-bold uppercase tracking-wider ${
                providerInfo?.is_polling === false ? 'text-amber-300' : 'text-emerald-300'
              }`}>
                {providerInfo?.is_polling === false ? 'Live Ingestion Paused • Monitoring Stopped' : 'Live Ethereum Mainnet Stream Active'}
              </span>
              <span className="text-slate-400 ml-2 hidden sm:inline">
                {providerInfo?.is_polling === false
                  ? 'Automatic background block ingestion is paused. On-chain dataset preserved in SQLite. Click "Resume Live" to continue or use "Poll Block" for manual ingestion.'
                  : (alerts.length === 0
                    ? 'Recent on-chain blocks ingested. Current activity is normal/benign (0 AML anomalies detected).'
                    : `${alerts.length} on-chain suspicious topology patterns detected across live blocks.`)}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-400 shrink-0">
            <span>Buffer: <strong className="text-indigo-300">{datasetInfo?.total_transactions ?? 0}</strong> txs</span>
            <span className="text-slate-700">&bull;</span>
            <span>Sliding Window: <strong className="text-cyan-300">2h</strong></span>
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card rounded-xl p-4.5 space-y-1">
          <div className="text-xs font-mono uppercase text-slate-400 flex items-center justify-between">
            <span>Total Alerts</span>
            <AlertTriangle className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-bold text-white font-mono tracking-tight">
            {summary?.total_alerts || 0}
          </div>
          <p className="text-[11px] text-slate-500 flex items-center gap-1">
            <span>Deduplicated forensic alerts</span>
          </p>
        </div>

        <div className="glass-card rounded-xl p-4.5 space-y-1 hover:border-purple-500/50">
          <div className="text-xs font-mono uppercase text-purple-400 flex items-center justify-between">
            <span>Critical Priority</span>
            <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse glow-critical" />
          </div>
          <div className="text-3xl font-bold text-purple-400 font-mono tracking-tight">
            {intelSummary?.priority_breakdown?.CRITICAL || 0}
          </div>
          <p className="text-[11px] text-slate-500">Immediate investigation targets</p>
        </div>

        <div className="glass-card rounded-xl p-4.5 space-y-1 hover:border-rose-500/50">
          <div className="text-xs font-mono uppercase text-rose-400 flex items-center justify-between">
            <span>Cross-Correlations</span>
            <GitMerge className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-bold text-rose-400 font-mono tracking-tight">
            {intelSummary?.total_correlations || 0}
          </div>
          <p className="text-[11px] text-slate-500">Multi-pattern convergence events</p>
        </div>

        <div className="glass-card rounded-xl p-4.5 space-y-1 hover:border-emerald-500/50">
          <div className="text-xs font-mono uppercase text-emerald-400 flex items-center justify-between">
            <span>Normal Baseline</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 glow-emerald" />
          </div>
          <div className="text-3xl font-bold text-emerald-400 font-mono tracking-tight">
            {intelSummary?.classification_breakdown?.NORMAL || 0}
          </div>
          <p className="text-[11px] text-slate-500">Benign verified retail accounts</p>
        </div>
      </div>

      {/* Phase 8: Behavioral Classification & Network Distribution Row */}
      {intelSummary && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Radar className="w-4 h-4 text-indigo-400" /> Behavioral Classification Distribution
            </h3>
            <span className="text-[10px] font-mono text-slate-500">
              {intelSummary.total_wallets} Wallets Profiled &bull; 9 Deterministic Taxonomies
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {Object.entries(intelSummary.classification_breakdown || {}).map(([type, count]) => {
              const label = CLASSIFICATION_LABELS[type] || type;
              const colorClass = CLASSIFICATION_COLORS[type] || 'bg-slate-800 text-slate-300 border-slate-700';
              return (
                <div
                  key={type}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-2 ${colorClass}`}
                >
                  <span className="font-semibold">{label}</span>
                  <span className="px-1.5 py-0.5 rounded-full bg-black/40 text-[10px] font-bold">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Content Split: Patterns + High-Priority Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detection Patterns Breakdown */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" /> Detection Patterns
            </h3>
            <span className="text-[10px] font-mono text-slate-500">6 Modular Algorithms</span>
          </div>

          <div className="space-y-3">
            {Object.entries(summary?.alerts_by_pattern || {}).map(([pattern, count]) => (
              <div
                key={pattern}
                onClick={() => onNavigateTab('alerts', { pattern })}
                className="bg-slate-950/70 border border-slate-800/80 hover:border-indigo-500/50 rounded-xl p-3 cursor-pointer transition-all hover:bg-slate-900/80 group"
              >
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-200 font-medium group-hover:text-indigo-300 transition-colors">
                    {pattern}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 font-bold">
                    {count}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 leading-snug line-clamp-2">
                  {PATTERN_DESCRIPTIONS[pattern] || 'Forensic pattern heuristic.'}
                </p>
                <div className="w-full bg-slate-800 h-1 rounded-full mt-2.5 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all"
                    style={{ width: `${(count / (summary?.total_alerts || 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Suspicious Activity & High Priority Alerts */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4 lg:col-span-2 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400" /> Critical & High-Priority Threats
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Topology alerts demanding analyst triage and case opening
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigateTab('alerts')}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-mono"
              >
                View All ({alerts.length}) <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-2.5">
              {highPriorityAlerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  onClick={() => onSelectAlert(alert)}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-indigo-500/60 rounded-xl p-3.5 flex items-center justify-between cursor-pointer transition-all hover:bg-slate-900/80"
                >
                  <div className="space-y-1 pr-3">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs font-mono font-bold text-white">{alert.pattern}</span>
                      <span className="text-[10px] font-mono text-slate-500">#{alert.alert_id}</span>
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-1">{alert.explanation}</p>
                    <div className="text-[11px] font-mono text-slate-500 flex items-center gap-2">
                      <span>Origin: {alert.wallets?.[0]?.slice(0, 12)}...</span>
                      <span>&bull;</span>
                      <span>{alert.wallets?.length} wallets involved</span>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-xs font-mono font-bold text-indigo-300">
                      {alert.total_amount ? `${alert.total_amount.toFixed(2)} ETH` : 'N/A'}
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onInvestigateWallet(alert.wallets?.[0]);
                      }}
                      className="mt-1.5 px-2.5 py-1 text-[10px] font-mono rounded bg-slate-900 hover:bg-indigo-600 text-slate-300 hover:text-white border border-slate-800 transition-colors flex items-center gap-1 ml-auto"
                    >
                      Investigate <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Shortcuts Bar */}
          <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <span className="text-slate-500 text-[11px]">Quick Forensic Jump:</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => onInvestigateWallet('0x71C8366420A85E1A0F9b123D377De304559B0975')}
                className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 hover:border-indigo-500 text-slate-300 hover:text-white transition-colors"
              >
                Circular Origin (0x71C8...)
              </button>
              <button
                type="button"
                onClick={() => onInvestigateWallet('0x981C30E3259838B4268e64cCE608aC68fD573c88')}
                className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 hover:border-indigo-500 text-slate-300 hover:text-white transition-colors"
              >
                Burst Sender (0x981C...)
              </button>
              <button
                type="button"
                onClick={() => onInvestigateWallet('0xEE01000000000000000000000000000000000001')}
                className="px-2.5 py-1 rounded bg-slate-950 border border-purple-800/80 hover:border-purple-500 text-purple-300 hover:text-white transition-colors"
              >
                Mixing Ring (0xEE01...)
              </button>
              <button
                type="button"
                onClick={() => onNavigateTab('cases')}
                className="px-2.5 py-1 rounded bg-indigo-950/70 border border-indigo-800/80 text-indigo-300 hover:text-white transition-colors flex items-center gap-1"
              >
                <FolderLock className="w-3 h-3" /> Open Cases
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Phase 8: Cross-Pattern Alert Correlations & Top Priority Intelligence */}
      {intelSummary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Cross-Pattern Correlations Feed */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                  <GitMerge className="w-4 h-4 text-purple-400" /> Cross-Pattern Correlations ({intelSummary.total_correlations})
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Topological convergence where multiple distinct suspicious patterns intersect
                </p>
              </div>
              <span className="text-[10px] font-mono text-purple-400 bg-purple-950/80 border border-purple-800/60 px-2 py-0.5 rounded">
                Multi-Vector Threats
              </span>
            </div>

            <div className="space-y-3">
              {(intelSummary.top_correlations || []).map((corr) => (
                <div
                  key={corr.correlation_id}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-purple-600/50 rounded-xl p-3.5 space-y-2 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      {corr.title}
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${getSeverityBadge(corr.severity)}`}>
                      {corr.severity}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {corr.explanation}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60 text-[11px] font-mono">
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-500">Converging:</span>
                      {corr.converging_patterns.map((p) => (
                        <span key={p} className="px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px]">
                          {p}
                        </span>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={() => onInvestigateWallet(corr.primary_wallet)}
                      className="text-indigo-400 hover:text-white flex items-center gap-1 text-[11px] ml-auto"
                    >
                      Investigate Node <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: High-Priority Behavioral Targets */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                  <Radar className="w-4 h-4 text-rose-400" /> Top Priority Intelligence Targets
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  High forensic risk scores combined with multi-topology behavioral flags
                </p>
              </div>
              <span className="text-[10px] font-mono text-slate-500">
                Ranked by Forensic Impact
              </span>
            </div>

            <div className="space-y-2.5">
              {(intelSummary.top_priority_wallets || []).map((target) => (
                <div
                  key={target.wallet_id}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 rounded-xl p-3 flex items-center justify-between transition-all"
                >
                  <div className="space-y-1 truncate mr-3">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${getSeverityBadge(target.investigation_priority)}`}>
                        {target.investigation_priority}
                      </span>
                      <span className="text-xs font-mono font-bold text-white truncate">
                        {target.wallet_id}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-1 pt-0.5">
                      {target.classifications.slice(0, 3).map((c) => (
                        <span
                          key={c.name}
                          className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-slate-300 border border-slate-800"
                        >
                          {c.label}
                        </span>
                      ))}
                      {target.classifications.length > 3 && (
                        <span className="text-[10px] font-mono text-slate-500">
                          +{target.classifications.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-right shrink-0 space-y-1">
                    <div className="text-xs font-mono font-bold text-rose-400">
                      Score: {target.risk_score}/100
                    </div>
                    <button
                      type="button"
                      onClick={() => onInvestigateWallet(target.wallet_id)}
                      className="px-2.5 py-1 text-[10px] font-mono rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-colors flex items-center gap-1 ml-auto"
                    >
                      Profile <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
