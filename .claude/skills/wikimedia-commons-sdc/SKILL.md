---
name: wikimedia-commons-sdc
description: Add, edit, and manage Structured Data on Commons (SDC) — MediaInfo captions, depicts statements, copyright and license metadata, qualifiers, references, and batch/GLAM workflows via the Wikibase Action API, web UI, and community tooling
depends_on: [wikimedia-api-access, wikimedia-auth-oauth]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["SDC", "structured data on Commons", "MediaInfo", "M ID", "depicts", "P180", "file captions", "Commons statements"]
  - keywords: ["AC/DC", "ISA Tool", "OpenRefine Commons", "QuickStatements Commons", "Pattypan"]
  - keywords: ["wbcreateclaim", "wbeditentity", "wbsetclaim", "wbsetlabel", "GLAM Commons"]
  - keywords: ["Structured data editing", "batch SDC", "Commons API editing", "copyright statement", "license statement"]
last_verified: 2026-06-12
---

> ⚠️ **User-Agent and authentication required:** All write operations to Wikimedia Commons require authentication. You need a Commons account and either a bot password or OAuth authorization. See the **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** skill for setup. All HTTP requests need a descriptive `User-Agent` header — see the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill.
>
> 💡 **Relationship to other skills:**
> - This skill covers **editing and managing** Structured Data on Commons. For **querying** SDC data via SPARQL, see the **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** skill.
> - The **[wikimedia-commons](../wikimedia-commons/SKILL.md)** skill covers file search, upload, licensing, and category navigation on Commons.
> - The **[wikidata](../wikidata/SKILL.md)** skill covers the general Wikibase data model and SPARQL query patterns.
> - The **[wikimedia-commons](../wikimedia-commons/SKILL.md)** skill covers file search, upload, licensing, and category navigation on Commons.
> - The **[wikidata](../wikidata/SKILL.md)** skill covers the general Wikibase data model and SPARQL query patterns.

---

## What Is Structured Data on Commons?

Structured Data on Commons (SDC) is a system of **machine-readable annotations** attached to every file on Wikimedia Commons. Every file page has two tabs:

- **"File information"** — traditional wikitext description (free-form, per-language file description pages)
- **"Structured data"** — Wikibase statements (machine-readable, multilingual, queryable)

SDC uses the same **Wikibase** technology that powers Wikidata, but with its own **MediaInfo entities** (identified by **M IDs** instead of Q IDs). Each Commons file has exactly one MediaInfo entity.

### What SDC Stores

