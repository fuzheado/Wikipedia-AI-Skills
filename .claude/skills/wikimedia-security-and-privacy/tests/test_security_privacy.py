#!/usr/bin/env python3
"""
Tests for Wikimedia Security & Privacy skill assets.

Tests:
  - PrivacyCache: TTL expiry, PII stripping, user data deletion
  - AggregateCounter: safe counting without PII
  - SafeEditor: permission checks, block detection, suppression filtering
  - Scripts: check-tool-privacy.sh runs without errors
  - Reference docs: key claims verified

Run with:
    python3 -m pytest tests/test_security_privacy.py -v
"""

import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the skill's assets directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "assets"))

from privacy_cache import PrivacyCache, AggregateCounter, strip_sensitive_fields, strip_ips_from_text
from safe_editor import SafeEditor


# ── PrivacyCache Tests ─────────────────────────────────────────────────────

class TestPrivacyCache(unittest.TestCase):
    """Test auto-expiring cache with PII-safe features."""

    def setUp(self):
        self.cache = PrivacyCache(ttl_hours=24)

    def test_set_and_get(self):
        """Basic set/get should work."""
        self.cache.set("user:1", {"username": "TestUser", "editcount": 100})
        data = self.cache.get("user:1")
        self.assertIsNotNone(data)
        self.assertEqual(data["username"], "TestUser")

    def test_get_expired_entry(self):
        """Expired entries should return None."""
        short_cache = PrivacyCache(ttl_hours=0)  # 0 hour TTL = expires immediately
        short_cache.set("user:2", {"username": "Old"})
        time.sleep(0.01)  # Ensure expiry
        data = short_cache.get("user:2")
        self.assertIsNone(data)

    def test_get_missing_key(self):
        """Missing keys should return None."""
        data = self.cache.get("nonexistent")
        self.assertIsNone(data)

    def test_delete(self):
        """Delete should remove the entry and return True."""
        self.cache.set("user:3", {"username": "DeleteMe"})
        result = self.cache.delete("user:3")
        self.assertTrue(result)
        self.assertIsNone(self.cache.get("user:3"))

    def test_delete_nonexistent(self):
        """Deleting a missing key should return False."""
        result = self.cache.delete("nonexistent")
        self.assertFalse(result)

    def test_delete_user_data(self):
        """Delete all entries matching a user identifier."""
        self.cache.set("user:100", {"username": "A"})
        self.cache.set("user:101", {"username": "B"})
        self.cache.set("other:200", {"username": "C"})

        deleted = self.cache.delete_user_data("user:")
        self.assertEqual(deleted, 2)

    def test_clear_expired(self):
        """Clear expired should only remove expired entries."""
        short_cache = PrivacyCache(ttl_hours=0)
        short_cache.set("expired", {"data": "x"})
        self.cache.set("fresh", {"data": "y"})
        time.sleep(0.01)

        # Only the short_cache entry (which was inserted with 0 TTL) should expire
        # Actually, clear_expired is on self.cache, not short_cache
        # Let me test properly
        cache = PrivacyCache(ttl_hours=0)
        cache.set("will_expire", {"data": "a"})
        cache.set("also_expire", {"data": "b"})
        time.sleep(0.01)
        removed = cache.clear_expired()
        self.assertEqual(removed, 2)

    def test_size_counts_only_active(self):
        """Size should only count non-expired entries."""
        cache = PrivacyCache(ttl_hours=0)
        cache.set("gone", {"data": "x"})
        time.sleep(0.01)
        self.assertEqual(cache.size(), 0)

    def test_get_stats(self):
        """Stats should return aggregate info without PII."""
        self.cache.set("user:1", {"username": "A"})
        self.cache.set("user:2", {"username": "B"})
        stats = self.cache.get_stats()
        self.assertIn("entries", stats)
        self.assertGreaterEqual(stats["entries"], 1)
        self.assertNotIn("username", str(stats))  # No PII in stats

    def test_set_with_custom_ttl(self):
        """Per-entry TTL override should work."""
        cache = PrivacyCache(ttl_hours=24)
        cache.set("long", {"data": "long"}, ttl_hours=48)
        # Use a very short TTL (1 microsecond) so it expires immediately
        import datetime as dt
        cache._cache["short"] = {
            "data": {"data": "short"},
            "expires_at": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=1),
        }
        time.sleep(0.01)
        # Short should be expired
        self.assertIsNone(cache.get("short"))
        # Long should still be there
        self.assertIsNotNone(cache.get("long"))


