#!/usr/bin/env python3
"""
Flask OAuth 2.0 Web App — Wikimedia Authentication Example

A complete Flask application demonstrating the OAuth 2.0 Authorization Code
Grant flow with Wikimedia. Users can log in with their Wikimedia account,
view their profile, and make simple edits.

Setup:
  1. Register an OAuth 2.0 consumer at:
     https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose
     - Callback URL: http://localhost:5000/oauth/callback
     - Grants: "Edit existing pages" + "High-volume text querying" (minimally)
     - OAuth protocol: OAuth 2.0

  2. Set environment variables:
     export OAUTH_CLIENT_ID="your_consumer_key"
     export OAUTH_CLIENT_SECRET="your_consumer_secret"
     export FLASK_SECRET_KEY="generate-a-random-secret-key"

  3. Install dependencies:
     pip install flask requests python-dotenv

  4. Run:
     python3 flask-oauth2-app.py

  5. Open http://localhost:5000 in your browser.
"""

import os
import secrets
import time
from functools import wraps
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request, session, url_for, render_template_string

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────

OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# OAuth 2.0 endpoints (using meta for cross-wiki access)
WIKI_DOMAIN = "meta.wikimedia.org"
OAUTH_BASE = f"https://{WIKI_DOMAIN}/rest.php/oauth2"
AUTHORIZE_URL = f"{OAUTH_BASE}/authorize"
TOKEN_URL = f"{OAUTH_BASE}/access_token"
PROFILE_URL = f"{OAUTH_BASE}/resource/profile"

# The callback URL must match what you registered
REDIRECT_URI = "http://localhost:5000/oauth/callback"

