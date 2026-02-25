"""
tests/test_garbage_collector.py

GarbageCollector tests.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from cognitio.garbage_collector import GarbageCollector
from cognitio.memory import MemoryRecord, MemoryStore, MemoryStatus


class MockVectorStore:
    """Simple mock VectorStore for testing."""
    def __init__(self):
        self._deleted = []

    def delete(self, memory_id: str):
        self._deleted.append(memory_id)

    def add(self, memory_id, embedding, metadata):
        pass

    def exists(self, memory_id):
        return False


@pytest.fixture
def store_gc():
    """MemoryStore + GarbageCollector."""
    memory_store = MemoryStore()
    vector_store = MockVectorStore()
    gc = GarbageCollector(
        memory_store=memory_store,
        vector_store=vector_store,
        config={
            "max_active_memories": 100,
            "prune_threshold_recency": 0.5,  # High threshold for easy testing
            "min_entrenchment_to_protect": 0.4,
            "prune_interval_hours": 24,
            "protect_recent_days": 7,
            "min_reinforcements_to_protect": 3,
        },
    )
    return memory_store, vector_store, gc


class TestGarbageCollector:
    def test_high_entrenchment_protected(self, store_gc):
        """High entrenchment records should not be pruned."""
        memory_store, vector_store, gc = store_gc

        from datetime import datetime, timedelta, timezone
        protected = MemoryRecord(content="Protected record")
        protected.entrenchment = 0.8
        protected.last_accessed = datetime.now(timezone.utc) - timedelta(days=100)
        memory_store.add(protected)

        gc.collect()
        assert memory_store.get(protected.id) is not None, "High entrenchment should not be pruned"
        assert protected.id not in vector_store._deleted

    def test_anchor_always_protected(self, store_gc):
        """Anchor records should never be pruned."""
        memory_store, vector_store, gc = store_gc

        from datetime import datetime, timedelta, timezone
        anchor = MemoryRecord(content="Anchor record")
        anchor.is_anchor = True
        anchor.entrenchment = 0.1  # Low entrenchment
        anchor.last_accessed = datetime.now(timezone.utc) - timedelta(days=200)
        memory_store.add(anchor)

        gc.collect()
        retrieved = memory_store.get(anchor.id)
        assert retrieved is not None, "Anchor should never be pruned"
        assert retrieved.status == MemoryStatus.ACTIVE

    def test_recent_access_protected(self, store_gc):
        """Records accessed in the last 7 days should not be pruned."""
        memory_store, vector_store, gc = store_gc

        from datetime import datetime, timezone
        recent = MemoryRecord(content="Recently accessed")
        recent.entrenchment = 0.1
        recent.last_accessed = datetime.now(timezone.utc)
        memory_store.add(recent)

        gc.collect()
        assert memory_store.get(recent.id) is not None

    def test_crisis_memory_protected(self, store_gc):
        """Records with an active crisis reference should not be pruned."""
        memory_store, vector_store, gc = store_gc

        from datetime import datetime, timedelta, timezone
        crisis_mem = MemoryRecord(content="Crisis memory")
        crisis_mem.entrenchment = 0.1
        crisis_mem.last_accessed = datetime.now(timezone.utc) - timedelta(days=100)
        memory_store.add(crisis_mem)

        gc.register_crisis_memory(crisis_mem.id)
        gc.collect()
        assert memory_store.get(crisis_mem.id) is not None

    def test_should_run_when_limit_approached(self, store_gc):
        """should_run should return True when approaching the memory limit."""
        memory_store, vector_store, gc = store_gc

        # Exceed 80% threshold: max=100, limit=80
        for i in range(85):
            m = MemoryRecord(content=f"Memory {i}")
            memory_store.add(m)

        assert gc.should_run() is True

    def test_get_stats(self, store_gc):
        """get_stats() should return a dict."""
        memory_store, vector_store, gc = store_gc

        for i in range(5):
            memory_store.add(MemoryRecord(content=f"Test {i}"))

        stats = gc.get_stats()
        assert "total" in stats
        assert "avg_entrenchment" in stats
        assert stats["total"] == 5
