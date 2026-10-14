import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

export default function GraphViewer({ graphData, onNodeClick, height = '450px' }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !graphData || !graphData.nodes) return;

    // Destroy any existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    const hasPathHighlight = (graphData.nodes || []).some(n => n.data?.is_path);

    const elements = [
      ...graphData.nodes.map(n => ({
        group: 'nodes',
        data: {
          id: n.data.id,
          label: n.data.label || `${n.data.id.slice(0, 8)}...`,
          flagged: Boolean(n.data.flagged),
          is_focus: Boolean(n.data.is_focus),
          is_source: Boolean(n.data.is_source),
          is_target: Boolean(n.data.is_target),
          is_path: Boolean(n.data.is_path),
          hop_index: n.data.hop_index ?? -1,
        },
      })),
      ...(graphData.edges || []).map(e => ({
        group: 'edges',
        data: {
          id: e.data.id,
          source: e.data.source,
          target: e.data.target,
          label: e.data.label || `${e.data.amount} ETH`,
          category: e.data.category || '',
          is_path: Boolean(e.data.is_path),
          hop_number: e.data.hop_number ?? 0,
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#334155',
            'label': 'data(label)',
            'color': '#cbd5e1',
            'font-size': '10px',
            'font-family': 'monospace',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'width': hasPathHighlight ? 26 : 30,
            'height': hasPathHighlight ? 26 : 30,
            'border-width': 1.5,
            'border-color': '#475569',
            'opacity': hasPathHighlight ? 0.35 : 1.0,
          },
        },
        {
          selector: 'node[?flagged]',
          style: {
            'background-color': '#e11d48',
            'border-color': '#fb7185',
            'border-width': 2.5,
            'color': '#fecdd3',
            'font-weight': 'bold',
          },
        },
        {
          selector: 'node[?is_focus]',
          style: {
            'background-color': '#0284c7',
            'border-color': '#38bdf8',
            'border-width': 3.5,
            'width': 40,
            'height': 40,
            'color': '#ffffff',
            'font-weight': 'bold',
            'opacity': 1.0,
            'z-index': 80,
          },
        },
        {
          selector: 'node[?is_path]',
          style: {
            'background-color': '#0284c7',
            'border-color': '#38bdf8',
            'border-width': 3,
            'width': 36,
            'height': 36,
            'color': '#ffffff',
            'font-weight': 'bold',
            'opacity': 1.0,
            'z-index': 50,
          },
        },
        {
          selector: 'node[?is_path][?flagged]',
          style: {
            'background-color': '#e11d48',
            'border-color': '#fb7185',
            'border-width': 3.5,
            'width': 38,
            'height': 38,
            'color': '#fecdd3',
            'font-weight': 'bold',
            'opacity': 1.0,
            'z-index': 60,
          },
        },
        {
          selector: 'node[?is_source]',
          style: {
            'background-color': '#059669',
            'border-color': '#34d399',
            'border-width': 4,
            'width': 42,
            'height': 42,
            'color': '#a7f3d0',
            'font-weight': 'bold',
            'opacity': 1.0,
            'z-index': 100,
          },
        },
        {
          selector: 'node[?is_target]',
          style: {
            'background-color': '#7c3aed',
            'border-color': '#c084fc',
            'border-width': 4,
            'width': 42,
            'height': 42,
            'color': '#ddd6fe',
            'font-weight': 'bold',
            'opacity': 1.0,
            'z-index': 100,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'font-family': 'monospace',
            'color': '#94a3b8',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'arrow-scale': 0.8,
            'opacity': hasPathHighlight ? 0.2 : 0.8,
          },
        },
        {
          selector: 'edge[?is_path]',
          style: {
            'width': 3.5,
            'line-color': '#38bdf8',
            'target-arrow-color': '#38bdf8',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.1,
            'curve-style': 'bezier',
            'color': '#7dd3fc',
            'font-size': '9px',
            'font-weight': 'bold',
            'opacity': 1.0,
            'z-index': 99,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#f59e0b',
            'border-width': 3.5,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        randomize: false,
        componentSpacing: 60,
        nodeRepulsion: 450000,
        edgeElasticity: 100,
        padding: 30,
      },
    });

    if (onNodeClick) {
      cy.on('tap', 'node', (evt) => {
        const nodeData = evt.target.data();
        cy.animate({
          center: { eles: evt.target },
          duration: 350,
          easing: 'ease-out-cubic',
        });
        onNodeClick(nodeData.id);
      });
    }

    cyRef.current = cy;

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [graphData, onNodeClick]);

  const handleZoomIn = () => {
    if (!cyRef.current) return;
    cyRef.current.animate({
      zoom: cyRef.current.zoom() * 1.3,
      duration: 250,
      easing: 'ease-out-cubic',
    });
  };

  const handleZoomOut = () => {
    if (!cyRef.current) return;
    cyRef.current.animate({
      zoom: cyRef.current.zoom() * 0.75,
      duration: 250,
      easing: 'ease-out-cubic',
    });
  };

  const handleReset = () => {
    if (!cyRef.current) return;
    cyRef.current.animate({
      fit: { padding: 30 },
      duration: 400,
      easing: 'ease-out-cubic',
    });
  };

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div
        className="flex items-center justify-center border border-slate-800 rounded-xl bg-slate-950/60 text-slate-500 text-sm font-mono"
        style={{ height }}
      >
        No graph nodes available for this selection.
      </div>
    );
  }

  const isPathView = Boolean(graphData.nodes?.some(n => n.data?.is_path));

  return (
    <div className="relative border border-slate-800 rounded-xl overflow-hidden bg-slate-950/80">
      {/* Controls Overlay */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-slate-900/90 border border-slate-800/80 rounded-lg p-1 backdrop-blur shadow-md">
        <button
          type="button"
          onClick={handleZoomIn}
          title="Zoom In"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={handleZoomOut}
          title="Zoom Out"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={handleReset}
          title="Reset View"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Graph Legend */}
      <div className="absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-3 bg-slate-900/90 border border-slate-800/80 rounded-lg px-2.5 py-1 text-[11px] font-mono text-slate-400 backdrop-blur">
        {isPathView ? (
          <>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-emerald-300" />
              <span className="text-emerald-300">Origin / Source</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600 border border-purple-400" />
              <span className="text-purple-300">Target / Destination</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 border border-sky-300" />
              <span className="text-sky-300">Flow Path Hop</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 border border-rose-400" />
              <span className="text-rose-300">Suspicious on Path</span>
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 border border-sky-300" />
              <span>Focus Wallet</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 border border-rose-400" />
              <span>Flagged Suspicious</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-600 border border-slate-400" />
              <span>Counterparty</span>
            </div>
          </>
        )}
      </div>

      <div ref={containerRef} style={{ width: '100%', height }} />
    </div>
  );
}
