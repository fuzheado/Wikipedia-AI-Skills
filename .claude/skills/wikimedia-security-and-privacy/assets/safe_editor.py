#!/usr/bin/env python3
"""
safe_editor.py — Safe page editing with Wikimedia authentication.

An importable module that wraps the MediaWiki edit API with safety checks:
  - Block status verification before editing
  - Page protection level checks
  - User rights verification
  - AbuseFilter warning handling
  - Suppressed/deleted revision awareness
  - CSRF token lifecycle management

Usage:
    from safe_editor import SafeEditor

    editor = SafeEditor(access_token="your_oauth_token")
    
    # Check before editing
    result = editor.can_edit("Sandbox")
    if result["can_edit"]:
        response = editor.edit("Sandbox", "New content", "Test edit")
    else:
        print(f"Cannot edit: {result['reason']}")
"""

import logging
from typing import Optional
import requests

logger = logging.getLogger("safe_editor")


class SafeEditor:
    """Safe page editing client with privacy and security checks.
    
    Wraps every edit operation with permission checks, block detection,
    protection level evaluation, and AbuseFilter handling.
    """
    
    def __init__(
        self,
        access_token: str,
        wiki: str = "en.wikipedia.org",
        user_agent: str = "",
    ):
        """
        Args:
            access_token: OAuth 2.0 Bearer token or bot password session token
            wiki: Wiki domain (default: en.wikipedia.org)
            user_agent: User-Agent string
        """
        self.access_token = access_token
        self.wiki = wiki
        self.api_url = f"https://{wiki}/w/api.php"
        
        default_ua = "SafeEditor/1.0 (https://example.com; user@example.com)"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or default_ua,
            "Authorization": f"Bearer {access_token}",
        })
    
    # ── Permission Checks ──────────────────────────────────────────────────
    
    def get_user_info(self) -> dict:
        """Fetch the authenticated user's info, rights, and block status."""
        resp = self.session.get(self.api_url, params={
            "action": "query",
            "meta": "userinfo",
            "uiprop": "rights|blockinfo|groups",
            "format": "json",
        })
        resp.raise_for_status()
        return resp.json()["query"]["userinfo"]
    
    def can_edit(self, title: str) -> dict:
        """Check if the user can edit a specific page.
        
        Returns:
            {"can_edit": bool, "reason": str, "details": dict}
        """
        userinfo = self.get_user_info()
        reasons = []
        
        # Check 1: Is the user blocked?
        if userinfo.get("blocked"):
            reasons.append(
                f"User is blocked: {userinfo.get('blockreason', 'No reason given')}"
            )
        
        # Check 2: Does the user have the 'edit' right?
        rights = userinfo.get("rights", [])
        if "edit" not in rights:
            reasons.append("User does not have the 'edit' right")
        
        # Check 3: Is the page protected beyond the user's level?
        protection = self._get_page_protection(title)
        if protection["protected"]:
            reasons.append(protection["reason"])
        
        return {
            "can_edit": len(reasons) == 0,
            "reason": " | ".join(reasons),
            "details": {
                "blocked": userinfo.get("blocked", False),
                "rights": rights[:15],  # First 15 rights
                "protection": protection,
            },
        }
    
    def _get_page_protection(self, title: str) -> dict:
        """Check if a page is protected and whether the user can edit it."""
        resp = self.session.get(self.api_url, params={
            "action": "query",
            "titles": title,
            "prop": "info",
            "inprop": "protection",
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()
        
        pages = data["query"]["pages"]
        page_id = list(pages.keys())[0]
        page = pages[page_id]
        
        protections = page.get("protection", [])
        if not protections:
            return {"protected": False, "level": None, "reason": ""}
        
        userinfo = self.get_user_info()
        user_rights = userinfo.get("rights", [])
        
        for prot in protections:
            level = prot.get("level", "")
            if level == "autoconfirmed" and "autoconfirmed" not in user_rights:
                return {"protected": True, "level": level,
                        "reason": "Page is semi-protected"}
            if level == "extendedconfirmed" and "extendedconfirmed" not in user_rights:
                return {"protected": True, "level": level,
                        "reason": "Page is extended-confirmed protected"}
            if level == "sysop" and "delete" not in user_rights:
                return {"protected": True, "level": level,
                        "reason": "Page is fully protected"}
        
        return {"protected": False, "level": None, "reason": ""}
    
    def check_rights(self, required_actions: list[str]) -> dict:
        """Check that the user has all required rights.
        
        Args:
            required_actions: e.g. ["edit", "delete", "move"]
        
        Returns:
            {"has_all": bool, "missing": list[str], "user_rights": list[str]}
        """
        RIGHT_MAP = {
            "edit": "edit",
            "delete": "delete",
            "protect": "protect",
            "block": "block",
            "rollback": "rollback",
            "patrol": "patrol",
            "upload": "upload",
            "move": "move",
        }
        
        userinfo = self.get_user_info()
        user_rights = userinfo.get("rights", [])
        missing = []
        
        for action in required_actions:
            right = RIGHT_MAP.get(action)
            if right and right not in user_rights:
                missing.append(action)
        
        return {
            "has_all": len(missing) == 0,
            "missing": missing,
            "user_rights": user_rights,
        }
    
    # ── Editing ────────────────────────────────────────────────────────────
    
    def get_csrf_token(self) -> str:
        """Fetch a CSRF token for write operations."""
        resp = self.session.get(self.api_url, params={
            "action": "query",
            "meta": "tokens",
            "type": "csrf",
            "format": "json",
        })
        resp.raise_for_status()
        token = resp.json()["query"]["tokens"]["csrftoken"]
        if token == "+\\":
            raise RuntimeError("Anonymous CSRF token — auth may have failed")
        return token
    
    def edit(
        self,
        title: str,
        text: str,
        summary: str = "",
        check_first: bool = True,
    ) -> dict:
        """Edit a page, with optional pre-check.
        
        Args:
            title: Page title to edit
            text: New wikitext content
            summary: Edit summary
            check_first: If True, check block/protection/rights before editing
        
        Returns:
            API response with edit status, or error dict
        """
        if check_first:
            check = self.can_edit(title)
            if not check["can_edit"]:
                logger.warning(f"Edit blocked: {check['reason']}")
                return {"edit": {"result": "Failure", "reason": check["reason"]}}
        
        csrf = self.get_csrf_token()
        
        resp = self.session.post(self.api_url, data={
            "action": "edit",
            "title": title,
            "text": text,
            "summary": summary,
            "token": csrf,
            "format": "json",
        })
        resp.raise_for_status()
        result = resp.json()
        
        # Check for AbuseFilter warnings
        edit_result = result.get("edit", {})
        if edit_result.get("result") == "Failure":
            abuse = edit_result.get("abuseFilter", {})
            if abuse:
                logger.warning(
                    f"AbuseFilter triggered: {abuse.get('code', 'unknown')}"
                )
        
        return result
    
    # ── Suppressed Revision Safety ─────────────────────────────────────────
    
    def safe_revision_data(self, revisions: list[dict]) -> list[dict]:
        """Filter revision data to exclude suppressed/deleted content.
        
        Use this before displaying revision data to users.
        
        Args:
            revisions: List of revision dicts from the API
        
        Returns:
            Filtered list with suppressed/deleted revisions removed
        """
        safe = []
        for rev in revisions:
            if rev.get("suppressed") or rev.get("deleted"):
                # Do not display, do not note, do not log
                continue
            safe.append({
                "revid": rev.get("revid"),
                "user": rev.get("user"),
                "timestamp": rev.get("timestamp"),
                "comment": rev.get("comment"),
                "content": rev.get("*"),
            })
        return safe