| Type | Example | Property |
|------|---------|----------|
| **Captions** | "Sugar cubes on a blue surface" | `rdfs:label` (not a property — it's the entity label) |
| **Depicts** | File depicts Douglas Adams | `wdt:P180` → `wd:Q42` |
| **Creator** | File created by Vincent van Gogh | `wdt:P170` → `wd:Q5582` |
| **Copyright status** | File is public domain | `wdt:P6216` → `wd:Q50402863` |
| **License** | File is CC BY-SA 4.0 | `wdt:P275` → `wd:Q50824428` |
| **Inception date** | File created on 15 January 2023 | `wdt:P571` → date value |
| **Source of file** | File available on the internet | `wdt:P7482` → `wd:Q74228490` |
| **Camera** | Captured with Canon EOS 5D | `wdt:P4082` → `wd:Q649631` |
| **Coordinates** | Point of view coordinates | `wdt:P1259` → coordinate value |
| **Location of creation** | Created in Paris | `wdt:P1071` → `wd:Q90` |
| **Genre** | Documentary photography | `wdt:P136` → `wd:Q615498` |
| **Main subject** | Primary topic of the work | `wdt:P921` → `wd:Q1003` |
| **Instance of** | File is a photograph | `wdt:P31` → `wd:Q125191` |
| **Fabrication method** | Digital photography | `wdt:P2079` → `wd:Q226881` |
| **Digital representation of** | File represents a specific artwork | `wdt:P6243` → `wd:Q179900` |
| **Described at URL** | Source URL for the file | `wdt:P973` → URL literal |
| **Inception** | Date of creation | `wdt:P571` → date value |

Each statement can also carry **qualifiers** (additional context, like "color" for a depicts statement) and **references** (source citations).

---

## The MediaInfo Data Model

### M IDs — MediaInfo Entity Identifiers

Every Commons file has a **MediaInfo entity** with an **M ID**:

```
File:Albert_Einstein_Head.jpg  →  page_id=12345  →  M12345
```

**How to find the M ID:**

```python
import requests

resp = requests.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "query",
        "prop": "info",
        "titles": "File:Albert Einstein Head.jpg",
        "format": "json",
    },
    headers={"User-Agent": "MyBot/1.0 (https://example.com; user@example.com)"},
)
data = resp.json()
pages = data["query"]["pages"]
for page_id, info in pages.items():
    m_id = f"M{page_id}"
    print(f"File: {info['title']} → M ID: {m_id}")
```

Or via `wbgetentities`:

```
https://commons.wikimedia.org/w/api.php?action=wbgetentities&sites=commonswiki&titles=File:Albert%20Einstein%20Head.jpg&props=info&format=json
```

### Entity Structure (JSON)

A MediaInfo entity in JSON looks like this:

```json
{
  "M12345": {
    "type": "mediainfo",
    "id": "M12345",
    "labels": {
      "en": { "language": "en", "value": "Sugar cubes on a blue surface" },
      "de": { "language": "de", "value": "Zuckerwürfel auf blauer Oberfläche" }
    },
    "descriptions": {},
    "aliases": {},
    "claims": {
      "P180": [
        {
          "mainsnak": {
            "snaktype": "value",
            "property": "P180",
            "datavalue": {
              "type": "wikibase-entityid",
              "value": { "id": "Q10860964", "numeric-id": 10860964 }
            },
            "datatype": "wikibase-item"
          },
          "type": "statement",
          "id": "M12345$6F8A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C",
          "rank": "normal"
        }
      ],
      "P6216": [
        {
          "mainsnak": {
            "snaktype": "value",
            "property": "P6216",
            "datavalue": {
              "type": "wikibase-entityid",
              "value": { "id": "Q50402863", "numeric-id": 50402863 }
            },
            "datatype": "wikibase-item"
          },
          "type": "statement",
          "id": "M12345$7A9B4C3D-2E5F-6A7B-8C9D-0E1F2A3B4C5D",
          "rank": "normal"
        }
      ]
    }
  }
}
```

### Key Differences from Wikidata Entities

| Aspect | Wikidata | Commons SDC |
|--------|----------|-------------|
| Entity type | `item` | `mediainfo` |
| ID prefix | `Q` | `M` |
| Labels | Multilingual labels for the concept | Multilingual **file captions** |
| Descriptions | Usually absent or minimal on Commons | Typically empty |
| Sitelinks | Links to Wikipedia articles | Not used (the file page IS the entity) |
| API endpoint | `https://www.wikidata.org/w/api.php` | `https://commons.wikimedia.org/w/api.php` |

---

## Quick Reference: What Do You Want to Do?

| Goal | Method | API Module | Key Parameters |
|------|--------|------------|----------------|
| Get all SDC for a file | Action API (read) | `wbgetentities` | `ids=M12345` or `sites=commonswiki&titles=File:Example.jpg` |
| Get claims only | Action API (read) | `wbgetclaims` | `entity=M12345` or `entity=M12345&property=P180` |
| Add a depicts statement | Action API (write) | `wbcreateclaim` | `entity=M12345&property=P180&value={"id":"Q42"}` |
| Set a file caption | Action API (write) | `wbsetlabel` | `id=M12345&language=en&value="A black hole"` |
| Update a claim value | Action API (write) | `wbsetclaimvalue` | `claim=M12345$...&value={"id":"Q42"}` |
| Set a full claim (value + qualifiers) | Action API (write) | `wbsetclaim` | `claim={...full claim JSON...}` |
| Add a qualifier | Action API (write) | `wbsetqualifier` | `claim=M12345$...&property=P462&value={...}` |
| Add a reference | Action API (write) | `wbsetreference` | `statement=M12345$...&snaks={...}` |
| Remove a claim | Action API (write) | `wbremoveclaims` | `claim=M12345$...` |
| Batch: add to category files | Gadget | AC/DC | Web UI gadget |
| Batch: spreadsheet workflow | Tool | OpenRefine | Desktop app with Commons schema |
| Batch: command-line | Tool | QuickStatements | Via web UI, M IDs in commands |
| Check constraints | Action API | `wbcheckconstraints` | `id=M12345` |

---

## Authentication

All write operations to Commons SDC require authentication. Choose one of these methods:

### Option 1: Bot Password (Recommended for scripts)

1. Visit `https://commons.wikimedia.org/wiki/Special:BotPasswords`
2. Create a bot password with the `Edit Wikidata` grant (this controls Wikibase entity editing on Commons)
3. Use the generated username (e.g., `User@botname`) and password in your scripts

**Python with bot password:**

> ⚠️ **Bot passwords are the simplest approach** for automated scripts. They work with HTTP Basic Auth and grant only the specific permissions your bot needs. However, you must follow the guardrails below to avoid accidentally editing as an anonymous/temp account.

```python
import requests

SESSION = requests.Session()
SESSION.auth = ("User@botname", "your_bot_password")
SESSION.headers.update({
    "User-Agent": "MyBot/1.0 (https://example.com; user@example.com)",
})

# 🛡️ Guardrail 1: Verify the authenticated user
user_resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={"action": "query", "meta": "userinfo", "format": "json"},
)
actual_user = user_resp.json()["query"]["userinfo"]["name"]
expected_user = "User"  # strip @botname from "User@botname"
assert actual_user == expected_user, f"Auth failed: got {actual_user}, expected {expected_user}"
print(f"Authenticated as {actual_user}")

# 🛡️ Guardrail 2: Get and validate CSRF token
# An anonymous session returns "+\\" as the CSRF token; an authed one returns 40+ hex chars
token_resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={"action": "query", "meta": "tokens", "type": "csrf", "format": "json"},
)
csrf_token = token_resp.json()["query"]["tokens"]["csrftoken"]
assert csrf_token != "+\\", f"CSRF token is anonymous — login failed"
assert len(csrf_token) > 10, f"CSRF token too short: {csrf_token[:10]}..."
print(f"CSRF token obtained ({len(csrf_token)} chars)")
```

> 🛡️ **Guardrails to apply to every write request:**
> 1. Verify `userinfo` matches the expected account **before** any write
> 2. Reject anonymous CSRF tokens (`+\`) — they mean you're not logged in
> 3. Add `"assert": "user"` to every write request — MediaWiki itself rejects the edit if you're not logged in

### Option 2: Pywikibot (Framework)

```python
import pywikibot

site = pywikibot.Site('commons', 'commons')
site.login()
```

Pywikibot handles token management, edit throttling, and conflict detection automatically. See the **[pywikibot](../pywikibot/SKILL.md)** skill for full usage.

### Option 3: OAuth (for web applications)

See the **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** skill for setting up OAuth 1.0a or 2.0 for web-based tools that edit on behalf of users.

---

## Core SDC Operations via the Action API

All examples below assume you have an authenticated `SESSION` object with a CSRF token as shown above. The CSRF token must be sent as the `token` parameter with every write request.

### 1. Reading SDC Data

#### Get all SDC for a file

```python
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetentities",
        "ids": "M12345",
        "props": "labels|claims",
        "format": "json",
    },
)
data = resp.json()
entity = data["entities"]["M12345"]

