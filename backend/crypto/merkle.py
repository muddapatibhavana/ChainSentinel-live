"""
ChainSentinel - Deterministic Merkle Tree Implementation (Phase 5)

Cryptographic Merkle tree implementation using SHA-256 for evidence integrity verification.
Supports empty collections, single items, odd leaf balancing, deterministic leaf sorting,
and cryptographic inclusion proofs.

Odd-Leaf Handling Specification
--------------------------------
When a tree level contains an odd number of nodes (> 1), the final un-partnered node
is duplicated (paired with itself: hash_pair(node, node)) to form an even pair.
This follows the standard RFC 6962 / Bitcoin binary tree balance specification.
"""

import hashlib
from typing import Any, Dict, List, Optional

# Canonical SHA-256 digest of empty bytes b""
EMPTY_MERKLE_ROOT = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def hash_pair(left: str, right: str) -> str:
    """
    Concatenate two hexadecimal hash strings and compute their SHA-256 digest.

    Parameters
    ----------
    left  : 64-char lowercase hex digest
    right : 64-char lowercase hex digest

    Returns
    -------
    64-char lowercase hexadecimal SHA-256 digest
    """
    combined = f"{left.lower()}{right.lower()}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def compute_merkle_root(leaf_hashes: List[str], sort_leaves: bool = True) -> str:
    """
    Compute the Merkle root of a collection of leaf hashes.

    Parameters
    ----------
    leaf_hashes : List of SHA-256 hex digests
    sort_leaves : When True (default), sort hashes lexicographically for determinism

    Returns
    -------
    Merkle root SHA-256 digest string
    """
    tree = MerkleTree(leaf_hashes, sort_leaves=sort_leaves)
    return tree.root


class MerkleTree:
    """
    Binary Merkle Tree for evidence collections.

    Attributes
    ----------
    leaves : List[str]
        Normalized list of leaf hashes (sorted if sort_leaves=True).
    root : str
        Calculated Merkle root digest.
    levels : List[List[str]]
        All tree levels from leaves (level 0) to root.
    """

    def __init__(self, leaf_hashes: List[str], sort_leaves: bool = True) -> None:
        if sort_leaves:
            self.leaves: List[str] = sorted(h.lower() for h in leaf_hashes)
        else:
            self.leaves: List[str] = [h.lower() for h in leaf_hashes]

        self.levels: List[List[str]] = []
        self._build_tree()

    def _build_tree(self) -> None:
        """Construct the tree levels and determine the root."""
        if not self.leaves:
            self.root = EMPTY_MERKLE_ROOT
            self.levels = [[]]
            return

        if len(self.leaves) == 1:
            self.root = self.leaves[0]
            self.levels = [[self.leaves[0]]]
            return

        current_level = list(self.leaves)
        self.levels.append(current_level)

        while len(current_level) > 1:
            # Duplicate trailing leaf if odd length
            working_level = list(current_level)
            if len(working_level) % 2 == 1:
                working_level.append(working_level[-1])

            next_level: List[str] = []
            for i in range(0, len(working_level), 2):
                parent = hash_pair(working_level[i], working_level[i + 1])
                next_level.append(parent)

            self.levels.append(next_level)
            current_level = next_level

        self.root = current_level[0]

    def get_proof(self, leaf_hash: str) -> Optional[List[Dict[str, str]]]:
        """
        Generate an audit path (inclusion proof) for a specific leaf hash.

        Returns
        -------
        List of proof steps [{'position': 'left'|'right', 'hash': '...'}]
        or None if leaf_hash is not present in the tree.
        """
        norm_leaf = leaf_hash.lower()
        if norm_leaf not in self.leaves:
            return None

        idx = self.leaves.index(norm_leaf)
        proof: List[Dict[str, str]] = []

        # Traverse upwards through all levels except the root level
        for lvl in self.levels[:-1]:
            working = list(lvl)
            if len(working) % 2 == 1:
                working.append(working[-1])

            if idx % 2 == 0:
                # Sibling is to the right
                sibling = working[idx + 1]
                proof.append({"position": "right", "hash": sibling})
            else:
                # Sibling is to the left
                sibling = working[idx - 1]
                proof.append({"position": "left", "hash": sibling})

            idx = idx // 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
        """
        Cryptographically verify an inclusion proof against an expected Merkle root.

        Parameters
        ----------
        leaf_hash     : Target leaf hash to verify
        proof         : List of audit path steps
        expected_root : Root digest to verify against

        Returns
        -------
        bool : True if the proof matches the root, False otherwise
        """
        curr = leaf_hash.lower()
        for step in proof:
            sibling = step["hash"].lower()
            if step["position"] == "left":
                curr = hash_pair(sibling, curr)
            elif step["position"] == "right":
                curr = hash_pair(curr, sibling)
            else:
                return False

        return curr.lower() == expected_root.lower()
