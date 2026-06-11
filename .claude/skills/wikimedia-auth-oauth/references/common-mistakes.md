# Common Auth Mistakes — Extended Reference

## 1. Credential Leakage

### Leaking via Git

```bash
# ❌ BAD: committing .env or config files with secrets
git add .env
git commit -m "Add config"
git push  # Secret is now public forever

# ✅ GOOD: use .gitignore
echo ".env" >> .gitignore
echo "*.secrets" >> .gitignore
echo "config.local.*" >> .gitignore
```

### Leaking via Environment Dumps

```bash
# ❌ BAD: dumping environment in debug output
print(os.environ)  # Everything, including secrets

# ✅ GOOD: only log non-sensitive values
safe_config = {k: v for k, v in os.environ.items() if "SECRET" not in k and "PASSWORD" not in k}
print(safe_config)
```

### Leaking in Error Messages

```python
# ❌ BAD: including credential in error
raise Exception(f"Login failed for {username} with password {password}")

# ✅ GOOD: log only what's safe
raise Exception(f"Login failed for user {username}")
```

---

## 2. Session Mismanagement

### Using a Single Session Across Users

```python
# ❌ BAD: global session with one user's auth
global_session = requests.Session()
global_session.headers["Authorization"] = f"Bearer {user_a_token}"

# Later, user B's request uses user A's token!
def handle_request(user_token):
    return global_session.get(API_URL)  # Still user A's token!

# ✅ GOOD: per-request or per-user session
def handle_request(user_token):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {user_token}"
    return session.get(API_URL)
```

### Not Rotating Stale Tokens

```python
# ❌ BAD: using the same token forever
token = load_from_disk("access_token.txt")
# Token expired 3 hours ago — all calls will fail with 401

# ✅ GOOD: check expiry and refresh
def get_token():
    token_data = load_from_disk("tokens.json")
    if time.time() >= token_data["expires_at"]:
        new_tokens = refresh_access_token(token_data["refresh_token"])
        save_to_disk("tokens.json", new_tokens)
        return new_tokens["access_token"]
    return token_data["access_token"]
```

---

## 3. CSRF Token Mistakes

### Using Anonymous CSRF Token for Authenticated Edits

The literal string `+\\` (backslash) is the CSRF token placeholder for
non-authenticated contexts. If you see `+\\` as your CSRF token, you
haven't logged in successfully.

### Reusing CSRF Tokens Across Requests

CSRF tokens are single-use for write actions. Fetch a fresh token for
each write operation. Reading the token is free and not rate-limited.

### Omitting the CSRF Token Entirely

Every `action=edit`, `action=delete`, `action=move`, `action=protect`,
`action=upload`, `action=rollback`, and `action=watch` call requires
a CSRF token. The API returns `"missingtoken"` or `"invalidtoken"`
errors if the token is omitted or wrong.

---

## 4. Bot Password Specific Mistakes

### Creating Bot Passwords with Too Many Rights

```python
# ❌ BAD: selecting all grants "just in case"
# Rights: edit, delete, protect, block, upload, rollback, userrights...

# ✅ GOOD: minimal grants
# Rights: edit existing pages, high-volume text querying
```

### Losing the Generated Password

Bot passwords are shown exactly once at creation. If you lose it,
you must delete the bot password and create a new one. There is no
"forgot password" option for bot passwords.

### Using Bot Passwords in Client-Side Code

```python
# ❌ BAD: bot password in browser JavaScript
fetch('/api.php', { headers: { 'Authorization': 'Bearer ' + botPassword } })
# Anyone can read this from the page source!

# ✅ GOOD: bot password stays server-side
# The browser talks to your server; your server uses the bot password.
```

---

## 5. OAuth 1.0a Specific Mistakes

### Forgetting the `title` Parameter

OAuth 1.0a signed requests MUST include the `title` parameter:

```python
# ❌ BAD
params = {"oauth_callback": "oob"}
# Missing 'title' — request will fail

# ✅ GOOD
params = {"title": "Special:OAuth/initiate", "oauth_callback": "oob"}
```

### Incorrect Signature Methods

Wikimedia OAuth 1.0a supports `HMAC-SHA1` and `RSA-SHA1`. Using a
different method (e.g., `PLAINTEXT`) will fail.

### Not Treating Tokens as Opaque

OAuth 1.0a tokens (request token, access token) are opaque strings.
Don't parse them, assume their format, or try to extract data from them.

---

## 6. OAuth 2.0 Specific Mistakes

### Not Validating State Parameter

```python
# ❌ BAD: ignoring state — vulnerable to CSRF
code = request.args["code"]
tokens = exchange_code(code)  # No state check!

# ✅ GOOD: validate state
code = request.args["code"]
state = request.args["state"]
if state != session.pop("oauth_state", None):
    abort(401, "State mismatch — possible CSRF attack")
tokens = exchange_code(code, state, expected_state)
```

### Exposing the Client Secret

```python
# ❌ BAD: client secret in client-side code
const CLIENT_SECRET = "abc123def456"

# ✅ GOOD: client secret is server-side only
# The browser never sees it.
```

### Not Using PKCE for Non-Confidential Clients

If your app is a single-page app or mobile app that cannot securely
store a client secret, you MUST use PKCE (Proof Key for Code Exchange).
Without it, your app is vulnerable to authorization code interception.

### Ignoring Token Expiry

Access tokens from the Authorization Code Grant typically expire after
1 hour. Always check `expires_in` and have a refresh strategy:

```python
# ❌ BAD: assuming tokens never expire
token_data = exchange_code(code, state, expected_state)
save_token(token_data["access_token"])  # Will break in 1 hour

# ✅ GOOD: store refresh token and expiry
token_data = exchange_code(code, state, expected_state)
save_token({
    "access_token": token_data["access_token"],
    "refresh_token": token_data["refresh_token"],
    "expires_at": time.time() + token_data["expires_in"],
})
```

### Using the Wrong Grant Type

```python
# ❌ BAD: using client_credentials for a public web app
# client_credentials is for owner-only consumers only!

# ✅ GOOD: public web app uses authorization_code
# owner-only tool uses client_credentials
```

---

## 7. General Wikimedia API Mistakes

### Not Sending User-Agent

Auth or no auth, every request needs a descriptive User-Agent.

### Not Handling 401 vs 403 vs 429

| Status | Meaning | What To Do |
|--------|---------|------------|
| 401 | Unauthorized (bad token) | Refresh/reauth |
| 403 | Forbidden (bad UA or no permission) | Check User-Agent and user rights |
| 429 | Rate limited | Wait and retry with Retry-After |

### Confusing Wikipedia API with Meta API for Auth

OAuth consumer registration is on **meta** (`meta.wikimedia.org`) for
cross-wiki consumers. Bot passwords are per-wiki
(`en.wikipedia.org/wiki/Special:BotPasswords`).

---

## 8. Security Anti-Patterns

### Shared Bot Passwords

Never share bot passwords across team members. Each person should have
their own bot password. If someone leaves, you can revoke just their
access.

### Tokens in URLs (Logs)

```python
# ❌ BAD: token appears in server logs
# GET /api/edit?title=Foo&text=Bar&token=abc123

# ✅ GOOD: token in Authorization header (may still be logged depending on config)
# Consider using POST for write actions instead
```

### Not Using HTTPS

Wikimedia APIs require HTTPS. Any tool that sends credentials over HTTP
is leaking them. This is especially important for callback URLs in OAuth
flows.