# Captions
en_caption = entity.get("labels", {}).get("en", {}).get("value", "")
print(f"English caption: {en_caption}")

# Depicts statements
depicts_claims = entity.get("claims", {}).get("P180", [])
for claim in depicts_claims:
    q_id = claim["mainsnak"]["datavalue"]["value"]["id"]
    print(f"Depicts: {q_id} (rank: {claim['rank']})")
```

#### Get claims for a specific property

```python
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetclaims",
        "entity": "M12345",
        "property": "P180",
        "format": "json",
    },
)
```

### 2. Setting File Captions (`wbsetlabel`)

File captions are the **entity label** for MediaInfo entities — short, multilingual descriptions without wikitext or hyperlinks.

```python
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbsetlabel",
        "id": "M12345",
        "language": "en",
        "value": "Sugar cubes on a blue surface",
        "token": csrf_token,
        "format": "json",
    },
)
```

**Multi-language captions** — call `wbsetlabel` once per language:

```python
captions = {
    "en": "Sugar cubes on a blue surface",
    "de": "Zuckerwürfel auf blauer Oberfläche",
    "fr": "Morceaux de sucre sur une surface bleue",
}
for lang, caption in captions.items():
    resp = SESSION.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbsetlabel",
            "id": "M12345",
            "language": lang,
            "value": caption,
            "token": csrf_token,
            "format": "json",
        },
    )
    resp.raise_for_status()
```

> ⚠️ **Caption length:** Captions should be short and factual — a few words to a sentence. They should describe the file, not editorialize. No wikitext, no links, no markup.

### 3. Adding Depicts Statements (`wbcreateclaim`)

`wbcreateclaim` creates a new claim on an entity. For item-type properties like `P180` (depicts), the value is a JSON object with the target Q ID.

```python
import json

resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P180",
        "value": json.dumps({"id": "Q42"}),       # depicts Douglas Adams
        "token": csrf_token,
        "format": "json",
    },
)
```

**Error handling:**

```python
resp = SESSION.post(...)
data = resp.json()
if "error" in data:
    code = data["error"]["code"]
    info = data["error"]["info"]
    print(f"Error {code}: {info}")
else:
    claim_id = data["claim"]["id"]
    print(f"Created claim: {claim_id}")
```

**Adding multiple depicts values** — call `wbcreateclaim` once per depicts statement. Each call adds a separate statement:

```python
depicts_qids = ["Q42", "Q5", "Q30"]   # Douglas Adams, human, United States
for qid in depicts_qids:
    resp = SESSION.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbcreateclaim",
            "entity": "M12345",
            "property": "P180",
            "value": json.dumps({"id": qid}),
            "token": csrf_token,
            "format": "json",
        },
    )
    # Optional: respect rate limits
    import time; time.sleep(0.5)
