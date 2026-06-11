---
name: wikimedia-security-and-privacy
description: Build tools that respect Wikimedia user privacy and security — data minimization, suppressed/deleted revision handling, deanonymization risks, AbuseFilter and block awareness, XSS prevention in gadgets/apps, and data retention policies for Toolforge tools
depends_on: [wikimedia-api-access, wikimedia-auth-oauth, wikimedia-toolforge]
license: MIT
compatibility: opencode
last_verified: 2026-06-11
skill_discovery_hints:
  - keywords: ["privacy", "security", "data minimization", "PII", "deanonymization"]
  - keywords: ["suppressed revision", "deleted revision", "AbuseFilter", "block", "XSS"]
  - keywords: ["data retention", "Toolforge privacy", "user data", "permission check"]
---

> ⚠️ **Prerequisites:** This skill assumes you can authenticate API clients and
> check user rights. See **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)**
> for OAuth flows, bot passwords, CSRF tokens, and permission checking.
> See **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** for User-Agent
> headers and rate limiting.

---

## Overview

Every Wikimedia tool that processes editor data, makes edits, or serves a web
interface has **privacy and security responsibilities**. This skill covers the
Wikimedia-specific concerns that general web security guides miss.

This skill is organized into two main sections:

| Section | Concern | For |
|---------|---------|-----|
| **Privacy** (user-facing) | What data you collect, keep, and expose | Tools that display or log editor info |
| **Security** (internal-facing) | How to prevent exploits and respect wiki protections | Tools that edit, patrol, or run gadgets |

---

## Reference: Quick Decision Flow

```
You're building a tool that...
│
├─ Collects ANY data about users (usernames, IPs, timestamps)
│  → Read SOP: Data Minimization
│  → Read SOP: Data Retention
│  → Read SOP: Public Logs and Leaks
│
├─ Displays or ranks editor activity
│  → Read SOP: Deanonymization Risks
│  → Read SOP: Suppressed/Deleted Revisions
│
├─ Makes edits or interacts with wiki content
│  → Read SOP: Block Awareness
│  → Read SOP: AbuseFilter Awareness
│  → Read SOP: Permission-Aware Design
│  → See also: wikimedia-auth-oauth (CSRF tokens, credential storage)
│
├─ Loads in a user's browser (gadget, userscript, Toolforge app)
│  → Read SOP: XSS Prevention
│
└─ You're unsure what's allowed
   → Read the WMF Privacy Policy and TOU (see references)
```

---

## SOP: Data Minimization

### Rule: Collect the Minimum Data Needed

When using the Action API or OAuth profile endpoint, request only the fields
you actually need.

```python
# ❌ BAD — requests everything, including sensitive fields
profile = client.get_profile(token)
user_ip = profile.get("ip")  # Not even available, but demonstrates the mindset

# ✅ GOOD — request only what you need
def get_username_only(token: str) -> str:
    """Get just the username. No IP, no email, no real name."""
    profile = client.get_profile(token)
    return profile.get("username")
```

### OAuth Grant Scopes

When registering an OAuth consumer, request the **minimum** grants:

```python
# ❌ BAD — requesting all grants "just in case"
# Grants: edit, delete, protect, block, upload, rollback, userrights, ...
# If your token leaks, an attacker can delete every page you can edit.

# ✅ GOOD — only what the tool needs
# Grant: "Edit existing pages"  (and nothing else)
```

### Action API: Request Only the Fields You Need

```python
# ❌ BAD — dumps all user properties
params = {
    "action": "query",
    "list": "allusers",
    "aulimit": "max",
}

# ✅ GOOD — request only the fields needed
params = {
    "action": "query",
    "list": "allusers",
    "aulimit": "max",
    "auprop": "editcount|registration",  # No email, no blockinfo unless needed
}
```

**Sensitive fields to avoid unless essential:**

| Property | Contains | Risk |
|----------|----------|------|
| `email` | User's email address | PII — never expose publicly |
| `realname` | Real name (if provided) | PII — avoid unless required |
| `blockedby` | Admin who placed a block | Can identify admins in private actions |
| `blockreason` | Reason for a block | May contain private information |
| `userid` | Internal user ID | Can be used to track users across renames |

