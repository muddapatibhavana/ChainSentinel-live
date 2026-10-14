import { useState, useEffect, useCallback } from 'react';
import {
  Compass,
  ArrowRight,
  ArrowLeftRight,
  AlertTriangle,
  Clock,
  Layers,
  RotateCcw,
  Copy,
  Check,
  CheckCircle2,
  FolderLock,
  Sparkles,
  Search,
  ExternalLink
} from 'lucide-react';
import { traceFlow, createCaseEvidence } from '../api';
import GraphViewer from './GraphViewer';

const PRESET_SCENARIOS = [
  {
    name: 'Rapid Layering Flow (3 Hops)',
    source: '0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66',
    target: '0xDeB94101e4a6eD75d19830Af36691C2817865239',
    depth: 4,
    description: 'Relay chain passthrough across 2 intermediate hops in under 130s.',
  },
  {
    name: 'Circular Flow Loop (4 Hops)',
    source: '0x71C8366420A85E1A0F9b123D377De304559B0975',
    target: '0x71C8366420A85E1A0F9b123D377De304559B0975',
    depth: 5,
    description: 'Closed fund-laundering loop returning ~97% capital back to originator.',
  },
  {
    name: 'Cluster Mixer Transit (3 Hops)',
    source: '0xEE01000000000000000000000000000000000001',
    target: '0xEE05000000000000000000000000000000000005',
    depth: 4,
    description: 'High-density mixing component circulating liquidity internally.',
  },
  {
    name: 'Smurfing Outflow Tree (All Destinations)',
    source: '0x323b5d4c32345ced77393b3530b1eed0f346429d',
    target: '',
    depth: 2,
    description: 'Dispersal hub branching out to multiple destination accounts.',
  },
  {
    name: 'Treasury Cold Vault Transfer (1 Hop)',
    source: '0x1000A892a0d1e38942b0e69F770b09489fDb1010',
    target: '0x2000B901C412356191910A9292837381920B2020',
    depth: 2,
    description: 'Legitimate enterprise treasury disbursement of 250 ETH.',
  },
];

