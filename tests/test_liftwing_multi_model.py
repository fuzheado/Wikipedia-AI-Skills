"""Tests for the Lift Wing multi-model scoring script."""

import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

# Add assets directory to path
_assets = Path(__file__).resolve().parent.parent / \
    '.claude/skills/wikimedia-ml-services/assets'
sys.path.insert(0, str(_assets))
import liftwing_multi_model  # noqa: E402


class TestScoreCache:
    """In-memory cache for ML scores."""

    def test_cache_hit(self):
        cache = liftwing_multi_model.ScoreCache(ttl=3600)
        cache.set("test-model", 12345, {"prediction": 0.5})
        result = cache.get("test-model", 12345)
        assert result == {"prediction": 0.5}

    def test_cache_miss(self):
        cache = liftwing_multi_model.ScoreCache(ttl=3600)
        result = cache.get("test-model", 99999)
        assert result is None

    def test_cache_clear(self):
        cache = liftwing_multi_model.ScoreCache(ttl=3600)
        cache.set("a", 1, {"x": 1})
        cache.set("b", 2, {"y": 2})
        cache.clear()
        assert cache.get("a", 1) is None
        assert cache.get("b", 2) is None

    def test_cache_expiry(self):
        """Cache entry should expire after TTL."""
        cache = liftwing_multi_model.ScoreCache(ttl=-1)  # Negative TTL = always expired
        cache.set("test-model", 12345, {"prediction": 0.5})
        result = cache.get("test-model", 12345)
        assert result is None


class TestExtractPrediction:
    """Parsing model responses into human-readable format."""

    def test_revscoring_ores_format(self):
        """Revscoring models use the old ORES nested format."""
        result = {
            "enwiki": {
                "models": {"articlequality": {"version": "0.9.2"}},
                "scores": {
                    "12345": {
                        "articlequality": {
                            "score": {
                                "prediction": "C",
                                "probability": {
                                    "B": 0.02, "C": 0.78, "FA": 0.0,
                                    "GA": 0.12, "Start": 0.07, "Stub": 0.01
                                }
                            }
                        }
                    }
                }
            }
        }
        extracted = liftwing_multi_model.extract_prediction(12345, "articlequality", result)
        assert extracted["prediction"] == "C"
        assert extracted["probability"]["C"] == 0.78

    def test_modern_revertrisk_format(self):
        """Modern revert-risk models use the Lift Wing unified envelope."""
        result = {
            "model_name": "revertrisk-language-agnostic",
            "model_version": "3",
            "output": {
                "prediction": False,
                "probabilities": {"true": 0.34, "false": 0.66}
            }
        }
        extracted = liftwing_multi_model.extract_prediction(12345, "revertrisk-language-agnostic", result)
        assert extracted["prediction"] is False
        assert extracted["probability"]["false"] == 0.66

    def test_readability_format(self):
        """Readability returns output.score and output.fk_score_proxy."""
        result = {
            "model_name": "readability",
            "model_version": "4",
            "output": {"score": 0.643, "fk_score_proxy": 9.4}
        }
        extracted = liftwing_multi_model.extract_prediction(12345, "readability", result)
        assert extracted["score"] == 0.643
        assert extracted["fk_score_proxy"] == 9.4

    def test_reference_format(self):
        """Reference models use top-level fields."""
        result = {
            "model_name": "reference-need",
            "revision_id": 12345,
            "reference_need_score": 0.923
        }
        extracted = liftwing_multi_model.extract_prediction(12345, "reference-need", result)
        assert extracted["reference_need_score"] == 0.923

    def test_reference_risk_format(self):
        result = {
            "model_name": "reference-risk",
            "reference_count": 7,
            "reference_risk_score": 0.0,
            "survival_ratio": {"min": 0.15, "mean": 0.68, "median": 0.72}
        }
        extracted = liftwing_multi_model.extract_prediction(12345, "reference-risk", result)
        assert extracted["reference_risk_score"] == 0.0
        assert extracted["reference_count"] == 7

    def test_empty_response(self):
        """Handle empty or malformed responses gracefully."""
        extracted = liftwing_multi_model.extract_prediction(12345, "test", {})
        assert "raw" in extracted


class TestFormatScoreLine:
    """Human-readable formatting of score lines."""

    def test_revertrisk_bool(self):
        line = liftwing_multi_model.format_score_line(
            "revertrisk",
            "revertrisk-language-agnostic (Revert risk)",
            {"prediction": False, "probability": {"true": 0.34, "false": 0.66}}
        )
        assert "SAFE" in line

    def test_revertrisk_risky(self):
        line = liftwing_multi_model.format_score_line(
            "revertrisk",
            "revertrisk-language-agnostic (Revert risk)",
            {"prediction": True, "probability": {"true": 0.87, "false": 0.13}}
        )
        assert "RISKY" in line

    def test_readability_format(self):
        line = liftwing_multi_model.format_score_line(
            "readability",
            "readability (Readability)",
            {"score": 0.643, "fk_score_proxy": 9.4}
        )
        assert "score=0.643" in line
        assert "grade=9.4" in line

    def test_reference_need(self):
        line = liftwing_multi_model.format_score_line(
            "reference-need",
            "reference-need (Reference need)",
            {"reference_need_score": 0.923}
        )
        assert "92.3%" in line

    def test_reference_risk(self):
        line = liftwing_multi_model.format_score_line(
            "reference-risk",
            "reference-risk (Reference risk)",
            {"reference_risk_score": 0.05, "reference_count": 7}
        )
        assert "refs=7" in line

    def test_revscoring_format(self):
        line = liftwing_multi_model.format_score_line(
            "goodfaith",
            "goodfaith (Good/bad faith)",
            {"prediction": True, "probability": {"true": 0.87, "false": 0.13}}
        )
        # Bool prediction renders as SAFE/RISKY
        assert "RISKY" in line


@patch('liftwing_multi_model.requests.Session')
def test_score_revision_success(mock_session_class):
    """score_revision should return parsed JSON on success."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"output": {"prediction": False}}
    mock_session.post.return_value = mock_resp

    cache = liftwing_multi_model.ScoreCache()
    result = liftwing_multi_model.score_revision(
        mock_session, cache, "enwiki", 12345, "revertrisk-language-agnostic", lang="en"
    )
    assert result == {"output": {"prediction": False}}
    assert cache.get("revertrisk-language-agnostic", 12345) == {"output": {"prediction": False}}


@patch('liftwing_multi_model.requests.Session')
def test_score_revision_returns_cached(mock_session_class):
    """score_revision should return cached results without API call."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    cache = liftwing_multi_model.ScoreCache()
    cache.set("test-model", 1, {"cached": True})

    result = liftwing_multi_model.score_revision(
        mock_session, cache, "enwiki", 1, "test-model", lang="en"
    )
    assert result == {"cached": True}
    mock_session.post.assert_not_called()


@patch('liftwing_multi_model.requests.Session')
def test_score_revision_http_error(mock_session_class):
    """score_revision should return None on HTTP error."""
    import requests
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_session.post.side_effect = requests.exceptions.HTTPError("HTTP 429")

    cache = liftwing_multi_model.ScoreCache()
    result = liftwing_multi_model.score_revision(
        mock_session, cache, "enwiki", 12345, "revertrisk-language-agnostic", lang="en"
    )
    assert result is None
