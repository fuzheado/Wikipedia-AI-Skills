#!/usr/bin/env python3
"""
bot-password-editor.py — Edit Wikipedia pages using a bot password.

A standalone script that demonstrates:
  - Bot password authentication (via action=login)
  - CSRF token fetching
  - Page editing with error handling
  - User rights checking before actions
  - Cookie-based session management

Usage:
  # Set credentials (or use environment variables)
  export WIKI_USERNAME="YourUsername"
  export WIKI_BOT_NAME="my-bot"
  export WIKI_BOT_PASSWORD="generated_password_from_special_botpasswords"

  # Read a page
  python3 bot-password-editor.py read "Sandbox"

  # Edit a page
  python3 bot-password-editor.py edit "Sandbox" --text "New content" --summary "Test edit"

  # Append to a page
  python3 bot-password-editor.py append "Sandbox" --text "\\n\\nNew section added by bot."

  # Check user rights
  python3 bot-password-editor.py rights

  # Dry-run mode (no actual edits)
  python3 bot-password-editor.py --dry-run edit "Sandbox" --text "Content"
"""

import argparse
import os
import sys
from typing import Optional

import requests

# ── Configuration ──────────────────────────────────────────────────────────

WIKI = os.environ.get("WIKI", "https://en.wikipedia.org")
API = f"{WIKI}/w/api.php"

# Read credentials from environment
WIKI_USERNAME = os.environ.get("WIKI_USERNAME", "")
WIKI_BOT_NAME = os.environ.get("WIKI_BOT_NAME", "")
WIKI_BOT_PASSWORD = os.environ.get("WIKI_BOT_PASSWORD", "")

# ── Bot Password Client ────────────────────────────────────────────────────

