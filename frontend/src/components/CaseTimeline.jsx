import { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  FolderOpen,
  ShieldCheck,
  Hash,
  Lock,
  FileText,
  AlertTriangle,
  RefreshCw,
  ArrowUpDown
} from 'lucide-react';
import { getCaseTimeline } from '../api';

export default function CaseTimeline({ caseId }) {
  const [events, setEvents] = useState([]);
  const [order, setOrder] = useState('asc');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTimeline = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getCaseTimeline(caseId, order);
      setEvents(res.events || []);
    } catch (err) {
      console.error('Failed to load timeline:', err);
      setError(`Failed to retrieve case timeline: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [caseId, order]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const getEventIcon = (type) => {
    switch (type) {
      case 'CASE_CREATED':
        return <FolderOpen className="w-3.5 h-3.5 text-indigo-400" />;
      case 'EVIDENCE_ANCHORED':
        return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
      case 'INTEGRITY_VERIFIED':
        return <Hash className="w-3.5 h-3.5 text-cyan-400" />;
      case 'STATUS_CHANGED':
        return <Lock className="w-3.5 h-3.5 text-amber-400" />;
      case 'NOTES_UPDATED':
        return <FileText className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'CASE_CREATED':
        return 'border-indigo-500/60 bg-indigo-950/40';
      case 'EVIDENCE_ANCHORED':
        return 'border-emerald-500/60 bg-emerald-950/40';
      case 'INTEGRITY_VERIFIED':
        return 'border-cyan-500/60 bg-cyan-950/40';
      case 'STATUS_CHANGED':
        return 'border-amber-500/60 bg-amber-950/40';
      case 'NOTES_UPDATED':
        return 'border-purple-500/60 bg-purple-950/40';
      default:
        return 'border-slate-700 bg-slate-900';
    }
  };

  return (
    <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <h4 className="text-sm font-bold text-white font-mono">Investigation Chronology</h4>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            {events.length} events
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setOrder(order === 'asc' ? 'desc' : 'asc')}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] font-mono flex items-center gap-1 transition-colors"
          >
            <ArrowUpDown className="w-3 h-3" />
            {order === 'asc' ? 'Oldest First' : 'Newest First'}
          </button>

          <button
            type="button"
            onClick={fetchTimeline}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-800 rounded hover:bg-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300 font-mono flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Timeline Stream */}
      {events.length === 0 ? (
        <p className="text-xs font-mono text-slate-500 py-6 text-center">
          No audit timeline events recorded for this case yet.
        </p>
      ) : (
        <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-px before:bg-slate-800 font-mono text-xs">
          {events.map((evt) => (
            <div key={evt.event_id} className="relative group">
              {/* Dot marker */}
              <div
                className={`absolute -left-6 top-1 p-1 rounded-full border shadow-sm ${getEventColor(
                  evt.event_type
                )}`}
              >
                {getEventIcon(evt.event_type)}
              </div>

              {/* Event card */}
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 space-y-1 hover:border-slate-700 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-xs">{evt.title}</span>
                    <span className="text-[10px] text-slate-500">[{evt.actor || 'Analyst'}]</span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {new Date(evt.timestamp).toLocaleString()}
                  </span>
                </div>

                <p className="text-[11px] text-slate-300 font-sans leading-relaxed pt-0.5">
                  {evt.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
