import { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Activity,
  AlertTriangle,
  FolderLock,
  Wallet,
  RefreshCw,
  Plus,
  Compass,
  Database,
  Radio,
  DownloadCloud,
  FileDown,
  Pause,
  Play
} from 'lucide-react';
import {
  getHealth,
  getDatasetInfo,
  getDetectionSummary,
  getAlerts,
  getInvestigations,
  createInvestigation,
  getProviderStatus,
  setProviderMode,
  fetchLiveBlock,
  exportLiveTransactionsCsv,
  pauseLiveMonitoring,
  resumeLiveMonitoring
} from './api';

import DashboardView from './components/DashboardView';
import AlertsView from './components/AlertsView';
import WalletInvestigationView from './components/WalletInvestigationView';
import InvestigationsView from './components/InvestigationsView';
import FlowTracerView from './components/FlowTracerView';
import AlertDetailModal from './components/AlertDetailModal';
import CreateCaseModal from './components/CreateCaseModal';

export default function App() {
  // Navigation State
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'alerts' | 'investigate' | 'flow' | 'cases'

  // Backend Health
  const [backendHealth, setBackendHealth] = useState({
    status: 'checking',
    message: 'Connecting to ChainSentinel API...'
  });

  // Global Core Data
  const [summary, setSummary] = useState(null);
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [investigationsCount, setInvestigationsCount] = useState(0);

  // Cross-View Focus State
  const [investigationTargetWallet, setInvestigationTargetWallet] = useState('0x71C8366420A85E1A0F9b123D377De304559B0975');
  const [flowSourceWallet, setFlowSourceWallet] = useState('0x5a180f959C5b4E44a2bAA16bF379EfAc7d057a66');
  const [flowTargetWallet, setFlowTargetWallet] = useState('0xDeB94101e4a6eD75d19830Af36691C2817865239');
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [activePatternFilter, setActivePatternFilter] = useState('ALL');

  // Modals State
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [isCreateCaseOpen, setIsCreateCaseOpen] = useState(false);
  const [createCaseDefaults, setCreateCaseDefaults] = useState({
    targetWallet: '',
    alertId: '',
    relatedWallets: []
  });

  // Transaction Provider State (Demo vs Live)
  const [dataMode, setDataMode] = useState('DEMO'); // 'DEMO' | 'LIVE'
  const [providerInfo, setProviderInfo] = useState(null);
  const [switchingMode, setSwitchingMode] = useState(false);
  const [monitoringLoading, setMonitoringLoading] = useState(false);
  const [pollingBlock, setPollingBlock] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [modeNotification, setModeNotification] = useState(null);

  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initial Data Fetch
  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const health = await getHealth();
      setBackendHealth({ status: 'connected', message: health.message || 'Engine Operational' });

      const [sumRes, infoRes, alertsRes, casesRes, provRes] = await Promise.all([
        getDetectionSummary(),
        getDatasetInfo().catch(() => null),
        getAlerts({ limit: 100 }),
        getInvestigations().catch(() => ({ investigations: [] })),
        getProviderStatus().catch(() => null),
      ]);

      setSummary(sumRes);
      setDatasetInfo(infoRes);
      setAlerts(alertsRes.alerts || []);
      setInvestigationsCount(casesRes.investigations?.length || 0);
      if (provRes) {
        const resolved = provRes.active_mode || provRes.mode || 'DEMO';
        setDataMode(resolved);
        setProviderInfo(provRes);
      }
    } catch (err) {
      console.error('API initialization error:', err);
      setBackendHealth({ status: 'disconnected', message: 'Backend Offline' });
      setError('Cannot connect to ChainSentinel backend at http://127.0.0.1:8000. Ensure the FastAPI service is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Live Mode Periodic Telemetry Polling (Every 6 seconds when LIVE)
  useEffect(() => {
    if (dataMode !== 'LIVE') return;
    let isMounted = true;

    const pollTimer = setInterval(async () => {
      try {
        const status = await getProviderStatus();
        if (!isMounted) return;
        setProviderInfo(status);

        // If transaction count changed, reload analytics and alerts
        if (status.active_transaction_count !== summary?.total_transactions) {
          const [sumRes, infoRes, alertsRes] = await Promise.all([
            getDetectionSummary(),
            getDatasetInfo().catch(() => null),
            getAlerts({ limit: 100 }),
          ]);
          if (isMounted) {
            setSummary(sumRes);
            setDatasetInfo(infoRes);
            setAlerts(alertsRes.alerts || []);
          }
        }
      } catch (pollErr) {
        console.warn('Live telemetry poll error:', pollErr);
      }
    }, 6000);

    return () => {
      isMounted = false;
      clearInterval(pollTimer);
    };
  }, [dataMode, summary?.total_transactions]);

  // Mode Switching Handler
  const handleToggleMode = async (targetMode) => {
    if (switchingMode) return;
    const currentMode = providerInfo?.active_mode || providerInfo?.mode || dataMode;
    if (targetMode === currentMode && targetMode === dataMode) return;

    setSwitchingMode(true);
    try {
      const res = await setProviderMode(targetMode);
      const resolvedMode = res.active_mode || res.mode || targetMode;
      setDataMode(resolvedMode);
      setProviderInfo(res);
      setModeNotification(
        resolvedMode === 'LIVE'
          ? `Switched to LIVE mode • Polling Ethereum Mainnet`
          : `Switched to DEMO mode • Benchmark Dataset Active (${res.active_transaction_count ?? 70} txs)`
      );
      setTimeout(() => setModeNotification(null), 4000);

      // Refresh data in-place without triggering full screen unmount
      const [sumRes, infoRes, alertsRes] = await Promise.all([
        getDetectionSummary(),
        getDatasetInfo().catch(() => null),
        getAlerts({ limit: 100 }),
      ]);
      setSummary(sumRes);
      setDatasetInfo(infoRes);
      setAlerts(alertsRes.alerts || []);
    } catch (err) {
      console.error('Failed to change mode:', err);
      setModeNotification(`Failed to switch data mode: ${err.message || 'API error'}`);
      setTimeout(() => setModeNotification(null), 4000);
    } finally {
      setSwitchingMode(false);
    }
  };

  // Live Monitoring Pause/Resume Handler
  const handleToggleMonitoring = async () => {
    if (monitoringLoading) return;
    setMonitoringLoading(true);
    try {
      const isCurrentlyPolling = providerInfo?.is_polling ?? true;
      let res;
      if (isCurrentlyPolling) {
        res = await pauseLiveMonitoring();
        setModeNotification('Live block monitoring paused • Dataset preserved in SQLite');
      } else {
        res = await resumeLiveMonitoring();
        setModeNotification('Live block monitoring resumed • Polling Ethereum Mainnet');
      }
      setProviderInfo(res);
      setTimeout(() => setModeNotification(null), 4000);
    } catch (err) {
      console.error('Failed to toggle live monitoring:', err);
      setModeNotification(`Monitoring control error: ${err.message || 'API error'}`);
      setTimeout(() => setModeNotification(null), 4000);
    } finally {
      setMonitoringLoading(false);
    }
  };

  // Live Block Polling Handler
  const handlePollLiveBlock = async () => {
    if (pollingBlock) return;
    setPollingBlock(true);
    try {
      const res = await fetchLiveBlock(15);
      const blk = res.latest_block_number || 'latest';
      const ingested = res.fetched_count ?? res.ingested_count ?? 0;
      setModeNotification(`Polled block #${blk}: ${ingested} txs ingested (${res.total_persisted_transactions ?? res.total_live_transactions ?? 0} total)`);
      setTimeout(() => setModeNotification(null), 5000);

      // Refresh in place
      const [sumRes, infoRes, alertsRes, provRes] = await Promise.all([
        getDetectionSummary(),
        getDatasetInfo().catch(() => null),
        getAlerts({ limit: 100 }),
        getProviderStatus().catch(() => null),
      ]);
      setSummary(sumRes);
      setDatasetInfo(infoRes);
      setAlerts(alertsRes.alerts || []);
      if (provRes) setProviderInfo(provRes);
    } catch (err) {
      console.error('Failed to poll live block:', err);
      setModeNotification('Live block poll failed: check RPC connectivity');
      setTimeout(() => setModeNotification(null), 4000);
    } finally {
      setPollingBlock(false);
    }
  };

  // Export CSV Handler
  const handleExportCsv = async () => {
    if (exportingCsv) return;
    setExportingCsv(true);
    try {
      await exportLiveTransactionsCsv();
      setModeNotification('Exported live transactions to CSV file');
      setTimeout(() => setModeNotification(null), 4000);
    } catch (err) {
      console.error('Failed to export CSV:', err);
      setModeNotification('Failed to export live transactions CSV');
      setTimeout(() => setModeNotification(null), 4000);
    } finally {
      setExportingCsv(false);
    }
  };

  // Navigate to Wallet Deep Dive
  const handleInvestigateWallet = (walletAddress) => {
    if (walletAddress) {
      setInvestigationTargetWallet(walletAddress);
      setActiveTab('investigate');
    }
  };

  // Navigate to Flow Tracer
  const handleTraceFlow = (source, target = '') => {
    if (source) setFlowSourceWallet(source);
    setFlowTargetWallet(target || '');
    setActiveTab('flow');
  };

  // Navigate to Alerts with Pattern Filter
  const handleNavigateToAlerts = (tab, params = {}) => {
    if (params.pattern) {
      setActivePatternFilter(params.pattern);
    } else {
      setActivePatternFilter('ALL');
    }
    setActiveTab(tab);
  };

  // Open Create Case Modal
  const handleOpenCreateCaseModal = (targetWallet = '', context = {}) => {
    setCreateCaseDefaults({
      targetWallet: targetWallet || investigationTargetWallet,
      alertId: context.alert_id || '',
      relatedWallets: context.related_wallets || context.wallets?.slice(1) || []
    });
    setIsCreateCaseOpen(true);
  };

  // Handle Case Created
  const handleCaseCreated = async (payload) => {
    const created = await createInvestigation(payload);
    setActiveCaseId(created.case_id);
    setInvestigationsCount(prev => prev + 1);
    setActiveTab('cases');
    return created;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Cybersecurity Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-cyan-500/10 border border-indigo-500/30 rounded-xl text-indigo-400 shadow-inner glow-indigo">
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider text-white flex items-center gap-2">
              CHAIN<span className="text-indigo-400">SENTINEL</span>
              <span className="text-[10px] font-mono uppercase bg-indigo-950/90 text-indigo-300 px-2.5 py-0.5 rounded-full border border-indigo-500/50 font-bold tracking-wide">
                Investigation Command Center
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Blockchain Forensic Intelligence &amp; Cryptographic Audit Cockpit</p>
          </div>
        </div>

        {/* Center Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800/80 font-mono">
          <button
            type="button"
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 font-medium ${
              activeTab === 'dashboard'
                ? 'bg-indigo-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> Dashboard
          </button>

          <button
            type="button"
            onClick={() => {
              setActivePatternFilter('ALL');
              setActiveTab('alerts');
            }}
            className={`px-3 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 font-medium ${
              activeTab === 'alerts'
                ? 'bg-indigo-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" /> Alerts ({alerts.length})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('investigate')}
            className={`px-3 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 font-medium ${
              activeTab === 'investigate'
                ? 'bg-indigo-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Wallet className="w-3.5 h-3.5" /> Wallet Deep Dive
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('flow')}
            className={`px-3 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 font-medium ${
              activeTab === 'flow'
                ? 'bg-indigo-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Compass className="w-3.5 h-3.5" /> Flow Tracer
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('cases')}
            className={`px-3 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 font-medium ${
              activeTab === 'cases'
                ? 'bg-indigo-600 text-white shadow-sm font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <FolderLock className="w-3.5 h-3.5" /> Cases ({investigationsCount})
          </button>
        </nav>

        {/* Right Status & Refresh */}
        <div className="flex items-center gap-3">
          {/* Data Mode Switcher (Demo vs Live) */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-xl border border-slate-800 bg-slate-950/90 font-mono text-xs shadow-inner">
            <div className="flex items-center gap-1 bg-slate-900/90 p-0.5 rounded-lg border border-slate-800">
              <button
                type="button"
                onClick={() => handleToggleMode('DEMO')}
                disabled={switchingMode}
                title="Synthetic Benchmark Dataset (70 curated transactions, 21 alerts)"
                className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all flex items-center gap-1 ${
                  dataMode === 'DEMO'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30 ring-1 ring-indigo-400 font-bold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                } disabled:opacity-50`}
              >
                <Database className="w-3 h-3" />
                DEMO
              </button>

              <button
                type="button"
                onClick={() => handleToggleMode('LIVE')}
                disabled={switchingMode}
                title="Live Blockchain Ingestion & Public RPC Feed"
                className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all flex items-center gap-1 ${
                  dataMode === 'LIVE'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/30 ring-1 ring-emerald-400 font-bold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                } disabled:opacity-50`}
              >
                <Radio className={`w-3 h-3 ${dataMode === 'LIVE' && (providerInfo?.is_polling !== false) ? 'animate-pulse text-emerald-200' : ''}`} />
                LIVE
              </button>
            </div>

            {dataMode === 'LIVE' && (
              <>
                {/* Background Monitoring Control: End Live vs Resume Live */}
                {providerInfo?.is_polling !== false ? (
                  <button
                    type="button"
                    onClick={handleToggleMonitoring}
                    disabled={monitoringLoading}
                    title="Stop automatic background live monitoring while keeping website and dataset running"
                    className="px-2.5 py-1 bg-amber-950/80 hover:bg-amber-900 text-amber-300 rounded-md text-[10px] font-bold flex items-center gap-1 transition-colors border border-amber-600/50 shadow-sm disabled:opacity-50"
                  >
                    <Pause className="w-3 h-3 text-amber-400" />
                    <span>End Live</span>
                  </button>
                ) : (
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 bg-amber-950/70 border border-amber-600/60 rounded text-[10px] text-amber-300 font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                      Monitoring Paused
                    </span>
                    <button
                      type="button"
                      onClick={handleToggleMonitoring}
                      disabled={monitoringLoading}
                      title="Resume automatic background live monitoring"
                      className="px-2.5 py-1 bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 rounded-md text-[10px] font-bold flex items-center gap-1 transition-colors border border-emerald-600/50 shadow-sm disabled:opacity-50"
                    >
                      <Play className="w-3 h-3 text-emerald-400" />
                      <span>Resume Live</span>
                    </button>
                  </div>
                )}

                {providerInfo?.latest_block_number && (
                  <span className="px-2 py-0.5 bg-slate-900 border border-slate-700/80 rounded text-[10px] text-cyan-300 font-bold hidden md:inline" title="Latest processed Ethereum block">
                    #{providerInfo.latest_block_number}
                  </span>
                )}

                <button
                  type="button"
                  onClick={handlePollLiveBlock}
                  disabled={pollingBlock}
                  title="Poll Latest Ethereum Block on Demand"
                  className="px-2 py-1 bg-slate-850 hover:bg-slate-750 text-cyan-300 rounded-md text-[10px] flex items-center gap-1 transition-colors border border-cyan-800/40 disabled:opacity-50"
                >
                  <DownloadCloud className={`w-3 h-3 ${pollingBlock ? 'animate-bounce' : ''}`} />
                  <span className="hidden sm:inline">Poll Block</span>
                </button>

                <button
                  type="button"
                  onClick={handleExportCsv}
                  disabled={exportingCsv}
                  title="Export all collected live transactions to Excel-compatible CSV"
                  className="px-2 py-1 bg-slate-850 hover:bg-slate-750 text-indigo-300 rounded-md text-[10px] flex items-center gap-1 transition-colors border border-indigo-800/40 disabled:opacity-50"
                >
                  <FileDown className="w-3 h-3" />
                  <span className="hidden sm:inline">Export CSV</span>
                </button>

                {providerInfo?.last_error && (
                  <span
                    className="text-[10px] text-amber-400 bg-amber-950/60 border border-amber-800/50 px-1.5 py-0.5 rounded cursor-help max-w-[130px] truncate hidden lg:inline"
                    title={`RPC Status: ${providerInfo.last_error}`}
                  >
                    ⚠ RPC Warning
                  </span>
                )}
              </>
            )}

            <span className="text-[10px] text-slate-400 px-1 hidden sm:inline" title="Loaded active transactions in analysis window">
              {providerInfo?.active_window_transactions ?? (datasetInfo?.total_transactions ?? '—')} txs
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-800 bg-slate-950 text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                backendHealth.status === 'connected'
                  ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50 animate-pulse'
                  : backendHealth.status === 'checking'
                  ? 'bg-amber-400'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-300 text-[11px]">{backendHealth.message}</span>
          </div>

          <button
            type="button"
            onClick={() => handleOpenCreateCaseModal()}
            className="hidden lg:flex px-3 py-1.5 bg-indigo-600/90 hover:bg-indigo-600 text-white rounded-xl text-xs font-mono font-medium items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" /> Open Case
          </button>

          <button
            type="button"
            onClick={loadInitialData}
            title="Refresh API Data"
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-400 hover:text-white hover:bg-slate-900 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Mode Switch Notification Banner */}
      {modeNotification && (
        <div className="bg-indigo-950/80 border-b border-indigo-700/60 px-6 py-2 flex items-center justify-between text-xs text-indigo-200 font-mono">
          <div className="flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            <span>{modeNotification}</span>
          </div>
          <button
            type="button"
            onClick={() => setModeNotification(null)}
            className="text-slate-400 hover:text-white text-[11px]"
          >
            &times; Dismiss
          </button>
        </div>
      )}

      {/* Error Notification Bar */}
      {error && (
        <div className="bg-rose-950/70 border-b border-rose-800 px-6 py-2.5 flex items-center justify-between text-xs text-rose-200 font-mono">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={loadInitialData}
            className="underline hover:text-white font-medium ml-4 shrink-0"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Forensic Investigation Workflow Pipeline Bar */}
      <div className="bg-slate-900/40 border-b border-slate-800/80 px-6 py-2.5 flex items-center justify-between text-xs font-mono overflow-x-auto">
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Forensic Lifecycle</span>
          <span className="text-slate-700">&bull;</span>
        </div>

        <div className="flex items-center gap-2 md:gap-3 shrink-0">
          {[
            { id: 'alerts', label: '1. Alert Triage', count: alerts.length },
            { id: 'investigate', label: '2. Wallet Deep Dive', count: null },
            { id: 'flow', label: '3. Flow Tracer', count: null },
            { id: 'cases', label: '4. Case Dossier & Cryptographic Audit', count: investigationsCount },
          ].map((stage, idx, arr) => (
            <div key={stage.id} className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveTab(stage.id)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 ${
                  activeTab === stage.id
                    ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500/50 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                }`}
              >
                <span>{stage.label}</span>
                {stage.count !== null && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300">
                    {stage.count}
                  </span>
                )}
              </button>
              {idx < arr.length - 1 && (
                <span className="text-slate-600 text-[10px]">&rarr;</span>
              )}
            </div>
          ))}
        </div>

        <div className="hidden xl:flex items-center gap-2 text-[11px] text-slate-400 shrink-0">
          <span className="text-slate-500">Active Focus:</span>
          <span className="text-indigo-300 font-bold truncate max-w-[140px]" title={investigationTargetWallet}>
            {investigationTargetWallet ? `${investigationTargetWallet.slice(0, 8)}...${investigationTargetWallet.slice(-4)}` : 'None'}
          </span>
        </div>
      </div>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 space-y-6">
        {/* Full Loading Skeleton */}
        {loading && !summary ? (
          <div className="py-28 flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
            <p className="text-sm font-mono text-slate-400">
              Synchronizing with ChainSentinel detection models & synthetic ledger...
            </p>
          </div>
        ) : (
          <>
            {/* VIEW 1: DASHBOARD (Phase 4C) */}
            {activeTab === 'dashboard' && (
              <DashboardView
                dataMode={dataMode}
                providerInfo={providerInfo}
                summary={summary}
                datasetInfo={datasetInfo}
                alerts={alerts}
                onSelectAlert={(al) => setSelectedAlert(al)}
                onInvestigateWallet={handleInvestigateWallet}
                onNavigateTab={handleNavigateToAlerts}
                onRefresh={loadInitialData}
                loading={loading}
              />
            )}

            {/* VIEW 2: ALERTS EXPLORER (Phase 4C) */}
            {activeTab === 'alerts' && (
              <AlertsView
                alerts={alerts}
                initialPatternFilter={activePatternFilter}
                onSelectAlert={(al) => setSelectedAlert(al)}
                onInvestigateWallet={handleInvestigateWallet}
                onTraceFlow={handleTraceFlow}
              />
            )}

            {/* VIEW 3: WALLET INVESTIGATION DEEP DIVE (Phase 4D) */}
            {activeTab === 'investigate' && (
              <WalletInvestigationView
                initialWallet={investigationTargetWallet}
                onCreateCaseForWallet={(wallet, riskProfile) => {
                  handleOpenCreateCaseModal(wallet, {
                    wallets: [wallet],
                    alert_id: riskProfile?.alerts?.[0]?.alert_id || ''
                  });
                }}
                onTraceFlow={handleTraceFlow}
              />
            )}

            {/* VIEW 4: FLOW TRACER & PATH RECONSTRUCTION (Phase 7) */}
            {activeTab === 'flow' && (
              <FlowTracerView
                initialSource={flowSourceWallet}
                initialTarget={flowTargetWallet}
                activeCaseId={activeCaseId}
                onInvestigateWallet={handleInvestigateWallet}
                onAnchorEvidence={loadInitialData}
              />
            )}

            {/* VIEW 5: INVESTIGATION CASES & DOSSIERS (Phases 4 & 6) */}
            {activeTab === 'cases' && (
              <InvestigationsView
                initialCaseId={activeCaseId}
                onOpenCreateCaseModal={() => handleOpenCreateCaseModal()}
                onInvestigateWallet={handleInvestigateWallet}
                onTraceFlow={handleTraceFlow}
              />
            )}
          </>
        )}
      </main>

      {/* Modals */}
      <AlertDetailModal
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onInvestigateWallet={handleInvestigateWallet}
        onViewGraph={(wallet) => {
          setInvestigationTargetWallet(wallet);
          setActiveTab('investigate');
        }}
        onTraceFlow={handleTraceFlow}
        onCreateCaseFromAlert={(al) => {
          handleOpenCreateCaseModal(al.wallets?.[0] || '', {
            alert_id: al.alert_id,
            related_wallets: al.wallets?.slice(1) || []
          });
        }}
      />

      <CreateCaseModal
        isOpen={isCreateCaseOpen}
        onClose={() => setIsCreateCaseOpen(false)}
        initialTargetWallet={createCaseDefaults.targetWallet}
        initialAlertId={createCaseDefaults.alertId}
        initialRelatedWallets={createCaseDefaults.relatedWallets}
        onCaseCreated={handleCaseCreated}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 px-6 py-4 text-center text-xs text-slate-500 font-mono">
        ChainSentinel &bull; Blockchain Forensic Intelligence &bull; Investigation Command Center
      </footer>
    </div>
  );
}
