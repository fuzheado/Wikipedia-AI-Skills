# WikiWho API — Endpoint Reference

Base URL: `https://wikiwho-api.wmcloud.org/<lang>/api/v1.0.0-beta/` (replace `<lang>` with a Wikipedia language code, e.g. `en`, `de`, `fr`, `zh`).

~72 languages are supported; the current list is at <https://www.mediawiki.org/wiki/WikiWho#Currently_supported_wikis>.

A Swagger 2.0 spec (the source of this reference) is served at the API root, e.g. `https://wikiwho-api.wmcloud.org/en/api/v1.0.0-beta/`.

All requests require a descriptive `User-Agent` header. No authentication. Data is CC-BY-SA 4.0.

## Common query flags

`rev_content`, `latest_rev_content`, `all_content` accept boolean flags to include per-token metadata:

| Flag | Includes |
|---|---|
| `o_rev_id=true` | Origin revision ID per token (where it was first added) |
| `editor=true` | Editor user ID per token |
| `token_id=true` | Internal token ID per token |
| `in=true` | Revisions where the token was reinserted after deletion |
| `out=true` | Revisions where the token was deleted |

Request only the flags you need — responses are large.

## Endpoints

### 1 — Content per revision

| Endpoint | Description |
|---|---|
| `GET /rev_content/{article_title}/{rev_id}/` | Token content of a specific revision |
| `GET /rev_content/rev_id/{rev_id}/` | Same, by revision ID alone |
| `GET /latest_rev_content/{article_title}/` | Token content of the most recent revision |
| `GET /latest_rev_content/page_id/{page_id}/` | Same, by page ID |
| `GET /range_rev_content/{article_title}/{start_rev_id}/{end_rev_id}/` | Tokens of revisions in range, ordered by **timestamp** (not rev-id order) |

Response shape:

```json
{
  "article_title": "Wikilambda",
  "page_id": 64444578,
  "success": true,
  "message": null,
  "revisions": [
    {
      "995998767": {
        "editor": "11292982",
        "time": "2020-12-24T00:15:32Z",
        "tokens": [
          {"str": "#", "token_id": 0, "o_rev_id": 965686479, "editor": "13006032"},
          {"str": "redirect", "token_id": 1, "o_rev_id": 965686479, "editor": "13006032"}
        ]
      }
    }
  ]
}
```

### 2 — All content (full token history)

| Endpoint | Description |
|---|---|
| `GET /all_content/{article_title}/` | Every token that has ever existed in the article, with its full change history |
| `GET /all_content/page_id/{page_id}/` | Same, by page ID |

Extra parameter: `threshold=N` — return only tokens deleted more than N times (default 0).

Response shape: `{"all_tokens": [ {token}, ... ], "threshold": 0, "article_title": ..., "page_id": ..., "success": true, "message": null}`

### 3 — Revision IDs

| Endpoint | Description |
|---|---|
| `GET /rev_ids/{article_title}/` | All revision IDs as processed by WikiWho |
| `GET /rev_ids/page_id/{page_id}/` | Same, by page ID |

Flags: `editor=true`, `timestamp=true`.

Response shape:

```json
{"revisions": [{"id": 1047879, "editor": "0|157.193.172.88", "timestamp": "2003-06-17T10:45:57Z"}, ...]}
```

### 4 — WhoColor & Edit Persistence

The home page (`https://wikiwho-api.wmcloud.org/gesis_home`) also lists **WhoColor** (per-language HTML markup APIs for inline authorship color display, used by the WhoColor userscript and the Who Wrote That? extension) and **Edit Persistence** services. These are specialized rendering/metric endpoints; the token endpoints above are the general-purpose interface.

## Token field semantics

| Field | Meaning |
|---|---|
| `str` | Token text (words, punctuation, wiki markup all separate tokens) |
| `token_id` | Internal ID, unique per article, increasing from 0 |
| `o_rev_id` | Revision where the token was first added (origin) |
| `editor` | User ID; `0` = unregistered accounts, anonymous IPs as `"0|<ip>"`; resolve to usernames via Action API `list=users&ususerids=` |
| `out` | Revisions where the token was deleted, in time order |
| `in` | Revisions where the token was reinserted after deletion (each follows an `out`) |

## Errors

| Code | Meaning | Handling |
|---|---|---|
| 400 | Bad request (bad title/rev/params) | Fix the request |
| 408 | Request timeout | Retry |
| 503 | Service unavailable | Back off and retry |

## Worked examples

```bash
# Revision IDs with editors and timestamps
curl -s "https://wikiwho-api.wmcloud.org/en/api/v1.0.0-beta/rev_ids/Wikilambda/?editor=true&timestamp=true" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"

# Current token-level content with full provenance
curl -s "https://wikiwho-api.wmcloud.org/en/api/v1.0.0-beta/latest_rev_content/Wikilambda/?o_rev_id=true&editor=true" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"

# All tokens ever added, with change history
curl -s "https://wikiwho-api.wmcloud.org/en/api/v1.0.0-beta/all_content/Wikilambda/?editor=true&in=true&out=true" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"

# Use a small article (like Wikilambda) for quick demos — on large articles the
# server computes the full response before sending headers, so even HEAD can
# take 15s+ and all_content downloads can be enormous.
```

## Background

- Algorithm: Flöck, F., & Acosta, M. (2014). "WikiWho: Precise and efficient attribution of authorship of revisioned content." WWW 2014 (DOI 10.1145/2566486.2568026). Open-access PDF at the WWW conference archives: <https://archives.iw3c2.org/www2014/proceedings/proceedings/p843.pdf>
- Moved to Wikimedia Cloud Services Aug 2021: <https://phabricator.wikimedia.org/T288840>
- Project page: <https://www.mediawiki.org/wiki/WikiWho>
- The API powers the "Who Wrote That?" extension (<https://github.com/wikimedia/WhoWroteThat>) and WhoColor.
- Known caveats: API is `v1.0.0-beta`; rate limits undocumented; the PyPI `wikiwho-wrapper` is stale (2019); the `wikimedia/wikiwho_api` code repo is archived (frozen behavior).
