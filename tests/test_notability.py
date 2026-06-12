"""Tests for the notability assessment skill — checker, source evaluator, templates, and scripts."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

SKILL_DIR = (
    Path(__file__).resolve().parent.parent
    / ".claude" / "skills" / "wikipedia-notability-assessment"
)
ASSETS_DIR = SKILL_DIR / "assets"
SCRIPTS_DIR = SKILL_DIR / "scripts"

sys.path.insert(0, str(ASSETS_DIR))


# =========================================================================
# NotabilityChecker tests
# =========================================================================


class TestSubjectClassification:
    """Tests for subject type classification."""

    def test_classify_academic(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        assert checker.classify_subject("Professor of physics at MIT") == "academic"
        assert checker.classify_subject("Research scientist at university lab") == "academic"

    def test_classify_politician(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        assert checker.classify_subject("US Senator from California") == "politician"
        assert checker.classify_subject("Prime Minister of Canada") == "politician"

    def test_classify_company(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        assert checker.classify_subject("Software company founded in 2010") == "company"

    def test_classify_sports(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        assert checker.classify_subject("Olympic gold medalist in swimming") == "sports"

    def test_classify_film(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        assert checker.classify_subject("A feature film released in 2025") == "film"

    def test_classify_fallback(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        assert checker.classify_subject("Something completely generic") == "person"


class TestGNG:
    """Tests for General Notability Guideline checking."""

    def test_gng_pass_all_criteria(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        sources = [
            {"title": "Nature article", "type": "academic", "reliable": True,
             "independent": True, "significant": True},
            {"title": "NYT feature", "type": "news", "reliable": True,
             "independent": True, "significant": True},
            {"title": "Book chapter", "type": "book", "reliable": True,
             "independent": True, "significant": True},
        ]
        result = checker.check_gng(sources, "test")
        assert result.passed
        assert result.significant_coverage
        assert result.reliable_sources
        assert result.independent_sources
        assert result.multiple_sources

    def test_gng_fail_no_sources(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_gng([], "test")
        assert not result.passed
        assert "No sources" in result.notes

    def test_gng_fail_press_release(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        sources = [
            {"title": "PR Newswire", "type": "press_release",
             "reliable": False, "independent": False, "significant": False},
        ]
        result = checker.check_gng(sources, "test")
        assert not result.passed
        assert not result.independent_sources

    def test_gng_fail_single_source(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        sources = [
            {"title": "Single article", "type": "news", "reliable": True,
             "independent": True, "significant": True},
        ]
        result = checker.check_gng(sources, "test")
        assert not result.multiple_sources
        assert not result.passed

    def test_gng_fail_not_significant(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        sources = [
            {"title": "Mention in article", "type": "news", "reliable": True,
             "independent": True, "significant": False},
            {"title": "Another mention", "type": "news", "reliable": True,
             "independent": True, "significant": False},
        ]
        result = checker.check_gng(sources, "test")
        assert not result.significant_coverage
        assert not result.passed


class TestSNG:
    """Tests for subject-specific notability guidelines."""

    def test_nacademic_named_chair(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NACADEMIC",
            "Professor of physics, named chair at MIT")
        assert result.applicable
        assert len(result.criteria_met) > 0
        assert result.confidence == "high"

    def test_nacademic_major_award(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NACADEMIC",
            "Nobel Prize winner in physics")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_nacademic_no_criteria(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NACADEMIC",
            "Professor of physics")  # No specific criteria met
        assert result.applicable
        assert len(result.criteria_met) == 0
        assert result.confidence == "low"

    def test_anybio_major_award(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("ANYBIO",
            "Won the Pulitzer Prize")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_anybio_no_criteria(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("ANYBIO", "A person")
        assert not result.applicable
        assert len(result.criteria_met) == 0

    def test_npol_senator(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NPOL",
            "US Senator from California")
        assert result.applicable
        assert len(result.criteria_met) > 0
        assert result.confidence == "high"

    def test_npol_mayor(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NPOL",
            "Mayor of Springfield")
        assert result.applicable
        assert len(result.criteria_met) > 0
        assert result.confidence == "medium"

    def test_nsport_olympic(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NSPORT",
            "Olympic gold medalist in swimming")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_nsport_professional(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NSPORT",
            "NBA player")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_creative_exhibition(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NCREATIVE",
            "Exhibition at the Museum of Modern Art")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_ngeo_settlement(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NGEO",
            "A village in France")
        assert result.applicable
        assert len(result.criteria_met) > 0
        assert result.confidence == "high"

    def test_nmusic_charted(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NMUSIC",
            "Album charted on Billboard 200")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_nfilm_released(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NFILM",
            "Released film with positive reviews")
        assert result.applicable

    def test_ncorp_default(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NCORP",
            "A technology company")
        assert result.applicable
        assert result.confidence == "low"  # NCORP needs source evaluation

    def test_nastro_exoplanet(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NASTRO",
            "Confirmed exoplanet orbiting Proxima Centauri")
        assert result.applicable
        assert len(result.criteria_met) > 0
        assert result.confidence == "high"

    def test_nnumber_known(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NNUMBER",
            "The number 42")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_nnumber_mathematical(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NNUMBER",
            "The constant pi")
        assert result.applicable
        assert len(result.criteria_met) > 0

    def test_nspecies_described(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NSPECIES",
            "A described species of butterfly")
        assert result.applicable
        assert len(result.criteria_met) > 0
        assert result.confidence == "high"

    def test_nastro_unclear(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        result = checker.check_sng("NASTRO",
            "A star in the sky")
        assert result.applicable
        assert len(result.criteria_met) == 0  # Unclear type
        assert result.confidence == "low"


class TestExclusions:
    """Tests for exclusion rule checking."""

    def test_not_inherited(self):
        from notability_checker import NotabilityChecker, NotabilityReport
        checker = NotabilityChecker()
        report = NotabilityReport("Jane Doe", "person", "Spouse of famous actor")
        flags = checker.check_exclusions("person", "spouse of John Smith", report)
        assert any("NOTINHERITED" in f for f in flags)

    def test_bio1e(self):
        from notability_checker import NotabilityChecker, NotabilityReport
        checker = NotabilityChecker()
        report = NotabilityReport("Jane Doe", "person",
            "Only known for being a witness to an event")
        flags = checker.check_exclusions("person",
            "Only known for being a witness to", report)
        assert any("BIO1E" in f for f in flags)

    def test_no_exclusions(self):
        from notability_checker import NotabilityChecker, NotabilityReport
        checker = NotabilityChecker()
        report = NotabilityReport("Jane Smith", "academic",
            "Professor at MIT")
        flags = checker.check_exclusions("academic",
            "Professor at MIT with notable research", report)
        assert len(flags) == 0


class TestFullAssessment:
    """Tests for complete notability assessments."""

    def test_assess_notable_academic(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        report = checker.assess(
            name="Jane Smith",
            subject_type="academic",
            description="Professor of quantum physics at MIT, named chair holder",
            sources=[
                {"title": "Nature profile", "type": "news_feature",
                 "reliable": True, "independent": True, "significant": True},
                {"title": "NYT article", "type": "news_article",
                 "reliable": True, "independent": True, "significant": True},
            ],
        )
        assert report.overall_verdict == "notable"

    def test_assess_notable_politician(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        report = checker.assess(
            name="John Doe",
            subject_type="politician",
            description="US Senator from California, served 2000-2010",
        )
        assert report.overall_verdict == "notable"

    def test_assess_unclear_no_sources(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        report = checker.assess(
            name="Unknown Person",
            subject_type="person",
            description="A person with no notable achievements",
        )
        assert report.overall_verdict == "unclear"

    def test_assess_auto_classify(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        report = checker.assess(
            name="Test",
            description="Professor at MIT, Nobel Prize winner",
        )
        assert report.subject_type == "academic"

    def test_assess_not_inherited_flag(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        report = checker.assess(
            name="Jane Doe",
            description="Spouse of famous actor, has no independent career",
            sources=[],
        )
        assert len(report.exclusion_flags) > 0
        assert any("NOTINHERITED" in f for f in report.exclusion_flags)

    def test_assess_no_exclusion(self):
        from notability_checker import NotabilityChecker
        checker = NotabilityChecker()
        report = checker.assess(
            name="Jane Smith",
            subject_type="academic",
            description="Professor at MIT, Nobel Prize winner",
        )
        assert len(report.exclusion_flags) == 0


class TestReportFormat:
    """Tests for report data model."""

    def test_report_to_dict(self):
        from notability_checker import NotabilityReport, GNGResult, SNGResult
        report = NotabilityReport(
            subject_name="Test",
            subject_type="person",
            description="A test subject",
            overall_verdict="notable",
            confidence="high",
        )
        report.gng.passed = True
        report.gng.source_count = 3

        d = report.to_dict()
        assert d["subject"]["name"] == "Test"
        assert d["verdict"]["overall"] == "notable"
        assert d["gng_assessment"]["passed"]
        assert d["gng_assessment"]["source_count"] == 3


# =========================================================================
# SourceEvaluator tests
# =========================================================================


class TestSourceEvaluator:
    """Tests for source evaluation."""

    def test_reliable_domain(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.evaluate(
            title="Nature article",
            url="https://nature.com/articles/123",
            source_type="academic_journal",
        )
        assert result["reliable"] is True
        assert result["score"] >= 5

    def test_unreliable_domain(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.evaluate(
            title="IMDb page",
            url="https://imdb.com/name/nm123",
        )
        assert result["reliable"] is False
        assert result["score"] <= 3

    def test_press_release(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.evaluate(
            title="PR Newswire: Company announces product",
            source_type="press_release",
        )
        assert result["independent"] is False
        assert result["significant"] is False

    def test_significant_signals(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.evaluate(
            title="In-depth profile of Dr. Smith",
            source_type="news_feature",
        )
        assert result["significant"] is True

    def test_routine_negative_signals(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.evaluate(
            title="Press release: Company announces new product",
        )
        # Should pick up negative signals
        assert result["score"] <= 5

    def test_unknown_domain_neutral(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.evaluate(
            url="https://example.com/article",
        )
        # Unknown domains treated as potentially unreliable
        assert "reliable" in result

    def test_classify_academic(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        assert evaluator.classify_source("https://nature.com/article") == "academic_journal"
        assert evaluator.classify_source("https://arxiv.org/abs/1234") == "academic_journal"

    def test_classify_database(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        assert evaluator.classify_source("https://imdb.com/title/") == "database"

    def test_classify_news(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        assert evaluator.classify_source("https://nytimes.com/article") == "news_article"

    def test_classify_feature(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        result = evaluator.classify_source(title="An in-depth profile of...")
        assert result == "news_feature"

    def test_classify_social_media(self):
        from source_evaluator import SourceEvaluator
        evaluator = SourceEvaluator()
        assert evaluator.classify_source("https://twitter.com/user") == "social_media"


# =========================================================================
# NotabilityTemplates tests
# =========================================================================


class TestNotabilityTemplates:
    """Tests for report templates."""

    def test_format_report(self):
        from notability_checker import NotabilityReport
        from notability_templates import format_report
        report = NotabilityReport("Test", "person", "desc",
                                   overall_verdict="notable", confidence="high")
        output = format_report(report)
        assert "NOTABLE" in output
        assert "Test" in output

    def test_format_short(self):
        from notability_checker import NotabilityReport
        from notability_templates import format_short
        report = NotabilityReport("Test", "person", "",
                                   overall_verdict="notable")
        output = format_short(report)
        assert "NOTABLE" in output
        assert "Test" in output

    def test_format_afd_summary_keep(self):
        from notability_checker import NotabilityReport, SNGResult
        from notability_templates import generate_afd_summary
        report = NotabilityReport("Test", "academic", "",
                                   overall_verdict="notable")
        report.sng_results = [
            SNGResult(sng="NACADEMIC", applicable=True,
                       criteria_met=["Named chair"],
                       confidence="high")
        ]
        output = generate_afd_summary(report)
        assert "Keep" in output or "keep" in output

    def test_format_afd_summary_delete(self):
        from notability_checker import NotabilityReport
        from notability_templates import generate_afd_summary
        report = NotabilityReport("Test", "person", "",
                                   overall_verdict="not_notable")
        output = generate_afd_summary(report)
        assert "Delete" in output or "delete" in output

    def test_notability_tag_unclear(self):
        from notability_checker import NotabilityReport
        from notability_templates import generate_notability_tag
        report = NotabilityReport("Test", "person", "",
                                   overall_verdict="unclear")
        tag = generate_notability_tag(report)
        assert "notability" in tag

    def test_notability_tag_notable(self):
        from notability_checker import NotabilityReport
        from notability_templates import generate_notability_tag
        report = NotabilityReport("Test", "person", "",
                                   overall_verdict="notable")
        tag = generate_notability_tag(report)
        assert tag == ""  # No tag needed for notable subjects

    def test_notability_tag_not_notable(self):
        """not_notable should suggest CSD/PROD, not return empty."""
        from notability_checker import NotabilityReport
        from notability_templates import generate_notability_tag
        report = NotabilityReport("Test", "person", "",
                                   overall_verdict="not_notable")
        tag = generate_notability_tag(report)
        assert tag != ""
        assert "CSD" in tag or "PROD" in tag


# =========================================================================
# Script tests
# =========================================================================


class TestScripts:
    """Tests for shell scripts."""

    def test_notability_check_help(self):
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "notability-check.sh"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_notability_check_basic(self):
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "notability-check.sh"),
             "Jane Smith",
             "--type", "academic",
             "--desc", "Professor at MIT, Nobel Prize winner"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "NOTABLE" in result.stdout

    def test_notability_check_missing_desc(self):
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "notability-check.sh"), "Test"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0 or "Error" in result.stderr

    def test_checker_script_help(self):
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "notability_checker.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout

    def test_checker_script_json(self):
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "notability_checker.py"),
             "Jane Smith",
             "--description", "Professor at MIT, Nobel Prize winner",
             "--type", "academic",
             "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["verdict"]["overall"] == "notable"

    def test_checker_script_afd(self):
        """Test --afd flag produces AfD-ready output."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "notability_checker.py"),
             "Jane Smith",
             "--description", "Professor at MIT, Nobel Prize winner",
             "--type", "academic",
             "--afd"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "Keep" in result.stdout or "Meets" in result.stdout

    def test_evaluator_script_help(self):
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "source_evaluator.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_evaluator_script_basic(self):
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "source_evaluator.py"),
             "--title", "Nature article",
             "--type", "academic_journal",
             "--url", "https://nature.com/article"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["reliable"] is True

    def test_templates_script_help(self):
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "notability_templates.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0


