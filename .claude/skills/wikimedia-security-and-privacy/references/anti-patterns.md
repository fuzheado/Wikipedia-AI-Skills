# Privacy & Security Anti-Patterns — Extended Catalog

## 1. Logging PII

### Anti-pattern: Logging raw request data
```python
# ❌ BAD
logger.info(f"Request from {request.remote_addr}: {request.headers.get('User-Agent')}")
logger.debug(f"Full API response: {response.json()}")  # May contain email, realname
```

### Fix: Strip PII before logging
```python
# ✅ GOOD
from privacy_cache import strip_sensitive_fields, strip_ips_from_text

safe_msg = strip_ips_from_text(f"Request received")
logger.info(safe_msg)

safe_data = strip_sensitive_fields(response.json())
logger.debug(f"API response: {safe_data}")
```

---

## 2. Storing User Data Indefinitely

### Anti-pattern: Persistent dictionary with no expiry
```python
# ❌ BAD
user_cache = {}  # Never expires, grows forever

def cache_user(username, data):
    user_cache[username] = data  # User data stored until process restart
```

### Fix: Use time-based expiry
```python
# ✅ GOOD
from privacy_cache import PrivacyCache

cache = PrivacyCache(ttl_hours=24)
cache.set("user:12345", {"editcount": 500})  # Auto-expires after 24h
```

---

## 3. Deanonymization via Edit Pattern Analysis

### Anti-pattern: Per-hour edit analysis
```python
# ❌ BAD — reveals time zone and sleep schedule
edits_by_hour = defaultdict(int)
for edit in edits:
    hour = edit["timestamp"][11:13]  # "14" = 2 PM UTC
    edits_by_hour[hour] += 1
return dict(edits_by_hour)
# If the user never edits between 02:00-08:00 UTC, they're likely
# sleeping then — reveals time zone!
```

### Fix: Aggregate coarsely
```python
# ✅ GOOD — monthly aggregation is safe
edits_by_month = defaultdict(int)
for edit in edits:
    month = edit["timestamp"][:7]  # "2026-06"
    edits_by_month[month] += 1
return dict(edits_by_month)
```

---

## 4. Cross-Wiki Deanonymization

### Anti-pattern: Linking accounts across projects
```python
# ❌ BAD — helps deanonymize users who maintain separate identities
def find_related_accounts(username, wiki):
    """Find same user on other wikis by edit pattern matching."""
    pattern = get_edit_pattern(username, wiki)
    related = []
    for other_wiki in all_wikis:
        for candidate in get_users(other_wiki):
            if edit_pattern_similar(pattern, get_edit_pattern(candidate, other_wiki)):
                related.append((other_wiki, candidate))
    return related
```

### Fix: Don't build this at all
This functionality should simply not exist. CentralAuth already links accounts
for users who choose to have unified logins — do not build alternative methods.

---

## 5. Exposing Suppressed Content Indicators

### Anti-pattern: Showing "[REDACTED]" placeholders
```python
# ❌ BAD — revealing that content was suppressed
if rev.get("suppressed"):
    return "[Content suppressed]"  # Even this leaks information!
```

### Fix: Omit entirely
```python
# ✅ GOOD — simply skip suppressed entries
safe_revisions = [r for r in all_revisions if not r.get("suppressed") and not r.get("deleted")]
```

---

## 6. Hardcoding Secrets in Source

### Anti-pattern: Token in source code
```python
# ❌ BAD
OAUTH_SECRET = "abc123def456"
BOT_PASSWORD = "my_secret_password"
```

### Fix: Environment variables
```python
# ✅ GOOD
import os
OAUTH_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")
BOT_PASSWORD = os.environ.get("BOT_PASSWORD")
if not OAUTH_SECRET:
    raise RuntimeError("OAUTH_CLIENT_SECRET environment variable is not set")
```

---

## 7. Not Checking Block Status Before Editing

### Anti-pattern: Blind edit attempts
```python
# ❌ BAD — will fail with confusing error
result = editor.edit("Some Page", "content", "my edit")
if "error" in result:
    print("Edit failed")  # User has no idea why
```

### Fix: Check first
```python
# ✅ GOOD
from safe_editor import SafeEditor

editor = SafeEditor(token)
check = editor.can_edit("Some Page")
if not check["can_edit"]:
    logger.warning(f"Edit blocked: {check['reason']}")
    return  # Graceful handling
result = editor.edit("Some Page", "content", "my edit")
```

---

## 8. Not Handling AbuseFilter Responses

### Anti-pattern: Ignoring AbuseFilter warnings
```python
# ❌ BAD
resp = session.post(api_url, data={"action": "edit", ...})
result = resp.json()
if result["edit"]["result"] == "Success":
    print("Edited!")  # But it may have been blocked by AbuseFilter
```

### Fix: Check AbuseFilter in the response
```python
# ✅ GOOD
resp = session.post(api_url, data={"action": "edit", ...})
result = resp.json()
edit_result = result.get("edit", {})
if edit_result.get("result") == "Failure":
    abuse = edit_result.get("abuseFilter", {})
    if abuse:
        print(f"AbuseFilter blocked: {abuse.get('description', 'unknown')}")
```

---

## 9. XSS via innerHTML in Gadgets

### Anti-pattern: Unsafe HTML injection
```javascript
// ❌ BAD
document.getElementById('output').innerHTML = userControlledData;

// ❌ BAD (jQuery)
$('#output').html(userControlledData);
```

### Fix: Safe DOM manipulation
```javascript
// ✅ GOOD
const el = document.getElementById('output');
el.textContent = userControlledData;  // Auto-escapes HTML

// ✅ GOOD (jQuery)
$('#output').text(userControlledData);
```

---

## 10. Exposing Raw API Error Messages

### Anti-pattern: Passing API errors to the user
```python
# ❌ BAD — API errors may contain internal info
@app.route("/api/edit")
def api_edit():
    try:
        result = editor.edit(title, text, summary)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # May leak internals
```

### Fix: Sanitize error messages
```python
# ✅ GOOD
@app.route("/api/edit")
def api_edit():
    try:
        result = editor.edit(title, text, summary)
        return jsonify({"status": result.get("edit", {}).get("result", "unknown")})
    except requests.HTTPError as e:
        logger.warning(f"Edit API error: {e}")
        return jsonify({"error": "An error occurred while editing. Please try again."}), 500
```

---

## 11. Storing IPs in Application Database

### Anti-pattern: Recording user IPs for "analytics"
```python
# ❌ BAD
INSERT INTO page_views (page, user_ip, timestamp) VALUES (%s, %s, %s)
# IPs should not be stored in application databases
```

### Fix: Use aggregate-only analytics
```python
# ✅ GOOD — count without identifying
from privacy_cache import AggregateCounter

counter = AggregateCounter()
counter.increment("page_views")
counter.increment(f"page:{page_id}:views")
```

---

## 12. Returning Full User Objects from API Endpoints

### Anti-pattern: Unfiltered user data in API responses
```python
# ❌ BAD
@app.route("/api/user/<username>")
def get_user(username):
    data = api_call(token, {"action": "query", "list": "users", "ususers": username, "usprop": "all"})
    return jsonify(data)
```

### Fix: Filter to safe fields
```python
# ✅ GOOD
@app.route("/api/user/<username>")
def get_user(username):
    data = api_call(token, {"action": "query", "list": "users", "ususers": username})
    user = data["query"]["users"][0]
    return jsonify({
        "name": user.get("name"),
        "editcount": user.get("editcount"),
        "registration": user.get("registration"),
        # Intentionally omitting: email, realname, groups
    })
```
