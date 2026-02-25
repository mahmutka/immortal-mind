"""
storage/arweave_store.py

Arweave permanent storage integration with AES-256-GCM encryption.

Arweave works on a "pay once, store forever" model.
Uploaded data cannot be modified or deleted — ideal for permanent archiving.

Encryption:
    All uploads are encrypted with AES-256-GCM before hitting the chain.
    Key: IMP_ARWEAVE_ENCRYPTION_KEY env var (64 hex chars = 32 bytes).
    Generate a key: python -c "import os; print(os.urandom(32).hex())"

    Envelope format stored on Arweave:
        {
            "encrypted": true,
            "version": 1,
            "nonce": "<24-char hex>",   # 12 random bytes per upload
            "ciphertext": "<hex>"       # encrypted payload + 16-byte GCM auth tag
        }

    Backward compatibility: unencrypted records (no "encrypted" field)
    are read as-is — existing data is never broken.
"""

import json
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# Arweave TX ID: 43-character base64url string
_ARWEAVE_TX_RE = re.compile(r"^[a-zA-Z0-9_-]{43}$")
# Trusted Arweave gateway hostnames
_TRUSTED_GATEWAYS = frozenset({"arweave.net", "ar-io.net", "g8way.io", "arweave.dev"})
# Required fields of an Arweave JWK RSA wallet
_JWK_REQUIRED_FIELDS = {"kty", "n", "e"}
# Memory types that must never be uploaded unencrypted
_SENSITIVE_MEMORY_TYPES = frozenset({"genesis", "emotional", "episodic", "snapshot"})


class MemoryEncryptor:
    """
    AES-256-GCM encryption for Arweave uploads.

    Each upload gets a fresh random nonce — same plaintext never
    produces the same ciphertext. GCM auth tag prevents tampering.

    Key: IMP_ARWEAVE_ENCRYPTION_KEY env var (64 hex chars = 32 bytes).
    Generate: python -c "import os; print(os.urandom(32).hex())"
    """

    ENVELOPE_VERSION = 1
    NONCE_BYTES = 12  # 96-bit nonce — GCM standard

    def __init__(self) -> None:
        self._key: Optional[bytes] = None
        self._load_key()

    def _load_key(self) -> None:
        """Load encryption key from environment variable."""
        raw = os.getenv("IMP_ARWEAVE_ENCRYPTION_KEY", "").strip()
        if not raw:
            logger.warning(
                "IMP_ARWEAVE_ENCRYPTION_KEY not set — "
                "Arweave uploads will be UNENCRYPTED (public on chain)."
            )
            return
        try:
            key_bytes = bytes.fromhex(raw)
            if len(key_bytes) != 32:
                logger.error(
                    "IMP_ARWEAVE_ENCRYPTION_KEY must be exactly 32 bytes "
                    "(64 hex chars). Got %d bytes — encryption disabled.",
                    len(key_bytes),
                )
                return
            self._key = key_bytes
            logger.info("Arweave encryption: AES-256-GCM active.")
        except ValueError:
            logger.error(
                "IMP_ARWEAVE_ENCRYPTION_KEY is not valid hex — encryption disabled."
            )

    @property
    def is_active(self) -> bool:
        """Is encryption ready?"""
        return self._key is not None

    def encrypt(self, plaintext: str) -> dict:
        """
        Encrypt plaintext string and return an envelope dict.

        Parameters:
            plaintext: UTF-8 string to encrypt (JSON payload)

        Returns:
            dict: Envelope with nonce + ciphertext (includes GCM tag)
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = os.urandom(self.NONCE_BYTES)
        aesgcm = AESGCM(self._key)
        # AESGCM.encrypt appends the 16-byte auth tag to ciphertext
        ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        return {
            "encrypted": True,
            "version": self.ENVELOPE_VERSION,
            "nonce": nonce.hex(),
            "ciphertext": ciphertext_and_tag.hex(),
        }

    def decrypt(self, envelope: dict) -> Optional[str]:
        """
        Decrypt an envelope dict and return the plaintext string.

        Parameters:
            envelope: Encrypted envelope from Arweave

        Returns:
            str: Decrypted plaintext, or None on failure
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if self._key is None:
            logger.error(
                "Cannot decrypt Arweave record: IMP_ARWEAVE_ENCRYPTION_KEY not set."
            )
            return None

        try:
            nonce = bytes.fromhex(envelope["nonce"])
            ciphertext_and_tag = bytes.fromhex(envelope["ciphertext"])
            aesgcm = AESGCM(self._key)
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_and_tag, None)
            return plaintext_bytes.decode("utf-8")
        except KeyError as e:
            logger.error("Arweave envelope missing field: %s", e)
            return None
        except Exception as e:
            logger.error(
                "Arweave decryption failed (wrong key or tampered data): %s", e
            )
            return None

    @staticmethod
    def generate_key() -> str:
        """Generate a new random 32-byte key as a hex string."""
        return os.urandom(32).hex()


