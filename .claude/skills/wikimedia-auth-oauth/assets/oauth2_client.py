#!/usr/bin/env python3
"""
oauth2-client.py — Reusable OAuth 2.0 client library for Wikimedia.

This module provides a clean, importable client for the Wikimedia OAuth 2.0
Authorization Code Grant and Client Credentials Grant flows.

Usage:
    from oauth2_client import WikimediaOAuth2Client

    # For a web app (Authorization Code Grant):
    client = WikimediaOAuth2Client(
        client_id="your_key",
        client_secret="your_secret",
        redirect_uri="https://example.com/callback"
    )
    auth_url, state = client.get_authorization_url()
    # Redirect user to auth_url...
    # On callback:
    tokens = client.exchange_code(code, state, expected_state)
    profile = client.get_profile(tokens["access_token"])
    result = client.edit_page(tokens["access_token"], "Sandbox", "Hello", "Test")

    # For an owner-only tool (Client Credentials Grant):
    client = WikimediaOAuth2Client(client_id="key", client_secret="secret")
    token = client.owner_only_token()
    profile = client.get_profile(token)
"""

import os
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import requests


class WikimediaOAuth2Client:
    """
    OAuth 2.0 client for Wikimedia authentication.

    Supports:
      - Authorization Code Grant (public web apps)
      - Client Credentials Grant (owner-only tools)
      - PKCE (non-confidential clients)
      - Token refresh
      - Authenticated API calls and page editing
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "",
        wiki_domain: str = "meta.wikimedia.org",
        user_agent: str = "",
    ):
        """
        Initialize the OAuth 2.0 client.

        Args:
            client_id: Consumer key from consumer registration
            client_secret: Consumer secret from consumer registration
            redirect_uri: Callback URL (required for Authorization Code Grant)
            wiki_domain: Wiki to authenticate against (default: meta.wikimedia.org)
            user_agent: Custom User-Agent string
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.wiki_domain = wiki_domain
        self._oauth_base = f"https://{wiki_domain}/rest.php/oauth2"

        default_ua = "WikimediaOAuth2Client/1.0 (https://example.com; user@example.com)"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or default_ua
        })

    # ── Authorization Code Grant ───────────────────────────────────────────

    def get_authorization_url(self, state: Optional[str] = None) -> tuple:
        """
        Generate the URL to redirect the user to for authorization.

        Args:
            state: Optional CSRF state token (auto-generated if not provided)

        Returns:
            (authorization_url, state) — store state in user session for verification.
        """
        if not self.redirect_uri:
            raise ValueError("redirect_uri is required for Authorization Code Grant")

        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        url = f"{self._oauth_base}/authorize?{urlencode(params)}"
        return url, state

    def get_authorization_url_pkce(
        self, code_verifier: str, code_challenge: str, state: Optional[str] = None
    ) -> tuple:
        """
        Generate authorization URL with PKCE for non-confidential clients.

        Args:
            code_verifier: PKCE code verifier (random string, 43-128 chars)
            code_challenge: PKCE code challenge = SHA256(base64url(code_verifier))
            state: Optional CSRF state token

        Returns:
            (authorization_url, state)
        """
        if not self.redirect_uri:
            raise ValueError("redirect_uri is required for Authorization Code Grant")

        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        url = f"{self._oauth_base}/authorize?{urlencode(params)}"
        return url, state

    def exchange_code(
        self, code: str, state: str, expected_state: str,
        code_verifier: Optional[str] = None
    ) -> dict:
        """
        Exchange an authorization code for access and refresh tokens.

        Args:
            code: The 'code' parameter from the callback
            state: The 'state' parameter from the callback
            expected_state: The state you stored before redirecting
            code_verifier: PKCE code verifier (if using PKCE)

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "token_type": "Bearer"
            }

        Raises:
            ValueError: If state doesn't match (possible CSRF attack)
        """
        if state != expected_state:
            raise ValueError(
                "State mismatch — possible CSRF attack. Aborting."
            )

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        resp = self.session.post(
            f"{self._oauth_base}/access_token",
            data=data,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Client Credentials Grant (Owner-Only) ──────────────────────────────

    def owner_only_token(self) -> str:
        """
        Get an access token for an owner-only consumer using the
        Client Credentials Grant. No browser redirect needed.

        Returns:
            The access token string.
        """
        resp = self.session.post(
            f"{self._oauth_base}/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    # ── Token Refresh ──────────────────────────────────────────────────────

    def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token.

        Args:
            refresh_token: The refresh token from a previous exchange

        Returns:
            New token data with access_token, refresh_token, expires_in
        """
        resp = self.session.post(
            f"{self._oauth_base}/access_token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ── Profile / Identity ─────────────────────────────────────────────────

    def get_profile(self, access_token: str) -> dict:
        """
        Get the authenticated user's profile from the OAuth resource endpoint.

        Returns:
            {
                "sub": 12345,
                "username": "ExampleUser",
                "editcount": 1500,
                "confirmed_email": true,
                "blocked": false,
                "groups": [...],
                "rights": [...],
                "realname": "...",      # Only with permission
                "email": "..."          # Only with permission
            }
        """
        resp = self.session.get(
            f"{self._oauth_base}/resource/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Authenticated API Calls ────────────────────────────────────────────

    def api_call(
        self, access_token: str, params: dict,
        wiki: str = "en.wikipedia.org"
    ) -> dict:
        """
        Make an authenticated Action API call.

        Args:
            access_token: A valid Bearer access token
            params: API parameters (e.g., {"action": "query", ...})
            wiki: Wiki domain to call (default: en.wikipedia.org)

        Returns:
            API response as a dict
        """
        params["format"] = "json"
        api_url = f"https://{wiki}/w/api.php"
        resp = self.session.get(
            api_url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()

    def get_csrf_token(
        self, access_token: str, wiki: str = "en.wikipedia.org"
    ) -> str:
        """Fetch a CSRF token for write operations.

        Returns:
            A validated CSRF token string.

        Raises:
            AssertionError: If the token is anonymous (not authenticated).
        """
        data = self.api_call(access_token, {
            "action": "query",
            "meta": "tokens",
            "type": "csrf",
        }, wiki)
        csrf = data["query"]["tokens"]["csrftoken"]
        # 🛡️ Guardrail: Reject anonymous CSRF token
        assert csrf != "+\\", \
            "CSRF token is anonymous — the OAuth session is not authenticated. " \
            "Check your access_token is valid and not expired."
        assert len(csrf) > 10, \
            f"CSRF token suspiciously short ({len(csrf)} chars)"
        return csrf

    def edit_page(
        self,
        access_token: str,
        title: str,
        text: str,
        summary: str = "",
        wiki: str = "en.wikipedia.org",
    ) -> dict:
        """
        Edit a wiki page using the authenticated user's credentials.

        Requires the consumer to have the 'Edit existing pages' grant.

        Args:
            access_token: A valid Bearer access token
            title: Page title to edit
            text: New wikitext content
            summary: Edit summary
            wiki: Wiki domain (default: en.wikipedia.org)

        Returns:
            API response from the edit action
        """
        csrf = self.get_csrf_token(access_token, wiki)
        api_url = f"https://{wiki}/w/api.php"

        # Use a fresh session for the POST to avoid mixing GET params
        post_session = requests.Session()
        post_session.headers.update(self.session.headers)
        post_session.headers["Authorization"] = f"Bearer {access_token}"

        resp = post_session.post(api_url, data={
            "action": "edit",
            "title": title,
            "text": text,
            "summary": summary,
            "token": csrf,
            "assert": "user",        # 🛡️ Guardrail: reject if not logged in
            "format": "json",
        })
        resp.raise_for_status()
        result = resp.json()

        # 🛡️ Guardrail: verify the edit was attributed to a user
        if "error" in result:
            raise RuntimeError(
                f"Edit failed: {result['error']['code']} — {result['error']['info']}"
            )
        edit = result.get("edit", {})
        assert edit.get("user"), \
            f"Edit not attributed to any user — anonymous fallback. Response: {result}"

        return result

    def check_right(
        self, access_token: str, right: str,
        wiki: str = "en.wikipedia.org"
    ) -> bool:
        """Check if the authenticated user has a specific right."""
        data = self.api_call(access_token, {
            "action": "query",
            "meta": "userinfo",
            "uiprop": "rights",
        }, wiki)
        return right in data["query"]["userinfo"].get("rights", [])


# ── CLI Test Mode ──────────────────────────────────────────────────────────

def main():
    """Run a quick test of the client against the Wikimedia API."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Wikimedia OAuth 2.0 client")
    parser.add_argument("--client-id", envvar="OAUTH_CLIENT_ID",
                        help="OAuth consumer key (or set OAUTH_CLIENT_ID)")
    parser.add_argument("--client-secret", envvar="OAUTH_CLIENT_SECRET",
                        help="OAuth consumer secret (or set OAUTH_CLIENT_SECRET)")
    parser.add_argument("--test", action="store_true",
                        help="Test owner-only token fetch and profile")
    args = parser.parse_args()

    # Fall back to environment variables
    client_id = args.client_id or os.environ.get("OAUTH_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("OAUTH_CLIENT_SECRET")
    access_token = os.environ.get("OAUTH_ACCESS_TOKEN")

    if not client_id or not client_secret:
        print("Error: OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET must be set")
        print("  export OAUTH_CLIENT_ID='your_consumer_key'")
        print("  export OAUTH_CLIENT_SECRET='your_consumer_secret'")
        sys.exit(1)

    client = WikimediaOAuth2Client(client_id, client_secret)

    if args.test:
        print("Testing owner-only token fetch...")
        try:
            token = client.owner_only_token()
            print(f"✅ Token obtained: {token[:30]}...")
        except Exception as e:
            print(f"❌ Token fetch failed: {e}")
            print("  (This is expected for non-owner-only consumers)")
            token = access_token

    if token or access_token:
        token = token or access_token
        print(f"\nTesting profile endpoint...")
        try:
            profile = client.get_profile(token)
            print(f"✅ Profile retrieved")
            print(f"   Username: {profile.get('username', 'N/A')}")
            print(f"   User ID:  {profile.get('sub', 'N/A')}")
            print(f"   Groups:   {', '.join(profile.get('groups', []))}")
            print(f"   Rights:   {len(profile.get('rights', []))} rights")
        except Exception as e:
            print(f"❌ Profile fetch failed: {e}")

        print(f"\nTesting API call...")
        try:
            data = client.api_call(token, {
                "action": "query",
                "meta": "userinfo",
                "uiprop": "editcount",
            })
            ui = data["query"]["userinfo"]
            print(f"✅ API call successful")
            print(f"   Authenticated as: {ui['name']}")
            print(f"   Edit count: {ui.get('editcount', '?')}")
        except Exception as e:
            print(f"❌ API call failed: {e}")
    else:
        print("\nNo token available to test. Use --test for owner-only, or")
        print("set OAUTH_ACCESS_TOKEN environment variable with a valid token.")


if __name__ == "__main__":
    main()
