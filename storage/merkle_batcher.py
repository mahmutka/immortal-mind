"""
storage/merkle_batcher.py

Merkle tree-based blockchain batch anchor system.

Instead of a separate TX per memory, accumulate hashes in a local Merkle tree.
When the batch fills up, write a single Merkle root hash on-chain.

100 memories → 1 TX (100x gas savings)
"""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MerkleBatcher:
    """
    Batch manager that accumulates memory hashes in a Merkle tree.

    Parameters:
        batch_size: How many hashes to accumulate before computing the Merkle root (default: 100)
    """

    def __init__(self, batch_size: int = 100) -> None:
        self._batch_size = batch_size
        self._pending: list[str] = []

    def add(self, content_hash: str) -> Optional[str]:
        """
        Add a hash. Returns the Merkle root when the batch is full, otherwise None.

        Parameters:
            content_hash: Hash to add (hex string)

        Returns:
            str | None: Merkle root when batch is full, otherwise None
        """
        self._pending.append(content_hash)
        if len(self._pending) >= self._batch_size:
            return self.flush()
        return None

    def flush(self) -> Optional[str]:
        """
        Force-finish the current batch and return the Merkle root.

        Called when a session closes or on kill switch.

        Returns:
            str | None: Merkle root (hex), or None if batch is empty
        """
        if not self._pending:
            return None
        root = self._merkle_root(self._pending.copy())
        count = len(self._pending)
        self._pending.clear()
        logger.info("Merkle batch flushed: %d hash → root %s...", count, root[:16])
        return root

    def pending_count(self) -> int:
        """Number of pending hashes."""
        return len(self._pending)

    @staticmethod
    def _merkle_root(hashes: list[str]) -> str:
        """
        Compute the Merkle root from the given list of hashes.

        Single-element list → returns itself.
        If count is odd, the last element is duplicated (standard Bitcoin approach).
        """
        if len(hashes) == 1:
            return hashes[0]
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])  # Duplicate last element
        parents = [
            hashlib.sha256((hashes[i] + hashes[i + 1]).encode()).hexdigest()
            for i in range(0, len(hashes), 2)
        ]
        return MerkleBatcher._merkle_root(parents)
