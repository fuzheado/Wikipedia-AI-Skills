---
name: wikimedia-eventstreams
description: Consume real-time streams of Wikimedia events (edits, page creations, deletions, moves, log entries) via Server-Sent Events (SSE). Covers the EventStreams HTTP service, stream schemas, client libraries (Python/JS/curl), filtering, historical replay, canary handling, auto-reconnect, and building live dashboards, patrol monitors, and cross-wiki trackers
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["real-time", "stream", "SSE", "EventStreams", "live", "recent change", "recentchange"]
  - keywords: ["new page", "page creation", "patrol", "monitor", "watch", "live feed"]
  - keywords: ["edit event", "revision create", "log event", "streaming"]
---

> ⚠️ **User-Agent required:** All examples in this skill connect to `stream.wikimedia.org`. Requests without a descriptive `User-Agent` header may be throttled. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns. Before writing code, load that skill for the required User-Agent boilerplate.

---

> 💡 **Related skills for common workflows:**
> - **[wikimedia-ml-services](../wikimedia-ml-services/SKILL.md)** — Score events from the stream (revert risk, goodfaith, damaging) for real-time patrol and vandalism detection
> - **[wikimedia-diffs](../wikimedia-diffs/SKILL.md)** — Fetch and classify diffs for edits detected in the stream (addition-heavy, deletion-heavy, replacement patterns)
> - **[pagetriage-api](../pagetriage-api/SKILL.md)** — Check PageTriage review status for new pages detected in the stream
> - **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — Required User-Agent headers and rate limiting for any follow-up API calls

---

## Table of Contents

