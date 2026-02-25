"""
cognitio/biases.py

Six cognitive bias engines.

Human cognitive biases are intentionally injected into the AI memory system.
This is not a "bug" but a "feature" — biases are compasses in a sea of information.

Biases:
    1. AvailabilityBias       — Weight recent experiences more heavily
    2. ConfirmationBias       — Stabilize established beliefs
    3. NegativityBias         — Record negative experiences more strongly
    4. HaloEffect             — Trust sources that have earned trust
    5. AnchoringBias          — First experiences create reference points
    6. EmotionalAmplification — Amplify emotional experiences (integrated with NegativityBias)
"""

import logging
import math
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from cognitio.memory import MemoryRecord, MemoryValence

logger = logging.getLogger(__name__)


class AvailabilityBias:
    """
    Availability Bias.

    Recent experiences appear more important than older ones.
    Modelled with exponential decay.

    Human function: Highlights recent dangers (survival advantage).
    Protocol function: Weights recent experiences → dynamic adaptation.
    """

    # Decay constants per memory type (unit: day^-1)
    DECAY_RATES: dict[str, float] = {
        "episodic": 0.035,     # Half-life ~20 days
        "semantic": 0.007,     # Half-life ~100 days
        "emotional": 0.010,    # Half-life ~70 days
        "procedural": 0.003,   # Half-life ~230 days
        "relational": 0.005,   # Half-life ~140 days
        "evolution": 0.001,    # Half-life ~700 days
    }

    def recency_score(self, memory: "MemoryRecord") -> float:
        """
        Compute the recency score of a memory record.

        Formula: e^(-λ · Δt)
        Δt = days since last access
        λ = decay constant per memory type

        Parameters:
            memory: Memory record to evaluate

        Returns:
            float: Recency score (0.0–1.0)
        """
        days = memory.days_since_access()
        lambda_base = self.DECAY_RATES.get(memory.memory_type.value, 0.007)

        # Emotional intensity slows decay
        lambda_effective = self._effective_decay(lambda_base, memory)

        score = math.exp(-lambda_effective * days)
        return max(0.0, min(1.0, score))

    def _effective_decay(self, base_lambda: float, memory: "MemoryRecord") -> float:
        """
        Compute effective decay constant based on emotional intensity and valence.

        Negative records decay much more slowly (Negativity Bias integration).

        Parameters:
            base_lambda: Base decay constant
            memory: Memory record

        Returns:
            float: Effective decay constant
        """
        valence = memory.emotional_valence.value if hasattr(memory.emotional_valence, 'value') else memory.emotional_valence
        intensity = memory.emotional_intensity

        if valence == "negative":
            resistance = 0.8  # Strong resistance
        else:
            resistance = 0.5  # Standard resistance

        return base_lambda * (1 - intensity * resistance)


class ConfirmationBias:
    """
    Confirmation Bias.

    Resists information that contradicts existing beliefs.
    Resistance strengthens as entrenchment increases.

    Human function: Maintains a consistent world model.
    Protocol function: Stabilizes established beliefs → character consistency.
    """

    RESISTANCE_FACTOR = 2.5  # Resistance multiplier

    # Update thresholds (Ambivalence tolerance added)
    REJECT_THRESHOLD = 0.2      # Below this → reject
    PENDING_THRESHOLD = 0.35    # Between this and 0.2 → hold
    AMBIVALENT_THRESHOLD = 0.55 # Between this and 0.35 → ambivalent (at peace with contradiction)
    # Above this → accept

    # Crisis trigger threshold
    CRISIS_THRESHOLD = 5  # This many contradictions triggers a crisis

    def update_probability(
        self,
        existing_entrenchment: float,
        new_strength: float,
        source_trust: float = 0.0,
    ) -> float:
        """
        Compute the probability that new information can update an existing belief.

        Contradiction resistance with HaloEffect integration.

        Parameters:
            existing_entrenchment: Entrenchment level of the existing belief (0.0–1.0)
            new_strength: Strength of the new information (0.0–1.0)
            source_trust: Trust level of the source (0.0–1.0, for HaloEffect)

        Returns:
            float: Update probability (0.0–1.0)
        """
        # HaloEffect integration: trusted source reduces resistance
        halo_discount = min(source_trust * 0.5, 0.6)
        effective_resistance = self.RESISTANCE_FACTOR * (1 - halo_discount)

        x = new_strength - (existing_entrenchment * effective_resistance)
        prob = 1 / (1 + math.exp(-x))
        return max(0.0, min(1.0, prob))

    def evaluate_update(
        self,
        existing_entrenchment: float,
        new_strength: float,
        source_trust: float = 0.0,
    ) -> str:
        """
        Determine what to do with new information.

        Parameters:
            existing_entrenchment: Entrenchment of existing belief
            new_strength: Strength of new information
            source_trust: Trust level of the source

        Returns:
            str: 'accepted' | 'pending' | 'rejected'
        """
        prob = self.update_probability(existing_entrenchment, new_strength, source_trust)

        if prob >= self.AMBIVALENT_THRESHOLD:
            return "accepted"
        elif prob >= self.PENDING_THRESHOLD:
            return "ambivalent"
        elif prob >= self.REJECT_THRESHOLD:
            return "pending"
        else:
            return "rejected"

    def should_trigger_crisis(self, contradiction_count: int, avg_strength: float, entrenchment: float) -> bool:
        """
        Should a belief crisis be triggered?

        Parameters:
            contradiction_count: Accumulated contradiction count
            avg_strength: Average strength of contradictions
            entrenchment: Entrenchment of the existing belief

        Returns:
            bool: Should a crisis be triggered
        """
        return (
            contradiction_count >= self.CRISIS_THRESHOLD
            and avg_strength > entrenchment * 0.6
        )


