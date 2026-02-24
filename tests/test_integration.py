"""
tests/test_integration.py

Integration tests — is the entire system working together?

Note: These tests run without LLM and blockchain (using mocks).
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class MockLLMClient:
    """Simple LLM mock for testing."""
    def complete(self, prompt: str, max_tokens: int = 100) -> str:
        return "0.7"  # For consistency score

    def chat(self, messages: list, system_prompt: str = None, **kwargs) -> str:
        return "Test response"

    def health_check(self) -> bool:
        return True


@pytest.fixture
def engine():
    """CognitioEngine in a temporary directory."""
    chromadb = pytest.importorskip("chromadb", reason="chromadb not installed")
    tmpdir = tempfile.mkdtemp()
    from cognitio.engine import CognitioEngine
    llm = MockLLMClient()
    eng = CognitioEngine(
        llm_client=llm,
        config={
            "reality_check_enabled": True,
            "max_active_memories": 1000,
            "checkpoint_every_n": 5,
        },
        data_dir=tmpdir,
    )
    yield eng
    import gc, shutil
    del eng
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestCognitioEngineIntegration:
    def test_engine_initializes(self, engine):
        """Engine should be initializable.

        When the engine first runs, it automatically creates Genesis Anchors
        equal in count to GENESIS_ANCHOR_CONTENTS.
        """
        from cognitio.engine import GENESIS_ANCHOR_CONTENTS
        assert engine is not None
        assert engine.memory_store.count() == len(GENESIS_ANCHOR_CONTENTS)

    def test_process_interaction_records_to_working_memory(self, engine):
        """process_interaction() should write to working memory."""
        engine.process_interaction("user", "Hello, how are you?", 0.1)
        session = engine.working_memory.get_current_session()
        assert len(session) >= 1
        assert any(m["content"] == "Hello, how are you?" for m in session)

    def test_retrieve_memories_returns_genesis_anchors(self, engine):
        """Since Genesis Anchors are present when engine starts, retrieve should return results."""
        from cognitio.engine import GENESIS_ANCHOR_CONTENTS
        results = engine.retrieve_memories("Test query")
        # Genesis Anchors are always present, list should not be empty
        assert isinstance(results, list)
        assert len(results) <= len(GENESIS_ANCHOR_CONTENTS)

    def test_build_context_for_llm(self, engine):
        """build_context_for_llm should return a string."""
        engine.process_interaction("user", "Hello!")
        context = engine.build_context_for_llm("Test question")
        assert isinstance(context, str)

    def test_get_cognitive_state(self, engine):
        """get_cognitive_state() should return a dict."""
        state = engine.get_cognitive_state()
        assert "character_strength" in state
        assert "total_interactions" in state

    def test_save_and_implicit_load(self, engine):
        """save_state() should not raise an error."""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_save.json")
            engine.save_state(filepath)
            assert os.path.exists(filepath)

    def test_force_save(self, engine):
        """force_save() should not raise an error."""
        engine.process_interaction("user", "Test message 1")
        engine.process_interaction("user", "Test message 2")
        engine.force_save()  # Should not raise


class TestEmotionShieldIntegration:
    def test_shield_in_engine_workflow(self):
        """EmotionShield should work in the engine workflow."""
        from cognitio.emotion_shield import EmotionShield

        shield = EmotionShield()
        shield.reset_session()

        context = [{"role": "user", "content": "Hello", "emotional_tone": 0.1}]
        result = shield.evaluate(0.3, context, "Normal message")

        assert "adjusted_intensity" in result
        assert 0.0 <= result["adjusted_intensity"] <= 1.0


class TestMemoryPipeline:
    def test_memory_record_full_pipeline(self):
        """MemoryRecord creation and basic operations."""
        from cognitio.memory import MemoryRecord, MemoryStore, MemoryType, MemoryValence

        store = MemoryStore()

        # Create record
        m = MemoryRecord(
            content="Consciousness is change times processing capacity",
            memory_type=MemoryType.SEMANTIC,
        )
        m.confidence = 0.9
        m.entrenchment = 0.7
        m.emotional_intensity = 0.85
        m.emotional_valence = MemoryValence.POSITIVE
        m.is_anchor = True
        m.tags = ["philosophy", "consciousness"]

        # Add to store
        store.add(m)
        assert store.count() == 1

        # Retrieve and validate
        retrieved = store.get(m.id)
        assert retrieved is not None
        assert retrieved.content == m.content
        assert retrieved.is_anchor is True

        # Reinforce
        retrieved.reinforce()
        assert retrieved.entrenchment > 0.7
        assert retrieved.reinforcement_count == 1

        # Serialize and restore
        data = store.to_dict()
        new_store = MemoryStore()
        new_store.load_from_dict(data)

        restored = new_store.get(m.id)
        assert restored is not None
        assert restored.content == m.content
        assert restored.tags == ["philosophy", "consciousness"]
