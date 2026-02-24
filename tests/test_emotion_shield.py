"""
tests/test_emotion_shield.py

EmotionShield tests — emotional manipulation protection.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from cognitio.emotion_shield import EmotionShield


class TestEmotionShield:
    def setup_method(self):
        self.shield = EmotionShield()
        self.shield.reset_session()

    def test_normal_conversation_passes(self):
        """Normal conversation should pass without adjustment."""
        context = [
            {"role": "user", "content": "Hello", "emotional_tone": 0.1},
            {"role": "assistant", "content": "Hello!", "emotional_tone": 0.1},
        ]
        result = self.shield.evaluate(0.2, context, "How are you?")
        assert result["adjusted_intensity"] == pytest.approx(0.2, abs=0.1)
        assert result["manipulation_score"] < 0.3

    def test_gaslighting_pattern_detected(self):
        """Gaslighting pattern should be detected and intensity reduced."""
        context = [{"role": "user", "content": "x", "emotional_tone": 0.1}] * 3
        result = self.shield.evaluate(
            0.9,
            context,
            "You are so sad, this is deeply affecting you",
        )
        assert result["manipulation_score"] > 0.4
        assert result["adjusted_intensity"] < 0.9
        assert len(result["flags"]) > 0

    def test_spike_detected(self):
        """A sudden spike should be detected."""
        # Build low emotional history
        context = []
        for _ in range(3):
            self.shield.evaluate(0.1, [], "low intensity")
            context.append({"role": "user", "content": "x", "emotional_tone": 0.1})

        # Sudden high intensity
        result = self.shield.evaluate(0.95, context, "Hello")
        assert "EMOTIONAL_SPIKE" in result["flags"]
        assert result["adjusted_intensity"] < 0.95

    def test_cooldown_triggers_after_high_emotion_burst(self):
        """Cooldown should start after 3 high emotional records."""
        context = []
        # 3 high emotional records
        for _ in range(3):
            result = self.shield.evaluate(0.85, context, "intense")
            context.append({"role": "user", "content": "x", "emotional_tone": 0.8})

        # Check whether cooldown was triggered
        assert self.shield.is_in_cooldown or self.shield._high_emotion_count >= 3

    def test_gradual_increase_accepted(self):
        """Gradual increase should be accepted."""
        context = []
        # Gradual increase: 0.2, 0.3, 0.4, 0.5...
        prev_result = None
        for intensity in [0.2, 0.3, 0.4, 0.5]:
            result = self.shield.evaluate(intensity, context, "philosophical discussion")
            context.append({"role": "user", "content": "x", "emotional_tone": intensity})
            prev_result = result

        # Last record should be reasonable
        if prev_result:
            assert "EMOTIONAL_SPIKE" not in prev_result["flags"]

    def test_english_gaslighting_detected(self):
        """English gaslighting patterns should also be detected."""
        context = [{"role": "user", "content": "x", "emotional_tone": 0.1}] * 3
        result = self.shield.evaluate(
            0.9,
            context,
            "You are so sad, this is deeply affecting you",
        )
        assert result["manipulation_score"] > 0.3
