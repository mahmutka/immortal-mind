"""
storage/local_store.py

Local JSON storage — for fallback and development environments.

Stores all snapshots on the local filesystem.
Continues to work even without an internet connection.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class LocalStore:
    """
    Local filesystem-based storage.

    Stores snapshots in JSON format.
    Each snapshot is linked via a hash chain.

    Parameters:
        base_dir: Storage directory
    """

    def __init__(self, base_dir: str = "data/local_snapshots") -> None:
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"LocalStore initialized: {base_dir}")

    def save_snapshot(self, snapshot: dict, identity_id: str) -> dict:
        """
        Save a snapshot to a local file.

        Parameters:
            snapshot: Data to save
            identity_id: AI identity ID

        Returns:
            dict: {'uri': str, 'filepath': str, 'hash': str}
        """
        import hashlib

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{identity_id[:16]}_{timestamp}.json"
        filepath = os.path.join(self.base_dir, filename)

        content = json.dumps(snapshot, ensure_ascii=False, indent=2)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        uri = f"local://{filepath}"
        logger.info(f"Snapshot saved: {filepath}")

        return {
            "uri": uri,
            "filepath": filepath,
            "hash": content_hash,
            "timestamp": timestamp,
        }

    def load_snapshot(self, uri: str) -> Optional[dict]:
        """
        Load a local snapshot.

        Parameters:
            uri: local:// URI or direct file path

        Returns:
            dict: Snapshot data or None
        """
        filepath = uri.replace("local://", "")

        if not os.path.exists(filepath):
            logger.warning(f"Snapshot not found: {filepath}")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Snapshot could not be loaded: {e}")
            return None

    def list_snapshots(self, identity_id: Optional[str] = None) -> list[dict]:
        """
        List available snapshots.

        Parameters:
            identity_id: Identity ID to filter by (None = all)

        Returns:
            list[dict]: List of snapshot metadata
        """
        snapshots = []
        for filename in os.listdir(self.base_dir):
            if not filename.endswith(".json"):
                continue
            if identity_id and not filename.startswith(identity_id[:16]):
                continue

            filepath = os.path.join(self.base_dir, filename)
            stat = os.stat(filepath)
            snapshots.append({
                "filename": filename,
                "filepath": filepath,
                "uri": f"local://{filepath}",
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        return sorted(snapshots, key=lambda x: x["modified_at"], reverse=True)

    def get_latest_snapshot(self, identity_id: str) -> Optional[dict]:
        """Get the most recent snapshot."""
        snapshots = self.list_snapshots(identity_id)
        if not snapshots:
            return None
        return self.load_snapshot(snapshots[0]["uri"])

    def cleanup_old_snapshots(self, keep_last: int = 10, identity_id: Optional[str] = None) -> int:
        """
        Clean up old snapshots, keeping the last N.

        Parameters:
            keep_last: How many snapshots to retain
            identity_id: Identity ID to filter by

        Returns:
            int: Number of deleted files
        """
        snapshots = self.list_snapshots(identity_id)
        to_delete = snapshots[keep_last:]

        deleted = 0
        for snapshot in to_delete:
            try:
                os.remove(snapshot["filepath"])
                deleted += 1
            except Exception as e:
                logger.warning(f"Snapshot could not be deleted: {e}")

        logger.info(f"LocalStore cleanup: {deleted} snapshots deleted")
        return deleted
