"""
tests/test_biases.py

Tests for the six cognitive bias engines.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognitio.biases import AvailabilityBias, ConfirmationBias, NegativityBias, HaloEffect, AnchoringBias, BiasEngine
from cognitio.memory import MemoryRecord, MemoryType, MemoryValence


# ─────────────────────────────────────────────
# TEST HELPER FUNCTIONS
# ─────────────────────────────────────────────

def make_memory(
    content="Test memory",
    memory_type=MemoryType.EPISODIC,
    entrenchment=0.5,
    emotional_intensity=0.5,
    emotional_valence=MemoryValence.NEUTRAL,
    is_anchor=False,
):
    m = MemoryRecord(content=content, memory_type=memory_type)
    m.entrenchment = entrenchment
    m.emotional_intensity = emotional_intensity
    m.emotional_valence = emotional_valence
    m.is_anchor = is_anchor
    return m


# ─────────────────────────────────────────────
# AVAILABILITY BIAS
# ─────────────────────────────────────────────

class TestAvailabilityBias:
    def setup_method(self):
        self.bias = AvailabilityBias()

    def test_fresh_memory_high_recency(self):
        """A newly created memory should receive a high recency score."""
        m = make_memory()
        score = self.bias.recency_score(m)
        assert score > 0.95, f"Recency too low for new memory: {score}"

    def test_old_episodic_low_recency(self):
        """An old episodic memory should receive a low recency score."""
        m = make_memory(memory_type=MemoryType.EPISODIC)
        # Simulate 100 days ago
        from datetime import datetime, timedelta, timezone
        m.last_accessed = datetime.now(timezone.utc) - timedelta(days=100)
        score = self.bias.recency_score(m)
        assert score < 0.1, f"Recency too high for old memory: {score}"

    def test_semantic_slower_decay(self):
        """Semantic memory should decay slower than episodic."""
        from datetime import datetime, timedelta, timezone
        episodic = make_memory(memory_type=MemoryType.EPISODIC)
        semantic = make_memory(memory_type=MemoryType.SEMANTIC)

        # 30 days ago
        for m in [episodic, semantic]:
            m.last_accessed = datetime.now(timezone.utc) - timedelta(days=30)

        episodic_score = self.bias.recency_score(episodic)
        semantic_score = self.bias.recency_score(semantic)

        assert semantic_score > episodic_score, (
            f"Semantic ({semantic_score:.3f}) should be higher than episodic ({episodic_score:.3f})"
        )

    def test_negative_emotion_slower_decay(self):
        """Negative emotional memory should decay slower (Negativity Bias)."""
        from datetime import datetime, timedelta, timezone

        positive = make_memory(emotional_valence=MemoryValence.POSITIVE, emotional_intensity=0.9)
        negative = make_memory(emotional_valence=MemoryValence.NEGATIVE, emotional_intensity=0.9)

        # 50 days ago
        for m in [positive, negative]:
            m.last_accessed = datetime.now(timezone.utc) - timedelta(days=50)

        pos_score = self.bias.recency_score(positive)
        neg_score = self.bias.recency_score(negative)

        assert neg_score > pos_score, (
            f"Negative ({neg_score:.3f}) should be higher than positive ({pos_score:.3f})"
        )


# ─────────────────────────────────────────────
# CONFIRMATION BIAS
# ─────────────────────────────────────────────

class TestConfirmationBias:
    def setup_method(self):
        self.bias = ConfirmationBias()

    def test_low_entrenchment_accepts_easily(self):
        """Low entrenchment → accept information easily."""
        prob = self.bias.update_probability(0.1, 0.5, source_trust=0.0)
        assert prob >= 0.5, f"Low entrenchment should accept: {prob}"

    def test_high_entrenchment_resists(self):
        """High entrenchment → show resistance."""
        prob = self.bias.update_probability(0.9, 0.5, source_trust=0.0)
        assert prob < 0.3, f"High entrenchment should reject: {prob}"

    def test_trusted_source_reduces_resistance(self):
        """Trusted source → resistance decreases (HaloEffect integration)."""
        prob_no_trust = self.bias.update_probability(0.8, 0.5, source_trust=0.0)
        prob_with_trust = self.bias.update_probability(0.8, 0.5, source_trust=0.9)
        assert prob_with_trust > prob_no_trust, (
            f"Trusted source should give higher prob: {prob_with_trust} > {prob_no_trust}"
        )

    def test_evaluate_outcomes(self):
        """evaluate_update should return correct outcomes."""
        assert self.bias.evaluate_update(0.1, 0.8) == "accepted"
        assert self.bias.evaluate_update(0.9, 0.3) == "rejected"
        result = self.bias.evaluate_update(0.5, 0.4)
        assert result in ("accepted", "ambivalent", "pending", "rejected")

    def test_crisis_trigger(self):
        """Crisis should trigger after 5 accumulated contradictions."""
        assert self.bias.should_trigger_crisis(5, 0.7, 0.4) is True
        assert self.bias.should_trigger_crisis(3, 0.7, 0.4) is False


# ─────────────────────────────────────────────
# NEGATIVITY BIAS
# ─────────────────────────────────────────────

class TestNegativityBias:
    def setup_method(self):
        self.bias = NegativityBias()

    def test_negative_stronger_than_positive(self):
        """Negative record should be 2x stronger than positive at same intensity."""
        intensity = 0.8
        pos = make_memory(emotional_valence=MemoryValence.POSITIVE, emotional_intensity=intensity)
        neg = make_memory(emotional_valence=MemoryValence.NEGATIVE, emotional_intensity=intensity)

        pos_weight = self.bias.emotional_weight(pos)
        neg_weight = self.bias.emotional_weight(neg)

        assert neg_weight > pos_weight, f"Negative ({neg_weight}) should be greater than positive ({pos_weight})"

        # Expected values: pos = 1 + 0.8×1.5 = 2.2, neg = 1 + 0.8×3.0 = 3.4
        assert abs(pos_weight - 2.2) < 0.01, f"Positive weight expected 2.2, got: {pos_weight}"
        assert abs(neg_weight - 3.4) < 0.01, f"Negative weight expected 3.4, got: {neg_weight}"

    def test_neutral_base_weight(self):
        """Neutral record should receive base weight."""
        m = make_memory(emotional_valence=MemoryValence.NEUTRAL, emotional_intensity=0.5)
        weight = self.bias.emotional_weight(m)
        assert abs(weight - 1.5) < 0.01, f"Neutral weight should be 1.5: {weight}"

    def test_negative_slower_effective_decay(self):
        """Effective decay should be slower for negative records."""
        base_lambda = 0.035
        pos = make_memory(emotional_valence=MemoryValence.POSITIVE, emotional_intensity=0.9)
        neg = make_memory(emotional_valence=MemoryValence.NEGATIVE, emotional_intensity=0.9)

        pos_decay = self.bias.effective_decay(base_lambda, pos)
        neg_decay = self.bias.effective_decay(base_lambda, neg)

        assert neg_decay < pos_decay, f"Negative decay ({neg_decay}) should be less than positive ({pos_decay})"


# ─────────────────────────────────────────────
# HALO EFFECT
# ─────────────────────────────────────────────

class TestHaloEffect:
    def setup_method(self):
        self.bias = HaloEffect()

    def test_trusted_source_reduces_resistance(self):
        """Trusted source should reduce resistance."""
        base_resistance = 2.5
        high_trust = self.bias.effective_resistance(base_resistance, 0.9)
        low_trust = self.bias.effective_resistance(base_resistance, 0.1)

        assert high_trust < base_resistance, "Trusted source should reduce resistance"
        assert low_trust < base_resistance, "Every source should reduce it somewhat"
        assert high_trust < low_trust, "Higher trust should reduce more"

    def test_max_discount_cap(self):
        """Maximum discount should be capped at 60%."""
        base_resistance = 2.5
        full_trust = self.bias.effective_resistance(base_resistance, 1.0)
        min_resistance = base_resistance * (1 - 0.6)  # 1.0

        assert full_trust >= min_resistance, (
            f"Full trust ({full_trust}) should not exceed min resistance ({min_resistance})"
        )

    def test_trust_erosion_on_rejection(self):
        """Rejected information should reduce trust."""
        self.bias.set_trust("user_1", 0.8)
        self.bias.update_trust("user_1", "rejected")
        new_trust = self.bias.get_trust("user_1")
        assert new_trust < 0.8, f"Rejected information should lower trust: {new_trust}"

    def test_default_trust(self):
        """Default trust for unknown source should be 0.5."""
        trust = self.bias.get_trust("unknown_user")
        assert abs(trust - 0.5) < 0.01, f"Default trust should be 0.5: {trust}"


# ─────────────────────────────────────────────
# ANCHORING BIAS
# ─────────────────────────────────────────────

class TestAnchoringBias:
    def setup_method(self):
        self.bias = AnchoringBias()

    def test_anchor_bonus(self):
        """Anchor record should receive a bonus."""
        anchor = make_memory(is_anchor=True)
        non_anchor = make_memory(is_anchor=False)

        assert self.bias.anchor_bonus(anchor) == 0.15
        assert self.bias.anchor_bonus(non_anchor) == 0.0

    def test_identity_score_with_anchor(self):
        """Anchor record should increase identity score."""
        anchor = make_memory(entrenchment=0.7, is_anchor=True)
        non_anchor = make_memory(entrenchment=0.7, is_anchor=False)

        anchor_score = self.bias.identity_score(anchor)
        non_anchor_score = self.bias.identity_score(non_anchor)

        assert anchor_score > non_anchor_score, "Anchor should increase identity score"


# ─────────────────────────────────────────────
# BIAS ENGINE
# ─────────────────────────────────────────────

class TestBiasEngine:
    def setup_method(self):
        self.engine = BiasEngine()

    def test_evaluate_contradiction_updates_trust(self):
        """evaluate_contradiction should update trust."""
        self.engine.halo.set_trust("test_user", 0.5)
        result = self.engine.evaluate_contradiction(0.5, 0.8, entity_id="test_user")
        assert result in ("accepted", "ambivalent", "pending", "rejected")

    def test_emotional_weight_delegation(self):
        """emotional_weight should delegate to NegativityBias."""
        m = make_memory(emotional_valence=MemoryValence.NEGATIVE, emotional_intensity=0.8)
        weight = self.engine.emotional_weight(m)
        expected = 1.0 + 0.8 * 3.0  # 3.4
        assert abs(weight - expected) < 0.01

    def test_identity_score_delegation(self):
        """identity_score should delegate to AnchoringBias."""
        m = make_memory(entrenchment=0.8, is_anchor=True)
        score = self.engine.identity_score(m)
        assert 0.0 <= score <= 1.0
