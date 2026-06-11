#!/usr/bin/env python3
"""
privacy_cache.py — Auto-expiring cache with PII-safe logging.

An importable module that provides:
  - Time-based expiration for cached data (default 24h TTL)
  - Automatic stripping of PII fields from logged data
  - Per-user deletion mechanism
  - Aggregate-only stats tracking (no individual user data)

Usage:
    from privacy_cache import PrivacyCache

    cache = PrivacyCache(ttl_hours=24)
    cache.set("user:12345", {"username": "Example", "editcount": 500})
    data = cache.get("user:12345")      # Returns None if expired
    cache.delete_user_data("user:12345")
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger("privacy_cache")

# Fields that should never appear in logs or export
SENSITIVE_FIELDS = frozenset({
    "email", "realname", "blockreason", "ip", "device",
    "phone", "address", "location", "coordinates",
})


def strip_sensitive_fields(data: dict) -> dict:
    """Return a copy of the dict with sensitive fields removed.
    
    Use this before logging or displaying API responses.
    """
    return {
        k: ("[REDACTED]" if k in SENSITIVE_FIELDS else v)
        for k, v in data.items()
    }


def strip_ips_from_text(text: str) -> str:
    """Remove IP addresses from a string (for log sanitization)."""
    # IPv4
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', text)
    # IPv6 (simplified)
    text = re.sub(r'\b[0-9a-fA-F:]{2,40}\b', '[IP]', text)
    return text


class PrivacyCache:
    """Auto-expiring cache with PII stripping and per-user deletion.
    
    Features:
      - Per-entry TTL (default 24 hours)
      - Bulk expiration sweep
      - Per-user data deletion
      - Safe logging (PII fields stripped automatically)
    """
    
    def __init__(self, ttl_hours: int = 24):
        """
        Args:
            ttl_hours: Default time-to-live in hours (default: 24)
        """
        self._ttl = timedelta(hours=ttl_hours)
        self._cache: dict[str, dict] = {}
    
    def set(self, key: str, value: dict, ttl_hours: Optional[int] = None) -> None:
        """Store data with an expiration timestamp.
        
        Args:
            key: Cache key (e.g., "user:<id>")
            value: Data to cache
            ttl_hours: Override TTL for this entry (uses default if None)
        """
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self._ttl
        entry = {
            "data": value,
            "expires_at": datetime.now(timezone.utc).replace(tzinfo=None) + ttl,
        }
        self._cache[key] = entry
        
        # Log without PII
        safe = strip_sensitive_fields(value)
        logger.debug(f"Cache SET {key}: {safe}")
    
    def get(self, key: str) -> Optional[dict]:
        """Get data if not expired. Returns None if expired or missing."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if datetime.now(timezone.utc).replace(tzinfo=None) > entry["expires_at"]:
            del self._cache[key]
            logger.debug(f"Cache EXPIRED {key}")
            return None
        return entry["data"]
    
    def delete(self, key: str) -> bool:
        """Delete a specific entry. Returns True if it existed."""
        if key in self._cache:
            del self._cache[key]
            logger.info(f"Cache DELETE {key}")
            return True
        return False
    
    def delete_user_data(self, user_identifier: str) -> int:
        """Delete all cache entries for a user (by key prefix matching).
        
        Args:
            user_identifier: Any part of the key that identifies the user,
                             e.g. "user:12345" or just "12345"
        
        Returns:
            Number of entries deleted
        """
        to_delete = [k for k in self._cache if user_identifier in k]
        for k in to_delete:
            del self._cache[k]
        if to_delete:
            logger.info(f"Cache user data deleted: {len(to_delete)} entries for {user_identifier}")
        return len(to_delete)
    
    def clear_expired(self) -> int:
        """Remove all expired entries.
        
        Returns:
            Number of entries removed.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expired = [k for k, v in self._cache.items()
                   if now > v["expires_at"]]
        for k in expired:
            del self._cache[k]
        if expired:
            logger.debug(f"Cache sweep: removed {len(expired)} expired entries")
        return len(expired)
    
    def size(self) -> int:
        """Return the number of entries currently in the cache."""
        self.clear_expired()
        return len(self._cache)
    
    def get_stats(self) -> dict:
        """Return aggregate statistics (no PII).
        
        Returns:
            {"entries": int, "oldest_entry_age_hours": float}
        """
        self.clear_expired()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        ages = [(now - e["expires_at"] + self._ttl).total_seconds() / 3600
                for e in self._cache.values()]
        return {
            "entries": len(self._cache),
            "oldest_entry_age_hours": max(ages) if ages else 0,
        }


class AggregateCounter:
    """Count events without storing individual user data.
    
    Safe for indefinite retention — no PII is stored.
    
    Usage:
        counter = AggregateCounter()
        counter.increment("edits")
        counter.increment("edits", count=5)
        print(counter.get("edits"))  # 6
    """
    
    def __init__(self):
        self._counts: dict[str, int] = {}
    
    def increment(self, key: str, count: int = 1) -> None:
        """Increment a counter. No user data is recorded."""
        self._counts[key] = self._counts.get(key, 0) + count
    
    def get(self, key: str) -> int:
        """Get the current count for a key."""
        return self._counts.get(key, 0)
    
    def all(self) -> dict[str, int]:
        """Get all counters (safe to export — no PII)."""
        return dict(self._counts)
    
    def reset(self, key: str) -> None:
        """Reset a specific counter."""
        self._counts.pop(key, None)