```

### 4. Adding Copyright Status (`wbcreateclaim` with item value)

```python
# Set copyright status to "public domain" (Q50402863)
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P6216",
        "value": json.dumps({"id": "Q50402863"}),
        "token": csrf_token,
        "format": "json",
    },
)
```

**Common copyright status values:**
- `Q50402863` — public domain
- `Q50402878` — copyrighted
- `Q50402887` — copyrighted, not necessarily subject to a free license
- `Q50402894` — copyright status not stated

### 5. Adding License (`wbcreateclaim` with item value)

```python
# Set license to CC0 (Q50829104)
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P275",
        "value": json.dumps({"id": "Q50829104"}),
        "token": csrf_token,
        "format": "json",
    },
)
```

**Common license values:**
- `Q50829104` — CC0 1.0 Universal
- `Q50824428` — CC BY-SA 4.0 International
- `Q50824423` — CC BY 4.0 International
- `Q14946043` — CC BY-SA 3.0 Unported
- `Q19168217` — CC BY 2.0 Generic

### 6. Adding Creator (`wbcreateclaim` with item value)

```python
# Set creator to Vincent van Gogh (Q5582)
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P170",
        "value": json.dumps({"id": "Q5582"}),
        "token": csrf_token,
        "format": "json",
    },
)
```

**For unknown or un-Wikidata creators**, use `wbsetclaim` with a qualifier `P2093` (author name string):

```python
# Creator as a named string with qualifier
claim_data = {
    "type": "statement",
    "mainsnak": {
        "snaktype": "somevalue",           # "somevalue" = "unknown value" for the Q item
        "property": "P170",
        "datatype": "wikibase-item",
    },
    "qualifiers": {
        "P2093": [{                         # author name string
            "snaktype": "value",
            "property": "P2093",
            "datatype": "string",
            "data": {"type": "string", "value": "John Smith (photographer)"},
        }]
    },
}

resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbsetclaim",
        "claim": json.dumps(claim_data),
        "token": csrf_token,
        "format": "json",
    },
)
```

### 7. Adding Inception Date (`wbcreateclaim` with time value)

Dates use Wikibase's time format: `+2023-01-15T00:00:00Z` (precision 11 = day).

```python
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P571",
        "value": json.dumps({
            "time": "+2023-01-15T00:00:00Z",
            "timezone": 0,
            "before": 0,
            "after": 0,
            "precision": 11,          # 11 = day, 10 = month, 9 = year
            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",  # Gregorian
        }),
        "token": csrf_token,
        "format": "json",
    },
)
```

**Precision values:**
- 9 — year
- 10 — month
- 11 — day
- 12 — hour
- 14 — minute

**Calendar models:**
- `Q1985727` — Gregorian calendar
- `Q1985786` — Julian calendar

### 8. Adding Source of File (`wbcreateclaim` with item value)

```python
# Source = "file available on the internet" (Q74228490)
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P7482",
        "value": json.dumps({"id": "Q74228490"}),
        "token": csrf_token,
        "format": "json",
    },
)
```

**Common source values:**
- `Q74228490` — file available on the internet
- `Q548662` — original creation by uploader
- `Q66458942` — file transferred from Flickr
- `Q21951427` — file transferred from Wikimedia Commons
- `Q21951635` — file donated by the copyright holder

### 9. Adding Coordinates (`wbcreateclaim` with globecoordinate value)

```python
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P1259",             # coordinates of point of view
        "value": json.dumps({
            "latitude": 48.8566,
            "longitude": 2.3522,
            "precision": 0.0001,
            "globe": "http://www.wikidata.org/entity/Q2",  # Earth
        }),
        "token": csrf_token,
        "format": "json",
    },
)
```

### 10. Adding a Qualifier (`wbsetqualifier`)

After creating a claim (you get the claim ID in the response), you can add qualifiers. For example, adding a color qualifier to a depicts statement:

```python
claim_id = "M12345$6F8A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C"  # from wbcreateclaim response

resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbsetqualifier",
        "claim": claim_id,
        "property": "P462",              # color
        "value": json.dumps({"id": "Q23444"}),  # blue
        "token": csrf_token,
        "format": "json",
    },
)
```

**Common qualifier properties:**
- `P462` — color (for depicts)
- `P6022` — expression, gesture or body pose (for depicts)
- `P518` — applies to part (for depicts)
- `P2093` — author name string (for creator)
- `P580` — start time
- `P582` — end time
- `P1545` — series ordinal

### 11. Setting a Rank

Claims have three possible ranks. Set the rank when creating or updating:

```python
# During creation, rank is optional (defaults to "normal")
# To change rank after creation:
claim_data = {
    "id": "M12345$6F8A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C",
    "type": "statement",
    "rank": "preferred",
    "mainsnak": {
        "snaktype": "value",
        "property": "P180",
        "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q42"}},
        "datatype": "wikibase-item",
    },
}

resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbsetclaim",
        "claim": json.dumps(claim_data),
        "token": csrf_token,
        "format": "json",
    },
)
```

**Rank meanings:**
| Rank | Meaning | Commons Use |
|------|---------|-------------|
| `preferred` | Most important statements | Prominent depicts — the main subjects of the file |
| `normal` | Standard statement | Regular depicts — all visible items |
| `deprecated` | Statement known to be incorrect | Used only for correcting errors |

### 12. Removing Claims (`wbremoveclaims`)

```python
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbremoveclaims",
        "claim": "M12345$6F8A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C",
        "token": csrf_token,
        "format": "json",
    },
)
```

### 13. Adding a Reference (`wbsetreference`)

```python
reference_snaks = json.dumps({
    "P854": [{                          # reference URL
        "snaktype": "value",
        "property": "P854",
        "datatype": "url",
        "data": {"type": "string", "value": "https://example.com/source"},
    }],
})

resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbsetreference",
        "statement": "M12345$6F8A3B2C-1D4E-5F6A-7B8C-9D0E1F2A3B4C",
        "snaks": reference_snaks,
        "token": csrf_token,
        "format": "json",
    },
)
```

**Common reference properties:**
- `P854` — reference URL (URL of the source)
- `P143` — imported from Wikimedia project (for migrated data)
- `P813` — retrieved (date when the source was accessed)
- `P248` — stated in (Wikidata item representing the source)
- `P4656` — Wikipedia article (as source)

---

## Batch and Workflow Patterns

### Pattern A: Adding SDC to All Files in a Category

```python
import requests
import json
import time

SESSION = requests.Session()
SESSION.auth = ("User@botname", "bot_password")
SESSION.headers.update({"User-Agent": "MyBot/1.0 (https://example.com; user@example.com)"})

# Step 1: Get CSRF token
token_resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={"action": "query", "meta": "tokens", "type": "csrf", "format": "json"},
)
csrf_token = token_resp.json()["query"]["tokens"]["csrftoken"]

# Step 2: Get all files in a category
def get_category_files(category, limit=500):
    """Get all file titles and page IDs in a Commons category."""
    files = []
    cmcontinue = None
    while len(files) < limit:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "file",
            "cmlimit": "max",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params=params)
        data = resp.json()
        for member in data["query"]["categorymembers"]:
            files.append({
                "title": member["title"],
                "pageid": member["pageid"],
                "m_id": f"M{member['pageid']}",
            })

        if "continue" in data and "cmcontinue" in data["continue"]:
            cmcontinue = data["continue"]["cmcontinue"]
        else:
            break

    return files[:limit]

# Step 3: Add depicts statement to each file
files = get_category_files("Bridges in Paris", limit=50)
for f in files:
    resp = SESSION.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbcreateclaim",
            "entity": f["m_id"],
            "property": "P180",
            "value": json.dumps({"id": "Q12280"}),   # bridge
            "token": csrf_token,
            "format": "json",
        },
    )
    print(f"{f['title']}: {resp.json().get('claim', {}).get('id', 'error')}")
    time.sleep(0.5)  # rate limiting
```

### Pattern B: Adding Captions from a Spreadsheet

```python
import csv
import json
import time

# CSV format: filename,caption_en,caption_de,caption_fr
with open("captions.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # First, get the M ID
        resp = SESSION.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "prop": "info",
                "titles": f"File:{row['filename']}",
                "format": "json",
            },
        )
        pages = resp.json()["query"]["pages"]
        for page_id, info in pages.items():
            m_id = f"M{page_id}"

        # Set caption for each language
        for lang in ["en", "de", "fr"]:
            caption = row.get(f"caption_{lang}", "").strip()
            if not caption:
                continue
            resp = SESSION.post(
                "https://commons.wikimedia.org/w/api.php",
                data={
                    "action": "wbsetlabel",
                    "id": m_id,
                    "language": lang,
                    "value": caption,
                    "token": csrf_token,
                    "format": "json",
                },
            )
        time.sleep(0.5)
```

### Pattern C: Copy SDC from One File to Another

```python
# Get claims from source file
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetclaims",
        "entity": "M12345",          # source file
        "format": "json",
    },
)
claims = resp.json()["claims"]

