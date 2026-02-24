"""
storage/ipfs_store.py

IPFS/Pinata storage — backup storage provider for Arweave.

Pinata provides IPFS pinning service — files must be pinned
before they can be deleted.
"""

import json
import logging
import os
import re
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# IPFS CID format: CIDv0 (Qm... 46 characters) or CIDv1 (baf... 57+ characters)
_IPFS_CID_RE = re.compile(r"^(Qm[1-9A-HJ-NP-Za-km-z]{44}|baf[a-z2-7]{55,})$")


class IPFSStore:
    """
    IPFS/Pinata storage client.

    Parameters:
        api_key: Pinata API key
        secret_key: Pinata secret key
        gateway: IPFS gateway URL
    """

    PINATA_UPLOAD_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    PINATA_UNPIN_URL = "https://api.pinata.cloud/pinning/unpin"

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        gateway: str = "https://gateway.pinata.cloud/ipfs",
    ) -> None:
        self.api_key = api_key or os.getenv("PINATA_API_KEY", "")
        self.secret_key = secret_key or os.getenv("PINATA_SECRET_KEY", "")
        self.gateway = gateway.rstrip("/")

        self._headers = {
            "pinata_api_key": self.api_key,
            "pinata_secret_api_key": self.secret_key,
            "Content-Type": "application/json",
        }

        logger.info(f"IPFSStore initialized: gateway={self.gateway}")

    def upload(self, data: dict, name: Optional[str] = None) -> Optional[dict]:
        """
        Upload data to IPFS (via Pinata).

        Parameters:
            data: Data to upload
            name: Pinata pin name

        Returns:
            dict: {'cid': str, 'uri': str} or None
        """
        if not self.api_key:
            logger.error("PINATA_API_KEY not found")
            return None

        try:
            payload = {
                "pinataContent": data,
                "pinataMetadata": {"name": name or "immortal_mind_snapshot"},
                "pinataOptions": {"cidVersion": 1},
            }

            response = requests.post(
                self.PINATA_UPLOAD_URL,
                headers=self._headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            cid = result["IpfsHash"]
            uri = f"{self.gateway}/{cid}"

            logger.info(f"IPFS upload successful: cid={cid[:16]}...")
            return {"cid": cid, "uri": uri}

        except Exception as e:
            logger.error(f"IPFS upload error: {e}")
            return None

    def download(self, cid_or_uri: str) -> Optional[dict]:
        """
        Download data from IPFS.

        Parameters:
            cid_or_uri: CID or IPFS URI

        Returns:
            dict: Downloaded data or None
        """
        try:
            cid = cid_or_uri.replace(f"{self.gateway}/", "").strip("/")
            if not _IPFS_CID_RE.match(cid):
                logger.error("Invalid IPFS CID format rejected: %s", cid[:60])
                return None
            url = f"{self.gateway}/{cid}"

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"IPFS download error: {e}")
            return None

    def health_check(self) -> bool:
        """Is the Pinata API accessible?"""
        try:
            response = requests.get(
                "https://api.pinata.cloud/data/testAuthentication",
                headers=self._headers,
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
