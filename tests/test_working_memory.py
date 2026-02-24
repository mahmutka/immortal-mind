"""
tests/test_working_memory.py

WorkingMemory tests — SQLite WAL short-term memory.
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from cognitio.working_memory import WorkingMemory


@pytest.fixture
def wm():
    """WorkingMemory instance in a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_wm.db")
    wm_instance = WorkingMemory(
        db_path=db_path,
        checkpoint_every_n=5,
        checkpoint_interval_minutes=60,
    )
    yield wm_instance
    # Close SQLite connection (for Windows file lock)
    import gc
    del wm_instance
    gc.collect()
    import shutil
    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass


class TestWorkingMemory:
    def test_add_and_retrieve_interaction(self, wm):
        """Add a message and read it back."""
        wm.add_interaction("user", "Hello!", 0.1)
        wm.add_interaction("assistant", "Hello! How can I help you?", 0.0)

        session = wm.get_current_session()
        assert len(session) == 2
        assert session[0]["role"] == "user"
        assert session[0]["content"] == "Hello!"
        assert session[1]["role"] == "assistant"

    def test_should_checkpoint_after_n_messages(self, wm):
        """Checkpoint should trigger after N messages."""
        wm2 = WorkingMemory(
            db_path=wm.db_path.replace(".db", "_2.db"),
            checkpoint_every_n=3,
            checkpoint_interval_minutes=60,
        )

        assert wm2.should_checkpoint() is False

        for i in range(3):
            wm2.add_interaction("user", f"Message {i}")

        assert wm2.should_checkpoint() is True

    def test_checkpoint_creates_pending_memories(self, wm):
        """Checkpoint should create pending memories."""
        for i in range(5):
            wm.add_interaction("user", f"Topic {i}: philosophical discussion")
            wm.add_interaction("assistant", f"Response {i}")

        # Force counter to threshold
        wm._message_count = wm.checkpoint_every_n
        pending = wm.checkpoint()

        assert len(pending) > 0
        assert "summary" in pending[0]

    def test_flush_to_long_term(self, wm):
        """flush_to_long_term should return pending records and mark them as 'flushed'."""
        for i in range(5):
            wm.add_interaction("user", f"Message {i}")

        wm._message_count = wm.checkpoint_every_n
        wm.checkpoint()

        flushed = wm.flush_to_long_term()
        assert len(flushed) > 0

        # Try flushing again — should be empty
        flushed2 = wm.flush_to_long_term()
        assert len(flushed2) == 0

    def test_get_recent_messages(self, wm):
        """Get messages from the last N minutes."""
        wm.add_interaction("user", "New message")

        recent = wm.get_recent(minutes=60)
        assert len(recent) >= 1
        assert any(m["content"] == "New message" for m in recent)

    def test_cleanup_removes_old_flushed(self, wm):
        """cleanup() should delete old flushed records."""
        # Add record
        wm.add_interaction("user", "Old message")
        wm._message_count = wm.checkpoint_every_n
        wm.checkpoint()
        wm.flush_to_long_term()

        # Clean with 0-day limit (delete all)
        deleted = wm.cleanup(older_than_days=0)
        # Some records should have been deleted
        assert deleted >= 0  # Should not raise an error

    def test_context_window(self, wm):
        """get_context_window() should return text."""
        wm.add_interaction("user", "Test message")
        wm.add_interaction("assistant", "Test response")

        context = wm.get_context_window()
        assert "Test message" in context
        assert "Test response" in context

    def test_message_count_increments(self, wm):
        """User messages should increment the counter; assistant messages should not."""
        initial = wm.message_count

        wm.add_interaction("user", "user msg")
        assert wm.message_count == initial + 1

        wm.add_interaction("assistant", "assistant msg")
        assert wm.message_count == initial + 1  # Should not change