### Never Log Raw API Responses

```python
# ❌ BAD — logs everything including sensitive data
logger.debug(f"API response: {api_response}")

# ✅ GOOD — log only non-sensitive fields
def safe_log_response(response: dict) -> None:
    """Log API response without user PII."""
    safe = {k: v for k, v in response.items()
            if k not in ("email", "realname", "blockreason", "ip")}
    logger.debug(f"API response: {safe}")
```

---

## SOP: Deanonymization Risks

### What Not To Do

Some tools can inadvertently enable stalking or harassment. Avoid these patterns:

```python
# ❌ BAD — exposing edit patterns that reveal real-world information
def get_user_edit_times(username: str) -> dict:
    """Return a user's edit times. Can reveal time zone / sleep schedule."""
    pass  # Don't build this.

# ❌ BAD — cross-correlating accounts across wikis
def find_same_user_across_wikis(pattern: str) -> list:
    """Find accounts with similar edit patterns on different wikis.
    This can deanonymize users who maintain separate accounts."""
    pass  # Don't build this.

# ❌ BAD — displaying IP-derived geolocation
def show_user_location(username: str) -> str:
    """Show city/country derived from IP. Enables harassment."""
    pass  # Don't build this.
```

### Allowed vs. Not Allowed

| Action | Privacy Risk | Verdict |
|--------|-------------|---------|
| Show a user's edit count | Low — already public on user pages | ✅ OK |
| Show a user's recent contributions list | Low — already public | ✅ OK |
| Aggregate stats ("top 100 editors by edits") | Low — group, not individual | ✅ OK |
| Show a user's edit times by hour of day | Medium — reveals time zone / sleep schedule | ❌ Avoid |
| Cross-reference edits across unrelated wikis | High — deanonymizes | ❌ Never |
| Display IP geolocation derived from edits | High — enables stalking | ❌ Never |
| Build a "users who edit X also edit Y" graph | Medium — can reveal relationships | ❌ Avoid |
| Export a list of all editors of a page | Low — already in page history | ✅ OK if attributed to the page |

### Safe Aggregation Principle

When building statistics or leaderboards, **aggregate enough that individuals
cannot be identified**:

```python
# ✅ GOOD — group by month, not by day, to avoid identifying patterns
def edits_by_month(edits: list) -> dict:
    """Count edits per month. Single-day granularity could identify patterns."""
    result = {}
    for edit in edits:
        month = edit["timestamp"][:7]  # "2026-06"
        result[month] = result.get(month, 0) + 1
    return result

# ❌ BAD — per-hour granularity reveals sleep schedule / time zone
def edits_by_hour(edits: list) -> dict:
    for edit in edits:
        hour = edit["timestamp"][11:13]  # "14"
        ...
```

---

## SOP: Public Logs and Leaks

### Toolforge Web Service Logs

Toolforge web services automatically log requests. These logs contain
**IP addresses and User-Agent strings**:

```
2026-06-11 12:34:56 INFO "GET /api/search" 200 -
   from 192.0.2.1 (Mozilla/5.0 ...)
```

**Rules:**
1. **Do not expose `.toolforge-log` files publicly** — they contain IPs.
   These are stored in `/data/project/<tool>/logs/` and are already
   access-restricted by Toolforge.
2. **Do not echo raw request data** in error messages or responses.
3. **Do not store IPs in your application database** — use
   Toolforge's existing logs if you need debugging info.
4. **Do not pass log data to external services** (Sentry, Logstash, etc.)
   unless you strip IPs and User-Agents first.

### Stripping IPs from Log Output