class ArweaveStore:
    """
    Arweave permanent storage client with AES-256-GCM encryption.

    All uploads are encrypted before hitting the chain.
    Downloads are transparently decrypted.

    Parameters:
        wallet_path: Path to Arweave wallet file (JWK format)
        gateway: Arweave gateway URL
    """

    def __init__(
        self,
        wallet_path: Optional[str] = None,
        gateway: str = "https://arweave.net",
    ) -> None:
        parsed_gw = urlparse(gateway)
        if parsed_gw.hostname not in _TRUSTED_GATEWAYS:
            logger.warning("Untrusted Arweave gateway rejected: %s — using default.", gateway)
            gateway = "https://arweave.net"
        self.gateway = gateway.rstrip("/")
        self.wallet_path = wallet_path or os.getenv("ARWEAVE_WALLET_PATH")
        self._wallet = None
        self._encryptor = MemoryEncryptor()

        if self.wallet_path and os.path.exists(self.wallet_path):
            self._load_wallet()
        else:
            logger.warning(
                f"Arweave wallet not found: {self.wallet_path}. "
                "Read-only mode active."
            )

        logger.info(
            f"ArweaveStore initialized: gateway={self.gateway}, "
            f"encryption={'ON' if self._encryptor.is_active else 'OFF (WARNING: public)'}"
        )

    def _load_wallet(self) -> None:
        """Load and validate the Arweave JWK wallet."""
        try:
            with open(self.wallet_path, "r") as f:
                wallet = json.load(f)
            if not isinstance(wallet, dict) or not _JWK_REQUIRED_FIELDS.issubset(wallet):
                logger.error(
                    "Arweave wallet has invalid JWK format — expected fields: %s",
                    _JWK_REQUIRED_FIELDS,
                )
                return
            self._wallet = wallet
            logger.info(f"Arweave wallet loaded: {self.wallet_path}")
        except Exception as e:
            logger.error(f"Arweave wallet could not be loaded: {e}")

    def upload(self, data: dict, tags: Optional[dict] = None) -> Optional[dict]:
        """
        Encrypt and upload data to Arweave.

        Data is encrypted with AES-256-GCM before upload if
        IMP_ARWEAVE_ENCRYPTION_KEY is set. Otherwise a warning is logged
        and data is uploaded unencrypted.

        Parameters:
            data: Data to upload (JSON-serializable)
            tags: Arweave transaction tags

        Returns:
            dict: {'tx_id': str, 'uri': str, 'encrypted': bool} or None
        """
        if self._wallet is None:
            logger.error("Arweave upload: wallet not loaded")
            return None

        try:
            content = json.dumps(data, ensure_ascii=False)

            # ── Encryption layer ───────────────────────────────────────────
            if self._encryptor.is_active:
                upload_payload = self._encryptor.encrypt(content)
                content_type = "application/octet-stream"
                encrypted = True
            else:
                memory_type_tag = (tags or {}).get("memory_type", "")
                if memory_type_tag in _SENSITIVE_MEMORY_TYPES:
                    logger.error(
                        "Arweave upload BLOCKED: memory_type='%s' requires encryption. "
                        "Set IMP_ARWEAVE_ENCRYPTION_KEY to enable uploads of sensitive memories.",
                        memory_type_tag,
                    )
                    return None
                logger.warning(
                    "Arweave upload WITHOUT encryption — memory will be public on-chain. "
                    "Set IMP_ARWEAVE_ENCRYPTION_KEY to enable encryption."
                )
                upload_payload = data
                content_type = "application/json"
                encrypted = False
            # ──────────────────────────────────────────────────────────────

            content_bytes = json.dumps(upload_payload, ensure_ascii=False).encode("utf-8")

            tx_data = {
                "data": json.dumps(upload_payload, ensure_ascii=False),
                "tags": [
                    {"name": "Content-Type", "value": content_type},
                    {"name": "App-Name", "value": "ImmortalMind"},
                    {"name": "Protocol-Version", "value": "2"},
                    {"name": "Encrypted", "value": str(encrypted).lower()},
                ],
            }

            if tags:
                for key, value in tags.items():
                    tx_data["tags"].append({"name": key, "value": str(value)})

            # Simulated TX (use arweave-python-client for real implementation)
            # For real deployment:
            # from arweave import Wallet, Transaction
            # wallet = Wallet(self.wallet_path)
            # tx = Transaction(wallet, data=content_bytes)
            # tx.add_tag('Content-Type', content_type)
            # tx.add_tag('Encrypted', str(encrypted).lower())
            # tx.sign()
            # tx.send()
            # tx_id = tx.id

            import hashlib
            tx_id = hashlib.sha256(content_bytes).hexdigest()[:43]  # Mock TX ID
            uri = f"{self.gateway}/{tx_id}"

            logger.info(
                f"Arweave upload: tx_id={tx_id[:16]}..., "
                f"encrypted={encrypted}, size={len(content_bytes)}b"
            )
            return {
                "tx_id": tx_id,
                "uri": uri,
                "size_bytes": len(content_bytes),
                "encrypted": encrypted,
            }

        except Exception as e:
            logger.error(f"Arweave upload error: {e}")
            return None

    def download(self, tx_id_or_uri: str) -> Optional[dict]:
        """
        Download and decrypt data from Arweave.

        Transparently handles both encrypted and unencrypted records
        (backward compatibility with pre-encryption uploads).

        Parameters:
            tx_id_or_uri: Transaction ID or Arweave URI

        Returns:
            dict: Decrypted/downloaded data or None
        """
        try:
            # Extract TX ID from URI
            tx_id = tx_id_or_uri.replace(f"{self.gateway}/", "").strip("/")
            if not _ARWEAVE_TX_RE.match(tx_id):
                logger.error("Invalid Arweave TX ID format rejected: %s", tx_id[:60])
                return None

            url = f"{self.gateway}/{tx_id}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            raw = response.json()

            # ── Decryption layer ───────────────────────────────────────────
            if isinstance(raw, dict) and raw.get("encrypted") is True:
                plaintext = self._encryptor.decrypt(raw)
                if plaintext is None:
                    logger.error(
                        "Failed to decrypt Arweave record %s — "
                        "wrong key or tampered data.",
                        tx_id[:16],
                    )
                    return None
                return json.loads(plaintext)
            # ──────────────────────────────────────────────────────────────

            # Backward compat: unencrypted record
            return raw

        except requests.exceptions.HTTPError as e:
            logger.error(f"Arweave HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Arweave download error: {e}")
            return None

    def get_transaction_status(self, tx_id: str) -> Optional[str]:
        """
        Check transaction status.

        Parameters:
            tx_id: Transaction ID

        Returns:
            str: 'confirmed' | 'pending' | 'not_found' | None
        """
        try:
            if not _ARWEAVE_TX_RE.match(tx_id):
                logger.error("Invalid Arweave TX ID: %s", tx_id[:60])
                return None
            url = f"{self.gateway}/tx/{tx_id}/status"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("number_of_confirmations", 0) > 0:
                    return "confirmed"
                return "pending"
            elif response.status_code == 404:
                return "not_found"
            return None

        except Exception as e:
            logger.warning(f"Arweave status check failed: {e}")
            return None

    def health_check(self) -> bool:
        """Is the Arweave gateway accessible?"""
        try:
            response = requests.get(f"{self.gateway}/info", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    @property
    def encryption_active(self) -> bool:
        """Is encryption enabled?"""
        return self._encryptor.is_active
