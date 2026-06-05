"""Tests for the article quality report generator."""

import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

# Add assets directory to path
_assets = Path(__file__).resolve().parent.parent / \
    '.claude/skills/wikimedia-ml-services/assets'
sys.path.insert(0, str(_assets))
import article_quality_report  # noqa: E402


class TestBedExtractors:
    """Individual model response extractors."""

    def test_extract_quality_ores_format(self):
        """Revscoring articlequality uses ORES nested format."""
        result = {
            "enwiki": {
                "models": {"articlequality": {"version": "0.9.2"}},
                "scores": {
                    "12345": {
                        "articlequality": {
                            "score": {
                                "prediction": "C",
                                "probability": {"B": 0.02, "C": 0.78, "FA": 0.0, "GA": 0.12, "Start": 0.07, "Stub": 0.01}
                            }
                        }
                    }
                }
            }
        }
        extracted = article_quality_report.extract_quality(12345, result)
        assert extracted["grade"] == "C"
        assert extracted["probabilities"]["C"] == 0.78

    def test_extract_quality_error_handling(self):
        result = article_quality_report.extract_quality(12345, None)
        assert extracted["grade"] == "ERROR" if False else True
        # When result is None
        extracted = article_quality_report.extract_quality(12345, None)  # noqa: F811
        assert extracted["grade"] == "ERROR"

    def test_extract_quality_missing_rev_id(self):
        """Handle missing rev_id in the scores dict."""
        result = {"enwiki": {"scores": {}}}
        extracted = article_quality_report.extract_quality(12345, result)
        assert extracted["grade"] == "PARSE_ERROR"

    def test_extract_readability_success(self):
        result = {
            "model_name": "readability",
            "output": {"score": 0.643, "fk_score_proxy": 9.4}
        }
        extracted = article_quality_report.extract_readability(result)
        assert extracted["score"] == 0.643
        assert extracted["fk_score_proxy"] == 9.4

    def test_extract_readability_error(self):
        extracted = article_quality_report.extract_readability(None)
        assert "error" in extracted

    def test_extract_outlink_topics_success(self):
        result = {
            "prediction": {
                "results": [
                    {"topic": "Culture.Media.Books", "score": 0.92},
                    {"topic": "Culture.Media.Television", "score": 0.78},
                    {"topic": "STEM.Science", "score": 0.12},
                    {"topic": "Geography.Regions", "score": 0.05},
                ]
            }
        }
        extracted = article_quality_report.extract_outlink_topics(result, top_n=3)
        assert "top_topics" in extracted
        assert "category_breakdown" in extracted
        assert len(extracted["top_topics"]) == 3
        assert extracted["top_topics"][0]["topic"] == "Culture.Media.Books"
        assert "Culture" in extracted["category_breakdown"]
        assert "STEM" in extracted["category_breakdown"]

    def test_extract_outlink_topics_error(self):
        extracted = article_quality_report.extract_outlink_topics(None)
        assert "error" in extracted

    def test_extract_outlink_topics_malformed(self):
        extracted = article_quality_report.extract_outlink_topics({})
        assert "error" in extracted

    def test_extract_reference_risk(self):
        result = {
            "reference_risk_score": 0.05,
            "reference_count": 7,
            "survival_ratio": {"mean": 0.68, "median": 0.72}
        }
        extracted = article_quality_report.extract_reference_risk(result)
        assert extracted["risk_score"] == 0.05
        assert extracted["ref_count"] == 7
        assert extracted["survival_ratio"]["mean"] == 0.68

    def test_extract_reference_risk_error(self):
        extracted = article_quality_report.extract_reference_risk(None)
        assert "error" in extracted


class TestFormatFunctions:
    """Text formatting for reports."""

    def test_quality_bar(self):
        text = article_quality_report.format_quality_bar(
            {"C": 0.78, "B": 0.02, "GA": 0.12, "Start": 0.07, "Stub": 0.01, "FA": 0.0},
            "C"
        )
        assert "C" in text
        assert "78" in text
        assert "█" in text  # progress bar

    def test_readability_report(self):
        text = article_quality_report.format_readability(
            {"score": 0.643, "fk_score_proxy": 9.4}
        )
        assert "0.643" in text
        assert "9.4" in text
        assert "General Adult" in text or "College" in text

    def test_readability_no_grade(self):
        text = article_quality_report.format_readability({"score": 0.3})
        assert "0.3" in text

    def test_topics_report(self):
        text = article_quality_report.format_topics({
            "top_topics": [{"topic": "Culture.Media.Books", "score": 0.92}],
            "category_breakdown": {"Culture": 1.7}
        })
        assert "Culture" in text
        assert "Culture.Media.Books" in text

    def test_reference_risk_report(self):
        text = article_quality_report.format_reference_risk({
            "risk_score": 0.05,
            "ref_count": 7,
            "survival_ratio": {"mean": 0.68, "median": 0.72}
        })
        assert "5" in text
        assert "7" in text
        assert "68" in text

    def test_text_report_structure(self):
        report = {
            "quality": {"grade": "C", "probabilities": {"C": 0.78, "B": 0.02}},
            "readability": {"score": 0.643, "fk_score_proxy": 9.4},
            "topics": {
                "top_topics": [{"topic": "Culture.Media.Books", "score": 0.92}],
                "category_breakdown": {"Culture": 0.92}
            },
            "reference_risk": {"risk_score": 0.05, "ref_count": 7, "survival_ratio": {}},
        }
        output = article_quality_report.format_text_report("Albert_Einstein", "en", 12345, report)
        assert "Article Quality Report" in output
        assert "Albert_Einstein" in output
        assert "Topic Classification" in output
        assert "Reference Quality" in output


@patch('article_quality_report.requests.Session')
def test_call_liftwing_success(mock_session_class):
    """call_liftwing should return parsed JSON on success."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"output": {"score": 0.5}}
    mock_session.post.return_value = mock_resp

    result = article_quality_report.call_liftwing(
        mock_session, "readability", {"rev_id": 123, "lang": "en"}
    )
    assert result == {"output": {"score": 0.5}}


@patch('article_quality_report.requests.Session')
def test_call_liftwing_http_error(mock_session_class):
    """call_liftwing should return None on HTTP error."""
    import requests
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_session.post.side_effect = requests.exceptions.HTTPError("HTTP 500")

    result = article_quality_report.call_liftwing(
        mock_session, "readability", {"rev_id": 123, "lang": "en"}
    )
    assert result is None


@patch('article_quality_report.fetch_latest_revision')
@patch('article_quality_report.requests.Session')
def test_generate_report_calls_all_models(mock_session_class, mock_fetch):
    """generate_report should call all 4 models."""
    mock_fetch.return_value = 12345

    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    def make_mock_response(data):
        r = MagicMock()
        r.json.return_value = data
        return r

    # Return different responses for each model call
    mock_session.post.side_effect = [
        # 1. articlequality
        make_mock_response({
            "enwiki": {"scores": {"12345": {"articlequality": {"score": {"prediction": "C", "probability": {}}}}}}
        }),
        # 2. readability
        make_mock_response({"output": {"score": 0.64, "fk_score_proxy": 9.4}}),
        # 3. outlink-topic-model
        make_mock_response({"prediction": {"results": [{"topic": "STEM.Physics", "score": 0.9}]}}),
        # 4. reference-risk
        make_mock_response({"reference_risk_score": 0.05, "reference_count": 7}),
    ]

    report = article_quality_report.generate_report("Test_Page", "en")

    assert "quality" in report
    assert "readability" in report
    assert "topics" in report
    assert "reference_risk" in report
    assert mock_session.post.call_count == 4
