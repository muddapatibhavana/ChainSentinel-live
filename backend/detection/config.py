"""
ChainSentinel - Detection Configuration
All detector thresholds are defined here, in one place.
Adjust these values without touching detector logic.
"""

# ---------------------------------------------------------------------------
# Circular Transaction Detector
# ---------------------------------------------------------------------------
CIRCULAR_MAX_WINDOW_SECONDS = 7200     # 2 hours: max time for a cycle to complete
CIRCULAR_MIN_CYCLE_LENGTH = 3          # minimum wallets in a cycle (A→B→C→A = 3)
CIRCULAR_MAX_CYCLE_LENGTH = 10         # avoid flagging planet-scale graph loops

# ---------------------------------------------------------------------------
# Rapid Movement Detector
# ---------------------------------------------------------------------------
RAPID_MIN_HOPS = 3                     # minimum chain length to be "rapid movement"
RAPID_MAX_HOP_SECONDS = 300            # max seconds between consecutive hops (5 min)
RAPID_CHAIN_WINDOW_SECONDS = 3600      # chain must complete within 1 hour

# ---------------------------------------------------------------------------
# Burst Detector
# ---------------------------------------------------------------------------
BURST_WINDOW_SECONDS = 300             # 5-minute sliding window
BURST_MIN_TX_COUNT = 5                 # minimum transactions in window to flag

# ---------------------------------------------------------------------------
# Fan-Out / Splitting Detector
# ---------------------------------------------------------------------------
FANOUT_WINDOW_SECONDS = 3600           # 1-hour window
FANOUT_MIN_DESTINATIONS = 4            # minimum unique destination wallets to flag
FANOUT_MIN_TOTAL_AMOUNT = 5.0          # minimum total ETH dispersed (filters noise)

# ---------------------------------------------------------------------------
# Fan-In / Recombination Detector
# ---------------------------------------------------------------------------
FANIN_WINDOW_SECONDS = 3600            # 1-hour window
FANIN_MIN_SOURCES = 4                  # minimum unique source wallets to flag
FANIN_MIN_TOTAL_AMOUNT = 5.0           # minimum total ETH collected

# ---------------------------------------------------------------------------
# Suspicious Cluster Detector
# ---------------------------------------------------------------------------
CLUSTER_MIN_NODES = 3                  # minimum wallets in a dense subgroup
CLUSTER_MIN_EDGES = 5                  # minimum directed edges within the group
CLUSTER_MIN_EDGE_DENSITY = 0.30        # min ratio: actual edges / max possible edges
                                       # For 5 nodes, max directed edges = 5*4 = 20

# ---------------------------------------------------------------------------
# Risk Scoring
# Scores are additive. Multiple alerts on one wallet accumulate.
# ---------------------------------------------------------------------------
RISK_WEIGHTS: dict = {
    "CIRCULAR_TRANSACTION":    30,
    "RAPID_MOVEMENT":          20,
    "TRANSACTION_BURST":       15,
    "FAN_OUT_SPLIT":           20,
    "FAN_IN_RECOMBINATION":    20,
    "SUSPICIOUS_CLUSTER":      25,
}

# Thresholds to map numeric score → severity label
RISK_THRESHOLDS = {
    "CRITICAL": 60,   # score >= 60 → CRITICAL
    "HIGH":     40,   # score >= 40 → HIGH
    "MEDIUM":   20,   # score >= 20 → MEDIUM
    # below 20   → LOW
}