```python
import re

def strip_ip_from_log(line: str) -> str:
    """Remove IP addresses from log lines before storage or display."""
    # IPv4
    line = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', line)
    # IPv6 (simplified)
    line = re.sub(r'\b[0-9a-fA-F:]{2,40}\b', '[IP]', line)
    return line

# Usage in a Flask app
@app.after_request
def sanitize_log(response):
    """Strip IPs from log messages before they reach stdout."""
    logging.getLogger().handlers[0].filters.append(
        lambda record: setattr(record, 'msg', strip_ip_from_log(record.msg)) or True
    )
    return response
```

### Never Return Sensitive Data in API Responses

```python
# ❌ BAD — returning user object with PII
@app.route("/api/profile")
def api_profile():
    user_data = get_user_data(user_id)
    return jsonify(user_data)  # May include email, realname, IP

# ✅ GOOD — return only safe fields
@app.route("/api/profile")
def api_profile():
    user_data = get_user_data(user_id)
    return jsonify({
        "username": user_data["username"],
        "edit_count": user_data["editcount"],
        "registration_date": user_data["registration"],
        # Intentionally omitting: email, realname, blockreason
    })
```

---

## SOP: Data Retention

### Why It Matters

Wikimedia's [Data Retention Guidelines](https://meta.wikimedia.org/wiki/Data_retention_guidelines)
state that data collected by tools should be retained only as long as necessary.
If your tool stores user data indefinitely, it becomes a privacy liability.

### Retention Rules

| Data Type | Max Retention | Notes |
|-----------|---------------|-------|
| OAuth access/refresh tokens | Until revoked by user | Must be deletable on request |
| Cached API responses with user data | 24 hours | Cache with `Cache-Control: private` |
| User IP addresses | **Do not store** | Use Toolforge logs for debugging |
| Aggregate statistics (no PII) | Indefinite | Safe if truly anonymous |
| User-identifiable logs | 90 days | After that, rotate or anonymize |

### Implementation Patterns

```python
import time
from datetime import datetime, timedelta

class UserDataCache:
    """Cache that auto-expires user data after TTL."""
    
    def __init__(self, ttl_hours: int = 24):
        self._cache = {}
        self._ttl = timedelta(hours=ttl_hours)
    
    def set(self, key: str, value: dict) -> None:
        """Store data with an expiration timestamp."""
        self._cache[key] = {
            "data": value,
            "expires_at": datetime.utcnow() + self._ttl,
        }
    
    def get(self, key: str) -> dict | None:
        """Get data if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if datetime.utcnow() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["data"]
    
    def delete_user_data(self, key: str) -> None:
        """Delete a specific user's data on request."""
        self._cache.pop(key, None)
    
    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        now = datetime.utcnow()
        expired = [k for k, v in self._cache.items()
                   if now > v["expires_at"]]
        for k in expired:
            del self._cache[k]
        return len(expired)


# Anonymous aggregate stats (safe to keep indefinitely)
class AggregateStats:
    """Store only counts, never individual user data."""
    
    def __init__(self):
        self.stats = {"total_users": 0, "total_edits": 0}
    
    def record_edit(self, username: str) -> None:
        """Increment counts without recording the username."""
        self.stats["total_users"] += 1
        self.stats["total_edits"] += 1
        # Note: username is discarded — we only increment counts
```

### User Data Deletion Policy

Every tool that stores user data should provide a deletion mechanism:

```python
@app.route("/api/delete-my-data", methods=["POST"])
@login_required
def delete_user_data():
    """Delete all data associated with the authenticated user."""
    username = session.get("profile", {}).get("username")
    if username:
        cache.delete_user_data(username)
        db.execute("DELETE FROM tool_data WHERE username = %s", (username,))
        log_action(f"Deleted data for user {username}")
    return jsonify({"status": "deleted"})
```

---

## SOP: XSS Prevention (Gadgets and Toolforge Apps)

### Context: Why XSS Matters on Wikimedia

Gadgets and user scripts run with the user's full session. An XSS vulnerability
in a popular gadget can compromise every user who has it enabled. Toolforge apps
that embed user-generated wikitext are also at risk.

### Never Trust Wikitext or User Input

