"""
cognitio/attention.py

Multi-Head Memory Attention mechanism.

Inspired by multi-head self-attention in Transformers,
memory records are evaluated through four distinct "heads".
Cognitive biases are added as an extra term (BiasMatrix) to the attention matrix.

Cognitio Attention formula:
    Attention(Q, K, V) = softmax(Q·Kᵀ / √d + B) · V
    B = BiasMatrix (extra term encoding cognitive biases)

Heads:
    Head 1: Semantic Relevance  — cosine similarity
    Head 2: Temporal Recency    — exponential decay (Availability Bias)
    Head 3: Emotional Resonance — emotional intensity + valence
    Head 4: Identity Anchor     — entrenchment + anchor bonus
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cognitio.memory import MemoryRecord
    from cognitio.biases import BiasEngine
    from cognitio.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class HeadWeights:
    """
    Head weights based on character maturity.

    Young character → exploratory (semantic heavy)
    Mature character → identity dominant (identity heavy)
    """

    # (semantic, temporal, emotional, identity)
    YOUNG = (0.35, 0.30, 0.20, 0.15)    # CharacterStrength < 5
    BALANCED = (0.30, 0.25, 0.20, 0.25)  # 5 ≤ CS < 15
    MATURE = (0.25, 0.20, 0.20, 0.35)    # CS ≥ 15

    @classmethod
    def for_character_strength(cls, character_strength: float) -> tuple[float, float, float, float]:
        """
        Return the appropriate weight set for the given character strength.

        Parameters:
            character_strength: Character crystallization score

        Returns:
            tuple: (w_semantic, w_temporal, w_emotional, w_identity)
        """
        if character_strength < 5:
            return cls.YOUNG
        elif character_strength < 15:
            return cls.BALANCED
        else:
            return cls.MATURE


class MultiHeadAttention:
    """
    Four-head memory attention mechanism.

    Each head evaluates a different cognitive dimension.
    Final salience = weighted sum of head weights.
    """

    MAX_EMOTIONAL_SCORE = 1.0  # Upper bound for emotional score

    def __init__(self, character_strength: float = 0.0) -> None:
        """
        Parameters:
            character_strength: Initial character strength
        """
        self.character_strength = character_strength
        self._update_weights()

    def update_character_strength(self, new_strength: float) -> None:
        """Update character strength and recompute weights."""
        self.character_strength = new_strength
        self._update_weights()

    def _update_weights(self) -> None:
        """Update head weights based on character strength."""
        self.weights = HeadWeights.for_character_strength(self.character_strength)

    def compute_salience(
        self,
        memory: "MemoryRecord",
        context_embedding: list[float],
        context_emotional_intensity: float = 0.0,
        bias_engine: "BiasEngine | None" = None,
        embedding_engine: "EmbeddingEngine | None" = None,
    ) -> float:
        """
        Compute the salience (importance) score of a memory record relative to context.

        Formula:
            Salience = Σᵢ wᵢ · headᵢ(memory, context)

        Parameters:
            memory: Memory record to evaluate
            context_embedding: Context embedding
            context_emotional_intensity: Emotional intensity of the context (0.0–1.0)
            bias_engine: BiasEngine instance (None → simple computation)
            embedding_engine: EmbeddingEngine instance (for cosine similarity)

        Returns:
            float: Salience score (0.0–1.0+)
        """
        w1, w2, w3, w4 = self.weights

        # Head 1: Semantic Relevance
        h1 = self._head_semantic(memory, context_embedding, embedding_engine)

        # Head 2: Temporal Recency (Availability Bias)
        h2 = self._head_temporal(memory, bias_engine)

        # Head 3: Emotional Resonance
        h3 = self._head_emotional(memory, context_emotional_intensity, bias_engine)

        # Head 4: Identity Anchor (Confirmation Bias + Anchoring)
        h4 = self._head_identity(memory, bias_engine)

        salience = w1 * h1 + w2 * h2 + w3 * h3 + w4 * h4

        logger.debug(
            f"Salience {memory.id[:8]}: H1={h1:.3f}, H2={h2:.3f}, "
            f"H3={h3:.3f}, H4={h4:.3f} → {salience:.3f}"
        )

        return salience

    def _head_semantic(
        self,
        memory: "MemoryRecord",
        context_embedding: list[float],
        embedding_engine: "EmbeddingEngine | None",
    ) -> float:
        """
        Head 1: Compute semantic relevance score.

        Cosine similarity between context embedding and memory embedding.

        Parameters:
            memory: Memory record
            context_embedding: Context embedding
            embedding_engine: EmbeddingEngine instance

        Returns:
            float: Semantic relevance score (0.0–1.0)
        """
        if memory.embedding is None or context_embedding is None:
            return 0.5  # Neutral score if no embedding

        if embedding_engine is not None:
            similarity = embedding_engine.cosine_similarity(
                memory.embedding, context_embedding
            )
            return max(0.0, similarity)

        # Fallback: simple dot product
        try:
            import numpy as np
            v1 = np.array(memory.embedding)
            v2 = np.array(context_embedding)
            norm = (np.linalg.norm(v1) * np.linalg.norm(v2))
            if norm == 0:
                return 0.0
            return float(max(0.0, np.dot(v1, v2) / norm))
        except Exception:
            return 0.5

    def _head_temporal(
        self,
        memory: "MemoryRecord",
        bias_engine: "BiasEngine | None",
    ) -> float:
        """
        Head 2: Compute temporal recency score.

        Exponential decay + Negativity Bias (negative records decay more slowly).

        Parameters:
            memory: Memory record
            bias_engine: BiasEngine instance

        Returns:
            float: Recency score (0.0–1.0)
        """
        if bias_engine is not None:
            return bias_engine.recency_score(memory)

        # Fallback: simple exponential decay
        import math
        days = memory.days_since_access()
        return math.exp(-0.007 * days)

    def _head_emotional(
        self,
        memory: "MemoryRecord",
        context_emotional_intensity: float,
        bias_engine: "BiasEngine | None",
    ) -> float:
        """
        Head 3: Compute emotional resonance score.

        Formula: emotional_intensity × (1 - |mem_emotion - context_emotion|) × emotional_weight
        Negativity Bias: Negative records are 2x stronger.

        Parameters:
            memory: Memory record
            context_emotional_intensity: Emotional intensity of the context
            bias_engine: BiasEngine instance

        Returns:
            float: Emotional resonance score (0.0–MAX_EMOTIONAL_SCORE)
        """
        # Emotional alignment: smaller |memory_emotion - context_emotion| = better
        emotional_match = 1.0 - abs(memory.emotional_intensity - context_emotional_intensity)

        # Emotional weight with Negativity Bias
        if bias_engine is not None:
            emotional_weight = bias_engine.emotional_weight(memory)
        else:
            emotional_weight = 1.0 + memory.emotional_intensity * 1.5

        score = memory.emotional_intensity * emotional_match * emotional_weight
        return min(score, self.MAX_EMOTIONAL_SCORE)

    def _head_identity(
        self,
        memory: "MemoryRecord",
        bias_engine: "BiasEngine | None",
    ) -> float:
        """
        Head 4: Compute identity anchor score.

        Formula: entrenchment × 0.7 + anchor_bonus × 0.3
        Combination of Confirmation Bias + Anchoring Bias.

        Parameters:
            memory: Memory record
            bias_engine: BiasEngine instance

        Returns:
            float: Identity score (0.0–1.0)
        """
        if bias_engine is not None:
            return bias_engine.identity_score(memory)

        # Fallback
        anchor_bonus = 0.15 if memory.is_anchor else 0.0
        return memory.entrenchment * 0.7 + anchor_bonus * 0.3

    def rank_memories(
        self,
        memories: list["MemoryRecord"],
        context_embedding: list[float],
        context_emotional_intensity: float = 0.0,
        bias_engine: "BiasEngine | None" = None,
        embedding_engine: "EmbeddingEngine | None" = None,
        top_k: int = 10,
    ) -> list[tuple["MemoryRecord", float]]:
        """
        Sort a memory list by salience and return the top_k.

        Parameters:
            memories: Memory records to rank
            context_embedding: Context embedding
            context_emotional_intensity: Emotional intensity of the context
            bias_engine: BiasEngine instance
            embedding_engine: EmbeddingEngine instance
            top_k: Maximum number of records to return

        Returns:
            list[tuple[MemoryRecord, float]]: (record, score) pairs in descending score order
        """
        scored = []
        for memory in memories:
            score = self.compute_salience(
                memory,
                context_embedding,
                context_emotional_intensity,
                bias_engine,
                embedding_engine,
            )
            scored.append((memory, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
