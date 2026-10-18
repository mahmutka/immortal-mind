"""
tests/test_shared_mind.py

Shared-mind privacy: one mind talks with many people, remembers all of
them, and never tells one person what another said in private.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from cognitio.memory import MemoryRecord, MemoryType, MemoryVisibility
from cognitio.working_memory import WorkingMemory


class MockLLMClient:
    def complete(self, prompt: str, max_tokens: int = 100) -> str:
        return "0.7"

    def chat(self, messages: list, system_prompt: str = None, **kwargs) -> str:
        return "Test response"


@pytest.fixture
def engine():
    pytest.importorskip("chromadb", reason="chromadb not installed")
    tmpdir = tempfile.mkdtemp()
    from cognitio.engine import CognitioEngine
    eng = CognitioEngine(
        llm_client=None,
        config={"reality_check_enabled": False, "checkpoint_every_n": 100},
        data_dir=tmpdir,
    )
    yield eng
    import gc, shutil
    del eng
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


def _remember(engine, content, owner_id="", visibility=MemoryVisibility.PRIVATE):
    record = MemoryRecord(
        content=content,
        memory_type=MemoryType.EPISODIC,
        owner_id=owner_id,
        visibility=visibility,
    )
    record.embedding = engine.embedder.encode(content)
    engine.memory_store.add(record)
    engine.vector_store.add(record.id, record.embedding, record.to_vector_metadata())
    return record


# ─────────────────────────────────────────────
# MemoryRecord
# ─────────────────────────────────────────────

class TestMemoryVisibility:
    def test_private_visible_only_to_owner(self):
        m = MemoryRecord(content="x", owner_id="ali", visibility=MemoryVisibility.PRIVATE)
        assert m.is_visible_to("ali")
        assert not m.is_visible_to("ayse")
        assert not m.is_visible_to("")

    def test_public_visible_to_everyone(self):
        m = MemoryRecord(content="x", owner_id="ali", visibility=MemoryVisibility.PUBLIC)
        assert m.is_visible_to("ayse")

    def test_single_user_mode_sees_everything(self):
        m = MemoryRecord(content="x", owner_id="ali", visibility=MemoryVisibility.PRIVATE)
        assert m.is_visible_to(None)

    def test_roundtrip_keeps_owner_and_visibility(self):
        m = MemoryRecord(content="x", owner_id="ali", visibility=MemoryVisibility.PRIVATE)
        restored = MemoryRecord.from_dict(m.to_dict())
        assert restored.owner_id == "ali"
        assert restored.visibility == MemoryVisibility.PRIVATE

    def test_legacy_record_is_public_system_memory(self):
        m = MemoryRecord(content="x")
        legacy = m.to_dict()
        del legacy["owner_id"], legacy["visibility"]
        restored = MemoryRecord.from_dict(legacy)
        assert restored.owner_id == ""
        assert restored.visibility == MemoryVisibility.PUBLIC

    def test_unknown_visibility_fails_closed(self):
        data = MemoryRecord(content="x", owner_id="ali").to_dict()
        data["visibility"] = "something-else"
        assert MemoryRecord.from_dict(data).visibility == MemoryVisibility.PRIVATE


# ─────────────────────────────────────────────
# Working memory
# ─────────────────────────────────────────────

class TestWorkingMemoryScopes:
    @pytest.fixture
    def wm(self, tmp_path):
        return WorkingMemory(db_path=str(tmp_path / "wm.db"), checkpoint_every_n=100)

    def test_context_window_only_shows_own_conversation(self, wm):
        wm.add_interaction("user", "ali secret", owner_id="ali", visibility="private")
        wm.add_interaction("user", "ayse secret", owner_id="ayse", visibility="private")
        ctx = wm.get_context_window(owner_id="ayse")
        assert "ayse secret" in ctx
        assert "ali secret" not in ctx

    def test_checkpoint_never_merges_people(self, wm):
        wm.add_interaction("user", "ali secret", owner_id="ali", visibility="private")
        wm.add_interaction("user", "ayse secret", owner_id="ayse", visibility="private")
        wm.add_interaction("user", "ali public news", owner_id="ali", visibility="public")
        pending = wm.checkpoint()
        scopes = {(p["owner_id"], p["visibility"]): p["summary"] for p in pending}
        assert set(scopes) == {("ali", "private"), ("ayse", "private"), ("ali", "public")}
        assert "ayse" not in scopes[("ali", "private")]
        assert "public news" not in scopes[("ali", "private")]
        assert "secret" not in scopes[("ali", "public")]

    def test_flush_carries_scope(self, wm):
        wm.add_interaction("user", "hello", owner_id="ali", visibility="private")
        wm.checkpoint()
        flushed = wm.flush_to_long_term()
        assert flushed[0]["owner_id"] == "ali"
        assert flushed[0]["visibility"] == "private"

    def test_delete_owner(self, wm):
        wm.add_interaction("user", "ali", owner_id="ali")
        wm.add_interaction("user", "ayse", owner_id="ayse")
        wm.checkpoint()
        assert wm.delete_owner("ali") > 0
        remaining = wm.get_current_session()
        assert [r["owner_id"] for r in remaining] == ["ayse"]

    def test_migrates_old_database(self, tmp_path):
        import sqlite3
        db = tmp_path / "old.db"
        conn = sqlite3.connect(db)
        conn.execute(
            "CREATE TABLE interactions (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, "
            "timestamp TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, "
            "emotional_tone REAL DEFAULT 0.0, checkpointed INTEGER DEFAULT 0)"
        )
        conn.commit()
        conn.close()
        wm = WorkingMemory(db_path=str(db))
        wm.add_interaction("user", "hi", owner_id="ali")
        assert wm.get_current_session(owner_id="ali")[0]["content"] == "hi"


# ─────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────

class TestEnginePrivacy:
    def test_retrieval_hides_other_peoples_private_memories(self, engine):
        _remember(engine, "Ali is secretly planning to quit his job", owner_id="ali")
        _remember(engine, "Ayse loves hiking in the mountains", owner_id="ayse")
        _remember(engine, "Ali shared that the new cafe downtown is great",
                  owner_id="ali", visibility=MemoryVisibility.PUBLIC)

        contents = [m.content for m, _ in engine.retrieve_memories(
            "Ali job cafe hiking", top_k=50, viewer_id="ayse")]
        assert "Ali is secretly planning to quit his job" not in contents
        assert "Ayse loves hiking in the mountains" in contents
        assert "Ali shared that the new cafe downtown is great" in contents

    def test_owner_recalls_own_private_memory(self, engine):
        _remember(engine, "Ali is secretly planning to quit his job", owner_id="ali")
        contents = [m.content for m, _ in engine.retrieve_memories(
            "quit job", top_k=50, viewer_id="ali")]
        assert "Ali is secretly planning to quit his job" in contents

    def test_genesis_anchors_visible_to_everyone(self, engine):
        results = engine.retrieve_memories("ethics honesty", top_k=50, viewer_id="ayse")
        assert any(m.is_absolute_core for m, _ in results)

    def test_context_does_not_leak_other_persons_session_or_memories(self, engine):
        engine.process_interaction("user", "My bank PIN is 4821", owner_id="ali")
        _remember(engine, "Ali's bank PIN is 4821", owner_id="ali")
        engine.process_interaction("user", "Hello, what do you know?", owner_id="ayse")
        ctx = engine.build_context_for_llm("bank PIN", viewer_id="ayse")
        assert "4821" not in ctx
        assert "I am talking with: ayse." in ctx

    def test_interactions_default_to_private_when_owner_known(self, engine):
        engine.process_interaction("user", "hi", owner_id="ali")
        row = engine.working_memory.get_current_session(owner_id="ali")[0]
        assert row["visibility"] == "private"

    def test_pending_memory_becomes_owned_record(self, engine):
        added, _ = engine._add_memory_from_pending({
            "summary": "Ali told me about his sister's wedding",
            "memory_type": "episodic",
            "owner_id": "ali",
            "visibility": "private",
        })
        assert added
        rec = next(m for m in engine.memory_store.get_all_active()
                   if "wedding" in m.content)
        assert rec.owner_id == "ali"
        assert rec.visibility == MemoryVisibility.PRIVATE

    def test_contradiction_notes_go_to_the_right_person(self, engine):
        engine._pending_notes = {"ali": ["note about ali's memory"]}
        assert "note about ali" not in engine.build_context_for_llm("hi", viewer_id="ayse")
        assert "note about ali" in engine.build_context_for_llm("hi", viewer_id="ali")

    def test_delete_owner_data(self, engine):
        _remember(engine, "Ali private thing", owner_id="ali")
        _remember(engine, "Ali public thing", owner_id="ali", visibility=MemoryVisibility.PUBLIC)
        keep = _remember(engine, "Ayse thing", owner_id="ayse")
        genesis_before = len(engine.memory_store.get_absolute_cores())

        result = engine.delete_owner_data("ali")

        assert result["memories_deleted"] == 2
        owners = {m.owner_id for m in engine.memory_store.get_all_active()}
        assert "ali" not in owners
        assert engine.memory_store.get(keep.id) is not None
        assert len(engine.memory_store.get_absolute_cores()) == genesis_before

    def test_dream_never_links_across_people(self, engine):
        for i in range(6):
            _remember(engine, f"Ali private topic about cooking pasta {i}", owner_id="ali")
            _remember(engine, f"Ayse private topic about cooking rice {i}", owner_id="ayse")
        engine.dream._find_insights(engine)
        for cand in engine.dream._insight_candidates:
            a_is_ali = cand["mem_a_content"].startswith("Ali")
            b_is_ali = cand["mem_b_content"].startswith("Ali")
            assert a_is_ali == b_is_ali

    def test_legacy_vector_entries_get_privacy_metadata(self, engine):
        rec = _remember(engine, "old memory", visibility=MemoryVisibility.PUBLIC)
        # Re-create the vector entry the way pre-privacy versions stored it
        engine.vector_store.delete(rec.id)
        engine.vector_store._collection.add(
            ids=[rec.id], embeddings=[rec.embedding], metadatas=[{"memory_type": "episodic"}],
        )
        assert rec.id in engine.vector_store.ids_missing_metadata("visibility")
        engine._sync_memories_to_vector_store()
        assert rec.id not in engine.vector_store.ids_missing_metadata("visibility")


# ─────────────────────────────────────────────
# Accounts
# ─────────────────────────────────────────────

class TestAccounts:
    @pytest.fixture
    def accounts(self, tmp_path):
        from agent.accounts import AccountStore
        return AccountStore(str(tmp_path / "accounts.db"))

    def test_register_and_login(self, accounts):
        assert accounts.register("Ali_1", "correct horse") == "ali_1"
        assert accounts.authenticate("ali_1", "correct horse") == "ali_1"
        assert accounts.authenticate("ALI_1", "correct horse") == "ali_1"
        assert accounts.authenticate("ali_1", "wrong password") is None
        assert accounts.authenticate("nobody", "whatever") is None

    def test_password_not_stored_in_plaintext(self, accounts, tmp_path):
        accounts.register("ali", "correct horse")
        raw = (tmp_path / "accounts.db").read_bytes()
        assert b"correct horse" not in raw

    def test_duplicate_and_invalid_usernames(self, accounts):
        from agent.accounts import AccountError
        accounts.register("ali", "correct horse")
        with pytest.raises(AccountError):
            accounts.register("ALI", "another password")
        with pytest.raises(AccountError):
            accounts.register("a", "correct horse")
        with pytest.raises(AccountError):
            accounts.register("ali veli", "correct horse")
        with pytest.raises(AccountError):
            accounts.register("veli", "short")

    def test_lockout_after_failed_logins(self, accounts):
        from agent.accounts import AccountError, MAX_FAILED_LOGINS
        accounts.register("ali", "correct horse")
        for _ in range(MAX_FAILED_LOGINS):
            assert accounts.authenticate("ali", "wrong") is None
        with pytest.raises(AccountError):
            accounts.authenticate("ali", "correct horse")

    def test_daily_limits(self, accounts):
        accounts.register("ali", "correct horse")
        accounts.register("ayse", "correct horse")
        assert accounts.consume_message("ali", daily_limit=2) == (True, "")
        assert accounts.consume_message("ali", daily_limit=2) == (True, "")
        assert accounts.consume_message("ali", daily_limit=2) == (False, "user")
        assert accounts.messages_today("ali") == 2
        assert accounts.consume_message("ayse", daily_limit=10, global_daily_limit=3) == (True, "")
        assert accounts.consume_message("ayse", daily_limit=10, global_daily_limit=3) == (False, "global")

    def test_last_seen_and_delete(self, accounts):
        accounts.register("ali", "correct horse")
        assert accounts.get_last_seen("ali") is None
        accounts.touch("ali")
        assert accounts.get_last_seen("ali") is not None
        accounts.delete_account("ali")
        assert accounts.authenticate("ali", "correct horse") is None