# Copy each claim to the target file (simplified — skips qualifiers/references)
for prop, claim_list in claims.items():
    for claim in claim_list:
        snak = claim.get("mainsnak", {})
        if snak.get("snaktype") == "value" and "datavalue" in snak:
            resp = SESSION.post(
                "https://commons.wikimedia.org/w/api.php",
                data={
                    "action": "wbcreateclaim",
                    "entity": "M67890",          # target file
                    "property": prop,
                    "value": json.dumps(snak["datavalue"]["value"]),
                    "token": csrf_token,
                    "format": "json",
                },
            )
        time.sleep(0.3)
```

### Pattern D: Update a Claim Value

```python
# First, get the claim ID
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetclaims",
        "entity": "M12345",
        "property": "P180",
        "format": "json",
    },
)
claim_id = resp.json()["claims"]["P180"][0]["id"]

# Then update its value
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbsetclaimvalue",
        "claim": claim_id,
        "value": json.dumps({"id": "Q42"}),
        "token": csrf_token,
        "format": "json",
    },
)
```

---

## Constraint Checking

Wikibase has a constraint checking system that validates statements against rules (e.g., "a file should have only one digital representation of statement", "depicts values should exist as Wikidata items").

### Check Constraints for a Single File

```python
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbcheckconstraints",
        "id": "M12345",
        "format": "json",
    },
)
```

The response shows constraint violations grouped by property:

```json
{
  "M12345": {
    "P180": [
      {
        "constraint": {
          "id": "P180$...",
          "type": "SingleValueConstraint",
          "status": "violation"
        },
        "claims": ["M12345$..."],
        "message": "..."
      }
    ]
  }
}
```

### Check Constraints on Batch Operations

Before running a batch edit, you can pre-validate by checking whether the entity already has the property:

```python
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetclaims",
        "entity": "M12345",
        "property": "P6243",          # digital representation of — single-value
        "format": "json",
    },
)
existing = resp.json().get("claims", {}).get("P6243", [])
if existing:
    print(f"Warning: M12345 already has a P6243 statement (single-value constraint)")
```

### Common Constraints on Commons

| Constraint Type | Properties | Effect |
|----------------|------------|--------|
| Single value | P6243 (digital representation of) | Each file should have at most one |
| Commons item | P180, P170, P6216, P275 | Value must be a valid Wikidata item |
| Used as qualifier | P462, P6022, P518 | Should only be used as qualifiers on Commons |
| Allowed units | P571 (date) | Must use Gregorian or Julian calendar |
| Format | P973 (described at URL) | Value must be a valid URL |

---

## Editing via the Web UI

### Adding Captions

1. Go to the file page on Commons
2. Click the **"File information"** tab (below the image)
3. Under the image, you'll see a **"Captions"** section
4. Click **"Add a caption"** or the pencil icon next to an existing caption
5. Select a language and enter the caption text
6. Click **"Save"**

### Adding Depicts

1. Go to the file page → click the **"Structured data"** tab
2. Click **"Edit"** or start typing in the search box
3. Search for the Wikidata item (e.g., "Douglas Adams")
4. Select the matching item from the autocomplete
5. Click **"Publish"**

### Adding Other Statements

1. Structured data tab → "Edit"
2. Click **"Add statement"** (above the existing statements)
3. Select a property from the dropdown (or search by name/PID)
4. Enter the value (item search, date picker, text field depending on property type)
5. Optionally add qualifiers or a reference
6. Click **"Publish"**

### The AC/DC Gadget (Batch Editing)

AC/DC stands for "Add to Commons, Descriptive Claims." It's a **gadget** that lets you add the same statements to every file in a category, search result, or user-defined set.

**To enable AC/DC:**
1. Go to `Preferences → Gadgets`
2. Check **"AC/DC: Add to Commons, Descriptive Claims"**
3. Click **"Save"**

**To use:**
1. Navigate to a category page (e.g., `Category:Bridges in Paris`)
2. A new **"AC/DC"** tab appears at the top of the page
3. Select properties and values to add (e.g., depicts → bridge)
4. Click **"Execute"** — it adds the statement to every file in the category

AC/DC supports adding, removing, and setting statements with qualifiers. It processes files in the background and reports progress.

---

## Community Tools for SDC

### ISA Tool — Gamified Depicts

[ISA Tool](https://isa.toolforge.org/) is a micro-contribution tool for adding depicts and captions through a game-like interface.

- **For campaign coordinators:** Create a campaign by selecting a Commons category. Participants add depicts/captions through a simple mobile-friendly interface. Track progress and leaderboard stats.
- **For participants:** See one image at a time, type what it depicts, and move to the next. Points and leaderboards add motivation.
- **API access:** ISA has its own API for programmatic campaign management.

### OpenRefine — Advanced Batch Edits

[OpenRefine](https://commons.wikimedia.org/wiki/Commons:OpenRefine) is a desktop application for data cleanup and batch editing. It supports:

- **Uploading files** with structured data in one workflow
- **Adding/editing** captions, depicts, creator, copyright, license, dates
- **Reconciling** values against Wikidata items
- **Template-based edits** (add `{{Information}}` template data alongside SDC)

Workflow:
1. Open OpenRefine → Create project (from CSV, Excel, or JSON)
2. Extend → Reconcile → Wikidata (for item values)
3. Choose "Wikimedia Commons" as the target
4. Map columns to SDC properties (captions, depicts, creator, etc.)
5. Preview and execute edits

### QuickStatements — Command-Line Batch

[QuickStatements](https://quickstatements.toolforge.org/#/) can now target Commons SDC. Switch the dropdown from "Wikidata" to "Commons" and use M IDs instead of Q IDs.

**Command syntax:**
```
M12345|P180|Q42                    # Add depicts → Douglas Adams
M12345|P180|Q42|P462|Q23444        # Add depicts + color qualifier
M12345|Len|"Sugar cubes"           # Set English caption
M12345|P6216|Q50402863             # Set copyright status → public domain
```

**Batch via curl (using the QuickStatements API):**
```
POST https://quickstatements.toolforge.org/api.php
  with commands as CSV or V1 format
