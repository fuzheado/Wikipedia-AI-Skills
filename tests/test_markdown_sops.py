"""Verify key content assertions in the newly modified/marked-up SKILL.md files."""

import re
import pytest
from conftest import read_skill  # noqa: E402


class TestWikidataBatchClassificationSop:
    """Verify the new Batch Entity Classification SOP in wikidata/SKILL.md."""

    def test_sop_section_exists(self):
        """The SOP section header must be present."""
        text = read_skill('wikidata')
        assert 'SOP: Batch Entity Classification from Wikipedia Titles' in text

    def test_title_normalization_warning(self):
        """Must warn about underscore-to-space normalization."""
        text = read_skill('wikidata')
        assert 'normalize' in text.lower() or 'Normalize' in text
        assert "replace('_', ' ')" in text or "underscores" in text.lower()
        assert 'Pageviews' in text or 'pageviews' in text

    def test_batch_limit_50(self):
        """Must specify batch limit of 50 titles per API call."""
        text = read_skill('wikidata')
        assert '50' in text
        assert 'batch' in text.lower()

    def test_p31_reference_table(self):
        """Must include a reference table of common P31 Q IDs."""
        text = read_skill('wikidata')
        assert 'Q5' in text       # human
        assert 'Q11424' in text   # film
        assert 'Q515' in text     # city
        assert 'Q16521' in text   # taxon

    def test_wbgetentities_not_entitydata(self):
        """Must warn against using Special:EntityData for batch lookups."""
        text = read_skill('wikidata')
        assert 'EntityData' in text or 'entitydata' in text.lower()
        assert 'single ID' in text or 'one ID' in text

    def test_cross_references(self):
        """Must cross-reference the API access skill's title format guide."""
        text = read_skill('wikidata')
        assert 'wikimedia-api-access' in text
        # Should link to endpoints.md or the title format section
        assert 'Title Format Guide' in text.lower() or 'endpoints' in text.lower()

    def test_subclass_hierarchy_handling(self):
        """Must mention P279 traversal for subclass hierarchy."""
        text = read_skill('wikidata')
        assert 'P279' in text
        assert 'subclass' in text.lower()


class TestPageviewsScenarioC:
    """Verify the new Scenario C in wikimedia-pageviews/SKILL.md."""

    def test_scenario_c_exists(self):
        """Scenario C header must be present."""
        text = read_skill('wikimedia-pageviews')
        assert 'Scenario C' in text

    def test_top_endpoint_url(self):
        """Must document the correct Top endpoint URL."""
        text = read_skill('wikimedia-pageviews')
        assert 'pageviews/top/' in text or 'pageviews/top' in text

    def test_slash_date_format_warning(self):
        """Must warn about slash vs compact date format."""
        text = read_skill('wikimedia-pageviews')
        assert 'YYYY/MM/DD' in text or 'slashes' in text.lower() or 'slash' in text.lower()

    def test_data_lag_warning(self):
        """Must mention ~48h data lag."""
        text = read_skill('wikimedia-pageviews')
        assert '48' in text

    def test_title_normalization_cross_reference(self):
        """Must cross-reference the title format gotcha."""
        text = read_skill('wikimedia-pageviews')
        assert 'normalize' in text.lower() or "replace('_', ' ')" in text
        # Should link to wikidata or api-access for more details
        assert 'wikidata' in text or 'wikimedia-api-access' in text

    def test_chaining_with_classification(self):
        """Must reference the entity classification SOP."""
        text = read_skill('wikimedia-pageviews')
        assert 'Batch Entity Classification' in text or 'entity classification' in text.lower()


class TestEndpointsTitleFormatGuide:
    """Verify the Title Format Guide in references/endpoints.md."""

    def test_title_format_section_exists(self):
        """Section 11 must exist."""
        text = read_skill('wikimedia-api-access')
        # Actually this is in references/endpoints.md, not the SKILL.md
        import os
        from conftest import SKILLS_DIR
        endpoints_path = SKILLS_DIR / 'wikimedia-api-access' / 'references' / 'endpoints.md'
        text = endpoints_path.read_text('utf-8')
        assert '## 11. Title Format Guide (Cross-API Gotcha)' in text

    def test_table_has_all_rows(self):
        """Must cover Pageviews Top, Per-Article, Action API, REST API, SQL."""
        from conftest import SKILLS_DIR
        endpoints_path = SKILLS_DIR / 'wikimedia-api-access' / 'references' / 'endpoints.md'
        text = endpoints_path.read_text('utf-8')
        assert 'Pageviews Top' in text
        assert 'Pageviews Per-Article' in text
        assert 'prop=pageprops' in text
        assert '/page/summary' in text or 'REST API' in text
        assert 'SQL' in text

    def test_code_example(self):
        """Must include the correct/wrong code comparison."""
        from conftest import SKILLS_DIR
        endpoints_path = SKILLS_DIR / 'wikimedia-api-access' / 'references' / 'endpoints.md'
        text = endpoints_path.read_text('utf-8')
        assert "action_api_dict.get(pageview_title)" in text  # wrong
        assert "action_api_dict.get(pageview_title.replace('_', ' '))" in text  # correct

    def test_rule_of_thumb(self):
        """Must include the 'Rule of thumb' guidance."""
        from conftest import SKILLS_DIR
        endpoints_path = SKILLS_DIR / 'wikimedia-api-access' / 'references' / 'endpoints.md'
        text = endpoints_path.read_text('utf-8')
        assert 'Rule of thumb' in text