```python
# ❌ BAD — directly embedding wikitext as HTML
html = f"<div>{page_content}</div>"

# ✅ GOOD — sanitize before rendering
import html

def render_safe_wikitext(wikitext: str) -> str:
    """Escape HTML entities in wikitext before rendering."""
    return html.escape(wikitext)
```

### Safe DOM Manipulation in Gadgets

```javascript
// ❌ BAD — innerHTML with user-controlled data
element.innerHTML = '<div>' + userControlled + '</div>';

// ✅ GOOD — use textContent or createElement
const div = document.createElement('div');
div.textContent = userControlled;
element.appendChild(div);

// ✅ GOOD — if you must set HTML, sanitize it first
element.textContent = '';  // Clear
const safe = document.createElement('div');
safe.textContent = userControlled;
element.appendChild(safe);
```

### Never Use `eval()` or Similar

```javascript
// ❌ BAD — eval with user-controlled data
const result = eval('(' + apiResponse + ')');

// ❌ BAD — jQuery's global-eval pattern
$.globalEval(someUserControlledString);

// ✅ GOOD — use JSON.parse for JSON
const data = JSON.parse(apiResponse);
```

### Content Security Policy for Toolforge Apps

```python
from flask import Flask
from flask_talisman import Talisman  # Optional: adds security headers

app = Flask(__name__)
Talisman(app, content_security_policy={
    'default-src': "'self'",
    'script-src': ["'self'", "https://tools-static.wmflabs.org"],
    'style-src': ["'self'", "https://tools-static.wmflabs.org"],
    'img-src': "'self' data:",
    # NEVER add 'unsafe-inline' or 'unsafe-eval' in production
})
```

### Safe MediaWiki API Responses in Gadgets

```javascript
// ❌ BAD — using mw.html.escape on user content that includes HTML
const userBio = data.query.pages[pageId].extract;
$('#bio').html(userBio);  // User-generated content may contain scripts

// ✅ GOOD — use mw.html.element or jQuery.text()
const userBio = data.query.pages[pageId].extract;
$('#bio').text(userBio);  // Escapes HTML automatically
```

---

## SOP: AbuseFilter and Block Awareness

### Why Check Before Acting

Tools that make edits or perform actions **must** check whether the user is
blocked and whether the action would trigger an AbuseFilter. Failure to do so
results in confusing errors and wasted API calls.

### Check Before Editing

```python
def can_user_edit(access_token: str, wiki: str = "en.wikipedia.org") -> dict:
    """Check if the authenticated user can edit on the target wiki.
    
    Returns:
        {"can_edit": True/False, "reason": "..."}
    """
    # Fetch user info with block status
    data = api_call(access_token, {
        "action": "query",
        "meta": "userinfo",
        "uiprop": "blockinfo|rights",
    }, wiki)
    
    userinfo = data["query"]["userinfo"]
    
    # Check block status
    if userinfo.get("blocked"):
        return {
            "can_edit": False,
            "reason": f"User is blocked: {userinfo.get('blockreason', 'No reason given')}"
        }
    
    # Check edit right
    if "edit" not in userinfo.get("rights", []):
        return {
            "can_edit": False,
            "reason": "User does not have the 'edit' right"
        }
    
    return {"can_edit": True, "reason": ""}


# Usage before making edits
def edit_page_safe(access_token, title, text, summary):
    """Edit a page, but only if the user can edit."""
    check = can_user_edit(access_token)
    if not check["can_edit"]:
        logger.warning(f"Edit blocked: {check['reason']}")
        return {"error": check["reason"]}
    # Proceed with edit...
```

### Handling AbuseFilter Warnings

When an edit triggers an AbuseFilter, the API returns an `abuseFilter` warning:

```python
def edit_page_with_abuse_filter_handling(
    access_token: str, title: str, text: str, summary: str
) -> dict:
    """Edit a page and handle AbuseFilter warnings gracefully."""
    result = edit_page(access_token, title, text, summary)
    
    # Check for AbuseFilter warnings
    edit_result = result.get("edit", {})
    if edit_result.get("result") == "Failure":
        abuse_info = edit_result.get("abuseFilter", {})
        if abuse_info:
            code = abuse_info.get("code", "unknown")
            description = abuse_info.get("description", "No description")
            return {
                "success": False,
                "reason": f"AbuseFilter triggered ({code}): {description}",
                "abuse_filter_code": code,
                "abuse_filter_description": description,
            }
    
    return result
```