# ── Flask App Setup ────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# ── HTML Templates ─────────────────────────────────────────────────────────

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Wikimedia OAuth 2.0 Demo</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; line-height: 1.6; }
pre { background: #f4f4f4; padding: 1em; border-radius: 4px; overflow-x: auto; }
.btn { display: inline-block; padding: 0.5em 1em; background: #36c; color: #fff; text-decoration: none; border-radius: 4px; }
.btn:hover { background: #2a4b8d; }
.btn-logout { background: #c33; }
.btn-logout:hover { background: #a22; }
.flash { padding: 0.75em; border-radius: 4px; margin: 1em 0; }
.flash-error { background: #fee; border: 1px solid #f99; }
.flash-success { background: #efe; border: 1px solid #9f9; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #ddd; padding: 0.5em; text-align: left; }
th { background: #f4f4f4; }
</style></head>
<body>
{% if profile %}
    <h1>Logged In</h1>
    <p>Authenticated as <strong>{{ profile.username }}</strong></p>
    <a href="{{ url_for('profile_view') }}" class="btn">View Profile</a>
    <a href="{{ url_for('edit_view') }}" class="btn">Edit a Page</a>
    <a href="{{ url_for('logout') }}" class="btn btn-logout">Log Out</a>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash flash-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
{% else %}
    <h1>Wikimedia OAuth 2.0 Demo</h1>
    <p>This app demonstrates the OAuth 2.0 Authorization Code Grant flow
       with Wikimedia. Click below to log in with your Wikipedia account.</p>
    <a href="{{ url_for('login') }}" class="btn">Log in with Wikimedia</a>
{% endif %}
</body>
</html>
"""

PROFILE_HTML = """
<!DOCTYPE html>
<html>
<head><title>User Profile</title>
<style>body { font-family: sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; }</style>
</head>
<body>
<h1>User Profile</h1>
<table>
{% for key, value in profile.items() %}
    <tr><th>{{ key }}</th><td>{{ value }}</td></tr>
{% endfor %}
</table>
<a href="{{ url_for('index') }}">← Back</a>
</body>
</html>
"""

EDIT_HTML = """
<!DOCTYPE html>
<html>
<head><title>Edit a Page</title>
<style>body { font-family: sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; }
input, textarea { width: 100%; padding: 0.5em; margin: 0.5em 0; box-sizing: border-box; }
textarea { height: 10em; }
button { padding: 0.5em 1em; background: #36c; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #2a4b8d; }
pre { background: #f4f4f4; padding: 1em; border-radius: 4px; }
</style></head>
<body>
<h1>Edit a Page</h1>
<form method="POST">
    <label>Page title:</label>
    <input type="text" name="title" value="{{ title or 'Sandbox' }}" required>
    <label>Edit summary:</label>
    <input type="text" name="summary" value="Test edit via OAuth 2.0 demo app">
    <label>New content (wikitext):</label>
    <textarea name="text">{{ text or 'Hello from the OAuth 2.0 demo app!' }}</textarea>
    <button type="submit">Submit Edit</button>
</form>

{% if result %}
<h3>API Response:</h3>
<pre>{{ result }}</pre>
{% endif %}

<a href="{{ url_for('index') }}">← Back</a>
</body>
</html>
"""

# ── Helper Functions ───────────────────────────────────────────────────────

def make_session() -> requests.Session:
    """Create a requests Session with proper User-Agent."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "FlaskOAuth2Demo/1.0 (https://example.com; user@example.com) OAuth2Demo"
    })
    return s


def get_profile(access_token: str) -> dict | None:
    """Fetch user profile from the OAuth resource endpoint."""
    session = make_session()
    resp = session.get(PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"})
    if resp.status_code == 200:
        return resp.json()
    return None


def api_call(access_token: str, params: dict, wiki: str = "en.wikipedia.org") -> dict:
    """Make an authenticated Action API call."""
    session = make_session()
    params["format"] = "json"
    resp = session.get(
        f"https://{wiki}/w/api.php",
        params=params,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    resp.raise_for_status()
    return resp.json()


def edit_page(access_token: str, title: str, text: str, summary: str = "",
              wiki: str = "en.wikipedia.org") -> dict:
    """Edit a wiki page using the authenticated user's credentials."""
    db = make_session()
    # Fetch CSRF token
    token_data = api_call(
        access_token,
        {"action": "query", "meta": "tokens", "type": "csrf"},
        wiki
    )
    csrf_token = token_data["query"]["tokens"]["csrftoken"]

    # 🛡️ Guardrail: reject anonymous CSRF token
    if csrf_token == "+\\":
        raise RuntimeError(
            "Anonymous CSRF token — user session is not authenticated. "
            "Check token is valid and not expired."
        )

    # Make the edit
    api_url = f"https://{wiki}/w/api.php"
    resp = db.post(api_url, data={
        "action": "edit",
        "title": title,
        "text": text,
        "summary": summary,
        "token": csrf_token,
        "assert": "user",        # 🛡️ Guardrail: reject if not logged in
        "format": "json",
    }, headers={"Authorization": f"Bearer {access_token}"})
    resp.raise_for_status()
    result = resp.json()
    if "error" in result:
        raise RuntimeError(
            f"Edit failed: {result['error']['code']} — {result['error']['info']}"
        )
    edit = result.get("edit", {})
    if not edit.get("user"):
        raise RuntimeError(
            f"Edit not attributed to any user — anonymous fallback. Response: {result}"
        )
    return result


def login_required(f):
    """Decorator: require a valid access token in the session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("index"))
        # Check if token is expired
        if session.get("token_expires_at", 0) < time.time():
            # Try to refresh
            if "refresh_token" in session:
                try:
                    tokens = refresh_token(session["refresh_token"])
                    session["access_token"] = tokens["access_token"]
                    session["refresh_token"] = tokens.get("refresh_token",
                                                          session["refresh_token"])
                    session["token_expires_at"] = time.time() + tokens.get("expires_in", 3600)
                except Exception:
                    session.clear()
                    return redirect(url_for("index"))
            else:
                session.clear()
                return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def refresh_token(refresh_token: str) -> dict:
    """Refresh an expired access token."""
    db = make_session()
    resp = db.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": OAUTH_CLIENT_ID,
        "client_secret": OAUTH_CLIENT_SECRET,
    })
    resp.raise_for_status()
    return resp.json()


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    profile = None
    if "access_token" in session:
        profile = session.get("profile")
    return render_template_string(INDEX_HTML, profile=profile)


@app.route("/login")
def login():
    """Step 1: Redirect user to Wikimedia to authorize this app."""
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    params = {
        "response_type": "code",
        "client_id": OAUTH_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    auth_url = f"{AUTHORIZE_URL}?{urlencode(params)}"
    return redirect(auth_url)


@app.route("/oauth/callback")
def oauth_callback():
    """Step 2: Handle the callback from Wikimedia, exchange code for token."""
    error = request.args.get("error")
    if error:
        return f"Authorization denied: {error}", 400

    code = request.args.get("code")
    state = request.args.get("state")

    # Validate state to prevent CSRF
    expected_state = session.pop("oauth_state", None)
    if not state or state != expected_state:
        return "State mismatch — possible CSRF attack.", 401

    # Exchange authorization code for access token
    db = make_session()
    resp = db.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": OAUTH_CLIENT_ID,
        "client_secret": OAUTH_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    })
    
    if resp.status_code != 200:
        return f"Token exchange failed: {resp.text}", 400

    tokens = resp.json()
    session["access_token"] = tokens["access_token"]
    session["refresh_token"] = tokens.get("refresh_token")
    session["token_expires_at"] = time.time() + tokens.get("expires_in", 3600)

    # Fetch and store the user's profile
    profile = get_profile(tokens["access_token"])
    if profile:
        session["profile"] = profile

    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile_view():
    profile = get_profile(session["access_token"])
    if not profile:
        return "Failed to fetch profile", 500
    return render_template_string(PROFILE_HTML, profile=profile)


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit_view():
    result = None
    title = request.form.get("title", "Sandbox")
    text = request.form.get("text", "")
    summary = request.form.get("summary", "Test edit via OAuth 2.0 demo app")

    if request.method == "POST":
        try:
            result = edit_page(
                session["access_token"],
                title=title,
                text=text,
                summary=summary,
            )
            if "error" in result:
                result = f"Error: {result['error']['info']}"
            else:
                result = f"Edit successful! (revision {result['edit'].get('newrevid', '?')})"
                result += f"\nFull response: {str(result) if isinstance(result, dict) else result}"
        except Exception as e:
            result = f"Edit failed: {e}"

    return render_template_string(EDIT_HTML, result=result, title=title, text=text)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not OAUTH_CLIENT_ID or not OAUTH_CLIENT_SECRET:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  Error: OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET must be set ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print("1. Register an OAuth 2.0 consumer at:")
        print("   https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose")
        print()
        print("2. Set the callback URL to: http://localhost:5000/oauth/callback")
        print()
        print("3. Set environment variables:")
        print("   export OAUTH_CLIENT_ID='your_consumer_key'")
        print("   export OAUTH_CLIENT_SECRET='your_consumer_secret'")
        print("   export FLASK_SECRET_KEY='some-random-secret'")
        print()
        print("4. Run again: python3 flask-oauth2-app.py")
        exit(1)

    print(f"Starting OAuth 2.0 demo on http://localhost:5000")
    print(f"Callback URL: {REDIRECT_URI}")
    app.run(debug=True, port=5000)