```

### Minefield — M ID Conversion

[Minefield](https://hay.toolforge.org/minefield/) converts a list of Commons file titles to M IDs — essential preparation for QuickStatements or API batch operations.

### Depictor — Focused Depicts Tool

[Depictor](https://hay.toolforge.org/depictor/) is a game-like tool specifically for adding depicts statements. You can customize it by selecting a specific Commons category or providing a SPARQL query to define the image set.

### SDC Tool (User Script)

[SDC tool](https://commons.wikimedia.org/wiki/User:Magnus_Manske/sdc_tool.js) is a user script (similar to Cat-a-lot) for adding limited SDC statements to files on category pages, gallery pages, and search results. Enable it in your `common.js`:

```javascript
mw.loader.load('//commons.wikimedia.org/w/index.php?title=User:Magnus_Manske/sdc_tool.js&action=raw&ctype=text/javascript');
```

### Image Annotator

[Image Annotator](https://image-annotator.toolforge.org/) runs image annotation campaigns. Users draw bounding boxes on images and tag what's inside them, generating coordinate-qualified depicts statements.

### Cat2Data

[Cat2Data](https://commons.wikimedia.org/wiki/User:TechieNK/Cat2Data) is a beginner-friendly user script for adding/removing statements on all files in a category.

---

## GLAM-Specific Workflows

### Workflow A: Batch Upload with SDC (Pattypan)

1. Prepare a spreadsheet with columns: filename, description, date, author, license, categories, and SDC properties
2. Use [Pattypan](https://commons.wikimedia.org/wiki/Commons:Pattypan) to upload the files
3. Pattypan can add basic SDC (captions, depicts) during upload
4. For additional SDC, follow up with OpenRefine or the Action API

### Workflow B: Post-Upload SDC Enrichment (OpenRefine)

1. Upload files via Pattypan or UploadWizard (no SDC during upload is fine)
2. Get the file list from the Commons category
3. Open OpenRefine → Create project → Import from Commons category
4. Reconcile columns against Wikidata for depicts, creator, location values
5. Map: column A → depicts (P180), column B → creator (P170), column C → inception (P571)
6. Execute batch edit — OpenRefine handles rate limiting and conflict detection

### Workflow C: Campaign-Based Annotation (ISA Tool)

1. Go to [ISA Tool](https://isa.toolforge.org/) → Create a Campaign
2. Select a Commons category (e.g., "Images from the National Archive")
3. Set the campaign description and target languages
4. Share the campaign link with volunteers or participants
5. Monitor progress in the ISA Tool dashboard
6. Export the results or verify quality via SPARQL

### Workflow D: Large-Scale Automated SDC (API Script)

For very large collections (10,000+ files), use the Action API directly with careful rate limiting:

```python
def batch_add_sdc(file_list, property_id, value_qid, batch_size=50):
    """Add a statement to many files with rate limiting."""
    for i, (title, m_id) in enumerate(file_list):
        try:
            resp = SESSION.post(
                "https://commons.wikimedia.org/w/api.php",
                data={
                    "action": "wbcreateclaim",
                    "entity": m_id,
                    "property": property_id,
                    "value": json.dumps({"id": value_qid}),
                    "token": csrf_token,
                    "format": "json",
                },
            )
            data = resp.json()
            if "error" in data:
                print(f"Error on {title}: {data['error']['info']}")
            elif i % batch_size == 0:
                print(f"Progress: {i}/{len(file_list)}")
        except Exception as e:
            print(f"Exception on {title}: {e}")

        time.sleep(0.5)  # 2 files/second — conservative
