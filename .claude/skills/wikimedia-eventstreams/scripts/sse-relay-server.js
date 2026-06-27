#!/usr/bin/env node
/**
 * SSE Relay: EventStreams → Your Server → Browser Clients
 *
 * Consumes Wikimedia EventStreams (recentchange) and relays filtered events
 * to browser clients via a secondary SSE endpoint.
 *
 * Usage:
 *   npm install express eventsource
 *   node scripts/sse-relay-server.js
 *
 * Then open http://localhost:3000 in a browser and connect to /events.
 */

const express = require('express');
const { EventSource } = require('eventsource');

const PORT = process.env.PORT || 3000;
const USER_AGENT = 'MyApp/1.0 (me@example.com) LiveDashboard';

// ── Connected browser clients ──
const clients = new Set();

function broadcast(data) {
    const msg = `event: update\ndata: ${JSON.stringify(data)}\n\n`;
    for (const client of clients) {
        try { client.write(msg); } catch { clients.delete(client); }
    }
}

// ── Consume EventStreams (single upstream connection) ──
const es = new EventSource(
    'https://stream.wikimedia.org/v2/stream/recentchange',
    { headers: { 'User-Agent': USER_AGENT } }
);

es.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.meta?.domain === 'canary') return;
    // Customize this filter to your needs
    if (data.wiki === 'enwiki' && data.type === 'edit' && !data.bot) {
        broadcast({ user: data.user, title: data.title, wiki: data.wiki });
    }
};

es.onerror = (err) => console.error('EventStreams error:', err.message);

// ── SSE endpoint for browser clients ──
const app = express();

app.get('/events', (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
    });
    clients.add(res);
    res.write('event: connected\ndata: {}\n\n');

    req.on('close', () => {
        clients.delete(res);
        console.log(`[SSE] Client disconnected (${clients.size} remaining)`);
    });
});

app.listen(PORT, () => {
    console.log(`\n  🌐 SSE Relay running at http://localhost:${PORT}`);
    console.log(`  📡 SSE endpoint: http://localhost:${PORT}/events\n`);
});
