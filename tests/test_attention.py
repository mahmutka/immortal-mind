"""
tests/test_attention.py

MultiHeadAttention tests — cognitive salience computation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from cognitio.attention import MultiHeadAttention, HeadWeights
from cognitio.memory import MemoryRecord, MemoryType, MemoryValence


def make_memory_with_embedding(content="Test", embedding=None, **kwargs):
    m = MemoryRecord(content=content)
    for k, v in kwargs.items():
        setattr(m, k, v)
    m.embedding = embedding or [0.5] * 384
    return m


class TestHeadWeights:
    def test_young_character(self):
        """Young character should receive explorer weights."""
        weights = HeadWeights.for_character_strength(2.0)
        assert weights == (0.35, 0.30, 0.20, 0.15)

    def test_balanced_character(self):
        """Balanced character should receive balanced weights."""
        weights = HeadWeights.for_character_strength(10.0)
        assert weights == (0.30, 0.25, 0.20, 0.25)

    def test_mature_character(self):
        """Mature character should receive identity-dominant weights."""
        weights = HeadWeights.for_character_strength(20.0)
        assert weights == (0.25, 0.20, 0.20, 0.35)


class TestMultiHeadAttention:
    def setup_method(self):
        self.attention = MultiHeadAttention(character_strength=5.0)

    def test_compute_salience_returns_float(self):
        """compute_salience should return a float."""
        m = make_memory_with_embedding(embedding=[1.0] + [0.0] * 383)
        context_emb = [1.0] + [0.0] * 383
        score = self.attention.compute_salience(m, context_emb)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_high_semantic_similarity_high_salience(self):
        """Same embedding → high salience."""
        embedding = [0.5] * 384
        m = make_memory_with_embedding(embedding=embedding)
        score = self.attention.compute_salience(m, embedding)
        assert score > 0.3, f"High similarity should give high salience: {score}"

    def test_anchor_increases_salience(self):
        """Anchor record should receive higher salience."""
        embedding = [0.5] * 384
        anchor = make_memory_with_embedding(
            embedding=embedding,
            is_anchor=True,
            entrenchment=0.8,
        )
        non_anchor = make_memory_with_embedding(
            embedding=embedding,
            is_anchor=False,
            entrenchment=0.8,
        )

        anchor_score = self.attention.compute_salience(anchor, embedding)
        non_anchor_score = self.attention.compute_salience(non_anchor, embedding)

        assert anchor_score >= non_anchor_score, "Anchor should receive higher salience"

    def test_rank_memories_returns_top_k(self):
        """rank_memories should return top_k records."""
        memories = [
            make_memory_with_embedding(content=f"Memory {i}", embedding=[float(i % 5) / 10] * 384)
            for i in range(20)
        ]
        context_emb = [0.3] * 384

        ranked = self.attention.rank_memories(memories, context_emb, top_k=5)
        assert len(ranked) == 5
        assert all(isinstance(score, float) for _, score in ranked)

    def test_rank_memories_descending_order(self):
        """rank_memories should return in descending score order."""
        memories = [
            make_memory_with_embedding(content=f"Memory {i}")
            for i in range(10)
        ]
        context_emb = [0.5] * 384
        ranked = self.attention.rank_memories(memories, context_emb, top_k=10)

        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True), "Score order should be descending"

    def test_character_strength_updates_weights(self):
        """update_character_strength should update head weights."""
        self.attention.update_character_strength(0.0)
        assert self.attention.weights == (0.35, 0.30, 0.20, 0.15)

        self.attention.update_character_strength(20.0)
        assert self.attention.weights == (0.25, 0.20, 0.20, 0.35)