```

### Workflow E: Quality Checking SDC via SPARQL

After adding SDC, verify it with the **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** skill. Example:

```sparql
# Check files in a specific category that are MISSING depicts
SELECT ?file ?title WHERE {
  SERVICE wikibase:mwapi {
    bd:serviceParam wikibase:endpoint "commons.wikimedia.org";
                    wikibase:api "Generator";
                    mwapi:generator "categorymembers";
                    mwapi:gcmtitle "Category:My_Collection";
                    mwapi:gcmtype "file";
                    mwapi:gcmlimit "max";
                    mwapi:gcmprop "title|pageid".
    ?title wikibase:apiOutput mwapi:title .
    ?pageid wikibase:apiOutput "@pageid" .
  }
  BIND(URI(CONCAT('https://commons.wikimedia.org/entity/M', ?pageid)) AS ?file)
  FILTER NOT EXISTS { ?file wdt:P180 [] . }
}
```

---

## Data Modeling Guidelines

### Depicts (P180)

- **Be specific** — if the file shows a particular species of rose, use that species Q ID, not just "rose" (Q34687)
- **Don't over-tag** — a portrait of a person shows a face, nose, mouth, hair, etc. Just tag the person
- **Group when applicable** — a photo of Bonnie and Clyde should tag both individuals + the group
- **Use prominence** — mark the main subject as `preferred` rank; supporting items as `normal`
- **Use qualifiers** — color (P462), expression/gesture (P6022), applies to part (P518) for precision

### Creator (P170)

- **Use Wikidata items** when the creator has a known Q ID
- **Use the author name string qualifier** (P2093) when the creator has no Wikidata item
- **Do not use P170 for uploader** — the uploader is not necessarily the creator

### Copyright / License

- **Always add both** copyright status (P6216) and license (P275) for completeness
- **Public domain files** use P6216 = Q50402863
- **CC-licensed files** use the appropriate license Q ID for P275

### Date (P571)

- Use the **most precise date available** (prefer day-level over year-level)
- Use **Gregorian calendar** model unless the source specifically uses Julian
- For approximate dates, set the precision accordingly (year-only = precision 9)

---

## Error Handling

### Common API Errors

| Error Code | Likely Cause | Fix |
|------------|-------------|-----|
| `no-such-entity` | Invalid M ID | Verify the M ID exists — check `prop=info` first |
| `failed-save` | Edit conflict | Re-fetch the entity, get the latest revision, retry |
| `invalid-entity-id` | Wrong format | M IDs must be `M` followed by numeric page ID |
| `modification-failed` | CSRF token expired | Get a fresh token before each write batch |
| `permission-denied` | Not authenticated or wrong grants | Check bot password has `Edit Wikidata` grant |
| `maxlag` | Server too busy | Wait and retry with exponential backoff |

### Rate Limiting

The Commons API follows the same rate limits as other Wikimedia wikis (see the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill). For batch SDC editing:

- Pause **0.5–1 second** between write operations
- Use **`maxlag=5`** parameter to let the server tell you when to back off
- Handle **429 Too Many Requests** responses by reading the `Retry-After` header

### Edit Conflict Detection

Always include `baserevid` in your write requests when available:

```python
# Fetch current state first
resp = SESSION.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetentities",
        "ids": "M12345",
        "props": "info",
        "format": "json",
    },
)
last_revid = resp.json()["entities"]["M12345"]["lastrevid"]

# Use it in the write request
resp = SESSION.post(
    "https://commons.wikimedia.org/w/api.php",
    data={
        "action": "wbcreateclaim",
        "entity": "M12345",
        "property": "P180",
        "value": '{"id":"Q42"}',
        "baserevid": last_revid,
        "token": csrf_token,
        "format": "json",
    },
)
```

---

## Tooling

### 🐍 Commons SDC Editor (`assets/commons-sdc-editor.py`)

A Python tool for editing Structured Data on Commons — add captions, depicts, copyright, license, and other statements to files with full error handling.

```bash
# Add a caption
python3 commons-sdc-editor.py caption M12345 en "Sugar cubes on a blue surface"

# Add a depicts statement
python3 commons-sdc-editor.py claim M12345 P180 Q42

# Batch from CSV
python3 commons-sdc-editor.py batch-csv my_data.csv
```

### 📚 SDC Properties Reference (`references/sdc-properties.md`)

Deep reference for all SDC-related properties, their data types, constraint rules, and Commons-specific usage patterns.

### 🔧 SDC Stats (`scripts/sdc-stats.sh`)

Check how much structured data a category has — counts of files with/without depicts, captions, copyright statements, etc.