class TestApiAccessRateLimitDetails:
    """Verify the expanded 429 handling in wikimedia-api-access/SKILL.md."""

    def test_429_subsection_exists(self):
        """Must have a dedicated subsection title."""
        text = read_skill('wikimedia-api-access')
        assert '429 Retry-After Handling' in text

    def test_warns_against_fixed_backoff(self):
        """Must warn against fixed backoff."""
        text = read_skill('wikimedia-api-access')
        assert 'Do not retry' in text and 'fixed backoff' in text.lower()
        assert 'fixed backoff' in text.lower()

    def test_common_causes_listed(self):
        """Must list common 429 causes."""
        text = read_skill('wikimedia-api-access')
        assert 'too many requests' in text.lower()
        assert 'too many titles' in text.lower() or 'titles' in text.lower()
        assert 'rvsection' in text or 'section=0' in text


class TestLiftWingLLMSection:
    """Verify the LiftWing LLM chat-completions section in wikimedia-ml-services."""

    def _text(self):
        from conftest import read_skill
        return read_skill("wikimedia-ml-services")

    def test_llm_models_listed(self):
        text = self._text()
        assert "llm-qwen3-14b" in text and "llm-qwen36-27b" in text
        assert "Qwen3-14B" in text and "Qwen3.6-27B" in text

    def test_openai_compatible_endpoint(self):
        text = self._text()
        assert "chat/completions" in text
        assert "api.wikimedia.org/service/lw/inference/v1/models/llm-" in text
        assert "api_key=\"none\"" in text

    def test_rate_limits(self):
        text = self._text()
        assert "100 requests/hour" in text
        assert "429" in text
        assert "Toolforge" in text

    def test_gotchas(self):
        text = self._text()
        assert "must match the URL path" in text  # model name == URL segment
        assert "think" in text  # reasoning wrapper


class TestPhabricatorResponsibleInteraction:
    """Verify the responsible-interaction policy gate in wikimedia-phabricator."""

    def _skill(self):
        from conftest import read_skill
        return read_skill('wikimedia-phabricator')

    def _reference(self):
        from conftest import SKILLS_DIR
        path = SKILLS_DIR / 'wikimedia-phabricator' / 'references' / 'responsible-interaction.md'
        assert path.exists(), 'references/responsible-interaction.md must exist'
        return path.read_text('utf-8')

    def test_gate_section_and_pointer(self):
        text = self._skill()
        assert 'Responsible Interaction' in text
        assert 'references/responsible-interaction.md' in text
        assert 'read-only' in text.lower()

    def test_read_only_default_in_reference(self):
        text = " ".join(self._reference().split())
        assert 'Default: read-only' in text
        assert 'Do not file, comment, edit, claim, assign' in text
        assert 'ERR-INVALID-SESSION' in text  # anonymous Conduit is expected, not a bug

    def test_ai_llm_responsibility_rule_quoted(self):
        text = self._reference()
        assert 'fully responsible for its content' in text
        assert 'represent your own understanding' in text

    def test_security_never_a_public_task(self):
        text = self._reference()
        assert 'security@wikimedia.org' in text
        assert 'form/75' in text
        assert 'never public' in text.lower()

    def test_status_priority_reflect_reality(self):
        text = " ".join(self._reference().split())
        assert 'do *not* cause it' in text
        assert 'prior agreement' in text  # no assigning without consent

    def test_bot_account_route(self):
        text = " ".join(self._reference().split())
        assert '#Phabricator-Bot-Requests' in text
        assert 'registered bot' in text and 'personal account' in text

    def test_robot_policy_limits_for_phabricator(self):
        text = " ".join(self._reference().split())
        assert 'concurrency of at most 1' in text
        assert 'at least 1 second between requests' in text
        assert '15 minutes' in text
        assert 'wikimedia-api-access' in text  # defers the full policy to the home skill

    def test_conduct_and_privacy(self):
        text = self._reference()
        assert 'techconduct@wikimedia.org' in text
        assert 'PermanentlyPrivate' in text
        assert 'Uploaded files are private until' in text

    def test_sources_listed(self):
        text = self._reference()
        for anchor in ('Bug_management/Phabricator_etiquette', 'Code_of_Conduct',
                       'Reporting_security_bugs', 'Phabricator/Bots', 'wiki/Robot_policy'):
            assert anchor in text, f'missing source: {anchor}'
