"""
tests/test_memory.py

MemoryRecord and MemoryStore tests.
"""

import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from cognitio.memory import MemoryRecord, MemoryStore, MemoryType, MemoryValence, MemoryStatus


class TestMemoryRecord:
    def test_default_values(self):
        """Default values should be correct."""
        m = MemoryRecord(content="Test")
        assert m.confidence == 0.5
        assert m.entrenchment == 0.1
        assert m.emotional_intensity == 0.0
        assert m.emotional_valence == MemoryValence.NEUTRAL
        assert m.is_anchor is False
        assert m.reinforcement_count == 0
        assert m.status == MemoryStatus.ACTIVE

    def test_reinforce_increases_entrenchment(self):
        """reinforce() should increase entrenchment."""
        m = MemoryRecord(content="Test")
        initial = m.entrenchment
        m.reinforce()
        assert m.entrenchment > initial
        assert m.reinforcement_count == 1

    def test_reinforce_caps_at_1(self):
        """reinforce() should not exceed 1.0."""
        m = MemoryRecord(content="Test")
        m.entrenchment = 0.99
        m.reinforce(delta=0.5)
        assert m.entrenchment == pytest.approx(1.0)

    def test_days_since_creation(self):
        """days_since_creation() should compute correctly."""
        m = MemoryRecord(content="Test")
        m.created_at = datetime.now(timezone.utc) - timedelta(days=5)
        days = m.days_since_creation()
        assert abs(days - 5.0) < 0.1

    def test_days_since_access(self):
        """days_since_access() should compute correctly."""
        m = MemoryRecord(content="Test")
        m.last_accessed = datetime.now(timezone.utc) - timedelta(days=10)
        days = m.days_since_access()
        assert abs(days - 10.0) < 0.1

    def test_to_dict_and_from_dict(self):
        """Serialization and deserialization should work correctly."""
        m = MemoryRecord(
            content="Serialization test",
            memory_type=MemoryType.EPISODIC,
        )
        m.confidence = 0.8
        m.entrenchment = 0.6
        m.emotional_intensity = 0.7
        m.emotional_valence = MemoryValence.POSITIVE
        m.is_anchor = True
        m.tags = ["test", "serialization"]

        data = m.to_dict()
        restored = MemoryRecord.from_dict(data)

        assert restored.id == m.id
        assert restored.content == m.content
        assert restored.confidence == pytest.approx(m.confidence)
        assert restored.entrenchment == pytest.approx(m.entrenchment)
        assert restored.emotional_valence == m.emotional_valence
        assert restored.is_anchor == m.is_anchor
        assert restored.tags == m.tags


class TestMemoryStore:
    def setup_method(self):
        self.store = MemoryStore()

    def test_add_and_get(self):
        """Add a record and retrieve it."""
        m = MemoryRecord(content="Test")
        self.store.add(m)

        retrieved = self.store.get(m.id)
        assert retrieved is not None
        assert retrieved.content == "Test"

    def test_get_nonexistent_returns_none(self):
        """Retrieving a non-existent record should return None."""
        assert self.store.get("nonexistent_id") is None

    def test_delete(self):
        """Delete a record."""
        m = MemoryRecord(content="To be deleted")
        self.store.add(m)
        assert self.store.delete(m.id) is True
        assert self.store.get(m.id) is None
        assert self.store.delete("nonexistent") is False

    def test_get_by_type(self):
        """Filter by type."""
        episodic = MemoryRecord(content="Episodic", memory_type=MemoryType.EPISODIC)
        semantic = MemoryRecord(content="Semantic", memory_type=MemoryType.SEMANTIC)
        self.store.add(episodic)
        self.store.add(semantic)

        episodics = self.store.get_by_type(MemoryType.EPISODIC)
        assert len(episodics) == 1
        assert episodics[0].content == "Episodic"

    def test_count(self):
        """Record count should be computed correctly."""
        initial = self.store.count()
        self.store.add(MemoryRecord(content="1"))
        self.store.add(MemoryRecord(content="2"))
        assert self.store.count() == initial + 2

    def test_get_all_active(self):
        """Get only active records."""
        active = MemoryRecord(content="Active")
        pruned = MemoryRecord(content="Pruned")
        pruned.status = MemoryStatus.PRUNED

        self.store.add(active)
        self.store.add(pruned)

        all_active = self.store.get_all_active()
        contents = [m.content for m in all_active]
        assert "Active" in contents
        assert "Pruned" not in contents

    def test_serialization(self):
        """Store serialization and deserialization."""
        m1 = MemoryRecord(content="Record 1")
        m2 = MemoryRecord(content="Record 2", memory_type=MemoryType.SEMANTIC)
        self.store.add(m1)
        self.store.add(m2)

        data = self.store.to_dict()

        new_store = MemoryStore()
        new_store.load_from_dict(data)

        assert new_store.count() == 2
        restored_m1 = new_store.get(m1.id)
        assert restored_m1 is not None
        assert restored_m1.content == "Record 1"