### Check Page Protection Before Editing

```python
def check_page_protection(
    access_token: str, title: str, wiki: str = "en.wikipedia.org"
) -> dict:
    """Check if a page is protected and whether the user can edit it."""
    data = api_call(access_token, {
        "action": "query",
        "titles": title,
        "prop": "info",
        "inprop": "protection",
    }, wiki)
    
    pages = data["query"]["pages"]
    page_id = list(pages.keys())[0]
    page = pages[page_id]
    
    protections = page.get("protection", [])
    if not protections:
        return {"protected": False, "reason": ""}
    
    # Check user's rights against protection levels
    userinfo = api_call(access_token, {
        "action": "query",
        "meta": "userinfo",
        "uiprop": "rights",
    }, wiki)
    user_rights = userinfo["query"]["userinfo"].get("rights", [])
    
    for protection in protections:
        level = protection.get("level", "")
        if level == "autoconfirmed" and "autoconfirmed" not in user_rights:
            return {"protected": True, "reason": "Page is semi-protected"}
        if level == "extendedconfirmed" and "extendedconfirmed" not in user_rights:
            return {"protected": True, "reason": "Page is extended-confirmed protected"}
        if level == "sysop" and "delete" not in user_rights:
            return {"protected": True, "reason": "Page is fully protected"}
    
    return {"protected": False, "reason": ""}
```

---

## SOP: Suppressed and Deleted Revisions

### What They Are

- **Deleted revisions** (`action=history&hide=1`) — Hidden from public view
  but still visible to admins.
- **Suppressed/oversighted revisions** — Completely hidden from all
  non-oversight users. Used for private information (addresses, phone
  numbers, threats).

### How the API Behaves

```python
# Fetching recent changes without special parameters
data = api_call(access_token, {
    "action": "query",
    "list": "recentchanges",
    "rcprop": "title|timestamp|user",
})
# Deleted and suppressed revisions are simply NOT returned.
# You won't see them, and you shouldn't try to find them.

# Attempting to access deleted revisions
data = api_call(access_token, {
    "action": "query",
    "prop": "deletedrevisions",  # Requires 'deletedhistory' right
    "titles": "Some Page",
})
# Returns empty if you don't have the right.
```

### Rules for Tool Developers

1. **Never attempt to circumvent visibility.** If an edit is deleted or
   suppressed, respect that. Do not try to find it through other means
   (archives, web caches, external mirrors).

2. **Never display deleted revision content** even if you have the right
   to view it. If your tool runs with admin credentials, check visibility
   flags before displaying content:

```python
def safe_display_revision(rev: dict) -> dict | None:
    """Return revision data only if it's safe to display.
    
    Revision visibility flags:
    - suppressed=1: Content should not be shown to anyone
    - deleted=1: Content deleted from public view
    """
    if rev.get("suppressed") or rev.get("deleted"):
        return None  # Do not display
    return {
        "revid": rev["revid"],
        "content": rev.get("*"),
        "user": rev.get("user"),
    }
```

3. **Do not cache or archive deleted/suppressed content.** If you
   accidentally retrieve it, discard it immediately.

4. **Do not reveal that suppressed content exists.** Don't show
   "[REDACTED]" or similar indicators — that itself leaks information.
   Simply omit the entry.

---

## SOP: Permission-Aware Design

### The Principle

Every API action your tool performs should be **preceded by a permission check**.
Don't assume a user has rights — verify them and handle denial gracefully.

### Check Rights Before Acting

