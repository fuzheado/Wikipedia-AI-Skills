# Publishing a Toolforge tool to Toolhub

Toolhub (<https://toolhub.wikimedia.org>) is the community catalogue of Wikimedia
tools: how editors discover a tool, and how a tool gets credited. Registering is
a few minutes of work, but the metadata format has several traps that reject an
otherwise-correct record, so validate **before** submitting.

## Three routes into the catalogue

| Route | Entry point | Use when |
|-------|-------------|----------|
| **toolsadmin record** | <https://toolsadmin.wikimedia.org/tools> | a Toolforge tool — Toolhub and Hay's Directory import Toolforge toolinfo records automatically |
| **`toolinfo.json` + crawler** | <https://toolhub.wikimedia.org/add-or-remove-tools?tab=urls> | metadata should live in the tool's own repo, where others can PR corrections |
| **Toolhub UI or API** | <https://toolhub.wikimedia.org/add-or-remove-tools?tab=tool-create> or `POST /api/tools/` | a one-off record with no repository to version |

All three need a Wikimedia login (OAuth); there is no anonymous submission. The
API surface is documented at <https://toolhub.wikimedia.org/api-docs>, and the
project documentation is <https://meta.wikimedia.org/wiki/Toolhub>.

With the crawler route, Toolhub re-reads the registered URL **about every 60
minutes**, so a merged metadata change propagates by itself — nothing to
re-submit.

> ⚠️ **`https://toolhub.wikimedia.org/tools/create` is NOT a creation form.** It is
> the *detail page of an existing tool named `create`*. A status-code check cannot
> tell the two apart: Toolhub is a JavaScript application whose HTML shell answers
> 200 for every client-side route. Render the page (or ask the API) whenever a URL
> matters — `/api/tools/create/` returns that tool's record.

## The schema, and the traps

The canonical schema is `jsonschema/toolinfo/1.2.2.json` in the Toolhub
repository:
<https://gerrit.wikimedia.org/r/plugins/gitiles/wikimedia/toolhub/+/refs/heads/main/jsonschema/toolinfo/>
— that directory holds every past version (1.0.0 → 1.2.2) plus `CHANGELOG.rst`,
which is the fastest way to see what a version changed. Current version: **1.2.2**
(2022-03-16).

Required: `name`, `title`, `description`, `url`.

Traps — every one of these is schema-enforced, and each is easy to get wrong from
memory:

- **`keywords` is a comma-separated string, not an array** — and it is
  **deprecated** in 1.2.x ("will be removed in the next major version"). The
  Toolhub *API* returns keywords as an array, which is what misleads people
  writing the file.
- **`tool_type` is a closed enum**: `web app`, `desktop app`, `bot`, `gadget`,
  `user script`, `command line tool`, `coding frame`, `lua module`, `template`.
- **`author`** takes a string *or* an array of person objects
  (`name`, `wiki_username`, `developer_username`, `email`, `url`); 1.2.2 added the
  multiple-author form. It is *self-reported* — see "Keeping it true" below.
- **`for_wikis`** entries must match a wiki host pattern (`en.wikipedia.org`,
  `www.wikidata.org`, `*`) — not arbitrary URLs.
- **Most URL fields are not plain strings.** `url`, `repository`, `api_url`,
  `translate_url` and `bugtracker_url` are strings;
  `user_docs_url`, `developer_docs_url`, `privacy_policy_url` and `feedback_url`
  take `{ "url": …, "language": "en" }` objects, or an array of them.
- **`license`** should be an SPDX identifier (`MIT`, `GPL-3.0-or-later`).
- **`$schema` names the *toolinfo* schema the file conforms to** (e.g.
  `"/toolinfo/1.2.2"`) — not the JSON-Schema meta-schema, and not the draft-04
  `id` that Hay's Directory-era files carried. Those two stray header fields were
  copied out of the schema document, and both are meaningless in an instance file:
  they are tolerated (unknown properties are allowed) but misdescribe the record.

## Validate before you register

Offline, against the real schema:

```bash
curl -s "https://gerrit.wikimedia.org/r/plugins/gitiles/wikimedia/toolhub/+/refs/heads/main/jsonschema/toolinfo/1.2.2.json?format=TEXT" \
  | base64 -d > /tmp/toolinfo-1.2.2.json
npx --yes -p ajv-cli@5 -p ajv-formats ajv validate --spec=draft7 -c ajv-formats \
  -s /tmp/toolinfo-1.2.2.json -d toolinfo.json
```

`ajv-formats` is required because the schema uses `format: "uri"`; without it ajv
reports the *schema* as invalid rather than complaining about your file.

Then prove the validator discriminates: corrupt the file five ways — drop a
required field, an invalid `tool_type`, a non-URI `url`, a non-wiki `for_wikis`
value, a non-person `author` — and confirm all five are rejected. A validator that
answers "valid" for everything says nothing, and neither does a probe that cannot
fire.

**Check the name is free** first: `name` is the catalogue key, and a second record
for the same tool splits discovery.

```bash
curl -s "https://toolhub.wikimedia.org/api/tools/?name=<name>"                      # count: 0 = free
curl -s -o /dev/null -w '%{http_code}\n' "https://toolhub.wikimedia.org/api/tools/<name>/"   # 404 = free
```

## A minimal, real-shaped file

```json
{
  "$schema": "/toolinfo/1.2.2",
  "name": "your-tool",
  "title": "Your Tool",
  "subtitle": "One line of extra context beyond the title",
  "description": "One paragraph: what it does, who it is for, and what it does not do.",
  "url": "https://example.org/your-tool",
  "keywords": "wikidata, categories, maintenance",
  "author": [{ "name": "Your Name", "wiki_username": "YourUsername" }],
  "repository": "https://github.com/your-user/your-tool",
  "license": "MIT",
  "tool_type": "web app",
  "for_wikis": ["en.wikipedia.org"],
  "technology_used": ["Node.js"],
  "api_url": "https://example.org/your-tool/api",
  "user_docs_url": [{ "url": "https://github.com/your-user/your-tool#readme", "language": "en" }],
  "bugtracker_url": "https://github.com/your-user/your-tool/issues",
  "experimental": false
}
```

A registered file in the wild, kept in the tool's own repository — exactly the
pattern the crawler route expects:
<https://github.com/eggpi/citationhunt/blob/master/static/toolinfo.json>.

## Keeping it true

- **`author` is self-reported.** Toolhub never checks it against Toolforge LDAP
  membership, so it is the only attribution the catalogue holds — and it must not
  be used as a maintainer or bus-factor source. For real maintainer data, crawl
  Striker instead (`references/maintainer-audit.md`).
- **Repo-versioned beats UI-entered.** A `toolinfo.json` in the tool's repository
  lets anyone PR a correction, and the crawler picks the change up within the hour.
- **`experimental: true`** means "unstable, can change or go offline at any time".
  Set it honestly: it is what tells a prospective user whether to depend on the
  tool, and it costs nothing to leave false once the tool is deployed and used.

## How this was verified (2026-10-05)

- the 1.2.2 schema was fetched from Gerrit and used to validate a real file with
  `ajv` (draft-07, plus `ajv-formats` for `format: "uri"`): valid — while five
  deliberate corruptions were each rejected, so the check discriminates;
- name availability was confirmed through the Toolhub API (`?name=` → `count: 0`;
  `/api/tools/<name>/` → 404);
- the registration routes were **rendered in a browser** (page title "Add or
  remove tools", selected tab "Create a new tool"), not status-checked — and the
  `/tools/create` warning above is the reason: that URL answers 200, and it is
  somebody else's tool;
- the route list, the ~60-minute crawler cadence, and the automatic import of
  Toolforge records come from <https://meta.wikimedia.org/wiki/Toolhub>.