class BotPasswordClient:
    """A client that authenticates with a bot password and can edit pages."""

    def __init__(self, username: str, bot_name: str, bot_password: str,
                 wiki_api: str = API, dry_run: bool = False):
        self.api = wiki_api
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BotPasswordEditor/1.0 (https://example.com; user@example.com) EditBot"
        })

        # Normalize: spaces → underscores (⚠️ critical for MediaWiki API)
        normalized = username.replace(" ", "_")
        self.bot_full = f"{normalized}@{bot_name}"
        self.bot_password = bot_password
        self.logged_in = False

    def login(self) -> bool:
        """Log in using the bot password. Returns True on success."""
        # Step 1: Get login token
        token_resp = self._api_get({
            "action": "query",
            "meta": "tokens",
            "type": "login",
        })
        if "query" not in token_resp:
            print(f"Error: Failed to get login token. Response: {token_resp}")
            return False
        login_token = token_resp["query"]["tokens"]["logintoken"]

        # Step 2: Log in
        login_resp = self._api_post({
            "action": "login",
            "lgname": self.bot_full,
            "lgpassword": self.bot_password,
            "lgtoken": login_token,
        })
        result = login_resp.get("login", {}).get("result", "Unknown")
        if result == "Success":
            self.logged_in = True
            return True
        else:
            print(f"Login failed: {result}")
            if "login" in login_resp:
                print(f"  Details: {login_resp['login']}")
            return False

    def get_csrf_token(self) -> str:
        """Fetch a CSRF token for write actions."""
        if not self.logged_in:
            raise RuntimeError("Not logged in. Call login() first.")
        resp = self._api_get({
            "action": "query",
            "meta": "tokens",
            "type": "csrf",
        })
        token = resp["query"]["tokens"]["csrftoken"]
        if token == "+\\":
            # The anonymous placeholder — something is wrong with the session
            raise RuntimeError(
                "Got anonymous CSRF token ('+\\\\'). Login may have failed "
                "or the session was lost."
            )
        return token

    def get_user_info(self) -> dict:
        """Fetch current user info and rights."""
        resp = self._api_get({
            "action": "query",
            "meta": "userinfo",
            "uiprop": "rights|blockinfo|groups",
        })
        return resp["query"]["userinfo"]

    def check_right(self, right: str) -> bool:
        """Check if the authenticated user has a specific right."""
        info = self.get_user_info()
        return right in info.get("rights", [])

    def read_page(self, title: str) -> Optional[str]:
        """Read the current wikitext of a page. Returns None on failure."""
        resp = self._api_get({
            "action": "parse",
            "page": title,
            "prop": "wikitext",
        })
        if "parse" in resp:
            return resp["parse"]["wikitext"]["*"]
        # Try the raw action API instead
        resp = self._api_get({
            "action": "raw",
            "title": title,
        })
        if isinstance(resp, dict) and "raw" in resp:
            return resp["raw"]
        if isinstance(resp, str):
            return resp
        print(f"Error reading page: {resp.get('error', {}).get('info', 'Unknown error')}")
        return None

    def edit_page(self, title: str, text: str, summary: str = "") -> dict:
        """Edit a page. Returns the API response."""
        if not self.check_right("edit"):
            print("Error: User does not have the 'edit' right. Aborting.")
            return {"error": {"info": "Missing 'edit' right"}}

        if self.dry_run:
            print(f"[DRY RUN] Would edit '{title}' with summary '{summary}'")
            print(f"[DRY RUN] Text length: {len(text)} chars")
            return {"dry_run": True}

        csrf = self.get_csrf_token()
        resp = self._api_post({
            "action": "edit",
            "title": title,
            "text": text,
            "summary": summary,
            "token": csrf,
        })
        return resp

    def append_to_page(self, title: str, text: str, summary: str = "") -> dict:
        """Append text to an existing page."""
        if self.dry_run:
            print(f"[DRY RUN] Would append to '{title}' with summary '{summary}'")
            print(f"[DRY RUN] Appending: {text[:200]}...")
            return {"dry_run": True}

        # Read current content
        current = self.read_page(title)
        if current is None:
            # Page doesn't exist — create it
            return self.edit_page(title, text, summary or "Created page")
        return self.edit_page(title, current + text, summary or "Appended text")

    def _api_get(self, params: dict) -> dict:
        """Make a GET request to the MediaWiki API."""
        params["format"] = "json"
        resp = self.session.get(self.api, params=params)
        resp.raise_for_status()
        return resp.json()

    def _api_post(self, data: dict) -> dict:
        """Make a POST request to the MediaWiki API."""
        data["format"] = "json"
        resp = self.session.post(self.api, data=data)
        resp.raise_for_status()
        return resp.json()


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Edit Wikipedia pages using a bot password",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s read "Sandbox"
  %(prog)s edit "Sandbox" --text "New content" --summary "Test"
  %(prog)s append "Sandbox" --text "\\nNew section"
  %(prog)s rights
  %(prog)s --dry-run edit "Sandbox" --text "Content"
        """
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate without making actual edits")
    parser.add_argument("--wiki", default=WIKI,
                        help=f"Wiki URL (default: {WIKI})")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read a page's wikitext")
    read_parser.add_argument("title", help="Page title to read")

    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit a page")
    edit_parser.add_argument("title", help="Page title to edit")
    edit_parser.add_argument("--text", required=True, help="New page content")
    edit_parser.add_argument("--summary", default="Bot edit", help="Edit summary")

    # Append command
    append_parser = subparsers.add_parser("append", help="Append text to a page")
    append_parser.add_argument("title", help="Page title")
    append_parser.add_argument("--text", required=True, help="Text to append")
    append_parser.add_argument("--summary", default="Bot edit", help="Edit summary")

    # Rights command
    subparsers.add_parser("rights", help="Check user rights")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Validate credentials
    if not all([WIKI_USERNAME, WIKI_BOT_NAME, WIKI_BOT_PASSWORD]):
        print("Error: Set WIKI_USERNAME, WIKI_BOT_NAME, and WIKI_BOT_PASSWORD")
        print("  export WIKI_USERNAME='YourUsername'")
        print("  export WIKI_BOT_NAME='my-bot'")
        print("  export WIKI_BOT_PASSWORD='password_from_wiki'")
        sys.exit(1)

    client = BotPasswordClient(
        username=WIKI_USERNAME,
        bot_name=WIKI_BOT_NAME,
        bot_password=WIKI_BOT_PASSWORD,
        wiki_api=f"{args.wiki}/w/api.php",
        dry_run=args.dry_run,
    )

    print(f"Logging in as {WIKI_USERNAME}@{WIKI_BOT_NAME}...")
    if not client.login():
        print("Login failed. Check your credentials.")
        sys.exit(1)
    print("Login successful!")

    if args.command == "read":
        content = client.read_page(args.title)
        if content is not None:
            print(f"\n--- {args.title} ---")
            print(content)
        else:
            sys.exit(1)

    elif args.command == "edit":
        result = client.edit_page(args.title, args.text, args.summary)
        if "error" in result:
            print(f"Error: {result['error']['info']}")
            sys.exit(1)
        edit_result = result.get("edit", {})
        if edit_result.get("result") == "Success":
            print(f"Edit successful! (revision {edit_result.get('newrevid', '?')})")
        else:
            print(f"Edit result: {result}")

    elif args.command == "append":
        result = client.append_to_page(args.title, args.text, args.summary)
        if isinstance(result, dict):
            if "error" in result:
                print(f"Error: {result['error']['info']}")
                sys.exit(1)
            edit_result = result.get("edit", {})
            if edit_result.get("result") == "Success":
                print(f"Append successful! (revision {edit_result.get('newrevid', '?')})")
            else:
                print(f"Append result: {result}")
        else:
            print(result)

    elif args.command == "rights":
        info = client.get_user_info()
        print(f"\nUsername: {info['name']}")
        print(f"User ID: {info['id']}")
        print(f"Groups: {', '.join(info.get('groups', []))}")
        print(f"Rights ({len(info.get('rights', []))}):")
        for right in sorted(info.get("rights", [])):
            print(f"  • {right}")
        if info.get("blocked"):
            print("\n⚠️  User is BLOCKED!")
        print(f"Edit count: {info.get('editcount', '?')}")


if __name__ == "__main__":
    main()
