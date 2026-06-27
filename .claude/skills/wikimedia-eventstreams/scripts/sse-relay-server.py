#!/usr/bin/env python3
"""
SSE Relay: EventStreams → Your Server → Browser Clients (Python/FastAPI)

Consumes Wikimedia EventStreams (recentchange) and relays filtered events
to browser clients via a secondary SSE endpoint.

Usage:
    pip install fastapi uvicorn aiohttp aiohttp-sse-client
    python scripts/sse-relay-server.py

Then open http://localhost:8000/events in a browser.
"""

import asyncio
import json

import aiohttp
from aiohttp_sse_client import client as sse_client
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()
clients = []


async def consume_eventstream():
    headers = {"User-Agent": "MyApp/1.0 (me@example.com) LiveDashboard"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with sse_client.EventSource(
            "https://stream.wikimedia.org/v2/stream/recentchange",
            session=session,
        ) as event_source:
            async for event in event_source:
                if event.type == "message":
                    change = json.loads(event.data)
                    if change.get("meta", {}).get("domain") == "canary":
                        continue
                    # Customize this filter to your needs
                    # For example, Commons uploads:
                    # if change.get("wiki") == "commonswiki" and ...
                    for q in clients:
                        await q.put(json.dumps(change))


@app.get("/events")
async def sse_endpoint(request: Request):
    queue: asyncio.Queue = asyncio.Queue()
    clients.append(queue)

    async def generate():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                data = await queue.get()
                yield f"event: update\ndata: {data}\n\n"
        except asyncio.CancelledError:
            clients.remove(queue)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.on_event("startup")
async def startup():
    asyncio.create_task(consume_eventstream())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
