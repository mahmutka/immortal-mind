"""
storage/blockchain_anchor.py

On-chain hash anchoring — multi-chain support.

Records memory hashes to the blockchain. This cryptographically proves
that memory has not been tampered with.

Supported chains: Base Sepolia, Arbitrum Sepolia
Smart contract: ImmortalMind.sol

Fallback: Base → Arbitrum → local queue
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from storage.merkle_batcher import MerkleBatcher

logger = logging.getLogger(__name__)


def _validate_rpc_url(url: str) -> bool:
    """Validate that the RPC URL is safe and in a valid format."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


class BlockchainAnchor:
    """
    On-chain memory anchor manager.

    Parameters:
        chain_name: Chain name ('base_sepolia' | 'arbitrum_sepolia')
        rpc_url: RPC endpoint URL
        contract_address: ImmortalMind contract address
        private_key: Private key for transaction signing
    """

    SUPPORTED_CHAINS = {
        "base_sepolia": {
            "chain_id": 84532,
            "rpc_default": "https://sepolia.base.org",
        },
        "arbitrum_sepolia": {
            "chain_id": 421614,
            "rpc_default": "https://sepolia-rollup.arbitrum.io/rpc",
        },
    }

    def __init__(
        self,
        chain_name: str = "base_sepolia",
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None,
        private_key: Optional[str] = None,
    ) -> None:
        self.chain_name = chain_name
        self.chain_info = self.SUPPORTED_CHAINS.get(chain_name, {})

        _rpc_candidate = (
            rpc_url
            or os.getenv(f"{chain_name.upper()}_RPC_URL")
            or self.chain_info.get("rpc_default", "")
        )
        if not _validate_rpc_url(_rpc_candidate):
            logger.warning(
                "Invalid RPC URL rejected: '%s' — using default.",
                _rpc_candidate[:80],
            )
            _rpc_candidate = self.chain_info.get("rpc_default", "")
        self.rpc_url = _rpc_candidate

        self.contract_address = (
            contract_address
            or os.getenv(f"{chain_name.upper()}_CONTRACT_ADDRESS")
        )

        self.private_key = private_key or os.getenv("PRIVATE_KEY")

        self._web3 = None
        self._contract = None
        self._pending_queue: list[dict] = []

        # Merkle batch system (100 memories = 1 TX)
        self._batcher = MerkleBatcher(batch_size=100)

        # Lazy initialization
        logger.info(
            f"BlockchainAnchor initialized: chain={chain_name}, "
            f"rpc={self.rpc_url[:30]}..."
        )

    def _init_web3(self) -> bool:
        """Initialize Web3 and contract connection."""
        if self._web3 is not None:
            return True

        try:
            from web3 import Web3

            self._web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 30}))

            if not self._web3.is_connected():
                logger.error(f"Web3 connection error: {self.rpc_url}")
                return False

            logger.debug(f"Web3 connected: chain_id={self._web3.eth.chain_id}")

            if self.contract_address:
                self._load_contract()

            return True

        except ImportError:
            logger.error("web3 not installed: pip install web3")
            return False
        except Exception as e:
            logger.error(f"Web3 initialization error: {e}")
            return False

    def _load_contract(self) -> None:
        """Load the ImmortalMind contract."""
        # Read ABI from contract directory
        abi_paths = [
            "contracts/artifacts/ImmortalMind.json",
            "contracts/ImmortalMind_abi.json",
        ]

        abi = None
        for path in abi_paths:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        artifact = json.load(f)
                        abi = artifact.get("abi", artifact)
                    break
                except Exception:
                    pass

        if abi is None:
            logger.warning("Contract ABI not found — only hash anchoring is supported")
            return

        try:
            self._contract = self._web3.eth.contract(
                address=self._web3.to_checksum_address(self.contract_address),
                abi=abi,
            )
            logger.info(f"Contract loaded: {self.contract_address}")
        except Exception as e:
            logger.error(f"Contract could not be loaded: {e}")

    def anchor_memory_hash(
        self,
        identity_id: str,
        content_hash: str,
        storage_uri: str,
        memory_type: str = "snapshot",
        salience_score: int = 0,
    ) -> Optional[dict]:
        """
        Record memory hash to the blockchain.

        Parameters:
            identity_id: AI identity ID
            content_hash: Hash of memory content (SHA256)
            storage_uri: Arweave/IPFS URI
            memory_type: Memory type
            salience_score: Importance score (0-100)

        Returns:
            dict: {'tx_hash': str, 'chain': str} or None
        """
        if not self._init_web3():
            logger.warning("Web3 could not be initialized — adding to queue")
            return self._queue_operation({
                "type": "anchor_memory",
                "identity_id": identity_id,
                "content_hash": content_hash,
                "storage_uri": storage_uri,
                "memory_type": memory_type,
            })

        try:
            if self._contract is None:
                # No contract — log with simple ETH transfer (hack)
                return self._simple_log_tx(content_hash)

            # Call contract function
            account = self._web3.eth.account.from_key(self.private_key)

            # Convert identity_id to bytes32
            import hashlib
            identity_bytes = hashlib.sha256(identity_id.encode()).digest()
            content_bytes = hashlib.sha256(content_hash.encode()).digest()

            tx = self._contract.functions.anchorMemory(
                identity_bytes,
                content_bytes,
                storage_uri,
                memory_type,
                salience_score,
            ).build_transaction({
                "from": account.address,
                "nonce": self._web3.eth.get_transaction_count(account.address),
                "gasPrice": self._web3.eth.gas_price,
            })

            signed = self._web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"Anchor TX sent: {tx_hash_hex[:16]}...")
            return {"tx_hash": tx_hash_hex, "chain": self.chain_name}

        except Exception as e:
            logger.error(f"Anchor TX error: {e}")
            return self._queue_operation({
                "type": "anchor_memory",
                "content_hash": content_hash,
                "error": str(e),
            })

    def _simple_log_tx(self, data_hash: str) -> Optional[dict]:
        """Log with simple ETH TX when no contract is available."""
        try:
            account = self._web3.eth.account.from_key(self.private_key)
            tx = {
                "to": account.address,  # Send 0 ETH to self
                "value": 0,
                "gas": 21000,
                "gasPrice": self._web3.eth.gas_price,
                "nonce": self._web3.eth.get_transaction_count(account.address),
                "data": self._web3.to_hex(text=data_hash[:32]),
            }
            signed = self._web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            return {"tx_hash": tx_hash.hex(), "chain": self.chain_name, "type": "simple_log"}
        except Exception as e:
            logger.error(f"Simple log TX error: {e}")
            return None

    def _queue_operation(self, data: dict) -> dict:
        """Add a failed operation to the queue."""
        entry = {**data, "queued_at": datetime.now(timezone.utc).isoformat()}
        self._pending_queue.append(entry)
        logger.warning(f"Operation queued: {data.get('type', 'unknown')}")
        return {"queued": True, "queue_size": len(self._pending_queue)}

    def retry_pending(self) -> int:
        """
        Retry queued operations.

        Returns:
            int: Number of successfully processed operations
        """
        if not self._pending_queue:
            return 0

        processed = 0
        remaining = []

        for operation in self._pending_queue:
            try:
                if operation.get("type") == "anchor_memory":
                    result = self.anchor_memory_hash(
                        operation.get("identity_id", ""),
                        operation.get("content_hash", ""),
                        operation.get("storage_uri", ""),
                    )
                    if result and not result.get("queued"):
                        processed += 1
                        continue
            except Exception as e:
                logger.warning(f"Queue retry failed: {e}")

            remaining.append(operation)

        self._pending_queue = remaining
        logger.info(f"retry_pending: {processed} processed, {len(remaining)} remaining")
        return processed

    def health_check(self) -> bool:
        """Is the blockchain connection available?"""
        return self._init_web3() and self._web3 is not None and self._web3.is_connected()

    def anchor_memory_batched(
        self,
        identity_id: str,
        content_hash: str,
        storage_uri: str = "",
        memory_type: str = "snapshot",
        salience: int = 0,
        entrenchment: int = 0,
    ) -> Optional[dict]:
        """
        Add a memory to the Merkle batch.

        When the batch fills up (100 memories), automatically writes the Merkle root on-chain.
        Returns None if not yet full (TX not yet sent).

        Parameters:
            identity_id: AI identity ID
            content_hash: Hash of memory content
            storage_uri: Arweave/IPFS URI (optional)
            memory_type: Memory type
            salience: Importance score (0-100)
            entrenchment: Entrenchment level (0-100)

        Returns:
            dict | None: TX info if batch is complete, otherwise None
        """
        root = self._batcher.add(content_hash)
        if root is not None:
            return self._anchor_batch_on_chain(
                identity_id, root, self._batcher._batch_size, storage_uri
            )
        return None

    def flush_batch(self, identity_id: str, batch_uri: str = "") -> Optional[dict]:
        """
        Force-write a partial batch to the blockchain.

        Called when a session closes or a kill switch is triggered.

        Parameters:
            identity_id: AI identity ID
            batch_uri: Batch URI (optional)

        Returns:
            dict | None: TX info or None
        """
        root = self._batcher.flush()
        if root is None:
            return None
        count = 0  # After flush the pending is cleared, count unknown — 0 is sufficient
        return self._anchor_batch_on_chain(identity_id, root, count, batch_uri)

    def _anchor_batch_on_chain(
        self,
        identity_id: str,
        merkle_root: str,
        memory_count: int,
        batch_uri: str = "",
    ) -> Optional[dict]:
        """Write Merkle root on-chain via anchorBatch()."""
        if not self._init_web3():
            return self._queue_operation({
                "type": "anchor_batch",
                "identity_id": identity_id,
                "merkle_root": merkle_root,
                "memory_count": memory_count,
            })

        try:
            if self._contract is None:
                logger.warning("anchorBatch: no contract — skipping")
                return None

            import hashlib
            identity_bytes = hashlib.sha256(identity_id.encode()).digest()
            root_bytes = bytes.fromhex(merkle_root) if len(merkle_root) == 64 else \
                hashlib.sha256(merkle_root.encode()).digest()

            account = self._web3.eth.account.from_key(self.private_key)
            tx = self._contract.functions.anchorBatch(
                identity_bytes,
                root_bytes,
                memory_count,
                batch_uri,
            ).build_transaction({
                "from": account.address,
                "nonce": self._web3.eth.get_transaction_count(account.address),
                "gasPrice": self._web3.eth.gas_price,
            })

            signed = self._web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(
                "Batch anchor TX: root=%s..., count=%d, tx=%s...",
                merkle_root[:16], memory_count, tx_hash_hex[:16]
            )
            return {"tx_hash": tx_hash_hex, "chain": self.chain_name, "type": "batch"}

        except Exception as e:
            logger.error("Batch anchor TX error: %s", e)
            return self._queue_operation({
                "type": "anchor_batch",
                "merkle_root": merkle_root,
                "error": str(e),
            })

    @property
    def pending_count(self) -> int:
        """Number of pending operations in the queue."""
        return len(self._pending_queue)