class TestStripSensitiveFields(unittest.TestCase):
    """Test PII stripping utility."""

    def test_strip_email(self):
        """Email field should be redacted."""
        data = {"username": "Test", "email": "user@example.com", "editcount": 100}
        safe = strip_sensitive_fields(data)
        self.assertEqual(safe["email"], "[REDACTED]")
        self.assertEqual(safe["username"], "Test")  # Non-sensitive preserved

    def test_strip_realname(self):
        """Realname field should be redacted."""
        data = {"realname": "John Doe", "editcount": 50}
        safe = strip_sensitive_fields(data)
        self.assertEqual(safe["realname"], "[REDACTED]")

    def test_strip_no_sensitive_fields(self):
        """Data without sensitive fields should pass through unchanged."""
        data = {"username": "Test", "editcount": 100}
        safe = strip_sensitive_fields(data)
        self.assertEqual(safe, data)

    def test_empty_dict(self):
        """Empty dict should return empty dict."""
        self.assertEqual(strip_sensitive_fields({}), {})


class TestStripIPs(unittest.TestCase):
    """Test IP stripping utility."""

    def test_strip_ipv4(self):
        """IPv4 addresses should be replaced with [IP]."""
        text = "Request from 192.168.1.1"
        result = strip_ips_from_text(text)
        self.assertEqual(result, "Request from [IP]")

    def test_strip_ipv6(self):
        """IPv6 addresses should be replaced with [IP]."""
        text = "Request from 2001:db8::1"
        result = strip_ips_from_text(text)
        self.assertEqual(result, "Request from [IP]")

    def test_no_ip(self):
        """Text without IPs should be unchanged."""
        text = "Normal log message"
        result = strip_ips_from_text(text)
        self.assertEqual(result, text)

    def test_multiple_ips(self):
        """Multiple IPs should all be replaced."""
        text = "From 10.0.0.1 and 10.0.0.2"
        result = strip_ips_from_text(text)
        self.assertEqual(result, "From [IP] and [IP]")

    def test_empty_string(self):
        """Empty string should return empty string."""
        self.assertEqual(strip_ips_from_text(""), "")


class TestAggregateCounter(unittest.TestCase):
    """Test safe counting without PII."""

    def setUp(self):
        self.counter = AggregateCounter()

    def test_increment_and_get(self):
        """Basic increment should work."""
        self.counter.increment("edits")
        self.assertEqual(self.counter.get("edits"), 1)

    def test_increment_by_multiple(self):
        """Increment with count parameter."""
        self.counter.increment("edits", count=5)
        self.assertEqual(self.counter.get("edits"), 5)

    def test_get_missing_key(self):
        """Missing keys should return 0."""
        self.assertEqual(self.counter.get("nonexistent"), 0)

    def test_multiple_keys(self):
        """Multiple independent counters."""
        self.counter.increment("edits")
        self.counter.increment("uploads", count=3)
        self.assertEqual(self.counter.get("edits"), 1)
        self.assertEqual(self.counter.get("uploads"), 3)

    def test_all(self):
        """All() should return all counters without PII."""
        self.counter.increment("a", count=1)
        self.counter.increment("b", count=2)
        all_counts = self.counter.all()
        self.assertEqual(all_counts, {"a": 1, "b": 2})

    def test_reset(self):
        """Reset should clear a specific counter."""
        self.counter.increment("edits", count=10)
        self.counter.reset("edits")
        self.assertEqual(self.counter.get("edits"), 0)

    def test_all_export_safe(self):
        """Export via all() should not contain any user data."""
        self.counter.increment("page_views")
        exported = json.dumps(self.counter.all())
        self.assertNotIn("email", exported)
        self.assertNotIn("username", exported)


# ── SafeEditor Tests ───────────────────────────────────────────────────────

