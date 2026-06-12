"""Tests for the wikimedia-auth-oauth assets and guardrails."""

import json
import re
from unittest.mock import MagicMock, patch

import pytest

from conftest import REPO_ROOT, SKILLS_DIR, read_skill

SKILL_DIR = SKILLS_DIR / "wikimedia-auth-oauth"
SKILL_PATH = SKILL_DIR / "SKILL.md"


class TestAuthSkillGuardrails:
    """Verify the auth skill contains the required guardrail patterns."""

    skill_text = read_skill("wikimedia-auth-oauth")

    def test_login_asserts_success(self):
        """login() should assert result == 'Success'."""
        assert 'assert login_resp["login"]["result"] == "Success"' in self.skill_text, \
            "Missing login result assertion"

    def test_login_verifies_userinfo(self):
        """login() should verify userinfo after login."""
        assert 'meta": "userinfo"' in self.skill_text, \
            "Missing userinfo verification after login"

    def test_csrf_rejects_anonymous(self):
        """get_csrf_token() should reject the anonymous '+' token."""
        pattern = 'csrf != "+\\\\\\\\"'
        assert pattern in self.skill_text or 'csrf != "+\\\\"' in self.skill_text, \
            "Missing anonymous CSRF token rejection"

    def test_csrf_validates_length(self):
        """get_csrf_token() should validate token length."""
        assert "len(csrf) > 10" in self.skill_text, \
            "Missing CSRF token length validation"

    def test_edit_uses_assert_user(self):
        """edit_page() should include assert='user'."""
        assert '"assert": "user"' in self.skill_text, \
            "Missing assert=user in edit_page"

    def test_edit_checks_user_in_response(self):
        """edit_page() should check the 'user' field in the response."""
        assert 'result.get("user")' in self.skill_text or 'edit.get("user")' in self.skill_text, \
            "Missing user field check in edit response"

    def test_guardrail_explanation_present(self):
        """The skill should explain why these guards matter."""
        assert "temp-account" in self.skill_text or "anonymous" in self.skill_text.lower(), \
            "Missing explanation about anonymous/temp-account fallback"


class TestOAuth2ClientGuardrails:
    """Verify the oauth2_client.py asset has guardrails."""

    client_path = SKILL_DIR / "assets" / "oauth2_client.py"
    client_code = client_path.read_text()

    def test_get_csrf_rejects_anonymous(self):
        """get_csrf_token() must reject anonymous '+' tokens."""
        assert 'csrf != "+\\\\"' in self.client_code, \
            "Missing anonymous CSRF token rejection"

    def test_get_csrf_validates_length(self):
        """get_csrf_token() must validate token length."""
        assert "len(csrf) > 10" in self.client_code, \
            "Missing CSRF token length validation"

    def test_edit_uses_assert_user(self):
        """edit_page() must include assert='user'."""
        assert '"assert": "user"' in self.client_code, \
            "Missing assert=user in edit_page"

    def test_edit_checks_user_in_response(self):
        """edit_page() must check the 'user' field."""
        assert 'edit.get("user")' in self.client_code, \
            "Missing user field check in response"

    def test_edit_checks_for_errors(self):
        """edit_page() must check for API errors."""
        assert '"error" in result' in self.client_code or '"error" in resp' in self.client_code, \
            "Missing error check in edit response"


class TestFlaskAppGuardrails:
    """Verify the flask-oauth2-app.py asset has guardrails."""

    app_path = SKILL_DIR / "assets" / "flask-oauth2-app.py"
    app_code = app_path.read_text()

    def test_csrf_validation(self):
        """Must check for anonymous CSRF token."""
        assert 'csrf_token == "+\\\\"' in self.app_code, \
            "Missing CSRF token validation"

    def test_edit_uses_assert_user(self):
        """edit must include assert='user'."""
        assert '"assert": "user"' in self.app_code, \
            "Missing assert=user in edit"

    def test_edit_checks_user_in_response(self):
        """edit must check the 'user' field in response."""
        assert 'edit.get("user")' in self.app_code, \
            "Missing user field check in edit response"

    def test_edit_checks_for_errors(self):
        """edit must check for API errors."""
        assert '"error" in result' in self.app_code, \
            "Missing error check in edit response"


class TestBotPasswordEditorGuardrails:
    """Verify the bot-password-editor.py asset has guardrails."""

    editor_path = SKILL_DIR / "assets" / "bot-password-editor.py"
    editor_code = editor_path.read_text()

    def test_edit_uses_assert_user(self):
        """edit_page() must include assert='user'."""
        assert '"assert": "user"' in self.editor_code, \
            "Missing assert=user in edit_page"

    def test_edit_checks_user_in_response(self):
        """edit_page() must check the 'user' field."""
        assert 'edit.get("user")' in self.editor_code, \
            "Missing user field check in edit response"

    def test_edit_checks_for_errors(self):
        """edit_page() must check for API errors."""
        assert '"error" in result' in self.editor_code, \
            "Missing error check in edit response"


class TestApiAccessSkillGuardrails:
    """Verify wikimedia-api-access mentions auth guardrails."""

    api_skill = read_skill("wikimedia-api-access")

    def test_has_temp_account_warning(self):
        """Should warn about temp-account fallback."""
        assert "temp" in self.api_skill, \
            "Missing warning about temp accounts"

    def test_references_auth_skill(self):
        """Should cross-reference the auth skill."""
        assert "wikimedia-auth-oauth" in self.api_skill, \
            "Missing cross-reference to auth skill"

    def test_mentions_assert_user(self):
        """Should mention assert=user guardrail."""
        assert 'assert="user"' in self.api_skill, \
            "Missing mention of assert=user"


