---
name: wikimedia-auth-oauth
description: Authenticate Wikimedia API clients for editing, patrol, upload, and user-specific operations — OAuth 1.0a/2.0 flows, bot passwords, CSRF tokens, permission checks, and secure credential storage for standalone tools and web apps
depends_on: [wikimedia-api-access, wikimedia-error-handling, wikimedia-toolforge]
license: MIT
compatibility: opencode
last_verified: 2026-06-11
---

> ⚠️ **User-Agent required:** All API calls below need a descriptive `User-Agent` header.
> See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.

> 💡 **Not sure which auth method?** See the [Authentication Decision Flow](#reference-authentication-decision-flow) at the end of this skill.

---

## Overview

Wikimedia provides three authentication mechanisms for programmatic access:

| Method | Best For | Rate Limits | Setup Effort |
|--------|----------|-------------|--------------|
| **Bot passwords** | Personal bots, cron jobs, single-user scripts | Higher (bot flag) | Low — create at `Special:BotPasswords` |
| **OAuth 2.0** | Public web apps, multi-user tools (recommended for new apps) | Higher (OAuth flag) | Medium — register consumer, implement auth code flow |
| **OAuth 1.0a** | Legacy tools, tools needing `/identify` JWT | Higher (OAuth flag) | Medium — requires signature process |
| **`action=login`** | Quick scripts, internal tools only | Standard user rate | Low — but exposes password; prefer bot passwords |

## SOP: Bot Passwords (Personal Bots)

Bot passwords are the simplest way to authenticate a single-user script or bot.
They avoid exposing your main account password and can be easily revoked.

### Create a Bot Password

1. Go to `https://en.wikipedia.org/wiki/Special:BotPasswords` (or equivalent on any wiki)
2. Click **"Create a new bot password"**
3. Enter a **Bot name** (e.g., `my-archiver-bot`)
4. Select the **grants** (permissions) your bot needs — be minimal:
   - For editing: `Edit existing pages`, `Create, edit, and move pages`
   - For patrol: `Patrol pages`
   - For uploads: `Upload new files`
   - For reading: `High-volume text querying`
5. Click **"Create"**
6. Copy the generated password — **it will never be shown again**

### Use a Bot Password

```python
import requests

WIKI = "https://en.wikipedia.org/w/api.php"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "MyBot/1.0 (https://example.com; user@example.com) ArchiverBot"
})

def login(bot_username: str, bot_password: str) -> str:
    """Log in with a bot password.

    Returns the authenticated username on success.
    Raises AssertionError if login fails — never silently falls back to anonymous.
    """
    # Step 1: Get login token
    token_resp = SESSION.get(WIKI, params={
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json",
    }).json()
    login_token = token_resp["query"]["tokens"]["logintoken"]

    # Step 2: Log in (username format: "YourAccount@BotName")
    # ⚠️ Spaces in username must be replaced with underscores
    login_resp = SESSION.post(WIKI, data={
        "action": "login",
        "lgname": bot_username,        # e.g. "My_Account@my-bot"
        "lgpassword": bot_password,
        "lgtoken": login_token,
        "format": "json",
    }).json()

    # 🛡️ Guardrail: Assert login succeeded
    assert login_resp["login"]["result"] == "Success", \
        f"Login failed: {login_resp['login'].get('reason', login_resp['login']['result'])}"

    # 🛡️ Guardrail: Verify the authenticated user matches expectations
    user_resp = SESSION.get(WIKI, params={
        "action": "query",
        "meta": "userinfo",
        "format": "json",
    }).json()
    actual_user = user_resp["query"]["userinfo"]["name"]
    # bot_username is "Account@BotName" — strip @BotName to get the canonical username
    expected_user = bot_username.split("@")[0].replace("_", " ")
    assert actual_user == expected_user, \
        f"Logged in as {actual_user}, expected {expected_user}"

    return actual_user

# Usage:
# authed_user = login("YourWikiUsername@MyBotName", "generated_password_from_special_botpasswords")
# print(f"Authenticated as {authed_user}")
```

> **⚠️ Always normalize spaces to underscores** in the `lgname` parameter.
> `"My Account@my-bot"` will fail silently. Use `"My_Account@my-bot"`.

### Get a CSRF Token for Editing

After logging in, fetch a CSRF token to make write actions:

```python
def get_csrf_token() -> str:
    resp = SESSION.get(WIKI, params={
        "action": "query",
        "meta": "tokens",
        "type": "csrf",
        "format": "json",
    }).json()
    csrf = resp["query"]["tokens"]["csrftoken"]

    # 🛡️ Guardrail: Reject anonymous CSRF token
    # An anonymous session returns `+\` as the CSRF token.
    # An authenticated session returns a 40+ character hex string.
    assert csrf != "+\\", \
        "CSRF token is anonymous (got '+\\'). Call login() first and verify it succeeded."
    assert len(csrf) > 10, \
        f"CSRF token suspiciously short ({len(csrf)} chars): {csrf[:10]}..."

    return csrf

def edit_page(title: str, text: str, summary: str) -> dict:
    csrf = get_csrf_token()
    # 🛡️ Guardrail: assert=user rejects the edit if not logged in
    resp = SESSION.post(WIKI, data={
        "action": "edit",
        "title": title,
        "text": text,
        "summary": summary,
        "token": csrf,
        "assert": "user",        # ← Prevents anonymous/temp-account edits
        "format": "json",
    }).json()

    # 🛡️ Guardrail: Verify the edit was attributed to the expected user
    if "error" in resp:
        raise RuntimeError(f"Edit failed: {resp['error']['code']} — {resp['error']['info']}")
    edit = resp.get("edit", {})
    assert edit.get("user"), \
        f"Edit not attributed to any user — may have fallen back to anonymous. Response: {resp}"

    return edit
```

> 💡 **Why these guards matter:** An anonymous session's CSRF token is the literal string `+\`.
> If login fails silently (e.g., wrong password, expired token, network issue), the code
> would get this anonymous token and proceed to edit — which succeeds but creates a
> temp-account edit attributed to `~2026-XXXXX-XX` instead of your bot.
>
> The three guardrails above catch this at different points:
> 1. `login()` asserts `result == "Success"` and verifies `userinfo` — catches login failure immediately
> 2. `get_csrf_token()` rejects `+\` tokens — catches anonymous sessions before any write
> 3. `edit_page()` uses `assert=user` — WMF-side check rejects the edit if not logged in
> 4. `edit_page()` checks `user` in response — final backstop after the edit

## SOP: OAuth 2.0 (Recommended for Public Tools)

OAuth 2.0 is the recommended authentication method for new tools, especially
web applications serving multiple users. It uses the **Authorization Code Grant**
flow with optional PKCE for non-confidential clients.

### Flow Diagram

```
User                    Your App                Wikimedia
  │                        │                       │
  │   Click "Login with    │                       │
  │   Wikimedia"           │                       │
  │ ──────────────────────►│                       │
  │                        │   Redirect to         │
  │                        │   oauth2/authorize    │
  │                        │ ─────────────────────►│
  │                        │                       │
  │   Authorize app        │                       │
  │ ◄──────────────────────│                       │
  │                        │                       │
  │                        │   Redirect back       │
  │                        │   with auth code      │
  │ ◄──────────────────────│                       │
  │                        │                       │
  │                        │   POST to             │
  │                        │   oauth2/access_token │
  │                        │ ─────────────────────►│
  │                        │                       │
  │                        │   Return access_token │
  │                        │ ◄─────────────────────│
  │                        │   + refresh_token     │
  │                        │                       │
  │   Make API calls       │   Bearer token in     │
  │   ────────────────────►│   Authorization header│
  │                        │ ─────────────────────►│
```

### Step 1: Register an OAuth Consumer

1. Go to `https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose`
2. Fill in:
   - **Application name** — Human-readable name users will see
   - **Application description** — What your tool does
   - **Callback URL** — Where users return after authorizing (e.g., `https://my-tool.toolforge.org/oauth/callback`)
   - **Callback URL is a prefix?** — Check if you want sub-paths to match
   - **Applicable project** — Usually `All projects` for most tools
   - **OAuth protocol version** — Select **OAuth 2.0**
   - **Types of grants** — Select the minimum permissions needed (see [Scopes Reference](references/scopes-reference.md))
   - **This consumer is for use only by [user]** — Check for owner-only (personal tool); leave unchecked for public tools
3. Submit. You'll receive a **client key** (public) and **client secret** (confidential).
4. For public tools, the consumer must be **approved by an administrator** before others can use it. Testing with your own account works immediately.

### Step 2: Implement the Authorization Code Flow

```python
import secrets
import requests
from urllib.parse import urlencode, quote

# Wikimedia OAuth 2.0 endpoints (for meta-wiki — change domain for other wikis)
OAUTH_BASE = "https://meta.wikimedia.org/rest.php/oauth2"
AUTHORIZE_URL = f"{OAUTH_BASE}/authorize"
TOKEN_URL = f"{OAUTH_BASE}/access_token"
PROFILE_URL = f"{OAUTH_BASE}/resource/profile"

# Your consumer credentials (from registration)
CLIENT_ID = "your_consumer_key"          # e.g. "abc123..."
CLIENT_SECRET = "your_consumer_secret"   # Keep secret! Never hardcode.

class WikimediaOAuth2Client:
    """A minimal OAuth 2.0 client for Wikimedia using the authorization code grant."""

    def __init__(self, client_id: str, client_secret: str,
                 redirect_uri: str, wiki_domain: str = "meta.wikimedia.org"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MyTool/1.0 (https://example.com; user@example.com) OAuth2Client"
        })
        self._oauth_base = f"https://{wiki_domain}/rest.php/oauth2"

    def get_authorization_url(self, state: str = None) -> tuple[str, str]:
        """Generate the URL to send the user to for authorization.
        
        Returns:
            (authorization_url, state) — store state in the user's session to verify on return.
        """
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

    def exchange_code(self, code: str, state: str, expected_state: str) -> dict:
        """Exchange an authorization code for access and refresh tokens.
        
        Args:
            code: The 'code' query parameter from the callback
            state: The 'state' query parameter from the callback
            expected_state: The state you stored before redirecting
        
        Raises:
            ValueError: If state doesn't match (possible CSRF attack)
        """
        if state != expected_state:
            raise ValueError("State mismatch — possible CSRF attack. Aborting.")
        
        resp = self.session.post(f"{self._oauth_base}/access_token", data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        })
        resp.raise_for_status()
        tokens = resp.json()
        # tokens contains: access_token, refresh_token, expires_in, token_type
        return tokens

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token using the refresh token."""
        resp = self.session.post(f"{self._oauth_base}/access_token", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        resp.raise_for_status()
        return resp.json()

    def get_profile(self, access_token: str) -> dict:
        """Get the authenticated user's profile (username, ID, groups, rights)."""
        resp = self.session.get(
            f"{self._oauth_base}/resource/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        return resp.json()

    def api_call(self, access_token: str, params: dict) -> dict:
        """Make an authenticated Action API call on behalf of the user.
        
        The access token is passed both in the Authorization header AND
        the query parameters are included normally. The token in the header
        authenticates the request; the parameters specify the action.
        """
        api_url = "https://en.wikipedia.org/w/api.php"
        params["format"] = "json"
        resp = self.session.get(
            api_url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        return resp.json()

    def edit_page(self, access_token: str, title: str, text: str,
                  summary: str, wiki: str = "en.wikipedia.org") -> dict:
        """Edit a page using the authenticated user's credentials.
        
        Requires the OAuth consumer to have the 'Edit existing pages' grant.
        """
        api_url = f"https://{wiki}/w/api.php"
        # First, get a CSRF token
        token_resp = self.session.get(api_url, params={
            "action": "query",
            "meta": "tokens",
            "type": "csrf",
            "format": "json",
        }, headers={"Authorization": f"Bearer {access_token}"}).json()
        
        csrf_token = token_resp["query"]["tokens"]["csrftoken"]
        
        # Make the edit
        edit_resp = self.session.post(api_url, data={
            "action": "edit",
            "title": title,
            "text": text,
            "summary": summary,
            "token": csrf_token,
            "format": "json",
        }, headers={"Authorization": f"Bearer {access_token}"}).json()
        return edit_resp
```

### Step 3: PKCE for Non-Confidential Clients

If your app cannot securely store a client secret (e.g., a single-page app or
mobile app), use **PKCE** (Proof Key for Code Exchange) instead:

```python
import hashlib, base64, secrets

def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code_verifier and code_challenge.
    
    Returns:
        (code_verifier, code_challenge)
    """
    code_verifier = secrets.token_urlsafe(64)[:128]
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge

# In the authorization redirect step, add:
#     &code_challenge={code_challenge}&code_challenge_method=S256
#
# In the token exchange step, add:
#     &code_verifier={code_verifier}
```

### Step 4: Identify the User Securely

After obtaining an access token, call the profile endpoint to verify identity:

```python
profile = client.get_profile(access_token)
# Returns:
# {
#   "sub": 12345,          # Central user ID
#   "username": "ExampleUser",
#   "editcount": 1500,
#   "confirmed_email": true,
#   "blocked": false,
#   "registered": "2020-01-15T00:00:00Z",
#   "groups": ["*", "user", "autoconfirmed"],
#   "rights": ["read", "edit", "createpage", "upload", ...],
#   "realname": "Example",    # Only if user granted permission
#   "email": "user@..."       # Only if user granted permission
# }
```

## SOP: OAuth 1.0a (Legacy Tools)

OAuth 1.0a is still supported but **OAuth 2.0 is strongly recommended for new
tools**. OAuth 1.0a requires request signing using HMAC-SHA1 or RSA-SHA1,
which is more complex than the Bearer token approach in OAuth 2.0.

### Key Endpoints

| Purpose | URL |
|---------|-----|
| Request token | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/initiate` |
| Authorize | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/authorize` |
| Access token | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/token` |
| Identify (JWT) | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/identify` |

### Using mwoauth (Python Library)

The `mwoauth` library handles all the signing complexity:

```python
from mwoauth import ConsumerToken, Handshaker
import requests

# Your consumer credentials (registered on meta)
consumer_token = ConsumerToken("your_consumer_key", "your_consumer_secret")
handshaker = Handshaker("https://meta.wikimedia.org/w/index.php",
                        consumer_token)

# Step 1: Get request token
redirect, request_token = handshaker.initiate()

# Step 2: Send user to authorize
print(f"Go to: {redirect}")

# Step 3: Exchange for access token
verifier = input("Paste the verification code: ").strip()
access_token = handshaker.complete(request_token, verifier)

# Step 4: Identify the user (uses JWT — secure!)
identity = handshaker.identify(access_token)
print(f"Authenticated as: {identity['username']}")

# Step 5: Make an authenticated API call
def oauth_api_call(params: dict) -> dict:
    """Make an authenticated API call using OAuth 1.0a."""
    api_url = "https://en.wikipedia.org/w/api.php"
    request = handshaker.sign_request(access_token, api_url, params)
    resp = requests.get(request.url, headers=request.headers)
    return resp.json()
```

### When to Choose OAuth 1.0a Over OAuth 2.0

- Your tool needs the **JWT-based `/identify`** endpoint for secure user identity (OAuth 2.0's `/resource/profile` serves a similar purpose)
- You're maintaining an existing OAuth 1.0a tool and migration isn't practical yet
- You need **RSA-signed requests** (extra security for high-value tools)

## SOP: Owner-Only Consumers

An **owner-only consumer** is an OAuth consumer that only you can authorize.
It skips the administrator review process and the user authorization dialog.
Best for personal tools running on Toolforge.

### Create One

1. Go to `Special:OAuthConsumerRegistration/propose` on meta
2. Check **"This consumer is for use only by [your username]"**
3. Choose OAuth 2.0
4. After creation, you'll get credentials. Since it's owner-only, you can use it immediately.

### Use It (No Browser Redirect Needed)

For owner-only OAuth 2.0 consumers, use the **Client Credentials Grant**
instead of the Authorization Code Grant:

```python
def owner_only_token(client_id: str, client_secret: str) -> str:
    """Get an access token for an owner-only OAuth 2.0 consumer."""
    resp = requests.post(
        "https://meta.wikimedia.org/rest.php/oauth2/access_token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"User-Agent": "MyTool/1.0 (user@example.com) OwnerOnlyBot"}
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

# Then use the token as a Bearer token for all API calls
token = owner_only_token(CLIENT_ID, CLIENT_SECRET)
# ... make API calls with Authorization: Bearer {token}
```

## SOP: Secure Credential Storage

### Never Hardcode Credentials

```python
# ❌ BAD — never do this
CLIENT_SECRET = "abc123def456"
BOT_PASSWORD = "my_secret_password"

# ✅ GOOD — use environment variables
import os
CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")
BOT_PASSWORD = os.environ.get("BOT_PASSWORD")
```

### On Toolforge

Use `toolforge env set` to store secrets:

```bash
# Set once
become my-tool
toolforge env set OAUTH_CLIENT_ID "your_consumer_key"
toolforge env set OAUTH_CLIENT_SECRET "your_consumer_secret"
toolforge env set OAUTH_ACCESS_TOKEN "your_stored_access_token"

# In your code
import os
client_id = os.environ["OAUTH_CLIENT_ID"]
client_secret = os.environ["OAUTH_CLIENT_SECRET"]
```

### For Local Development

Use a `.env` file (gitignored):

```bash
# .env — NEVER commit this to version control
OAUTH_CLIENT_ID=abc123
OAUTH_CLIENT_SECRET=def456
BOT_USERNAME=MyAccount@MyBot
BOT_PASSWORD=generated_password
```

```python
from dotenv import load_dotenv
load_dotenv()  # Reads .env file
```

### For Bot Passwords on Toolforge

Store in the tool's home directory with restricted permissions:

```bash
become my-tool
touch /data/project/my-tool/.bot-credentials
chmod 600 /data/project/my-tool/.bot-credentials
# Edit the file with:
# USERNAME=MyAccount@MyBot
# PASSWORD=generated_password
```

## SOP: Permission Checks

Always verify that the authenticated user has the necessary rights before
attempting an action. Wikimedia's Action API provides two ways to check:

### Method 1: Check User Rights from the Profile

```python
def check_right(profile: dict, required_right: str) -> bool:
    """Check if the authenticated user has a specific right."""
    return required_right in profile.get("rights", [])

profile = client.get_profile(access_token)
if not check_right(profile, "edit"):
    print("User does not have edit rights. Aborting.")
    return
```

### Method 2: Check via the Action API

```python
def get_user_rights(access_token: str, wiki: str = "en.wikipedia.org") -> list:
    """Fetch the authenticated user's rights from the API."""
    resp = requests.get(
        f"https://{wiki}/w/api.php",
        params={
            "action": "query",
            "meta": "userinfo",
            "uiprop": "rights",
            "format": "json",
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "MyTool/1.0 (user@example.com) RightsChecker"
        }
    )
    data = resp.json()
    return data["query"]["userinfo"]["rights"]
```

### Common Rights to Check

| Right | Required For | OAuth Grant |
|-------|-------------|-------------|
| `read` | Reading pages | Basic access |
| `edit` | Editing pages | Edit existing pages |
| `createpage` | Creating new pages | Create, edit, and move pages |
| `move` | Moving/renaming pages | Create, edit, and move pages |
| `upload` | Uploading files | Upload new files |
| `patrol` | Marking pages as patrolled | Patrol pages |
| `delete` | Deleting pages | Delete pages, revisions |
| `protect` | Protecting pages | Protect pages |
| `block` | Blocking users | Block users |
| `rollback` | Reverting edits | Rollback edits |
| `userrights` | Changing user groups | Manage user rights |

## SOP: Anti-Patterns and Common Mistakes

### ❌ Hardcoding Credentials in Source Code

```python
# NEVER
client_secret = "abc123def456"
```

This is the #1 cause of credential leaks. Use environment variables or a
gitignored config file.

### ❌ Using Personal Account Cookies in Scripts

```python
# NEVER — don't copy browser cookies into a script
cookies = {"enwikiSession": "abc123", "enwikiUserID": "12345"}
```

This breaks when the session expires, creates security risks, and violates
Wikimedia's terms of use. Use bot passwords or OAuth instead.

### ❌ Scraping Special Pages While Logged In

```python
# NEVER — Special: pages are not stable APIs
resp = requests.get(
    "https://en.wikipedia.org/wiki/Special:RecentChanges",
    cookies=my_cookies
)
```

Use the Action API (`action=query&list=recentchanges`) instead. It's
stable, documented, and designed for programmatic access.

### ❌ Failing to Check User Rights Before Actions

```python
# ❌ BAD — will fail with a confusing API error
edit_page("Some Page", "new text", "my edit")  # User may not have 'edit' right

# ✅ GOOD — check first
profile = client.get_profile(token)
if "edit" not in profile.get("rights", []):
    print("Cannot edit — missing 'edit' right.")
    return
edit_page("Some Page", "new text", "my edit")
```

### ❌ Forgetting the CSRF Token for Write Actions

```python
# ❌ BAD — will fail
session.post(API_URL, data={"action": "edit", "title": "Foo", "text": "Bar"})

# ✅ GOOD — always include the CSRF token
csrf = get_csrf_token()
session.post(API_URL, data={"action": "edit", "title": "Foo", "text": "Bar", "token": csrf})
```

Every write action in the Action API requires a CSRF token. The token is
user-specific and session-specific.

### ❌ Normalization: Spaces vs. Underscores in Usernames

```python
# ❌ BAD — will fail with "Unknown error"
lgname = "My Account@MyBot"

# ✅ GOOD — replace spaces with underscores
lgname = "My_Account@MyBot"
```

### ❌ Using `action=login` When Bot Passwords Would Work

`action=login` requires your main account password. Bot passwords are
preferred because they:
- Can be limited to specific permissions
- Can be revoked independently
- Don't expose your main password
- Work with rate limit benefits

### ❌ Storing Tokens in World-Readable Files

```bash
# ❌ BAD
echo "TOKEN=abc123" >> ~/.bashrc
chmod 644 ~/.bashrc  # World-readable!

# ✅ GOOD
echo "TOKEN=abc123" >> /data/project/my-tool/.secrets
chmod 600 /data/project/my-tool/.secrets  # Owner-only
```

### ❌ Not Handling Token Expiry

OAuth 2.0 access tokens expire after a set period (typically 1 hour for
Authorization Code Grant). Always implement refresh token logic:

```python
# ✅ GOOD — refresh automatically
def get_valid_token(access_token, refresh_token, expires_at):
    if time.time() >= expires_at:
        tokens = client.refresh_access_token(refresh_token)
        return tokens["access_token"], tokens["refresh_token"], time.time() + tokens["expires_in"]
    return access_token, refresh_token, expires_at
```

### ❌ OAuth 1.0a: Forgetting the `title` Parameter in Signed Requests

OAuth 1.0a requests to `Special:OAuth/*` endpoints must include the
`title` parameter in the signed parameters:

```python
# The 'title' parameter is REQUIRED in signed requests to OAuth endpoints
params = {"title": "Special:OAuth/initiate", "oauth_callback": "oob"}
```

## Reference: Authentication Decision Flow

```
What kind of tool are you building?
│
├─ Single-user script or cron job
│  └─ Bot passwords (simplest)
│     → Create at Special:BotPasswords on your wiki
│     → Store in environment variable or .secrets file
│     → Log in with action=login using bot credentials
│
├─ Multi-user web app
│  ├─ New app → OAuth 2.0 Authorization Code Grant
│  │  → Register consumer on meta
│  │  → Implement /authorize + /access_token flow
│  │  → Store refresh tokens for each user
│  │
│  └─ Legacy app → OAuth 1.0a
│     → Register consumer on meta
│     → Use mwoauth (Python) or similar library
│     → Handle signature process
│
├─ Personal tool on Toolforge
│  └─ Owner-only OAuth 2.0 consumer
│     → Register with "for use only by me" checked
│     → Use client_credentials grant (no browser redirect)
│     → Store creds via `toolforge env set`
│
└─ Quick test / internal script
   └─ action=login (last resort)
      → Requires main password — use bot passwords instead
```

---

## Tooling

### 🔧 Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`scripts/register-consumer.sh`](./scripts/register-consumer.sh) | Interactive guide for registering an OAuth consumer | `./register-consumer.sh` |
| [`scripts/test-auth.sh`](./scripts/test-auth.sh) | Test that your authentication setup works end-to-end | `./test-auth.sh --method bot-password` |

### 🐍 Python Assets

| Asset | Purpose | Usage |
|-------|---------|-------|
| [`assets/flask-oauth2-app.py`](./assets/flask-oauth2-app.py) | Full Flask web app with OAuth 2.0 login, profile display, and page editing | `python3 flask-oauth2-app.py` |
| [`assets/bot-password-editor.py`](./assets/bot-password-editor.py) | Standalone script using bot passwords to edit pages, check rights, and handle errors | `python3 bot-password-editor.py --help` |
| [`assets/oauth2_client.py`](./assets/oauth2_client.py) | Reusable Python library for Wikimedia OAuth 2.0 (importable) | `from oauth2_client import WikimediaOAuth2Client` |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/oauth-endpoints.md`](./references/oauth-endpoints.md) | Complete reference of all OAuth endpoints, URLs, and request formats |
| [`references/scopes-reference.md`](./references/scopes-reference.md) | All OAuth grants/scopes with descriptions, required rights, and common use cases |
| [`references/common-mistakes.md`](./references/common-mistakes.md) | Extended anti-pattern catalog with before/after examples |
