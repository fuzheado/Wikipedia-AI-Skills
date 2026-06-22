# Flask App Template for Toolforge

Copy this file to `app.py`, customize, and deploy.

```python
# app.py — Flask web service for Wikimedia Toolforge
import os
import logging
import sys

from flask import Flask, jsonify, request, send_from_directory

# --- Configuration ---
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 8765))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# --- Cache Headers ---
@app.after_request
def add_cache_headers(response):
    if response.mimetype and response.mimetype.startswith('image/'):
        response.headers['Cache-Control'] = 'public, max-age=604800, immutable'
    elif request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    else:
        response.headers['Cache-Control'] = 'no-store'
    return response


# --- Routes ---
@app.route('/')
def home():
    return '''
    <h1>Toolforge Flask App</h1>
    <p>Endpoints:</p>
    <ul>
        <li><a href="/api/status">/api/status</a> — Health check</li>
        <li><a href="/api/summary/Python_(programming_language)">/api/summary/&lt;title&gt;</a> — Wikipedia page summary</li>
        <li><a href="/api/search?q=test">/api/search?q=&lt;query&gt;</a> — Wikipedia search</li>
    </ul>
    '''


@app.route('/api/status')
def status():
    return jsonify(status='ok', port=PORT)


@app.route('/api/summary/<path:title>')
def wikipedia_summary(title):
    """Proxy: fetch a Wikipedia page summary."""
    import requests
    url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{title}'
    headers = {'User-Agent': os.environ.get(
        'WIKIMEDIA_USER_AGENT',
        f'ToolforgeApp/1.0 ({os.environ.get("TOOLFORGE_TOOL", "unknown")}@toolforge.org)'
    )}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        logger.error(f'Summary fetch failed: {e}')
        return jsonify(error=str(e)), 502


@app.route('/api/search')
def wikipedia_search():
    """Proxy: search Wikipedia."""
    import requests
    query = request.args.get('q', '')
    if not query:
        return jsonify(error='Missing ?q= parameter'), 400
    url = 'https://en.wikipedia.org/w/api.php'
    params = {
        'action': 'query', 'list': 'search', 'srsearch': query,
        'format': 'json', 'srlimit': 10,
    }
    headers = {'User-Agent': os.environ.get(
        'WIKIMEDIA_USER_AGENT',
        f'ToolforgeApp/1.0 ({os.environ.get("TOOLFORGE_TOOL", "unknown")}@toolforge.org)'
    )}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return jsonify(resp.json().get('query', {}).get('search', []))
    except Exception as e:
        logger.error(f'Search failed: {e}')
        return jsonify(error=str(e)), 502


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        filename,
    )


if __name__ == '__main__':
    logger.info(f'Starting Flask app on port {PORT}')
    app.run(host='0.0.0.0', port=PORT)
```