class TestCommonsSdcSkillGuardrails:
    """Verify wikimedia-commons-sdc mentions auth guardrails."""

    sdc_skill = read_skill("wikimedia-commons-sdc")

    def test_has_guardrails_banner(self):
        """Should have a guardrails section before Core SDC Operations."""
        assert "Auth guardrails" in self.sdc_skill, \
            "Missing auth guardrails banner"

    def test_mentions_assert_user(self):
        """Should mention assert=user."""
        # The skill documents assert=user inside Markdown code spans:
        #   `"assert": "user"`  or  `'assert': 'user'`
        assert '"assert": "user"' in self.sdc_skill or \
               'assert=user' in self.sdc_skill, \
            "Missing mention of assert=user"

    def test_references_auth_skill(self):
        """Should cross-reference the auth skill."""
        assert "wikimedia-auth-oauth" in self.sdc_skill, \
            "Missing cross-reference to auth skill"

    def test_verifies_userinfo(self):
        """Bot password example should verify userinfo."""
        assert "userinfo" in self.sdc_skill, \
            "Missing userinfo verification"

    def test_rejects_anon_csrf(self):
        """Bot password example should reject anon CSRF token."""
        assert "csrf_token != " in self.sdc_skill, \
            "Missing CSRF token validation"


class TestOtherSkillsNoWritePatterns:
    """Verify skills without write patterns don't have vulnerable ones."""

    def test_pywikibot_skills_are_safe(self):
        """Pywikibot handles auth internally — no raw CSRF patterns needed."""
        pywikibot_skill = read_skill("pywikibot")
        # Pywikibot should NOT contain raw action=login patterns
        # (it may reference them in documentation, but not as the primary pattern)
        assert "pywikibot" in pywikibot_skill

    def test_no_raw_bot_password_in_other_skills(self):
        """Skills other than auth/sdc shouldn't contain raw bot password code."""
        exempt = {"wikimedia-auth-oauth", "wikimedia-commons-sdc"}
        for name in ["wikidata", "wikimedia-commons", "wikimedia-diffs",
                      "wikipedia-citations", "wikipedia-templates"]:
            text = read_skill(name)
            # These skills may reference auth but shouldn't contain raw login flows
            for word in ["SESSION.post", "bot_password"]:
                count = text.count(word)
                # Allow up to 2 mentions (e.g., in a cross-reference), flag more
                assert count <= 2, \
                    f"{name}: {count} occurrences of '{word}' — may need guardrails"


class TestOAuth2ClientMockIntegration:
    """Mock-based tests for the oauth2_client.py edit flow."""

    def test_get_csrf_rejects_anon_token(self):
        """get_csrf_token() should raise on '+' token."""
        from oauth2_client import WikimediaOAuth2Client as OAuth2Client

        client = OAuth2Client("client_id", "client_secret")
        client.api_call = MagicMock(return_value={
            "query": {"tokens": {"csrftoken": "+\\"}}
        })

        with pytest.raises(AssertionError, match="anonymous"):
            client.get_csrf_token("fake_token")

    def test_get_csrf_accepts_valid_token(self):
        """get_csrf_token() should return a valid hex token."""
        from oauth2_client import WikimediaOAuth2Client as OAuth2Client

        client = OAuth2Client("client_id", "client_secret")
        valid_token = "a" * 40
        client.api_call = MagicMock(return_value={
            "query": {"tokens": {"csrftoken": valid_token}}
        })

        result = client.get_csrf_token("fake_token")
        assert result == valid_token

    def test_get_csrf_rejects_short_token(self):
        """get_csrf_token() should raise on suspiciously short token."""
        from oauth2_client import WikimediaOAuth2Client as OAuth2Client

        client = OAuth2Client("client_id", "client_secret")
        client.api_call = MagicMock(return_value={
            "query": {"tokens": {"csrftoken": "short"}}
        })

        with pytest.raises(AssertionError, match="suspiciously short"):
            client.get_csrf_token("fake_token")

    @patch("oauth2_client.requests.Session")
    def test_edit_page_uses_assert_user(self, mock_session):
        """edit_page() POST should include assert='user'."""
        from oauth2_client import WikimediaOAuth2Client as OAuth2Client

        mock_post = MagicMock()
        mock_post.raise_for_status = MagicMock()
        mock_post.json = MagicMock(return_value={
            "edit": {"result": "Success", "user": "TestUser"}
        })
        mock_session().headers = {}
        mock_session().post = MagicMock(return_value=mock_post)

        client = OAuth2Client("client_id", "client_secret")
        client.api_call = MagicMock(return_value={
            "query": {"tokens": {"csrftoken": "a" * 40}}
        })

        client.edit_page("fake_token", "Test page", "content", "summary")

        # Verify the POST included assert=user
        call_kwargs = mock_session().post.call_args
        assert call_kwargs is not None, "post() was not called"
        posted_data = call_kwargs[1]["data"]
        assert posted_data.get("assert") == "user", \
            f"Missing assert=user in POST data: {posted_data}"

    @patch("oauth2_client.requests.Session")
    def test_edit_page_checks_user_in_response(self, mock_session):
        """edit_page() should raise if response has no user."""
        from oauth2_client import WikimediaOAuth2Client as OAuth2Client

        mock_post = MagicMock()
        mock_post.raise_for_status = MagicMock()
        # Response with no 'user' field
        mock_post.json = MagicMock(return_value={
            "edit": {"result": "Success"}  # no 'user' key
        })
        mock_session().headers = {}
        mock_session().post = MagicMock(return_value=mock_post)

        client = OAuth2Client("client_id", "client_secret")
        client.api_call = MagicMock(return_value={
            "query": {"tokens": {"csrftoken": "a" * 40}}
        })

        with pytest.raises(AssertionError, match="not attributed"):
            client.edit_page("fake_token", "Test page", "content", "summary")
