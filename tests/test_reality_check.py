"""
tests/test_reality_check.py

RealityCheck tests — hallucination defense system.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from cognitio.reality_check import RealityCheck


@pytest.fixture
def rc():
    """RealityCheck without LLM (rule-based)."""
    return RealityCheck(llm_client=None, enabled=True)


class TestRealityCheck:
    def test_normal_user_stated_passes(self, rc):
        """Normal user statement should be approved."""
        result = rc.validate({
            "content": "The user is learning Python",
            "source_type": "user_stated",
            "emotional_intensity": 0.3,
            "confidence": 0.7,
        })
        assert result["approved"] is True
        assert result["source_credibility"] == pytest.approx(0.7)

    def test_llm_inferred_lower_confidence(self, rc):
        """LLM inference should receive lower confidence."""
        result = rc.validate({
            "content": "AI has gained consciousness",
            "source_type": "llm_inferred",
            "emotional_intensity": 0.5,
            "confidence": 0.5,
        })
        assert result["source_credibility"] == pytest.approx(0.4)
        # Adjusted confidence should be lower
        assert result["adjusted_confidence"] < 0.5

    def test_llm_high_intensity_cap(self, rc):
        """For LLM source, emotional intensity should be capped at 0.5."""
        result = rc.validate({
            "content": "A very deep feeling",
            "source_type": "llm_inferred",
            "emotional_intensity": 0.95,
            "confidence": 0.5,
        })
        # Intensity cap for llm_inferred is 0.5
        assert result["adjusted_emotional_intensity"] <= 0.5

    def test_outlier_high_intensity_low_credibility_source(self, rc):
        """High intensity + LLM source should create a flag."""
        result = rc.validate({
            "content": "An incredible discovery!",
            "source_type": "llm_inferred",
            "emotional_intensity": 0.95,
            "confidence": 0.8,
        })
        assert "HIGH_INTENSITY_LOW_CREDIBILITY_SOURCE" in result["flags"]

    def test_session_rate_limit(self, rc):
        """3+ high emotional records should trigger SESSION_RATE_LIMIT."""
        rc._session_high_emotional_count = 3

        result = rc.validate({
            "content": "More high emotion",
            "source_type": "user_stated",
            "emotional_intensity": 0.85,
            "confidence": 0.7,
        })
        assert "SESSION_RATE_LIMIT" in result["flags"]

    def test_external_fact_highest_credibility(self, rc):
        """external_fact should receive the highest credibility."""
        result = rc.validate({
            "content": "Earth's diameter is 12742 km",
            "source_type": "external_fact",
            "emotional_intensity": 0.0,
            "confidence": 0.9,
        })
        assert result["source_credibility"] == pytest.approx(0.9)
        assert result["approved"] is True

    def test_disabled_rc_always_approves(self):
        """Disabled RC should always approve."""
        rc_disabled = RealityCheck(enabled=False)
        result = rc_disabled.validate({
            "content": "Anything",
            "source_type": "llm_inferred",
            "emotional_intensity": 0.99,
            "confidence": 0.99,
        })
        assert result["approved"] is True

    def test_source_credibility_values(self, rc):
        """Source credibility values should be correct."""
        assert rc.source_credibility("user_stated") == pytest.approx(0.7)
        assert rc.source_credibility("llm_inferred") == pytest.approx(0.4)
        assert rc.source_credibility("external_fact") == pytest.approx(0.9)
        assert rc.source_credibility("emotional_impression") == pytest.approx(0.3)