1. [What EventStreams Is](#what-eventstreams-is)
2. [Where It Fits in the API Universe](#where-it-fits-in-the-api-universe)
3. [Stream Catalog](#stream-catalog)
4. [Quick Start](#quick-start)
5. [Event Schema Reference](#event-schema-reference)
6. [Client-Side Filtering](#client-side-filtering)
7. [Canary Events — Mandatory Handling](#canary-events--mandatory-handling)
8. [Connection Reliability & Auto-Reconnect](#connection-reliability--auto-reconnect)
9. [Historical Replay](#historical-replay)
10. [Python Clients in Depth](#python-clients-in-depth)
11. [JavaScript Clients in Depth](#javascript-clients-in-depth)
12. [Command-Line & Browser](#command-line--browser)
13. [Building Real-Time Tools](#building-real-time-tools)
14. [When NOT to Use EventStreams](#when-not-to-use-eventstreams)
15. [Reference Links](#reference-links)

---

## What EventStreams Is

EventStreams is a **real-time event streaming service** operated by the Wikimedia Foundation. Unlike every other Wikimedia API (which follows a **request-response** pattern), EventStreams uses **Server-Sent Events (SSE)** — the server **pushes** structured JSON events to you over HTTP as they happen.

**Key facts:**

- **Backend:** Apache Kafka clusters (hundreds of thousands of messages/second across multiple data centers)
- **Protocol:** Standard HTTP SSE (`text/event-stream`) via chunked transfer encoding
- **Supersedes:** RCStream (the old Socket.IO-based service), and may eventually replace `irc.wikimedia.org`
- **Read-only:** Events flow server → client. You cannot publish events through EventStreams.
- **External use only:** WMF production services should consume Kafka directly — the public HTTP service is for external tool developers.

### How SSE Works

SSE is a standard web protocol (part of HTML5) where a server opens a long-lived HTTP connection and writes lines of data as events occur:

```
event: message
id: [{"topic":"eqiad.mediawiki.recentchange","partition":0,"timestamp":1532031066001},...]
data: {"event": "data", "is": "here"}

```

Each event has:
- `event`: `message` for data, `error` for errors
- `id`: JSON array of Kafka topic/partition/timestamp metadata (used for reconnection)
- `data`: The actual JSON payload (the event)

The connection stays open until the client disconnects or a 15-minute server-side timeout kicks in. Good clients **auto-reconnect** using the `Last-Event-ID` header to resume where they left off.

---

## Where It Fits in the API Universe

EventStreams occupies a unique position — it's the **only push-based, real-time data source** in the Wikimedia ecosystem.

| Data Source | Paradigm | Latency | Use Case |
|---|---|---|---|
| **REST API v1** | Request-response (HTTP GET) | Minutes old | Read page content, summaries |
| **Action API** (`api.php`) | Request-response | Minutes old | Query, edit, upload, delete |
| **EventStreams** | Push (SSE / Kafka) | Sub-second | Real-time monitoring, live dashboards |
| **SQL Replicas** | Poll (SQL queries) | Hours–days old | Deep analysis, JOINs, bulk stats |
| **Dumps** | Batch download | Days–months old | Offline/ML training, full corpus |
| **SPARQL** | Request-response | Minutes old | Graph queries over Wikidata |

**Complementary to existing skills:**

| Skill | How EventStreams relates |
|---|---|
| [`wikimedia-diffs`](../wikimedia-diffs/SKILL.md) | Diffs are static comparisons of two revisions. EventStreams gives you the live firehose of changes — pipe events into diff-analysis for real-time monitoring. |
| [`wikipedia-edit-history`](../wikipedia-edit-history/SKILL.md) | History is retrospective (looking at past edits). EventStreams is prospective (watching edits happen in real-time). |
| [`pywikibot`](../pywikibot/SKILL.md) | Pywikibot's `comms.eventstreams.EventStreams` is the most Pythonic way to consume EventStreams. See the [Python Clients](#python-clients-in-depth) section. |
| [`wikimedia-api-access`](../wikimedia-api-access/SKILL.md) | Sets the User-Agent and rate-limiting patterns for all HTTP-based access, including EventStreams. |

---

## Stream Catalog

These are all available streams as of v2 of the EventStreams HTTP service. Streams are grouped by what they emit.

### MediaWiki Core Streams

| Canonical Stream | Aliases | What It Emits | Schema |
|---|---|---|---|
| `mediawiki.recentchange` | `recentchange` | Every edit, page creation, log entry, categorize action, or external change — **the main firehose** | `/mediawiki/recentchange` |
| `mediawiki.revision-create` | `revision-create` | Every new revision (page saves). Does NOT include log events or categorizations. | `/mediawiki/revision/create` |
| `mediawiki.page-create` | `page-create` | First revision of a newly created page (subset of revision-create) | `/mediawiki/revision/create` |
| `mediawiki.page-delete` | `page-delete` | Page deletions | `/mediawiki/page/delete` |
| `mediawiki.page-undelete` | `page-undelete` | Page restorations | `/mediawiki/page/undelete` |
| `mediawiki.page-move` | `page-move` | Page renames/moves | `/mediawiki/page/move` |
| `mediawiki.page-links-change` | `page-links-change` | When a page's outgoing links change (triggers update of WhatLinksHere) | `/mediawiki/page/links-change` |
| `mediawiki.page-properties-change` | `page-properties-change` | When page properties change | `/mediawiki/page/properties-change` |
| `mediawiki.page_change.v1` | — | Unified page change event | `/mediawiki/page/change` |
| `mediawiki.revision-tags-change` | — | When revision tags are added or removed | `/mediawiki/revision/tags-change` |
| `mediawiki.revision-visibility-change` | — | When revision visibility is suppressed or restored | `/mediawiki/revision/visibility-change` |

### Machine Learning / Prediction Streams

| Canonical Stream | What It Emits | Schema |
|---|---|---|
| `mediawiki.page_outlink_topic_prediction_change.v1` | Topic predictions for outlinks change (MOR/ORES model) | `/mediawiki/page/prediction_classification_change` |
| `mediawiki.page_revert_risk_prediction_change.v1` | Revert-risk scores change (ORES model) | `/mediawiki/page/prediction_classification_change` |
| `mediawiki.page_revert_risk_multilingual_prediction_change.v1` | Multilingual revert-risk predictions change | `/mediawiki/page/prediction_classification_change` |

### Wikidata / Wikibase Streams

| Canonical Stream | What It Emits |
|---|---|
| `rdf-streaming-updater.mutation.v2` | Wikidata RDF changes (consumed by the Wikidata Query Service updater) |
| `rdf-streaming-updater.mutation-main.v2` | Wikidata main namespace entity changes |
| `rdf-streaming-updater.mutation-scholarly.v2` | Scholarly entity changes |
| `mediainfo-streaming-updater.mutation.v2` | Commons media info entity changes (structured data on Commons) |

### Test Stream

| Canonical Stream | Aliases | What It Emits |
|---|---|---|
| `eventgate-main.test.event` | `test` | One artificial event per minute for testing connectivity |

### Composite Streams

To subscribe to multiple streams simultaneously, join them with commas in the URL:

```
https://stream.wikimedia.org/v2/stream/recentchange,page-create,page-delete
```

The `{streams}` path parameter in the Swagger spec accepts comma-separated stream names. Each event carries its own stream name in `meta.stream`.

### Getting the Live List

The list of streams changes over time. To see the current catalog:

```bash
# OpenAPI/Swagger UI (human-readable)
open https://stream.wikimedia.org/?doc

# Raw Swagger spec (machine-readable)
curl -s https://stream.wikimedia.org/?spec | jq '.paths | keys'
```

---

## Quick Start

### 1. curl + jq (simplest, no dependencies)

```bash
curl -s -H 'Accept: application/json' \
  -H 'User-Agent: MyBot/1.0 (me@example.com)' \
  https://stream.wikimedia.org/v2/stream/recentchange
```

With `Accept: application/json`, EventStreams sends newline-delimited JSON instead of SSE format, making it pipeable to `jq`:

```bash
curl -sN -H 'Accept: application/json' \
  -H 'User-Agent: MyBot/1.0 (me@example.com)' \
  https://stream.wikimedia.org/v2/stream/recentchange \
  | jq 'select(.wiki == "enwiki" and .type == "edit") | {user, title}'
```

> **Note:** The `-sN` (silent, no-buffering) flag is important — without it `curl` may buffer output.

### 2. Python (with requests-sse)

```python
import json
from requests_sse import EventSource

url = 'https://stream.wikimedia.org/v2/stream/recentchange'
headers = {'User-Agent': 'MyBot/1.0 (me@example.com)'}

with EventSource(url, headers=headers) as stream:
    for event in stream:
        if event.type == 'message':
            change = json.loads(event.data)
            # Always discard canary events!
            if change['meta']['domain'] == 'canary':
                continue
            print(f"{change['user']} edited {change['title']}")
```

### 3. Python (with Pywikibot — recommended)

```python
from pywikibot.comms.eventstreams import EventStreams

stream = EventStreams(streams='recentchange')
stream.register_filter(server_name='en.wikipedia.org', type='edit')

for change in stream:
    # Canary events are automatically filtered by Pywikibot
    print(f"{change['user']} edited {change['title']}")
```

### 4. JavaScript (browser)

```javascript
const url = 'https://stream.wikimedia.org/v2/stream/recentchange';
const eventSource = new EventSource(url);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.meta.domain === 'canary') return;
    if (data.server_name === 'en.wikipedia.org') {
        console.log(`${data.user} edited ${data.title}`);
    }
};
```

### 5. Node.js (with wikimedia-streams)

```javascript
import WikimediaStream from 'wikimedia-streams';

const stream = new WikimediaStream('recentchange');
stream
    .filter('mediawiki.recentchange')
    .all({ wiki: 'enwiki' })
    .on('recentchange', (data) => {
        console.log(`${data.user} edited ${data.title}`);
    });
```

---

## Event Schema Reference

### The `recentchange` Event (the main stream)

This is the most commonly consumed stream. All fields from `Manual:RCFeed` are preserved. The schema version is `mediawiki/recentchange/1.0.1`.

```json
{
  "$schema": "/mediawiki/recentchange/1.0.1",
  "meta": {
    "dt": "2024-06-04T21:00:00Z",     // UTC event datetime (ISO-8601)
    "id": "uuid-string",               // Unique event ID
    "stream": "mediawiki.recentchange", // Stream name
    "domain": "en.wikipedia.org",      // Domain this event pertains to
    "request_id": "uuid",              // Request that caused this event (optional)
    "uri": "https://en.wikipedia.org/wiki/Albert_Einstein",  // Unique event URI
    "partition": 0,                    // Kafka partition
    "offset": 4000957901               // Kafka offset (timestamps in multi-DC)
  },
  "title": "Albert Einstein",           // Full page name (Title::getPrefixedText)
  "type": "edit",                       // "edit" | "new" | "log" | "categorize" | "external"
  "bot": false,                         // Was this a bot edit?
  "comment": "/* lede */ added citation",  // Edit summary
  "id": 123456789,                      // Recentchanges ID (rcid)
  "length": {                           // Byte length change
    "new": 84721,
    "old": 84650
  },
  "minor": false,                       // Minor edit flag (rc_minor)
  "namespace": 0,                       // Page namespace ID (-1 for Special)
  "patrolled": true,                    // Patrolled? (only if patrol enabled on wiki)
  "revision": {                         // Revision IDs
    "new": 123456789,                   // rc_last_oldid
    "old": 123456788                    // rc_this_oldid
  },
  "server_name": "en.wikipedia.org",    // $wgServerName
  "server_script_path": "/w",           // $wgScriptPath
  "server_url": "https://en.wikipedia.org",  // $wgCanonicalServer
  "timestamp": 1717540800,              // Unix timestamp (derived from rc_timestamp)
  "user": "ExampleEditor",              // rc_user_text
  "wiki": "enwiki",                     // wfWikiID ($wgDBprefix, $wgDBname)
  "parsedcomment": "<p>comment</p>",    // Parsed HTML of comment (optional)
  "log_action": null,                   // Log action (only for type="log")
  "log_action_comment": null,           // Log action comment
  "log_id": null,                       // Log entry ID
  "log_params": null,                   // Log parameters
  "log_type": null                      // Log type (delete, move, protect, etc.)
}
```

**The `type` field values:**

| Value | Meaning |
|---|---|
| `"edit"` | An existing page was edited |
| `"new"` | A new page was created |
| `"log"` | A log entry was made (delete, move, protect, block, upload, etc.) |
| `"categorize"` | A page was added/removed from a category |
| `"external"` | An external change was recorded |

**The `wiki` field** is the internal database name — the key identifier for filtering by wiki:

| Wiki | `wiki` value | `server_name` |
|---|---|---|
| English Wikipedia | `enwiki` | `en.wikipedia.org` |
| Wikimedia Commons | `commonswiki` | `commons.wikimedia.org` |
| Wikidata | `wikidatawiki` | `www.wikidata.org` |
| German Wikipedia | `dewiki` | `de.wikipedia.org` |
| French Wikipedia | `frwiki` | `fr.wikipedia.org` |

### Notable Fields in Other Streams

**`revision-create`** (schema: `/mediawiki/revision/create`): Similar to recentchange but only for revision creations. Has `page_id`, `rev_id`, `page_title`, `page_namespace`, `user`, `comment`, `bot` flags. Does NOT include log events or categorize events.

**`page-delete`** (schema: `/mediawiki/page/delete`): Has `page_id`, `page_title`, `page_namespace`, `rev_id` of the last revision before deletion, `suppressed` boolean (for oversight deletions), `user`, and `comment`.

**`page-move`** (schema: `/mediawiki/page/move`): Has `page_id`, `page_title` (old title), `page_namespace`, `new_title`, `new_namespace`, `user`, `comment`, `suppressed_redirect` boolean.

**`page-links-change`** (schema: `/mediawiki/page/links-change`): Has `page_id`, `page_title`, `page_namespace`, `added_links` array, `removed_links` array. Useful for tracking what links to what in real time.

---

## Client-Side Filtering

**EventStreams has no server-side filtering.** You must filter on the client side. The most common patterns:

### By Wiki (most common)

```python
# Filter to English Wikipedia only
wiki = 'enwiki'
with EventSource(url, headers=headers) as stream:
    for event in stream:
        if event.type == 'message':
            change = json.loads(event.data)
            if change['meta']['domain'] == 'canary':
                continue
            if change['wiki'] == wiki:
                print(change['title'])
```

### By Wiki Server Name

```python
if change['server_name'] == 'en.wikipedia.org':
    ...
```

### By Event Type

```python
# Edits only (skip new pages, logs, categorizations)
if change['type'] == 'edit':
    ...
```

### By Namespace

```python
# Main namespace articles only
if change['namespace'] == 0:
    ...

# Talk pages
if change['namespace'] % 2 == 1:
    ...
```

### By Bot Flag

```python
# Human edits only (exclude bots)
if not change.get('bot', False):
    ...

# Bot edits only
if change.get('bot', False):
    ...
```

### By User

```python
# Watch a specific user
if change.get('user') == 'VandalBot123':
    alert('Suspicious account active!')
```

### By Page Title Pattern

```python
# Track specific pages
import fnmatch
if fnmatch.fnmatch(change.get('title', ''), 'Albert*'):
    ...
```

### Combining Filters (real-world pattern)

```python
def relevant(change):
    """Track human edits to main-namespace enwiki articles."""
    if change['meta']['domain'] == 'canary':
        return False
    if change['wiki'] != 'enwiki':
        return False
    if change['namespace'] != 0:
        return False
    if change.get('bot', False):
        return False
    if change['type'] not in ('edit', 'new'):
        return False
    return True
```

### Using Pywikibot's Built-In Filtering

Pywikibot's `EventStreams` class provides a declarative filtering API:

```python
stream = EventStreams(streams='recentchange')
stream.register_filter(
    server_name='en.wikipedia.org',
    type='edit',
    bot=False
)
# Pywikibot also automatically filters out canary events
```

---

## Canary Events — Mandatory Handling

**The Wikimedia Data Engineering team** injects artificial "canary" events into every stream multiple times per hour. These events exist to distinguish between a broken stream and an empty one (monitoring).

**As a consumer, you MUST discard all canary events.** They are not real changes. The simplest and fastest check:

```python
if change['meta']['domain'] == 'canary':
    continue   # ← ALWAYS DO THIS
```

Pywikibot's `EventStreams` class handles this automatically — canary events are dropped before they reach your code. If you use a raw SSE client or `curl`, you must check manually.

Canary events copy their fields from the example event in the stream's JSON schema. For `recentchange`, they look like a real edit but with `meta.domain: "canary"`.

---

## Connection Reliability & Auto-Reconnect

### 15-Minute Timeout

WMF's HTTP connection termination layer enforces a **15-minute timeout** on idle SSE connections. A well-behaved client must:

1. Detect the disconnection
2. Reconnect to the stream URL
3. Send a `Last-Event-ID` header to resume from where it left off

### Standard SSE Reconnection (browser EventSource)

Browsers handle this automatically. `EventSource` reconnects on error and sends the `Last-Event-ID` header with the last received event ID. This is transparent to your code.

### Python Reconnection (requests-sse)

```python
import json
import time
from requests_sse import EventSource

url = 'https://stream.wikimedia.org/v2/stream/recentchange'
headers = {'User-Agent': 'MyBot/1.0 (me@example.com)'}

last_id = None
max_retries = 10
retry_delay = 1

for attempt in range(max_retries):
    try:
        with EventSource(url, headers=headers, last_event_id=last_id) as stream:
            for event in stream:
                if event.type == 'message':
                    change = json.loads(event.data)
                    if change['meta']['domain'] == 'canary':
                        continue
                    # Process the event
                    print(f"{change['user']} edited {change['title']}")
                    last_id = event.last_event_id
                retry_delay = 1  # Reset on successful event
    except (ConnectionError, TimeoutError) as e:
        print(f'Connection lost ({e}), reconnecting in {retry_delay}s...')
        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)  # Exponential backoff cap at 60s
```

### Pywikibot Auto-Reconnection

Pywikibot's `EventStreams` handles reconnection transparently — it uses `requests-sse` under the hood with the `last_event_id` parameter and automatically retries on connection errors.

### Detecting Stale Connections

If you receive no events for 10 minutes (but the connection is still open), consider proactively closing and reconnecting:

```python
import time

last_event_time = time.time()
timeout_threshold = 600  # 10 minutes

with EventSource(url, headers=headers) as stream:
    for event in stream:
        if event.type == 'message':
            last_event_time = time.time()
            # ... process event ...
        if time.time() - last_event_time > timeout_threshold:
            print('Stream appears stale, reconnecting...')
            break  # Exit the with block, reconnect in outer loop
```

---

## Historical Replay

Since June 2018, EventStreams supports **timestamp-based historical consumption**. This lets you replay events from a past point in time.

### Using the `since` Query Parameter

Add `?since=<timestamp>` to the stream URL:

```bash
# Replay all recentchanges since a specific date
curl -sN -H 'Accept: application/json' \
  'https://stream.wikimedia.org/v2/stream/recentchange?since=2026-06-01T00:00:00Z'
```

The `since` parameter accepts anything parseable by JavaScript `Date.parse()` — ISO-8601 datetimes work best.

### Using `Last-Event-ID` for Manual Offset

For precise control, set `Last-Event-ID` to a JSON array specifying topic, partition, and offset or timestamp:

```json
[{"topic": "eqiad.mediawiki.recentchange", "partition": 0, "offset": 1234567}]
```

In Python:

```python
# Resume from specific offsets (useful for multi-partition streams)
with EventSource(url, headers=headers, last_event_id='[{"topic":"eqiad.mediawiki.recentchange","partition":0,"offset":1234567}]') as stream:
    ...
```

### Retention Limits

**Events are not kept indefinitely.** Depending on the stream's Kafka topic configuration:

| Stream type | Typical retention |
|---|---|
| `mediawiki.recentchange` | ~7–31 days |
| `mediawiki.revision-create` | ~7–31 days |
| `rdf-streaming-updater.mutation.v2` | May vary (consumed by WDQS) |

Check with the Data Engineering team or the stream's configuration for exact retention.

### Rate Limiting on Replay

**Be kind when requesting historical data.** Replaying many days of events can be compute-intensive for the service. Only request the minimum data you need. If you need bulk historical analysis, use API queries, SQL replicas, or XML dumps instead.

---

## Python Clients in Depth

### Option 1: `requests-sse` (low-level, no dependencies beyond requests)

```bash
pip install requests-sse
```

Full example with all features:

```python
import json
import time
from requests_sse import EventSource

# EventStreams connection configuration
CONFIG = {
    'url': 'https://stream.wikimedia.org/v2/stream/recentchange',
    'headers': {'User-Agent': 'MyBot/1.0 (me@example.com)'},
}

def process_change(change):
    """Handle a single recentchange event."""
    # Canary filtering (MANDATORY)
    if change.get('meta', {}).get('domain') == 'canary':
        return

    # Only human edits in main namespace on enwiki
    if (change.get('wiki') == 'enwiki'
        and change.get('namespace') == 0
        and change.get('type') == 'edit'
        and not change.get('bot')):

        print(f"[{change['meta']['dt']}] "
              f"{change['user']} edited {change['title']} "
              f"(+{change.get('length', {}).get('new', 0) - change.get('length', {}).get('old', 0)} bytes)")

def main():
    """Run the EventStreams consumer with auto-reconnect."""
    last_id = None
    retry_delay = 1

    while True:
        try:
            with EventSource(
                CONFIG['url'],
                headers=CONFIG['headers'],
                last_event_id=last_id
            ) as stream:
                print('Connected to EventStreams')
                for event in stream:
                    if event.type == 'message':
                        change = json.loads(event.data)
                        process_change(change)
                        last_id = event.last_event_id
                    retry_delay = 1  # Reset on success
        except (ConnectionError, TimeoutError, Exception) as e:
            print(f'Disconnected: {e}. Reconnecting in {retry_delay}s...')
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)

if __name__ == '__main__':
    main()
```

### Option 2: Pywikibot `EventStreams` (recommended for Python)

```python
from pywikibot.comms.eventstreams import EventStreams
```

This is the **most feature-rich** Python client:

```python
stream = EventStreams(
    streams='recentchange',          # single stream name
    # streams=['recentchange', 'page-create'],  # or a list for composite
    since='2026-06-01T00:00:00Z',   # optional historical start
    # last_event_id='...json...'     # or manual resume
)

# Declarative filtering (multiple filters ANDed together)
stream.register_filter(
    server_name='en.wikipedia.org',  # only English Wikipedia
    type='edit',                     # only edits
    bot=False                        # only human editors
)

# Iterate as a generator
for change in stream:
    # Canary events are already filtered out by Pywikibot
    print(f"{change['user']} edited {change['title']}")

# Or use with max items limit
stream.set_maximum_items(10)
for change in stream:
    print(change['title'])  # Only processes 10 events then stops
```

**Pywikibot's EventStreams advantages:**

- Automatic canary filtering ✓
- Automatic reconnection ✓
- Declarative filter API ✓
- Composite streams from a list ✓
- Generator interface (works with `next()`, `for`, etc.) ✓
- Historical replay via `since=` ✓
- Uses Pywikibot's configured User-Agent ✓

```python
# Using the filter/shorthand approach
stream = EventStreams(streams='recentchange')

# Chain multiple filter conditions
stream.register_filter(
    server_name=['en.wikipedia.org', 'de.wikipedia.org'],  # list = OR
    type='edit',
    bot=False
)

for change in stream:
    print(f"[{change['wiki']}] {change['user']} → {change['title']}")
```

### Option 3: Asynchronous (aiohttp-sse-client)

For high-throughput applications that need async IO:

```python
import json
import aiohttp
from aiohttp_sse_client import client as sse_client

async def listen():
    async with aiohttp.ClientSession(
        headers={'User-Agent': 'MyBot/1.0 (me@example.com)'}
    ) as session:
        async with sse_client.EventSource(
            'https://stream.wikimedia.org/v2/stream/recentchange',
            session=session
        ) as event_source:
            async for event in event_source:
                if event.type == 'message':
                    change = json.loads(event.data)
                    if change.get('meta', {}).get('domain') == 'canary':
                        continue
                    print(f"{change['user']} edited {change['title']}")
```

---

## JavaScript Clients in Depth

### Browser — EventSource API

Built into every modern browser. Zero dependencies.

```html
<!DOCTYPE html>
<html>
<head>
    <title>Live Wikipedia Edits</title>
</head>
<body>
    <ul id="edits"></ul>
    <script>
        const url = 'https://stream.wikimedia.org/v2/stream/recentchange';
        const es = new EventSource(url);
        const list = document.getElementById('edits');

        es.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Discard canary events
            if (data.meta.domain === 'canary') return;

            if (data.server_name === 'en.wikipedia.org' && data.type === 'edit') {
                const li = document.createElement('li');
                li.textContent = `${data.user} edited ${data.title}`;
                list.prepend(li);
                // Keep list manageable
                while (list.children.length > 100) {
                    list.removeChild(list.lastChild);
                }
            }
        };

        es.onerror = () => {
            console.error('Connection lost, browser will auto-reconnect');
        };
    </script>
</body>
</html>
```

### Node.js — `wikimedia-streams` package

```bash
npm install wikimedia-streams
```

This library provides type-safe event handlers, fluent filtering, and automatic canary event filtering:

```javascript
import WikimediaStream from 'wikimedia-streams';

const stream = new WikimediaStream('recentchange');

stream
    .filter('mediawiki.recentchange')
    .all({ wiki: 'enwiki' })
    .on('recentchange', (data) => {
        console.log(`[${data.meta.dt}] ${data.user} → ${data.title}`);
    });

stream.on('open', () => console.log('Connected'));
stream.on('error', (err) => console.error('Error:', err));
```

### Node.js — `eventsource` package (standard EventSource polyfill)

```bash
npm install eventsource
```

```javascript
import { EventSource } from 'eventsource';

const url = 'https://stream.wikimedia.org/v2/stream/recentchange';
const es = new EventSource(url);

es.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.meta.domain === 'canary') return;
    if (data.wiki === 'enwiki') {
        console.log(`${data.user} edited ${data.title}`);
    }
};
```

---

## Command-Line & Browser

### curl + jq — one-liner for inspection

```bash
# Watch human edits on English Wikipedia in real time
curl -sN -H 'Accept: application/json' \
  https://stream.wikimedia.org/v2/stream/recentchange \
  | jq 'select(.wiki == "enwiki" and .type == "edit" and .bot == false) | {user, title, comment}'
```

### Browser Swagger UI — interactive exploration

```
open https://stream.wikimedia.org/?doc
```

The Swagger UI lets you:
- See all available streams with descriptions
- Click "Try it out" to connect to a stream directly in the browser
- View sample event data
- Discover schemas via the linked schema registry

### Browser — Codepen demos

These are live, editable demos you can run in the browser:

- **RecentChanges stats:** [codepen.io/Krinkle/pen/BwEKgW](https://codepen.io/Krinkle/pen/BwEKgW)
- **RDF stream viewer:** [codepen.io/ottomata/pen/LYpPpxj](https://codepen.io/ottomata/pen/LYpPpxj)

---

## Building Real-Time Tools

EventStreams is the foundation for a wide range of real-time applications. Here are proven patterns:

### Live Edit Counter

```python
from pywikibot.comms.eventstreams import EventStreams
from collections import Counter
import time

stream = EventStreams(streams='recentchange')
stream.register_filter(server_name='en.wikipedia.org')

counts = Counter()
window_start = time.time()

for change in stream:
    # Count edits per user
    counts[change['user']] += 1

    # Print top 10 every 30 seconds
    elapsed = time.time() - window_start
    if elapsed >= 30:
        print(f"\nTop editors in last {elapsed:.0f}s:")
        for user, count in counts.most_common(10):
            print(f"  {user}: {count}")
        counts.clear()
        window_start = time.time()
```

### Cross-Wiki Patrol Monitor

Track edits by the same user across multiple wikis simultaneously:

```python
from pywikibot.comms.eventstreams import EventStreams
from collections import defaultdict

stream = EventStreams(streams='recentchange')
# No server filter — we want ALL wikis

user_edits = defaultdict(list)

for change in stream:
    if change['meta']['domain'] == 'canary':
        continue

    user = change['user']
    wiki = change['wiki']
    title = change['title']

    user_edits[user].append((wiki, title, change['meta']['dt']))

    # Alert if same user edits 3+ different wikis within 60 seconds
    recent = [e for e in user_edits[user]
              if (time.time() - parse_timestamp(e[2])) < 60]
    if len(set(w for w, _, _ in recent)) >= 3:
        print(f"⚠️  Cross-wiki activity: {user}")
        for w, t, dt in recent:
            print(f"   {w}: {t} @ {dt}")
```

### Wikidata Batch Edit Detector

Detect when a single user makes many edits to Wikidata items in a short period (useful for spotting automated imports or vandalism):

```python
from pywikibot.comms.eventstreams import EventStreams
from collections import Counter
import time

stream = EventStreams(streams='recentchange')
stream.register_filter(server_name='www.wikidata.org')

user_counter = Counter()
window = 60  # seconds

for change in stream:
    user = change['user']
    user_counter[user] += 1

    # If a user exceeds 50 edits in a minute, flag them
    if user_counter[user] > 50:
        print(f"🚨 High-volume editor: {user} "
              f"({user_counter[user]} edits/min)")

    # Reset counters periodically
    # (In production, use a sliding window with timestamps)
```

### Live Edit Feed for a Specific Page or Category

```python
from pywikibot.comms.eventstreams import EventStreams
from fnmatch import fnmatch

# Track edits to physics-related articles
physics_pages = [
    'Physics',
    'Quantum mechanics',
    'Theory of relativity',
    'Thermodynamics',
]

stream = EventStreams(streams='recentchange')
stream.register_filter(server_name='en.wikipedia.org')

for change in stream:
    title = change.get('title', '')
    if any(fnmatch(title, f'{pattern}*') for pattern in physics_pages):
        print(f"🔬 {change['user']} edited {title}")
```

### Real-Time Dashboard Widget (HTML/JS)

Build a live counter that shows edits per minute, latest edits, or bot vs. human ratio. See the example at [codepen.io/Krinkle/pen/BwEKgW](https://codepen.io/Krinkle/pen/BwEKgW).

---

## When NOT to Use EventStreams

| Scenario | Better Approach |
|---|---|
| **WMF production service** | Consume Kafka directly (the public HTTP service is for external tools only) |
| **Historical analysis** | SQL replicas, XML dumps, or Action API queries — EventStreams only retains 7–31 days |
| **Single page read** | REST API v1 `GET /page/{title}/html` — simpler and stateless |
| **Bulk data export** | Download [XML dumps](https://dumps.wikimedia.org) — gigabytes of data for offline processing |
| **Complex queries across wikis** | SQL replicas on Toolforge — JOINs are impossible with a stream |
| **Need server-side filtering** | Use the Action API `list=recentchanges` with `rcprop=` parameters (but you lose real-time speed) |
| **One-off data check** | `curl` the Action API — no long-lived connection needed |
| **High-frequency, low-effort tasks** | EventStreams is for continuous monitoring, not batch jobs |
| **Offline / batch ML training** | XML dumps — you need the full revision history, not a real-time sample |

**Rule of thumb:** EventStreams is for **real-time visibility** — live dashboards, patrol monitors, cross-wiki trackers, and tools that need to react within seconds. If your data need is retrospective, bulk, or infrequent, use the request-response APIs or database replicas.

---

## Reference Links

| Resource | URL |
|---|---|
| EventStreams HTTP service | [stream.wikimedia.org](https://stream.wikimedia.org) |
| Swagger UI (docs + try-it) | [stream.wikimedia.org/?doc](https://stream.wikimedia.org/?doc) |
| Raw Swagger spec | [stream.wikimedia.org/?spec](https://stream.wikimedia.org/?spec) |
| Wikitech documentation | [wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service) |
| Source code (GitLab) | [gitlab.wikimedia.org/repos/data-engineering/eventstreams](https://gitlab.wikimedia.org/repos/data-engineering/eventstreams) |
| GitHub mirror | [github.com/wikimedia/eventstreams](https://github.com/wikimedia/eventstreams) |
| Pywikibot EventStreams docs | [doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.comms.html](https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.comms.html) |
| `requests-sse` (PyPI) | [pypi.org/project/requests-sse](https://pypi.org/project/requests-sse/) |
| `wikimedia-streams` (npm) | [npmjs.com/package/wikimedia-streams](https://www.npmjs.com/package/wikimedia-streams) |
| Event schema registry | [schema.wikimedia.org](https://schema.wikimedia.org) |
| Recentchange schema | [schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml](https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml) |
| Manual:RCFeed | [mediawiki.org/wiki/Manual:RCFeed](https://www.mediawiki.org/wiki/Manual:RCFeed) |
| CodePen: RC stats demo | [codepen.io/Krinkle/pen/BwEKgW](https://codepen.io/Krinkle/pen/BwEKgW) |
| Powered By gallery | [wikitech.wikimedia.org/wiki/EventStreams/Powered_By](https://wikitech.wikimedia.org/wiki/EventStreams/Powered_By) |
| RCStream (predecessor) | [wikitech.wikimedia.org/wiki/RCStream](https://wikitech.wikimedia.org/wiki/RCStream) |
| Skill: API access | [wikimedia-api-access](../wikimedia-api-access/SKILL.md) |
| Skill: Pywikibot | [pywikibot](../pywikibot/SKILL.md) |
| Skill: Toolforge | [wikimedia-toolforge](../wikimedia-toolforge/SKILL.md) |
