import { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  ArrowDownLeft,
  ArrowUpRight,
  Copy,
  Check,
  FolderPlus,
  RefreshCw,
  Search,
  AlertTriangle,
  Layers,
  Compass,
  Radar,
  GitMerge,
  ShieldAlert,
  TrendingUp,
  TrendingDown,
  Clock,
  Users
} from 'lucide-react';
import {
  getWalletRisk,
  getWalletTransactions,
  getWalletGraph,
  getWalletIntelligence
} from '../api';
import GraphViewer from './GraphViewer';

const PRESET_WALLETS = [
  { label: 'Circular Origin A', address: '0x71C8366420A85E1A0F9b123D377De304559B0975', desc: 'Mule routing loop' },
  { label: 'Burst Sender', address: '0x981C30E3259838B4268e64cCE608aC68fD573c88', desc: '10 rapid txs in 2m' },
  { label: 'Fan-In Collector', address: '0x9999f8e404F75eB9Ac49A1B3a0279c78D548F567', desc: 'Smurfing aggregation' },
  { label: 'Cluster Ring Node', address: '0xEE01000000000000000000000000000000000001', desc: 'Mixing ring node' },
];

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

export default function WalletInvestigationView({
  initialWallet = '0x71C8366420A85E1A0F9b123D377De304559B0975',
  onCreateCaseForWallet,
  onTraceFlow
}) {
  const [walletInput, setWalletInput] = useState(initialWallet);
  const [activeWallet, setActiveWallet] = useState(initialWallet);
  const [depth, setDepth] = useState(2);

  const [risk, setRisk] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [intelligence, setIntelligence] = useState(null);

  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  const fetchWalletProfile = useCallback(async (addr, hopDepth = depth) => {
    if (!addr || !addr.trim()) return;
    const cleanAddr = addr.trim();
    setLoading(true);
    setError(null);
    try {
      const [riskRes, txsRes, graphRes, intelRes] = await Promise.all([
        getWalletRisk(cleanAddr),
        getWalletTransactions(cleanAddr, 50),
        getWalletGraph(cleanAddr, hopDepth),
        getWalletIntelligence(cleanAddr).catch(() => null),
      ]);
      setRisk(riskRes);
      setTransactions(txsRes.transactions || []);
      setGraphData(graphRes);
      setIntelligence(intelRes);
      setActiveWallet(cleanAddr);
      setWalletInput(cleanAddr);
    } catch (err) {
      console.error('Wallet profile fetch failed:', err);
      setError(`Failed to retrieve wallet dossier: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [depth]);

  useEffect(() => {
    fetchWalletProfile(initialWallet, depth);
  }, [initialWallet, fetchWalletProfile, depth]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (walletInput.trim()) {
      fetchWalletProfile(walletInput.trim(), depth);
    }
  };

  const handleCopy = () => {
    if (activeWallet) {
      navigator.clipboard.writeText(activeWallet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

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

  const behavior = intelligence?.behavior_profile;

  return (
    <div className="space-y-6">
      {/* Wallet Search & Quick Presets Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4.5 space-y-3.5 shadow-lg">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={walletInput}
              onChange={(e) => setWalletInput(e.target.value)}
              placeholder="Enter target wallet address (e.g. 0x71C83664...)"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-mono font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Investigate
            </button>
          </div>
        </form>

        {/* Preset quick links */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80 text-xs font-mono">
          <span className="text-slate-500 text-[11px] mr-1">Demo Scenarios:</span>
          {PRESET_WALLETS.map((preset) => (
            <button
              key={preset.address}
              type="button"
              onClick={() => fetchWalletProfile(preset.address, depth)}
              className={`px-2.5 py-1 rounded-lg border text-[11px] transition-all ${
                activeWallet === preset.address
                  ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                  : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white hover:border-slate-700'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => fetchWalletProfile(activeWallet, depth)}
            className="underline hover:text-white ml-3"
          >
            Retry
          </button>
        </div>
      )}

      {/* Target Wallet Dossier Card */}
      {risk && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                  Target Account
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${getSeverityBadge(risk.risk_level)}`}>
                  {risk.risk_level} RISK
                </span>
                {intelligence?.investigation_priority && (
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${getSeverityBadge(intelligence.investigation_priority)}`}>
                    {intelligence.investigation_priority} PRIORITY
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 pt-0.5">
                <h2 className="text-sm md:text-base font-bold font-mono text-white truncate max-w-xl">
                  {activeWallet}
                </h2>
                <button
                  type="button"
                  onClick={handleCopy}
                  title="Copy address"
                  className="p-1.5 text-slate-400 hover:text-white bg-slate-800/60 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans max-w-3xl pt-1">
                {intelligence?.explanation || risk.explanation}
              </p>
            </div>

            {/* Score & Case creation button */}
            <div className="flex items-center gap-4 shrink-0">
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-3.5 text-center min-w-[120px]">
                <span className="text-[10px] font-mono uppercase text-slate-500 block">Risk Score</span>
                <span className="text-3xl font-bold font-mono text-white">
                  {risk.risk_score}
                  <span className="text-xs text-slate-500 font-normal">/100</span>
                </span>
                <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                  {risk.alert_count} alert{risk.alert_count === 1 ? '' : 's'}
                </div>
              </div>

              {onTraceFlow && (
                <button
                  type="button"
                  onClick={() => onTraceFlow(activeWallet)}
                  className="py-3 px-3.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sky-300 hover:text-white rounded-xl text-xs font-mono font-medium transition-all flex items-center gap-1.5"
                  title="Trace fund flows from this wallet"
                >
                  <Compass className="w-4 h-4 text-sky-400" /> Trace Flow
                </button>
              )}

              <button
                type="button"
                onClick={() => onCreateCaseForWallet(activeWallet, risk)}
                className="py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-mono font-medium shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2"
              >
                <FolderPlus className="w-4 h-4" /> Open Case Dossier
              </button>
            </div>
          </div>

          {/* Implicated topologies */}
          {risk.pattern_types?.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/60">
              <span className="text-[11px] font-mono text-slate-500">Implicated Topologies:</span>
              {risk.pattern_types.map((p) => (
                <span
                  key={p}
                  className="text-[10px] font-mono bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 px-2 py-0.5 rounded font-bold"
                >
                  {p}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Phase 8: Behavioral Profiling & Forensics Intelligence Card */}
      {behavior && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Radar className="w-4 h-4 text-indigo-400" /> Behavioral Forensics &amp; Flow Dynamics
            </h3>
            <span className="text-[10px] font-mono text-slate-500">
              Deterministic Profiling &bull; Behavioral Intelligence
            </span>
          </div>

          {/* Classifications Tags */}
          <div className="space-y-2">
            <div className="text-[11px] font-mono text-slate-400">Assigned Behavioral Classifications:</div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {behavior.classifications.map((c) => (
                <div
                  key={c.name}
                  className={`p-3 rounded-xl border text-xs font-mono space-y-1 ${
                    CLASSIFICATION_COLORS[c.name] || 'bg-slate-950 border-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold">
                    <span>{c.label}</span>
                    <span className="text-[10px] uppercase opacity-75">{c.severity}</span>
                  </div>
                  <p className="text-[11px] font-sans opacity-90 leading-tight">
                    {c.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Flow Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" /> Inbound Flow
              </span>
              <div className="text-base font-bold text-emerald-400">
                {behavior.inbound_volume?.toFixed(2)} ETH
              </div>
              <div className="text-[10px] text-slate-400">{behavior.inbound_tx_count} transfers</div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                <TrendingDown className="w-3 h-3 text-rose-400" /> Outbound Flow
              </span>
              <div className="text-base font-bold text-rose-400">
                {behavior.outbound_volume?.toFixed(2)} ETH
              </div>
              <div className="text-[10px] text-slate-400">{behavior.outbound_tx_count} transfers</div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase">Net Flow</span>
              <div className={`text-base font-bold ${behavior.net_flow >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {behavior.net_flow >= 0 ? '+' : ''}{behavior.net_flow?.toFixed(2)} ETH
              </div>
              <div className="text-[10px] text-slate-400">
                {behavior.net_flow >= 0 ? 'Net Accumulator' : 'Net Distributor'}
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                <Users className="w-3 h-3 text-indigo-400" /> Counterparties
              </span>
              <div className="text-base font-bold text-white">
                {behavior.unique_counterparties_count}
              </div>
              <div className="text-[10px] text-slate-400">
                {behavior.unique_inbound_counterparties_count} in / {behavior.unique_outbound_counterparties_count} out
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                <Clock className="w-3 h-3 text-amber-400" /> Frequency
              </span>
              <div className="text-base font-bold text-amber-400">
                {behavior.tx_frequency_per_hour?.toFixed(1)} /hr
              </div>
              <div className="text-[10px] text-slate-400">
                Active: {(behavior.active_time_span_seconds / 60)?.toFixed(0)}m
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 font-mono space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase">Avg / Peak Tx</span>
              <div className="text-base font-bold text-indigo-300">
                {behavior.avg_tx_value?.toFixed(1)} ETH
              </div>
              <div className="text-[10px] text-slate-400">
                Peak: {behavior.largest_tx_value?.toFixed(1)} ETH
              </div>
            </div>
          </div>

          {/* Observable Signals */}
          {behavior.signals?.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
              <span className="text-[10px] font-mono uppercase text-slate-500">
                Observable Forensic Signals:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                {behavior.signals.map((sig, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 text-slate-300 flex items-center gap-2"
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span className="truncate">{sig}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cross-Pattern Correlations for this wallet */}
          {intelligence?.correlations?.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-purple-400 font-bold">
                <GitMerge className="w-3.5 h-3.5 text-purple-400" />
                Cross-Pattern Convergence Events ({intelligence.correlations.length})
              </div>
              <div className="space-y-2">
                {intelligence.correlations.map((corr) => (
                  <div
                    key={corr.correlation_id}
                    className="bg-purple-950/20 border border-purple-800/50 rounded-xl p-3 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between font-mono">
                      <span className="font-bold text-purple-300">{corr.title}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded border font-bold ${getSeverityBadge(corr.severity)}`}>
                        {corr.severity}
                      </span>
                    </div>
                    <p className="text-slate-300 font-sans text-xs leading-relaxed">
                      {corr.explanation}
                    </p>
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
                      <span>Converging Patterns:</span>
                      {corr.converging_patterns.map((p) => (
                        <span key={p} className="px-1.5 py-0.2 rounded bg-purple-900/60 text-purple-200 border border-purple-700">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Workspace Split: Interactive Graph & Transaction Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Cytoscape Relationship Graph */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" /> Interactive Relationship Graph
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Cytoscape visual topology centered on {activeWallet.slice(0, 10)}...
              </p>
            </div>

            {/* Depth Selector */}
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <span className="text-slate-500 text-[11px]">Hops:</span>
              {[1, 2, 3].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => {
                    setDepth(d);
                    fetchWalletProfile(activeWallet, d);
                  }}
                  className={`px-2 py-0.5 rounded text-[11px] border transition-colors ${
                    depth === d
                      ? 'bg-indigo-600 text-white border-indigo-500'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 min-h-[420px]">
            <GraphViewer
              graphData={graphData}
              height="440px"
              onNodeClick={(clickedId) => {
                fetchWalletProfile(clickedId, depth);
              }}
            />
          </div>
        </div>

        {/* Right: Inbound & Outbound Transactions */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" /> Transaction Ledger Activity
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {transactions.length} transfer{transactions.length === 1 ? '' : 's'} recorded involving this address
              </p>
            </div>
            <span className="text-[11px] font-mono text-slate-500">FastAPI /transactions</span>
          </div>

          {/* Transactions List */}
          <div className="space-y-2 overflow-y-auto max-h-[440px] pr-1">
            {transactions.length === 0 ? (
              <div className="p-12 text-center text-slate-500 font-mono text-xs border border-dashed border-slate-800 rounded-xl">
                No transactions indexed for this account.
              </div>
            ) : (
              transactions.map((tx) => {
                const isOutbound = tx.from_wallet.toLowerCase() === activeWallet.toLowerCase();
                const counterparty = isOutbound ? tx.to_wallet : tx.from_wallet;

                return (
                  <div
                    key={tx.tx_id}
                    className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex items-center justify-between text-xs font-mono hover:border-slate-700 transition-colors"
                  >
                    <div className="space-y-1 truncate mr-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded font-bold flex items-center gap-1 ${
                            isOutbound
                              ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
                              : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                          }`}
                        >
                          {isOutbound ? (
                            <>
                              <ArrowUpRight className="w-3 h-3" /> OUT
                            </>
                          ) : (
                            <>
                              <ArrowDownLeft className="w-3 h-3" /> IN
                            </>
                          )}
                        </span>
                        <span className="text-slate-400 text-[10px]">#{tx.tx_id.slice(0, 10)}...</span>
                        <span className="text-[10px] text-slate-500 px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800">
                          {tx.category_label}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-300 truncate">
                        {isOutbound ? 'To: ' : 'From: '}
                        <button
                          type="button"
                          onClick={() => fetchWalletProfile(counterparty, depth)}
                          className="hover:underline hover:text-indigo-400 text-slate-300 text-left"
                        >
                          {counterparty}
                        </button>
                      </div>

                      {tx.description && (
                        <p className="text-[10px] text-slate-400 font-sans truncate">{tx.description}</p>
                      )}
                    </div>

                    <div className="text-right shrink-0">
                      <div className={`font-bold font-mono text-sm ${isOutbound ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {isOutbound ? '-' : '+'}{tx.amount?.toFixed(2)} ETH
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        {tx.gas_fee ? `${tx.gas_fee} fee` : '0 gas'}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
