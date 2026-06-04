#!/usr/bin/env python3
"""
EventStreams Consumer — reusable Python module for consuming Wikimedia
real-time event streams.

Usage:
    pip install requests-sse
    python eventstreams-consumer.py                    # watch enwiki edits
    python eventstreams-consumer.py --wiki dewiki       # German Wikipedia
    python eventstreams-consumer.py --wiki wikidatawiki --type edit  # Wikidata edits
    python eventstreams-consumer.py --stream revision-create         # revision stream
    python eventstreams-consumer.py --since 2026-06-01T00:00:00Z     # historical replay

Example output:
    [enwiki] ExampleEditor → Albert Einstein (+71 bytes)
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone

try:
    from requests_sse import EventSource
except ImportError:
    print("Install requests-sse: pip install requests-sse")
    sys.exit(1)


# ──────────────────────────────────────────────
# EventStreams Client
# ──────────────────────────────────────────────

class EventStreamsConsumer:
    """Consume Wikimedia EventStreams with auto-reconnect and filtering."""

    BASE_URL = 'https://stream.wikimedia.org/v2/stream'

    def __init__(self, stream='recentchange', since=None, user_agent=None):
        self.stream = stream
        self.since = since
        self.user_agent = user_agent or 'EventStreamsConsumer/1.0 (python)'

    def url(self):
        base = f'{self.BASE_URL}/{self.stream}'
        if self.since:
            base += f'?since={self.since}'
        return base

    def stream_events(self, filter_fn=None):
        """
        Generator that yields parsed event dicts.

        Args:
            filter_fn: Optional callable(event_dict) -> bool.
                       Return True to include the event.

        Yields:
            Parsed event dictionaries (with canary events already removed).
        """
        last_id = None
        retry_delay = 1
        headers = {'User-Agent': self.user_agent}

        while True:
            try:
                with EventSource(
                    self.url(),
                    headers=headers,
                    last_event_id=last_id
                ) as es:
                    for event in es:
                        if event.type != 'message':
                            continue
                        try:
                            data = json.loads(event.data)
                        except (ValueError, json.JSONDecodeError):
                            continue

                        # Discard canary events (MANDATORY)
                        if data.get('meta', {}).get('domain') == 'canary':
                            continue

                        # Apply user filter if provided
                        if filter_fn and not filter_fn(data):
                            continue

                        yield data
                        last_id = event.last_event_id
                        retry_delay = 1  # Reset on success

            except (ConnectionError, TimeoutError, Exception) as e:
                now = datetime.now(timezone.utc).isoformat()
                print(f'[{now}] Disconnected: {e}. '
                      f'Reconnecting in {retry_delay}s...',
                      file=sys.stderr)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)


# ──────────────────────────────────────────────
# Built-in Filters
# ──────────────────────────────────────────────

def wiki_filter(wiki_id):
    """Filter: only events from a specific wiki (e.g. 'enwiki')."""
    return lambda e: e.get('wiki') == wiki_id

def type_filter(*event_types):
    """Filter: only events of given types ('edit', 'new', 'log', ...)."""
    return lambda e: e.get('type') in event_types

def human_edits_filter(e):
    """Filter: only human (non-bot) edits in main namespace."""
    return (e.get('type') == 'edit'
            and not e.get('bot')
            and e.get('namespace') == 0)

def user_filter(username):
    """Filter: track a specific user."""
    return lambda e: e.get('user') == username

def title_pattern_filter(pattern):
    """Filter: events where title starts with a pattern."""
    return lambda e: e.get('title', '').startswith(pattern)


# ──────────────────────────────────────────────
# Formatters
# ──────────────────────────────────────────────

def format_recentchange(change):
    """Pretty-print a recentchange event."""
    wiki = change.get('wiki', '?')
    user = change.get('user', '?')
    title = change.get('title', '?')
    etype = change.get('type', '?')

    # Byte diff
    lo = change.get('length', {}).get('old', 0) or 0
    ln = change.get('length', {}).get('new', 0) or 0
    diff = ln - lo
    sign = '+' if diff >= 0 else ''

    return f'[{wiki}] {user} {etype} → {title} ({sign}{diff} bytes)'


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Consume Wikimedia EventStreams in real time')
    parser.add_argument('--stream', default='recentchange',
                        help='Stream name (default: recentchange)')
    parser.add_argument('--wiki', default='enwiki',
                        help='Filter by wiki ID (default: enwiki)')
    parser.add_argument('--type', choices=['edit', 'new', 'log', 'categorize'],
                        help='Filter by event type')
    parser.add_argument('--since',
                        help='Historical replay timestamp (ISO-8601)')
    parser.add_argument('--no-filter', action='store_true',
                        help='Show all events from all wikis (no filter)')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                        help='Output format')
    args = parser.parse_args()

    consumer = EventStreamsConsumer(
        stream=args.stream,
        since=args.since,
        user_agent='EventStreamsConsumer/1.0 (eventstreams-consumer.py)'
    )

    # Build filter
    filters = []
    if not args.no_filter:
        filters.append(wiki_filter(args.wiki))
        if args.type:
            filters.append(type_filter(args.type))

    def combined_filter(e):
        return all(f(e) for f in filters)

    print(f'Connecting to stream: {args.stream}', file=sys.stderr)
    if not args.no_filter:
        print(f'Filtering: wiki={args.wiki}', file=sys.stderr)
    if args.since:
        print(f'Historical replay from: {args.since}', file=sys.stderr)
    print(file=sys.stderr)

    try:
        for event in consumer.stream_events(
            filter_fn=combined_filter if filters else None
        ):
            if args.format == 'json':
                print(json.dumps(event))
            else:
                print(format_recentchange(event))
    except KeyboardInterrupt:
        print('\nShutting down.', file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