# =========================================================================
# Reference docs tests
# =========================================================================


class TestReferences:
    """Tests for reference documentation files."""

    def test_sng_decision_trees_exists(self):
        path = SKILL_DIR / "references" / "sng-decision-trees.md"
        assert path.exists()
        content = path.read_text()
        assert len(content) > 2000
        assert "NACADEMIC" in content
        assert "NCORP" in content
        assert "NMUSIC" in content
        assert "NGEO" in content

    def test_invalid_arguments_exists(self):
        path = SKILL_DIR / "references" / "invalid-arguments.md"
        assert path.exists()
        content = path.read_text()
        assert len(content) > 2000
        assert "NOTINHERITED" in content
        assert "CONTN" in content
        assert "GOOGLEHITS" in content


# =========================================================================
# SKILL.md tests
# =========================================================================


class TestSkillFile:
    """Tests for the main SKILL.md file."""

    def test_skill_file_exists(self):
        path = SKILL_DIR / "SKILL.md"
        assert path.exists()

    def test_skill_file_has_yaml_frontmatter(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert content.startswith("---")
        second = content.find("---", 3)
        assert second > 3
        frontmatter = content[3:second].strip()
        assert "name:" in frontmatter
        assert "description:" in frontmatter
        assert "license: MIT" in frontmatter
        assert "last_verified:" in frontmatter
        assert "depends_on:" in frontmatter

    def test_skill_file_references_related_skills(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "wikipedia-en-biography-writing" in content
    def test_skill_file_cross_references_pagetriage(self):
        """Verifies the new skill name appears in cross-references."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "wikipedia-pagetriage-api" in content
        assert "wikimedia-api-access" in content

    def test_skill_file_has_sops(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "## SOP:" in content or "### SOP:" in content

    def test_skill_file_has_guardrails(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "## Guardrails" in content or "### Guardrails" in content

    def test_skill_file_covers_key_concepts(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        for concept in [
            "GNG", "SNG", "significant coverage", "reliable source",
            "independent", "NOTINHERITED", "NACADEMIC", "NCORP",
            "BIO1E", "CONTN", "NEXIST",
        ]:
            assert concept in content, f"Missing: {concept}"

    def test_skill_file_mentions_all_13_sngs(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        sngs = ["NACADEMIC", "NASTRO", "NBOOK", "NEVENT", "NFILM",
                "NGEO", "NMUSIC", "NNUMBER", "NCORP", "BIO",
                "NSPECIES", "NSPORT", "NWEB"]
        for sng in sngs:
            assert sng in content, f"Missing SNG: {sng}"

    def test_skill_file_has_source_hierarchy(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "hierarchy" in content.lower() or "tier" in content.lower()