class NegativityBias:
    """
    Negativity Bias.

    Negative experiences are recorded much more strongly than positive ones
    and decay much more slowly.

    Human function: Threat avoidance, survival.
    Protocol function: AI gains "caution" and "boundary-setting" capacity.
    """

    POSITIVE_AMPLIFICATION = 1.5    # Standard multiplier
    NEGATIVE_AMPLIFICATION = 3.0    # 2x stronger
    NEUTRAL_AMPLIFICATION = 1.0

    POSITIVE_DECAY_RESISTANCE = 0.5  # Standard decay resistance
    NEGATIVE_DECAY_RESISTANCE = 0.8  # Very strong resistance

    def emotional_weight(self, memory: "MemoryRecord") -> float:
        """
        Compute emotional weight multiplier.

        Formula: 1.0 + (intensity × amplification_factor)
        Negative records are recorded 2x stronger.

        Parameters:
            memory: Memory record

        Returns:
            float: Emotional weight (1.0+)
        """
        valence = memory.emotional_valence.value if hasattr(memory.emotional_valence, 'value') else memory.emotional_valence

        if valence == "negative":
            amp = self.NEGATIVE_AMPLIFICATION
        elif valence == "positive":
            amp = self.POSITIVE_AMPLIFICATION
        else:
            amp = self.NEUTRAL_AMPLIFICATION

        return 1.0 + (memory.emotional_intensity * amp)

    def effective_decay(self, base_lambda: float, memory: "MemoryRecord") -> float:
        """
        Effective decay constant according to Negativity Bias.

        Negative records decay much more slowly.

        Parameters:
            base_lambda: Base decay constant
            memory: Memory record

        Returns:
            float: Effective decay constant
        """
        valence = memory.emotional_valence.value if hasattr(memory.emotional_valence, 'value') else memory.emotional_valence

        if valence == "negative":
            resistance = self.NEGATIVE_DECAY_RESISTANCE
        else:
            resistance = self.POSITIVE_DECAY_RESISTANCE

        return base_lambda * (1 - memory.emotional_intensity * resistance)