export default function FlowTracerView({
  initialSource = '0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66',
  initialTarget = '0xDeB94101e4a6eD75d19830Af36691C2817865239',
  activeCaseId = null,
  onInvestigateWallet,
  onAnchorEvidence,
}) {
  const [sourceWallet, setSourceWallet] = useState(initialSource);
  const [targetWallet, setTargetWallet] = useState(initialTarget);
  const [maxDepth, setMaxDepth] = useState(4);
  const [loading, setLoading] = useState(false);
  const [traceResult, setTraceResult] = useState(null);
  const [selectedPathIndex, setSelectedPathIndex] = useState(0);
  const [error, setError] = useState(null);
  const [copiedAddress, setCopiedAddress] = useState(null);
  const [anchoredNotification, setAnchoredNotification] = useState(null);

  // Execute Flow Trace
  const handleRunTrace = useCallback(async (src = sourceWallet, tgt = targetWallet, depth = maxDepth) => {
    if (!src.trim()) {
      setError('Please provide a source wallet address.');
      return;
    }

    setLoading(true);
    setError(null);
    setTraceResult(null);
    setSelectedPathIndex(0);

    try {
      const res = await traceFlow(src.trim(), tgt && tgt.trim() ? tgt.trim() : null, depth);
      setTraceResult(res);
      if (res.error) {
        setError(res.error);
      }
    } catch (err) {
      console.error('Flow trace error:', err);
      setError(err.message || 'Failed to execute flow trace');
    } finally {
      setLoading(false);
    }
  }, [sourceWallet, targetWallet, maxDepth]);

  // Run on mount or when initial props change
  useEffect(() => {
    if (initialSource) {
      setSourceWallet(initialSource);
      if (initialTarget !== undefined) setTargetWallet(initialTarget);
      handleRunTrace(initialSource, initialTarget, maxDepth);
    }
  }, [initialSource, initialTarget, maxDepth, handleRunTrace]);

  // Swap Source and Target
  const handleSwapAddresses = () => {
    const temp = sourceWallet;
    setSourceWallet(targetWallet);
    setTargetWallet(temp);
  };

  // Copy address helper
  const handleCopy = (address) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(address);
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  // Apply Preset
  const handleApplyPreset = (preset) => {
    setSourceWallet(preset.source);
    setTargetWallet(preset.target);
    setMaxDepth(preset.depth);
    handleRunTrace(preset.source, preset.target, preset.depth);
  };

  // Anchor flow trace as evidence in active case
  const handleAnchorTraceAsEvidence = async () => {
    if (!activeCaseId || !traceResult?.primary_path) return;
    try {
      const pathData = traceResult.primary_path;
      const payload = {
        evidence_type: 'CUSTOM',
        source_ref: `FLOW-TRACE-${pathData.source.slice(0, 8)}-${pathData.target.slice(0, 8)}`,
        content: {
          trace_type: 'FLOW_RECONSTRUCTION',
          source: pathData.source,
          target: pathData.target,
          hops: pathData.hops,
          total_value_eth: pathData.total_value,
          duration_seconds: pathData.duration_seconds,
          suspicion_score: pathData.path_suspicion_score,
          suspicion_level: pathData.path_suspicion_level,
          wallets: pathData.wallets,
          transactions: pathData.hops_detail.map(h => ({
            tx_id: h.tx_id,
            from: h.from_wallet,
            to: h.to_wallet,
            amount: h.amount,
            timestamp: h.timestamp,
            category: h.category,
          })),
        },
        metadata: {
          analyst_note: `Reconstructed ${pathData.hops}-hop flow path with suspicion score ${pathData.path_suspicion_score}.`,
        },
      };

      await createCaseEvidence(activeCaseId, payload);
      setAnchoredNotification('Flow trace cryptographically anchored as case evidence!');
      if (onAnchorEvidence) onAnchorEvidence();
      setTimeout(() => setAnchoredNotification(null), 3500);
    } catch (err) {
      console.error('Failed to anchor evidence:', err);
      setError(`Failed to anchor evidence: ${err.message}`);
    }
  };

  // Determine active displayed path (primary or alternative)
  const allPaths = traceResult?.primary_path
    ? [traceResult.primary_path, ...(traceResult.alternative_paths || [])]
    : [];
  const currentPath = allPaths[selectedPathIndex] || traceResult?.primary_path;

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="border border-slate-800 rounded-2xl bg-gradient-to-r from-slate-900/90 via-slate-950 to-indigo-950/40 p-6 backdrop-blur shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="p-1.5 bg-indigo-500/20 rounded-lg text-indigo-400 border border-indigo-500/30">
                <Compass className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-indigo-400 font-bold">
                Topological Path Reconstruction
              </span>
              {activeCaseId && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-400 text-[10px] font-mono flex items-center gap-1 font-bold">
                  <FolderLock className="w-3 h-3" /> Case #{activeCaseId} Active
                </span>
              )}
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Flow Tracer &amp; Route Analysis
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl font-mono">
              Reconstruct deterministic directed transaction pathways across intermediate hops, inspect transit velocity, and assess path suspicion levels.
            </p>
          </div>

          {/* Preset scenarios dropdown */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Presets:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {PRESET_SCENARIOS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleApplyPreset(preset)}
                  className="px-2.5 py-1 bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg text-[11px] font-mono text-slate-300 hover:text-white transition-colors"
                >
                  {preset.name.split(' (')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Control / Query Bar */}
      <div className="border border-slate-800 rounded-xl bg-slate-950/80 p-5 space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-end">
          {/* Source Wallet */}
          <div className="lg:col-span-5 space-y-1.5">
            <label className="text-[11px] font-mono font-medium text-slate-400 flex items-center justify-between">
              <span>Source Origin Wallet <span className="text-rose-400">*</span></span>
              {sourceWallet && (
                <button
                  type="button"
                  onClick={() => handleCopy(sourceWallet)}
                  className="text-slate-500 hover:text-slate-300 flex items-center gap-1"
                >
                  {copiedAddress === sourceWallet ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedAddress === sourceWallet ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </label>
            <div className="relative">
              <input
                type="text"
                value={sourceWallet}
                onChange={(e) => setSourceWallet(e.target.value)}
                placeholder="0x... (Origin Address)"
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:outline-none transition-colors"
              />
            </div>
          </div>

          {/* Swap Button */}
          <div className="lg:col-span-1 flex items-center justify-center pb-1">
            <button
              type="button"
              onClick={handleSwapAddresses}
              title="Swap Source and Destination"
              className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white rounded-xl transition-colors"
            >
              <ArrowLeftRight className="w-4 h-4" />
            </button>
          </div>

          {/* Target Wallet */}
          <div className="lg:col-span-4 space-y-1.5">
            <label className="text-[11px] font-mono font-medium text-slate-400 flex items-center justify-between">
              <span>Target Destination <span className="text-slate-500">(Optional)</span></span>
              {targetWallet && (
                <button
                  type="button"
                  onClick={() => handleCopy(targetWallet)}
                  className="text-slate-500 hover:text-slate-300 flex items-center gap-1"
                >
                  {copiedAddress === targetWallet ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedAddress === targetWallet ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </label>
            <div className="relative">
              <input
                type="text"
                value={targetWallet}
                onChange={(e) => setTargetWallet(e.target.value)}
                placeholder="Leave blank to discover all downstream flows..."
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:outline-none transition-colors"
              />
            </div>
          </div>

          {/* Max Depth */}
          <div className="lg:col-span-1 space-y-1.5">
            <label className="text-[11px] font-mono font-medium text-slate-400">Max Hops</label>
            <select
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2.5 text-xs text-white font-mono focus:outline-none transition-colors"
            >
              <option value={1}>1 Hop</option>
              <option value={2}>2 Hops</option>
              <option value={3}>3 Hops</option>
              <option value={4}>4 Hops</option>
              <option value={5}>5 Hops</option>
              <option value={6}>6 Hops</option>
            </select>
          </div>

          {/* Submit Button */}
          <div className="lg:col-span-1">
            <button
              type="button"
              onClick={() => handleRunTrace()}
              disabled={loading || !sourceWallet.trim()}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-all shadow-md"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" /> Trace
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Notifications Bar */}
      {anchoredNotification && (
        <div className="p-3 bg-emerald-950/70 border border-emerald-800 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{anchoredNotification}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/70 border border-rose-800 rounded-xl text-xs font-mono text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {traceResult && (
        <div className="space-y-6">
          {/* Path Status & High-level Metrics Strip */}
          <div className="border border-slate-800 rounded-xl bg-slate-900/60 p-5 backdrop-blur">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${
                      traceResult.path_found
                        ? 'bg-emerald-950/80 border-emerald-700/60 text-emerald-400'
                        : 'bg-rose-950/80 border-rose-700/60 text-rose-400'
                    }`}
                  >
                    {traceResult.path_found ? (traceResult.is_cycle ? 'Circular Loop Reconstructed' : 'Directed Path Reconstructed') : 'No Flow Path Found'}
                  </span>
                  {currentPath && (
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${
                        currentPath.path_suspicion_level === 'CRITICAL'
                          ? 'bg-rose-950/80 border-rose-700/60 text-rose-300'
                          : currentPath.path_suspicion_level === 'HIGH'
                          ? 'bg-amber-950/80 border-amber-700/60 text-amber-300'
                          : currentPath.path_suspicion_level === 'MEDIUM'
                          ? 'bg-blue-950/80 border-blue-700/60 text-blue-300'
                          : 'bg-slate-900 border-slate-700 text-slate-300'
                      }`}
                    >
                      Suspicion: {currentPath.path_suspicion_level} ({currentPath.path_suspicion_score}/100)
                    </span>
                  )}
                </div>
                <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                  <span className="text-emerald-400">{traceResult.source?.slice(0, 10)}...</span>
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                  <span className={traceResult.target ? 'text-purple-400' : 'text-slate-400'}>
                    {traceResult.target ? `${traceResult.target.slice(0, 10)}...` : 'Downstream Network Discovery'}
                  </span>
                </h3>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                {activeCaseId && currentPath && (
                  <button
                    type="button"
                    onClick={handleAnchorTraceAsEvidence}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    <FolderLock className="w-3.5 h-3.5" /> Anchor to Case #{activeCaseId}
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => {
                    setTraceResult(null);
                    setError(null);
                  }}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-mono transition-colors flex items-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Clear Trace
                </button>
              </div>
            </div>

            {/* Metrics Grid */}
            {currentPath && (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mt-4">
                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-slate-400">Total Hops</div>
                  <div className="text-xl font-bold font-mono text-white mt-0.5">{currentPath.hops}</div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                    {currentPath.wallets.length} Wallets
                  </div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-slate-400">Total Transferred</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
                    {currentPath.total_value.toFixed(2)} ETH
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">Along Reconstructed Path</div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-slate-400">Transit Duration</div>
                  <div className="text-xl font-bold font-mono text-white mt-0.5">
                    {currentPath.duration_seconds < 60
                      ? `${Math.round(currentPath.duration_seconds)}s`
                      : `${Math.round(currentPath.duration_seconds / 60)}m`}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                    {currentPath.temporal_consistent ? 'Chronological order' : 'Out-of-order timing'}
                  </div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-slate-400">Suspicious Wallets</div>
                  <div className="text-xl font-bold font-mono text-rose-400 mt-0.5">
                    {currentPath.suspicious_wallets.length}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">Score &ge; 40 or Flagged</div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-slate-400">Patterns Detected</div>
                  <div className="text-xl font-bold font-mono text-indigo-400 mt-0.5">
                    {currentPath.patterns_encountered.length}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">Forensic Signatures</div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-slate-400">Suspicion Tier</div>
                  <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">
                    {currentPath.path_suspicion_score}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">Scale: 0 – 100</div>
                </div>
              </div>
            )}
          </div>

          {/* Alternative Paths Tab Bar (if multiple paths exist) */}
          {allPaths.length > 1 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <span className="text-xs font-mono text-slate-400 whitespace-nowrap">Discovered Paths ({allPaths.length}):</span>
              {allPaths.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedPathIndex(idx)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                    selectedPathIndex === idx
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  <span>Route #{idx + 1}</span>
                  <span className="text-[10px] opacity-75">({p.hops} hops &bull; {p.total_value.toFixed(1)} ETH)</span>
                </button>
              ))}
            </div>
          )}

          {/* Cytoscape Graph Canvas with Path Highlighting */}
          {traceResult.graph && traceResult.graph.nodes?.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  Visual Route Topology &amp; Neighborhood (Interactive Cytoscape Canvas)
                </span>
                <span className="text-[11px] text-slate-500">
                  {traceResult.graph.nodes.length} nodes &bull; {traceResult.graph.edges.length} edges
                </span>
              </div>
              <GraphViewer
                graphData={traceResult.graph}
                height="460px"
                onNodeClick={(walletId) => {
                  if (onInvestigateWallet) onInvestigateWallet(walletId);
                }}
              />
            </div>
          )}

          {/* Hop-by-Hop Chronological Movement Ledger */}
          {currentPath && currentPath.hops_detail?.length > 0 && (
            <div className="border border-slate-800 rounded-xl bg-slate-950/70 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                  <Clock className="w-4 h-4 text-sky-400" /> Chronological Hop-by-Hop Movement Timeline
                </h4>
                <span className="text-xs font-mono text-slate-400">
                  {currentPath.hops_detail.length} Transaction Hop(s)
                </span>
              </div>

              <div className="space-y-3">
                {currentPath.hops_detail.map((hop, index) => (
                  <div
                    key={index}
                    className="border border-slate-800/80 hover:border-slate-700 bg-slate-900/60 rounded-xl p-4 transition-colors space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-sky-950 text-sky-400 border border-sky-700/60 flex items-center justify-center text-xs font-mono font-bold">
                          {hop.hop_index}
                        </span>
                        <span className="text-xs font-mono font-bold text-white">
                          Hop {hop.hop_index} of {currentPath.hops}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300">
                          {hop.category}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          {new Date(hop.timestamp).toLocaleTimeString()} ({new Date(hop.timestamp).toLocaleDateString()})
                        </span>
                        <span className="text-emerald-400 font-bold">
                          {hop.amount.toFixed(4)} ETH
                        </span>
                      </div>
                    </div>

                    {/* Flow routing cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                      {/* From */}
                      <div className="bg-slate-950/70 border border-slate-800/60 rounded-lg p-2.5 space-y-1">
                        <div className="text-[10px] text-slate-500 flex items-center justify-between">
                          <span>Sender (Hop Origin)</span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                              hop.from_risk.level === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300'
                                : hop.from_risk.level === 'HIGH'
                                ? 'bg-amber-950 text-amber-300'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            Risk: {hop.from_risk.level} ({hop.from_risk.score})
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-1 text-slate-200">
                          <span className="truncate">{hop.from_wallet}</span>
                          <button
                            type="button"
                            onClick={() => onInvestigateWallet && onInvestigateWallet(hop.from_wallet)}
                            title="Investigate Wallet"
                            className="p-1 hover:text-indigo-400 transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* To */}
                      <div className="bg-slate-950/70 border border-slate-800/60 rounded-lg p-2.5 space-y-1">
                        <div className="text-[10px] text-slate-500 flex items-center justify-between">
                          <span>Recipient (Next Hop)</span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                              hop.to_risk.level === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300'
                                : hop.to_risk.level === 'HIGH'
                                ? 'bg-amber-950 text-amber-300'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            Risk: {hop.to_risk.level} ({hop.to_risk.score})
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-1 text-slate-200">
                          <span className="truncate">{hop.to_wallet}</span>
                          <button
                            type="button"
                            onClick={() => onInvestigateWallet && onInvestigateWallet(hop.to_wallet)}
                            title="Investigate Wallet"
                            className="p-1 hover:text-indigo-400 transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Hop tx details and description */}
                    <div className="text-[11px] font-mono text-slate-400 flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1 border-t border-slate-800/40">
                      <div className="truncate flex items-center gap-1.5">
                        <span className="text-slate-500">Tx Hash:</span>
                        <span className="text-indigo-300 truncate">{hop.tx_id}</span>
                      </div>
                      {hop.description && (
                        <div className="text-slate-400 italic text-right">
                          {hop.description}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Discovered Destinations Table (When target was left blank) */}
          {traceResult.destinations && traceResult.destinations.length > 0 && (
            <div className="border border-slate-800 rounded-xl bg-slate-950/70 p-5 space-y-4">
              <h4 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Compass className="w-4 h-4 text-emerald-400" /> Discovered Downstream Flow Destinations ({traceResult.destinations.length})
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Destination Wallet</th>
                      <th className="py-2.5 px-3">Hops</th>
                      <th className="py-2.5 px-3">Total Value</th>
                      <th className="py-2.5 px-3">Suspicion</th>
                      <th className="py-2.5 px-3">Patterns</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {traceResult.destinations.map((dest, i) => (
                      <tr key={i} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-white truncate max-w-xs">
                          {dest.destination_wallet}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 font-bold">
                          {dest.hops}
                        </td>
                        <td className="py-2.5 px-3 text-emerald-400 font-bold">
                          {dest.total_value.toFixed(2)} ETH
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              dest.path_suspicion_level === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300'
                                : dest.path_suspicion_level === 'HIGH'
                                ? 'bg-amber-950 text-amber-300'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {dest.path_suspicion_level} ({dest.path_suspicion_score})
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">
                          {dest.patterns?.join(', ') || 'Normal'}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            type="button"
                            onClick={() => {
                              setTargetWallet(dest.destination_wallet);
                              handleRunTrace(sourceWallet, dest.destination_wallet, maxDepth);
                            }}
                            className="px-2.5 py-1 bg-indigo-600/80 hover:bg-indigo-600 text-white rounded text-[11px] font-mono transition-colors"
                          >
                            Trace Route
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
