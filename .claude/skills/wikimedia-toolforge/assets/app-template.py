#!/usr/bin/env python3
"""Basic Flask app template for Toolforge web services.

Copy this file to your tool directory, customize, and deploy:

   1. Edit the app name and routes below
   2. Deploy:  ./scripts/deploy.sh ./my-tool-dir my-tool-name
   3. Start:   ssh login.toolforge.org "become my-tool-name; webservice --backend=kubernetes python3.11 start"
   4. Visit:   https://my-tool-name.toolforge.org/

Requirements (deploy alongside):
   requirements.txt with:
     flask
     requests
"""

import os
import socket
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template_string, request

# ────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────

TOOL_NAME = "my-tool-name"

# Default User-Agent for outgoing Wikimedia API requests
USER_AGENT = f"{TOOL_NAME}/1.0 (https://{TOOL_NAME}.toolforge.org/; toolforge@{TOOL_NAME}.toolforge.org) ToolforgeApp"

app = Flask(__name__)


# ────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────

@app.route("/")
def index():
    """Home page with tool status."""
    hostname = socket.gethostname()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ tool_name }}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
            h1 { color: #333; }
            .status { background: #e8f5e9; padding: 10px 20px; border-radius: 4px; }
            .info { color: #666; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <h1>{{ tool_name }}</h1>
        <div class="status">
            <p>✅ Running on {{ hostname }}</p>
            <p>🕐 {{ now }}</p>
        </div>
        <p class="info">
            Try <a href="/api/status">/api/status</a> for health check or
            <a href="/api/summary/Albert_Einstein">/api/summary/Albert_Einstein</a>
            for a Wikipedia page summary.
        </p>
    </body>
    </html>
    """, tool_name=TOOL_NAME, hostname=hostname, now=now)


@app.route("/api/status")
def api_status():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "tool": TOOL_NAME,
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/api/summary/<path:title>")
def page_summary(title):
    """Fetch a Wikipedia page summary via the REST API."""
    headers = {"User-Agent": USER_AGENT}
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/search")
def search():
    """Search Wikipedia using the Action API."""
    query = request.args.get("q", "")
    limit = request.args.get("limit", 10, type=int)

    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    headers = {"User-Agent": USER_AGENT}
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": min(limit, 50),
        "format": "json",
        "formatversion": "2",
    }

    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("query", {}).get("search", [])
        return jsonify({"query": query, "results": results})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


# ────────────────────────────────────────────────────
# WSGI entry point
# ────────────────────────────────────────────────────

if __name__ == "__main__":
    # For local testing only
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    # Production WSGI (gunicorn) entry point
    # Toolforge webservice looks for `server.py` by default,
    # or you can point to this file with a launch.sh script.
    application = app