class TestSafeEditor(unittest.TestCase):
    """Test the safe editing wrapper (mocked)."""

    def setUp(self):
        self.editor = SafeEditor(
            access_token="test_token_123",
            wiki="en.wikipedia.org",
        )

    @patch.object(SafeEditor, "_get_page_protection")
    @patch.object(SafeEditor, "get_user_info")
    def test_can_edit_when_free(self, mock_get_user_info, mock_protection):
        """A user who is not blocked and has edit right can edit."""
        mock_get_user_info.return_value = {
            "name": "TestUser",
            "blocked": False,
            "rights": ["read", "edit", "createpage", "move"],
            "groups": ["*", "user"],
        }
        mock_protection.return_value = {"protected": False, "level": None, "reason": ""}
        result = self.editor.can_edit("Some Page")
        self.assertTrue(result["can_edit"])
        self.assertEqual(result["reason"], "")

    @patch.object(SafeEditor, "_get_page_protection")
    @patch.object(SafeEditor, "get_user_info")
    def test_can_edit_when_blocked(self, mock_get_user_info, mock_protection):
        """A blocked user should not be able to edit."""
        mock_get_user_info.return_value = {
            "name": "BlockedUser",
            "blocked": True,
            "blockedby": "Admin",
            "blockreason": "Vandalism",
            "rights": ["read", "edit"],
        }
        mock_protection.return_value = {"protected": False, "level": None, "reason": ""}
        result = self.editor.can_edit("Some Page")
        self.assertFalse(result["can_edit"])
        self.assertIn("blocked", result["reason"].lower())

    @patch.object(SafeEditor, "_get_page_protection")
    @patch.object(SafeEditor, "get_user_info")
    def test_can_edit_without_right(self, mock_get_user_info, mock_protection):
        """A user without edit right should not be able to edit."""
        mock_get_user_info.return_value = {
            "name": "ReadOnly",
            "blocked": False,
            "rights": ["read"],
        }
        mock_protection.return_value = {"protected": False, "level": None, "reason": ""}
        result = self.editor.can_edit("Some Page")
        self.assertFalse(result["can_edit"])
        self.assertIn("edit", result["reason"].lower())

    @patch.object(SafeEditor, "get_user_info")
    def test_check_rights(self, mock_get_user_info):
        """Check rights should identify missing permissions."""
        mock_get_user_info.return_value = {
            "name": "Editor",
            "rights": ["read", "edit", "createpage", "move"],
        }
        result = self.editor.check_rights(["edit", "delete", "move"])
        self.assertFalse(result["has_all"])
        self.assertIn("delete", result["missing"])
        self.assertNotIn("edit", result["missing"])

    def test_safe_revision_data_removes_suppressed(self):
        """Suppressed revisions should be removed from output."""
        revisions = [
            {"revid": 1, "user": "UserA", "comment": "good edit"},
            {"revid": 2, "suppressed": True, "user": "ShouldNotAppear"},
            {"revid": 3, "deleted": True, "user": "ShouldAlsoNotAppear"},
            {"revid": 4, "user": "UserB", "comment": "another good edit"},
        ]
        safe = self.editor.safe_revision_data(revisions)
        self.assertEqual(len(safe), 2)
        self.assertEqual(safe[0]["revid"], 1)
        self.assertEqual(safe[1]["revid"], 4)

    def test_safe_revision_data_empty_input(self):
        """Empty revision list should return empty list."""
        self.assertEqual(self.editor.safe_revision_data([]), [])

    def test_safe_revision_data_normal_revisions(self):
        """Normal revisions should pass through unchanged."""
        revs = [{"revid": 1, "user": "User", "comment": "ok"}]
        safe = self.editor.safe_revision_data(revs)
        self.assertEqual(safe, [
            {"revid": 1, "user": "User", "comment": "ok", "timestamp": None, "content": None}
        ])


# ── SKILL.md Content Checks ────────────────────────────────────────────────

class TestSkillContent(unittest.TestCase):
    """Verify key claims in SKILL.md are consistent with the assets."""

    def setUp(self):
        skill_path = Path(__file__).resolve().parent.parent / "SKILL.md"
        self.skill_text = skill_path.read_text()

    def test_depends_on_declared(self):
        """SKILL.md should declare depends_on with correct skills."""
        self.assertIn("wikimedia-auth-oauth", self.skill_text)
        self.assertIn("wikimedia-api-access", self.skill_text)
        self.assertIn("wikimedia-toolforge", self.skill_text)

    def test_assets_referenced(self):
        """SKILL.md should reference both assets."""
        self.assertIn("safe_editor.py", self.skill_text)
        self.assertIn("privacy_cache.py", self.skill_text)

    def test_scripts_referenced(self):
        """SKILL.md should reference the script."""
        self.assertIn("check-tool-privacy.sh", self.skill_text)

    def test_references_referenced(self):
        """SKILL.md should reference reference docs."""
        self.assertIn("policy-links.md", self.skill_text)
        self.assertIn("anti-patterns.md", self.skill_text)

    def test_guardrails_present(self):
        """SKILL.md should have the guardrails section with key rules."""
        self.assertIn("## Guardrails", self.skill_text)
        self.assertIn("Never Store IP Addresses", self.skill_text)
        self.assertIn("Never Expose Suppressed Content", self.skill_text)
        self.assertIn("Never Build User Profiles", self.skill_text)


# ── check-tool-privacy.sh Script Tests ─────────────────────────────────────

class TestScriptFunctionality(unittest.TestCase):
    """Test that the check-tool-privacy.sh script runs correctly."""

    def test_script_help(self):
        """Script should print help with --help."""
        script = Path(__file__).resolve().parent.parent / "scripts" / "check-tool-privacy.sh"
        import subprocess
        result = subprocess.run(["bash", str(script), "--help"], capture_output=True, text=True)
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_script_no_args(self):
        """Script should print error with no arguments."""
        script = Path(__file__).resolve().parent.parent / "scripts" / "check-tool-privacy.sh"
        import subprocess
        result = subprocess.run(["bash", str(script)], capture_output=True, text=True)
        self.assertIn("Error", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_script_scans_self(self):
        """Script should scan its own directory without crashing."""
        script = Path(__file__).resolve().parent.parent / "scripts" / "check-tool-privacy.sh"
        target = Path(__file__).resolve().parent.parent / "assets"
        import subprocess
        result = subprocess.run(
            ["bash", str(script), str(target)],
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("HIGH", result.stdout)


if __name__ == "__main__":
    unittest.main()