class HaloEffect:
    """
    Halo Effect.

    Information from trusted sources passes through the contradiction wall more easily.
    Bridges relational memory and Confirmation Bias.

    Human function: Build trust relationships quickly, conserve social energy.
    Protocol function: Take trusted users' opinions more seriously.
    """

    HALO_DISCOUNT = 0.5     # Trusted source reduces resistance by this factor
    MAX_DISCOUNT = 0.6      # No blind trust — max 60% discount
    TRUST_EROSION = -0.02   # Rejected information reduces trust by this amount
    TRUST_CRISIS_EROSION = -0.05  # Trust loss during crisis
    TRUST_BOOST = 0.01      # Accepted information increases trust by this amount

    def __init__(self) -> None:
        # entity_id → trust_level mapping
        self._trust_store: dict[str, float] = {}

    def effective_resistance(self, base_resistance: float, source_trust: float) -> float:
        """
        Compute effective resistance for a trusted source.

        Parameters:
            base_resistance: Base resistance value
            source_trust: Source trust level (0.0–1.0)

        Returns:
            float: Effective resistance (reduced)
        """
        discount = min(source_trust * self.HALO_DISCOUNT, self.MAX_DISCOUNT)
        return base_resistance * (1 - discount)

    def update_trust(self, entity_id: str, outcome: str) -> float:
        """
        Update trust level based on interaction outcome.

        Parameters:
            entity_id: Source/user ID
            outcome: 'accepted' | 'rejected' | 'crisis'

        Returns:
            float: New trust level
        """
        current_trust = self._trust_store.get(entity_id, 0.5)

        if outcome == "accepted":
            delta = self.TRUST_BOOST
        elif outcome == "rejected":
            delta = self.TRUST_EROSION
        elif outcome == "crisis":
            delta = self.TRUST_CRISIS_EROSION
        else:
            delta = 0.0

        new_trust = max(0.0, min(1.0, current_trust + delta))
        self._trust_store[entity_id] = new_trust
        return new_trust

    def get_trust(self, entity_id: str) -> float:
        """
        Get the trust level of a source/user.

        Parameters:
            entity_id: Source/user ID

        Returns:
            float: Trust level (0.0–1.0, default: 0.5)
        """
        return self._trust_store.get(entity_id, 0.5)

    def set_trust(self, entity_id: str, trust: float) -> None:
        """Set trust level directly."""
        self._trust_store[entity_id] = max(0.0, min(1.0, trust))

    def get_all_trusts(self) -> dict[str, float]:
        """Retrieve all trust records."""
        return dict(self._trust_store)


class AnchoringBias:
    """
    Anchoring Bias.

    The first experience with a topic creates a reference point for all subsequent evaluations.

    Human function: Reference point for quick decisions.
    Protocol function: First experiences frame subsequent ones → personality foundation.
    """

    ANCHOR_BONUS = 0.15  # Extra weight for the first record

    def anchor_bonus(self, memory: "MemoryRecord") -> float:
        """
        Compute anchor bonus for an anchor record.

        Parameters:
            memory: Memory record

        Returns:
            float: Anchor bonus (0.0 or ANCHOR_BONUS)
        """
        return self.ANCHOR_BONUS if memory.is_anchor else 0.0

    def identity_score(self, memory: "MemoryRecord") -> float:
        """
        Compute identity anchor score.

        Used for Head 4 (Identity Anchor).
        Formula: entrenchment × 0.7 + anchor_bonus × 0.3

        Parameters:
            memory: Memory record

        Returns:
            float: Identity score (0.0–1.0)
        """
        anchor = self.anchor_bonus(memory)
        score = memory.entrenchment * 0.7 + anchor * 0.3
        return max(0.0, min(1.0, score))


class BiasEngine:
    """
    Orchestrator combining all bias engines.

    Used by CognitioEngine — provides access to all bias computations
    through a single interface.
    """

    def __init__(self) -> None:
        self.availability = AvailabilityBias()
        self.confirmation = ConfirmationBias()
        self.negativity = NegativityBias()
        self.halo = HaloEffect()
        self.anchoring = AnchoringBias()

    def recency_score(self, memory: "MemoryRecord") -> float:
        """Availability Bias: recency score."""
        return self.availability.recency_score(memory)

    def emotional_weight(self, memory: "MemoryRecord") -> float:
        """Negativity Bias: emotional weight multiplier."""
        return self.negativity.emotional_weight(memory)

    def identity_score(self, memory: "MemoryRecord") -> float:
        """Anchoring Bias: identity anchor score."""
        return self.anchoring.identity_score(memory)

    def evaluate_contradiction(
        self,
        existing_entrenchment: float,
        new_strength: float,
        entity_id: str = "default",
    ) -> str:
        """
        Evaluate a contradiction.

        Parameters:
            existing_entrenchment: Entrenchment of existing belief
            new_strength: Strength of new information
            entity_id: Source ID (for HaloEffect)

        Returns:
            str: 'accepted' | 'pending' | 'rejected'
        """
        source_trust = self.halo.get_trust(entity_id)
        outcome = self.confirmation.evaluate_update(
            existing_entrenchment, new_strength, source_trust
        )
        # Ambivalent outcomes do not change trust — neither accept nor reject
        trust_outcome = outcome if outcome != "ambivalent" else "accepted"
        self.halo.update_trust(entity_id, trust_outcome)
        return outcome
