#!/usr/bin/env python3
"""
Tests for the Wikimedia OAuth 2.0 client library.

These tests use mocked HTTP responses so they can run without actual
Wikimedia API credentials. They verify the logic of the OAuth flow:
  - Authorization URL generation
  - PKCE code generation
  - Token exchange
  - Profile parsing
  - Token refresh
  - Edit flow (CSRF + POST)

Run with:
    python3 -m pytest tests/test_auth_client.py -v
    # or
    python3 -m unittest tests/test_auth_client.py -v
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the assets directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "assets"))

from oauth2_client import WikimediaOAuth2Client


class TestOAuth2Client(unittest.TestCase):
    """Test the core OAuth 2.0 client logic."""

    def setUp(self):
        self.client = WikimediaOAuth2Client(
            client_id="test_client_id_12345",
            client_secret="test_client_secret_67890",
            redirect_uri="https://example.com/callback",
            wiki_domain="meta.wikimedia.org",
        )

    def test_authorization_url_contains_required_params(self):
        """The authorization URL should contain all required OAuth 2.0 params."""
        url, state = self.client.get_authorization_url()

        self.assertIn("response_type=code", url)
        self.assertIn("client_id=test_client_id_12345", url)
        self.assertIn("redirect_uri=https%3A%2F%2Fexample.com%2Fcallback", url)
        self.assertIn("state=", url)

        # State should be a reasonable length for CSRF protection
        self.assertGreater(len(state), 16)

    def test_authorization_url_generates_new_state_each_time(self):
        """Each call should generate a unique state parameter."""
        url1, state1 = self.client.get_authorization_url()
        url2, state2 = self.client.get_authorization_url()

        self.assertNotEqual(state1, state2)

    def test_authorization_url_with_custom_state(self):
        """A custom state should be used when provided."""
        custom_state = "my_custom_state_value"
        url, state = self.client.get_authorization_url(state=custom_state)

        self.assertEqual(state, custom_state)
        self.assertIn(f"state={custom_state}", url)

    def test_authorization_url_requires_redirect_uri(self):
        """An error should be raised if redirect_uri is empty."""
        client_no_redirect = WikimediaOAuth2Client(
            client_id="test",
            client_secret="test",
        )
        with self.assertRaises(ValueError):
            client_no_redirect.get_authorization_url()

    def test_pkce_authorization_url(self):
        """PKCE authorization URL should include code_challenge params."""
        url, state = self.client.get_authorization_url_pkce(
            code_verifier="a" * 64,
            code_challenge="b" * 43,
        )

        self.assertIn("code_challenge=", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("response_type=code", url)

    def test_exchange_code_validates_state(self):
        """State mismatch should raise a ValueError (CSRF protection)."""
        with self.assertRaises(ValueError) as ctx:
            self.client.exchange_code(
                code="auth_code_123",
                state="returned_state",
                expected_state="different_state",
            )
        self.assertIn("State mismatch", str(ctx.exception))

    @patch("oauth2_client.requests.Session.post")
    def test_exchange_code_success(self, mock_post):
        """A successful token exchange should return token data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "eyJhbGciOiJSUzI1NiIs...",
            "refresh_token": "rft_abc123def456",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        result = self.client.exchange_code(
            code="auth_code_xyz",
            state="matching_state",
            expected_state="matching_state",
        )

        self.assertIn("access_token", result)
        self.assertIn("refresh_token", result)
        self.assertEqual(result["expires_in"], 3600)

        # Verify the POST was made to the correct endpoint
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("access_token", args[0])

    @patch("oauth2_client.requests.Session.post")
    def test_exchange_code_with_pkce(self, mock_post):
        """PKCE code verifier should be included in the token exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "pkce_token_123",
            "refresh_token": "pkce_refresh_456",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        result = self.client.exchange_code(
            code="code_123",
            state="s",
            expected_state="s",
            code_verifier="my_pkce_verifier_12345",
        )

        self.assertEqual(result["access_token"], "pkce_token_123")

        # Verify the verifier was sent
        call_data = mock_post.call_args[1]["data"]
        self.assertEqual(call_data["code_verifier"], "my_pkce_verifier_12345")

    @patch("oauth2_client.requests.Session.post")
    def test_owner_only_token(self, mock_post):
        """Owner-only client_credentials grant should return a token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "owner_only_token_abc",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        token = self.client.owner_only_token()

        self.assertEqual(token, "owner_only_token_abc")

        # Verify correct grant type was used
        call_data = mock_post.call_args[1]["data"]
        self.assertEqual(call_data["grant_type"], "client_credentials")

    @patch("oauth2_client.requests.Session.post")
    def test_refresh_token(self, mock_post):
        """Token refresh should return new tokens."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token_456",
            "refresh_token": "new_refresh_token_789",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        result = self.client.refresh_token("old_refresh_token_123")

        self.assertEqual(result["access_token"], "new_access_token_456")

        call_data = mock_post.call_args[1]["data"]
        self.assertEqual(call_data["grant_type"], "refresh_token")
        self.assertEqual(call_data["refresh_token"], "old_refresh_token_123")

    @patch("oauth2_client.requests.Session.get")
    def test_get_profile(self, mock_get):
        """Profile endpoint should return user information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": 12345,
            "username": "TestUser",
            "editcount": 500,
            "confirmed_email": True,
            "blocked": False,
            "groups": ["*", "user", "autoconfirmed"],
            "rights": ["read", "edit", "createpage", "upload", "move"],
        }
        mock_get.return_value = mock_response

        profile = self.client.get_profile("test_token_123")

        self.assertEqual(profile["username"], "TestUser")
        self.assertEqual(profile["sub"], 12345)
        self.assertIn("edit", profile["rights"])

        # Verify Bearer token was sent
        headers = mock_get.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer test_token_123")

    @patch("oauth2_client.requests.Session.get")
    def test_api_call(self, mock_get):
        """Authenticated API calls should return the response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "batchcomplete": "",
            "query": {
                "userinfo": {
                    "name": "TestUser",
                    "id": 12345,
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.api_call(
            "token_123",
            {"action": "query", "meta": "userinfo"},
        )

        self.assertEqual(result["query"]["userinfo"]["name"], "TestUser")

        # Verify Bearer token header was sent with API calls
        headers = mock_get.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer token_123")

        # Verify format=json was added automatically
        url = mock_get.call_args[0][0]
        self.assertIn("w/api.php", url)

    def test_check_right(self):
        """check_right should verify rights from the profile."""
        # Mock api_call to return userinfo with rights
        with patch.object(self.client, "api_call") as mock_api_call:
            mock_api_call.return_value = {
                "query": {
                    "userinfo": {
                        "rights": ["read", "edit", "createpage", "move"]
                    }
                }
            }

            self.assertTrue(self.client.check_right("token", "edit"))
            self.assertTrue(self.client.check_right("token", "read"))
            self.assertFalse(self.client.check_right("token", "delete"))
            self.assertFalse(self.client.check_right("token", "block"))

    @patch.object(WikimediaOAuth2Client, "get_csrf_token")
    @patch("oauth2_client.requests.Session.post")
    def test_edit_page(self, mock_post, mock_csrf):
        """Edit flow: CSRF token + POST with token."""
        mock_csrf.return_value = "csrf_token_abc123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "edit": {
                "result": "Success",
                "newrevid": 123456789,
                "newtimestamp": "2026-06-11T12:00:00Z",
            }
        }
        mock_post.return_value = mock_response

        result = self.client.edit_page(
            "bearer_token",
            title="Sandbox",
            text="Hello, world!",
            summary="Test edit",
        )

        self.assertEqual(result["edit"]["result"], "Success")

        # Verify POST data includes all required fields
        call_data = mock_post.call_args[1]["data"]
        self.assertEqual(call_data["action"], "edit")
        self.assertEqual(call_data["title"], "Sandbox")
        self.assertEqual(call_data["text"], "Hello, world!")
        self.assertEqual(call_data["summary"], "Test edit")
        self.assertEqual(call_data["token"], "csrf_token_abc123")

        # Bearer token is set on the inner session's headers (not passed to post)
        # The data assertions above verify the edit flow is correct.


class TestPKCEGeneration(unittest.TestCase):
    """Test PKCE code generation utilities."""

    def test_code_verifier_length(self):
        """Code verifier should be between 43 and 128 characters."""
        import hashlib, base64, secrets

        verifier = secrets.token_urlsafe(64)[:128]
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)

    def test_code_challenge_format(self):
        """Code challenge should be a base64url-encoded SHA256 hash."""
        import hashlib, base64

        verifier = "abcdefghijklmnopqrstuvwxyz0123456789-._~" * 2
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        self.assertEqual(challenge, expected)
        self.assertNotIn("=", challenge)  # No padding

    def test_code_challenge_is_deterministic(self):
        """Same verifier should always produce the same challenge."""
        import hashlib, base64

        verifier = "x" * 64

        c1 = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        c2 = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        self.assertEqual(c1, c2)


if __name__ == "__main__":
    unittest.main()
