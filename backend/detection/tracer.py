"""
ChainSentinel - Flow Tracer & Path Reconstruction Engine
Phase 7 - Directed flow tracing, path reconstruction, and suspicion contextualization.

This module inspects the transaction multigraph to answer:
"How did funds move between these wallets, and what suspicious path connects them?"

Core capabilities:
  - Directed simple path search between source and target with bounded traversal depth
  - Reconstructs specific chronological transactions along each hop
  - Calculates transferred volume, transit duration, and temporal consistency
  - Reuses existing DetectionEngine alerts and risk scoring (zero artificial ML/guessing)
  - Detects self-contained cycles when source == target
  - Discovers all downstream outflow branches when target is not specified
  - Generates Cytoscape.js compatible graph payloads with visual path highlighting flags
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx

from .models import Transaction, Alert, WalletRiskAssessment, Severity


@dataclass
class FlowHop:
    """A single hop along a reconstructed flow path."""
    hop_index: int
    from_wallet: str
    to_wallet: str
    tx_id: str
    amount: float
    timestamp: datetime
    category: str
    gas_fee: float
    description: str
    from_risk_score: float = 0.0
    from_risk_level: str = Severity.LOW
    to_risk_score: float = 0.0
    to_risk_level: str = Severity.LOW
    alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "hop_index": self.hop_index,
            "from_wallet": self.from_wallet,
            "to_wallet": self.to_wallet,
            "tx_id": self.tx_id,
            "amount": round(self.amount, 4),
            "timestamp": self.timestamp.isoformat(),
            "category": self.category,
            "gas_fee": self.gas_fee,
            "description": self.description,
            "from_risk": {
                "score": self.from_risk_score,
                "level": self.from_risk_level,
            },
            "to_risk": {
                "score": self.to_risk_score,
                "level": self.to_risk_level,
            },
            "alerts": self.alerts,
        }


@dataclass
class FlowPath:
    """A reconstructed flow path containing wallets, hops, and metrics."""
    path_id: str
    source: str
    target: str
    hops: int
    wallets: List[str]
    intermediate_wallets: List[str]
    flow_hops: List[FlowHop]
    total_value: float
    first_timestamp: Optional[datetime]
    last_timestamp: Optional[datetime]
    duration_seconds: float
    temporal_consistent: bool
    suspicious_wallets: List[str]
    patterns_encountered: List[str]
    path_suspicion_score: float
    path_suspicion_level: str
    explanation: str

    def to_dict(self) -> Dict:
        return {
            "path_id": self.path_id,
            "source": self.source,
            "target": self.target,
            "hops": self.hops,
            "wallets": self.wallets,
            "intermediate_wallets": self.intermediate_wallets,
            "hops_detail": [h.to_dict() for h in self.flow_hops],
            "total_value": round(self.total_value, 4),
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "duration_seconds": round(self.duration_seconds, 1),
            "temporal_consistent": self.temporal_consistent,
            "suspicious_wallets": self.suspicious_wallets,
            "patterns_encountered": self.patterns_encountered,
            "path_suspicion_score": self.path_suspicion_score,
            "path_suspicion_level": self.path_suspicion_level,
            "explanation": self.explanation,
        }


class FlowTracer:
    """
    High-performance flow-tracing engine for blockchain transaction graphs.
    Reuses existing NetworkX infrastructure and DetectionEngine risk profiles.
    """

    def __init__(self, transactions: List[Transaction], engine=None) -> None:
        self._transactions: List[Transaction] = transactions
        self._engine = engine

        # Build directed multigraph and edge lookup
        self._graph = nx.MultiDiGraph()
        self._edge_txs: Dict[Tuple[str, str], List[Transaction]] = {}
        self._known_wallets: Set[str] = set()

        for tx in self._transactions:
            self._known_wallets.add(tx.from_wallet)
            self._known_wallets.add(tx.to_wallet)
            self._graph.add_edge(tx.from_wallet, tx.to_wallet, tx_id=tx.tx_id, amount=tx.amount)
            key = (tx.from_wallet, tx.to_wallet)
            self._edge_txs.setdefault(key, []).append(tx)

        # Sort each edge list chronologically
        for key in self._edge_txs:
            self._edge_txs[key].sort(key=lambda t: t.timestamp)

    @property
    def known_wallets(self) -> Set[str]:
        return self._known_wallets

    def trace_flow(
        self,
        source: str,
        target: Optional[str] = None,
        max_depth: int = 4,
    ) -> Dict:
        """
        Execute flow tracing from source wallet to target (or discover all downstream flows).
        Bounded depth between 1 and 6 hops to prevent unbounded traversal.
        """
        # Parameter validation
        depth = max(1, min(max_depth, 6))

        if source not in self._known_wallets:
            return {
                "source": source,
                "target": target,
                "max_depth": depth,
                "path_found": False,
                "error": f"Source wallet '{source}' not found in transaction ledger.",
                "primary_path": None,
                "alternative_paths": [],
                "graph": {"nodes": [], "edges": []},
            }

        # Case 1: Target is unspecified -> discover downstream outflow tree
        if target is None or target == "":
            return self._trace_outflow_discovery(source, depth)

        if target not in self._known_wallets:
            return {
                "source": source,
                "target": target,
                "max_depth": depth,
                "path_found": False,
                "error": f"Target wallet '{target}' not found in transaction ledger.",
                "primary_path": None,
                "alternative_paths": [],
                "graph": {"nodes": [], "edges": []},
            }

        # Case 2: Source == Target -> check for circular flow loops or 0-hop self-path
        if source == target:
            return self._trace_cycle_or_self(source, depth)

        # Case 3: Source != Target -> simple directed path search
        return self._trace_source_to_target(source, target, depth)

    # ------------------------------------------------------------------
    # Internal: Source to Target Search
    # ------------------------------------------------------------------

    def _trace_source_to_target(self, source: str, target: str, max_depth: int) -> Dict:
        raw_paths: List[List[str]] = []
        try:
            # Simple paths generator with cutoff
            paths_gen = nx.all_simple_paths(self._graph, source, target, cutoff=max_depth)
            for p in paths_gen:
                raw_paths.append(p)
                if len(raw_paths) >= 20:  # Bound exploration
                    break
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            raw_paths = []

        if not raw_paths:
            # Build 1-hop neighborhood of source and target for graph context
            subgraph_data = self._build_path_graph([], source, target)
            return {
                "source": source,
                "target": target,
                "max_depth": max_depth,
                "path_found": False,
                "explanation": (
                    f"No directed transaction flow found from {source[:10]}... "
                    f"to {target[:10]}... within {max_depth} hops."
                ),
                "primary_path": None,
                "alternative_paths": [],
                "graph": subgraph_data,
            }

        # Reconstruct all candidate FlowPath objects
        reconstructed_paths: List[FlowPath] = []
        for idx, wallet_seq in enumerate(raw_paths):
            flow_path = self._reconstruct_path(f"path_{idx+1}", wallet_seq)
            if flow_path:
                reconstructed_paths.append(flow_path)

        if not reconstructed_paths:
            return {
                "source": source,
                "target": target,
                "max_depth": max_depth,
                "path_found": False,
                "explanation": "Paths were topologically present but contained no valid matching transactions.",
                "primary_path": None,
                "alternative_paths": [],
                "graph": {"nodes": [], "edges": []},
            }

        # Sort paths by: 1) suspicion score descending, 2) hops ascending, 3) total value descending
        reconstructed_paths.sort(
            key=lambda p: (-p.path_suspicion_score, p.hops, -p.total_value)
        )

        primary = reconstructed_paths[0]
        alternatives = reconstructed_paths[1:]

        # Build Cytoscape graph payload centered on the primary path
        graph_payload = self._build_path_graph(primary.wallets, source, target, primary)

        return {
            "source": source,
            "target": target,
            "max_depth": max_depth,
            "path_found": True,
            "primary_path": primary.to_dict(),
            "alternative_paths": [p.to_dict() for p in alternatives],
            "total_paths_found": len(reconstructed_paths),
            "graph": graph_payload,
            "explanation": primary.explanation,
        }

    # ------------------------------------------------------------------
    # Internal: Source == Target (Cycle / Loop)
    # ------------------------------------------------------------------

    def _trace_cycle_or_self(self, source: str, max_depth: int) -> Dict:
        """Find if a cycle loops back to source, or return 0-hop self path."""
        cycle_paths: List[List[str]] = []
        for successor in self._graph.successors(source):
            if max_depth > 1:
                try:
                    for p in nx.all_simple_paths(self._graph, successor, source, cutoff=max_depth - 1):
                        cycle_paths.append([source] + p)
                        if len(cycle_paths) >= 10:
                            break
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

        if cycle_paths:
            reconstructed: List[FlowPath] = []
            for idx, c in enumerate(cycle_paths):
                path_obj = self._reconstruct_path(f"cycle_{idx+1}", c)
                if path_obj:
                    reconstructed.append(path_obj)

            if reconstructed:
                reconstructed.sort(key=lambda p: (-p.path_suspicion_score, p.hops))
                primary = reconstructed[0]
                primary.explanation = (
                    f"Identified closed circular flow of {primary.hops} hops looping "
                    f"back to origin wallet ({primary.total_value:.2f} ETH total transit)."
                )
                graph_payload = self._build_path_graph(primary.wallets, source, source, primary)
                return {
                    "source": source,
                    "target": source,
                    "max_depth": max_depth,
                    "path_found": True,
                    "is_cycle": True,
                    "primary_path": primary.to_dict(),
                    "alternative_paths": [p.to_dict() for p in reconstructed[1:]],
                    "total_paths_found": len(reconstructed),
                    "graph": graph_payload,
                    "explanation": primary.explanation,
                }

        # No cycle exists; return valid 0-hop identity path
        risk_profile = self._get_wallet_risk(source)
        nodes = [{
            "data": {
                "id": source,
                "label": source[:8] + "...",
                "is_source": True,
                "is_target": True,
                "is_path": True,
                "hop_index": 0,
                "flagged": risk_profile["score"] >= 40,
                "risk_score": risk_profile["score"],
                "risk_level": risk_profile["level"],
            }
        }]
        return {
            "source": source,
            "target": source,
            "max_depth": max_depth,
            "path_found": True,
            "is_cycle": False,
            "primary_path": {
                "path_id": "self_0",
                "source": source,
                "target": source,
                "hops": 0,
                "wallets": [source],
                "intermediate_wallets": [],
                "hops_detail": [],
                "total_value": 0.0,
                "first_timestamp": None,
                "last_timestamp": None,
                "duration_seconds": 0.0,
                "temporal_consistent": True,
                "suspicious_wallets": [source] if risk_profile["score"] >= 40 else [],
                "patterns_encountered": risk_profile.get("pattern_types", []),
                "path_suspicion_score": risk_profile["score"],
                "path_suspicion_level": risk_profile["level"],
                "explanation": "Source and target are the same address; no closed directed transaction cycle exists.",
            },
            "alternative_paths": [],
            "graph": {"nodes": nodes, "edges": []},
            "explanation": "Source and destination are the identical wallet with no cyclic flows.",
        }

    # ------------------------------------------------------------------
    # Internal: Outflow Discovery (Target Unspecified)
    # ------------------------------------------------------------------

    def _trace_outflow_discovery(self, source: str, max_depth: int) -> Dict:
        """Discover downstream reachable destinations and flow branches from source."""
        # Find all reachable nodes within max_depth via BFS
        reachable_destinations: List[Dict] = []
        discovered_paths: List[FlowPath] = []
        visited: Set[str] = {source}

        # Collect candidate targets
        for target_candidate in self._known_wallets:
            if target_candidate == source:
                continue
            try:
                if nx.has_path(self._graph, source, target_candidate):
                    # Get shortest path
                    sp = nx.shortest_path(self._graph, source, target_candidate)
                    if len(sp) - 1 <= max_depth:
                        path_obj = self._reconstruct_path(f"branch_{target_candidate[:8]}", sp)
                        if path_obj:
                            discovered_paths.append(path_obj)
                            visited.update(sp)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        # Sort discovered paths by suspicion score descending, then value descending
        discovered_paths.sort(key=lambda p: (-p.path_suspicion_score, -p.total_value, p.hops))

        # Build composite graph of all discovered branches
        all_path_wallets = list(visited)
        composite_graph = self._build_path_graph(all_path_wallets, source, None)

        destinations_summary = [
            {
                "destination_wallet": p.target,
                "hops": p.hops,
                "total_value": p.total_value,
                "path_suspicion_score": p.path_suspicion_score,
                "path_suspicion_level": p.path_suspicion_level,
                "suspicious_wallets_count": len(p.suspicious_wallets),
                "patterns": p.patterns_encountered,
                "path_wallets": p.wallets,
            }
            for p in discovered_paths
        ]

        primary = discovered_paths[0] if discovered_paths else None

        return {
            "source": source,
            "target": None,
            "max_depth": max_depth,
            "path_found": bool(discovered_paths),
            "total_destinations_discovered": len(discovered_paths),
            "destinations": destinations_summary,
            "primary_path": primary.to_dict() if primary else None,
            "alternative_paths": [p.to_dict() for p in discovered_paths[1:10]],
            "graph": composite_graph,
            "explanation": (
                f"Discovered {len(discovered_paths)} downstream flow destinations reachable "
                f"within {max_depth} hops from source."
            ),
        }

    # ------------------------------------------------------------------
    # Path Reconstruction & Metrics
    # ------------------------------------------------------------------

    def _reconstruct_path(self, path_id: str, wallet_seq: List[str]) -> Optional[FlowPath]:
        """Convert a sequence of wallet addresses into a fully contextualized FlowPath."""
        if len(wallet_seq) < 2:
            return None

        flow_hops: List[FlowHop] = []
        total_value = 0.0
        prev_ts: Optional[datetime] = None
        temporal_consistent = True

        for i in range(len(wallet_seq) - 1):
            u, v = wallet_seq[i], wallet_seq[i + 1]
            key = (u, v)
            if key not in self._edge_txs or not self._edge_txs[key]:
                return None

            candidates = self._edge_txs[key]
            # Pick transaction: prefer earliest that occurs after prev_ts for chronological consistency
            chosen_tx = candidates[0]
            if prev_ts is not None:
                valid_later = [t for t in candidates if t.timestamp >= prev_ts]
                if valid_later:
                    chosen_tx = valid_later[0]
                else:
                    chosen_tx = candidates[0]
                    temporal_consistent = False

            prev_ts = chosen_tx.timestamp
            total_value += chosen_tx.amount

            # Wallet risks
            u_risk = self._get_wallet_risk(u)
            v_risk = self._get_wallet_risk(v)

            # Alerts for this hop
            hop_alerts = self._get_alerts_for_tx(chosen_tx.tx_id)

            flow_hops.append(
                FlowHop(
                    hop_index=i + 1,
                    from_wallet=u,
                    to_wallet=v,
                    tx_id=chosen_tx.tx_id,
                    amount=chosen_tx.amount,
                    timestamp=chosen_tx.timestamp,
                    category=chosen_tx.category_label,
                    gas_fee=chosen_tx.gas_fee,
                    description=chosen_tx.description,
                    from_risk_score=u_risk["score"],
                    from_risk_level=u_risk["level"],
                    to_risk_score=v_risk["score"],
                    to_risk_level=v_risk["level"],
                    alerts=hop_alerts,
                )
            )

        if not flow_hops:
            return None

        first_ts = flow_hops[0].timestamp
        last_ts = flow_hops[-1].timestamp
        duration_seconds = max(0.0, (last_ts - first_ts).total_seconds())

        intermediate = wallet_seq[1:-1]

        # Calculate path suspicion score & patterns
        patterns: Set[str] = set()
        suspicious_wallets: List[str] = []
        risk_scores: List[float] = []

        for w in wallet_seq:
            w_risk = self._get_wallet_risk(w)
            risk_scores.append(w_risk["score"])
            if w_risk["score"] >= 40 or w_risk["level"] in (Severity.HIGH, Severity.CRITICAL):
                if w not in suspicious_wallets:
                    suspicious_wallets.append(w)
            for pat in w_risk.get("pattern_types", []):
                patterns.add(pat)

        for hop in flow_hops:
            if hop.category in ("circular", "rapid_movement", "burst", "split", "recombination", "cluster"):
                patterns.add(hop.category.upper())

        # Deterministic Path Suspicion Formula:
        # Base: 60% max wallet risk + 40% avg wallet risk
        max_r = max(risk_scores) if risk_scores else 0.0
        avg_r = (sum(risk_scores) / len(risk_scores)) if risk_scores else 0.0
        base_score = 0.6 * max_r + 0.4 * avg_r

        # Pattern bonus: +10 for 1 pattern, +5 for each additional up to +20
        pattern_bonus = 0.0
        if patterns:
            pattern_bonus = min(20.0, 10.0 + 5.0 * (len(patterns) - 1))

        # Velocity bonus: multi-hop movement within 30 minutes
        velocity_bonus = 10.0 if (len(flow_hops) >= 2 and duration_seconds <= 1800.0) else 0.0

        path_suspicion = min(100.0, round(base_score + pattern_bonus + velocity_bonus, 1))

        if path_suspicion >= 60.0:
            suspicion_level = Severity.CRITICAL
        elif path_suspicion >= 40.0:
            suspicion_level = Severity.HIGH
        elif path_suspicion >= 20.0:
            suspicion_level = Severity.MEDIUM
        else:
            suspicion_level = Severity.LOW

        hops_count = len(flow_hops)
        explanation = (
            f"Reconstructed {hops_count}-hop flow moving {total_value:.2f} ETH across "
            f"{len(wallet_seq)} wallets in {int(duration_seconds)}s with suspicion level {suspicion_level}."
        )

        return FlowPath(
            path_id=path_id,
            source=wallet_seq[0],
            target=wallet_seq[-1],
            hops=hops_count,
            wallets=wallet_seq,
            intermediate_wallets=intermediate,
            flow_hops=flow_hops,
            total_value=total_value,
            first_timestamp=first_ts,
            last_timestamp=last_ts,
            duration_seconds=duration_seconds,
            temporal_consistent=temporal_consistent,
            suspicious_wallets=suspicious_wallets,
            patterns_encountered=sorted(list(patterns)),
            path_suspicion_score=path_suspicion,
            path_suspicion_level=suspicion_level,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Cytoscape Graph Builder with Highlighting
    # ------------------------------------------------------------------

    def _build_path_graph(
        self,
        path_wallets: List[str],
        source: str,
        target: Optional[str] = None,
        flow_path: Optional[FlowPath] = None,
    ) -> Dict:
        """
        Generate Cytoscape.js compatible nodes and edges with distinct flow-tracing flags.
        Nodes include is_source, is_target, is_path, hop_index, and risk metrics.
        Edges include is_path, hop_number, amount, and timestamp.
        """
        path_wallet_set = set(path_wallets)
        path_tx_ids = set(h.tx_id for h in flow_path.flow_hops) if flow_path else set()

        # Gather wallets to render: path wallets + 1-hop connected neighbors for spatial context
        rendered_wallets: Set[str] = set(path_wallets)
        if source:
            rendered_wallets.add(source)
            rendered_wallets.update(list(self._graph.successors(source))[:4])
            rendered_wallets.update(list(self._graph.predecessors(source))[:4])
        if target:
            rendered_wallets.add(target)
            rendered_wallets.update(list(self._graph.predecessors(target))[:4])

        # Build nodes
        nodes = []
        for w in rendered_wallets:
            w_risk = self._get_wallet_risk(w)
            is_path_node = w in path_wallet_set
            is_src = (w == source)
            is_tgt = (w == target)

            # Determine hop index along path if present
            hop_idx = -1
            if is_path_node and w in path_wallets:
                try:
                    hop_idx = path_wallets.index(w)
                except ValueError:
                    hop_idx = -1

            nodes.append({
                "data": {
                    "id": w,
                    "label": w[:8] + "...",
                    "is_path": is_path_node,
                    "is_source": is_src,
                    "is_target": is_tgt,
                    "hop_index": hop_idx,
                    "flagged": w_risk["score"] >= 40,
                    "risk_score": w_risk["score"],
                    "risk_level": w_risk["level"],
                }
            })

        # Build edges: path edges first, plus context edges between rendered wallets
        edges = []
        seen_edges = set()

        # 1. Path edges (highest priority)
        if flow_path:
            for hop in flow_path.flow_hops:
                seen_edges.add(hop.tx_id)
                edges.append({
                    "data": {
                        "id": hop.tx_id,
                        "source": hop.from_wallet,
                        "target": hop.to_wallet,
                        "amount": hop.amount,
                        "label": f"{hop.amount:.2f} ETH",
                        "timestamp": hop.timestamp.isoformat(),
                        "category": hop.category,
                        "is_path": True,
                        "hop_number": hop.hop_index,
                    }
                })

        # 2. Context edges between rendered nodes
        for tx in self._transactions:
            if tx.tx_id in seen_edges:
                continue
            if tx.from_wallet in rendered_wallets and tx.to_wallet in rendered_wallets:
                seen_edges.add(tx.tx_id)
                edges.append({
                    "data": {
                        "id": tx.tx_id,
                        "source": tx.from_wallet,
                        "target": tx.to_wallet,
                        "amount": tx.amount,
                        "label": f"{tx.amount:.2f} ETH",
                        "timestamp": tx.timestamp.isoformat(),
                        "category": tx.category_label,
                        "is_path": False,
                        "hop_number": 0,
                    }
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "path_wallet_count": len(path_wallets),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    # ------------------------------------------------------------------
    # Risk & Alert Helpers
    # ------------------------------------------------------------------

    def _get_wallet_risk(self, wallet_id: str) -> Dict:
        if self._engine is not None:
            assessment = self._engine.get_wallet_risk(wallet_id)
            return {
                "score": assessment.risk_score,
                "level": assessment.risk_level,
                "pattern_types": assessment.pattern_types,
            }
        return {"score": 0.0, "level": Severity.LOW, "pattern_types": []}

    def _get_alerts_for_tx(self, tx_id: str) -> List[str]:
        if self._engine is not None:
            all_alerts = self._engine.detect_all()
            return [a.pattern for a in all_alerts if tx_id in a.transaction_ids]
        return []