```python
REQUIRED_RIGHTS = {
    "edit": "edit",
    "delete": "delete",
    "protect": "protect",
    "block": "block",
    "rollback": "rollback",
    "patrol": "patrol",
    "upload": "upload",
    "move": "move",
}

def check_rights(
    access_token: str, required_actions: list[str],
    wiki: str = "en.wikipedia.org"
) -> dict:
    """Check that the user has all required rights.
    
    Args:
        access_token: OAuth Bearer token
        required_actions: List of actions the user wants to perform
        wiki: Target wiki
    
    Returns:
        {"has_all": True/False, "missing": [...], "user_rights": [...]}
    """
    data = api_call(access_token, {
        "action": "query",
        "meta": "userinfo",
        "uiprop": "rights",
    }, wiki)
    
    user_rights = data["query"]["userinfo"].get("rights", [])
    missing = []
    
    for action in required_actions:
        right = REQUIRED_RIGHTS.get(action)
        if right and right not in user_rights:
            missing.append(action)
    
    return {
        "has_all": len(missing) == 0,
        "missing": missing,
        "user_rights": user_rights,
    }


# Usage in a tool
def handle_batch_delete(access_token: str, pages: list[str]):
    """Delete multiple pages. Check permissions first."""
    check = check_rights(access_token, ["delete"])
    if not check["has_all"]:
        return {
            "error": "Cannot delete: missing required rights",
            "missing": check["missing"],
        }
    # Proceed with deletions...
```

### Graceful Degradation

When a user lacks a right, show a clear message and **offer alternatives**
rather than a hard failure:

```python
def perform_action(action: str, rights_check: dict) -> str | None:
    """Return a user-facing error message if the action can't be performed."""
    if not rights_check["has_all"]:
        missing = rights_check["missing"]
        if "delete" in missing:
            return "You don't have permission to delete. Would you like to nominate the page for deletion instead?"
        if "protect" in missing:
            return "You don't have permission to protect. You can request protection at WP:RFPP."
        if "block" in missing:
            return "You don't have permission to block. Report the user at WP:AIV."
        return f"Missing rights: {', '.join(missing)}"
    return None
```

---

## Guardrails

### ❌ Never Store IP Addresses
Toolforge already logs IPs. Your application should not store them too.
If you need request tracking, use a session ID instead.

### ❌ Never Expose Suppressed Content
If you have admin access and retrieve deleted/suppressed revisions, do not
display, cache, or forward them. Discard them immediately.

### ❌ Never Build User Profiles
Do not aggregate edit data to build behavior profiles, infer demographics,
or predict personal information about editors.

### ❌ Never Deanonymize
Do not cross-correlate accounts across wikis, expose edit patterns that
reveal time zones or schedules, or derive location data from IPs.

### ❌ Never Log Sensitive API Responses
Strip `email`, `realname`, `blockreason`, and `ip` fields from log output.

### ❌ Never Use `eval()` or Dynamic HTML in Gadgets
All user-controlled content must be escaped. Use `textContent`, not `innerHTML`.

### ❌ Never Assume Permission
Check user rights before every action. A user may lose rights between
when they logged in and when they click a button.

### ❌ Never Store Data Indefinitely
Implement automatic data expiration. Provide a user-facing deletion mechanism.

---

## Tooling

### 🔧 Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`scripts/check-tool-privacy.sh`](./scripts/check-tool-privacy.sh) | Scan your tool's source for common privacy issues | `./check-tool-privacy.sh /path/to/tool` |

### 🐍 Python Assets

| Asset | Purpose | Usage |
|-------|---------|-------|
| [`assets/safe_editor.py`](./assets/safe_editor.py) | Importable module: safe editing with block/protection/rights checks, AbuseFilter handling, and suppressed revision awareness | `from safe_editor import SafeEditor` |
| [`assets/privacy_cache.py`](./assets/privacy_cache.py) | Importable module: auto-expiring cache that strips PII from logged data | `from privacy_cache import PrivacyCache` |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/policy-links.md`](./references/policy-links.md) | Quick-reference links to WMF Privacy Policy, TOU, Data Retention Guidelines, and more |
| [`references/anti-patterns.md`](./references/anti-patterns.md) | Extended catalog of privacy and security anti-patterns with before/after examples |
