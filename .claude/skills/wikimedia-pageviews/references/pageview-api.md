# Pageviews API Reference

All pageview data is served from `wikimedia.org`, not from individual project
domains. Data is delayed by approximately **48 hours**.

---

## Base URL

```
https://wikimedia.org/api/rest_v1/metrics/pageviews/
```

Documentation: https://wikimedia.org/api/rest_v1/

---

## Endpoints

### Top Pages

```
GET /top/{project}/{access}/{date}
```

Returns the most viewed pages for a project on a given date.

| Parameter | Description | Example |
|---|---|---|
| `project` | Wikimedia project | `en.wikipedia`, `de.wikipedia`, `commons.wikimedia`, `www.mediawiki.org` |
| `access` | Access method | `all-access`, `desktop`, `mobile-web`, `mobile-app` |
| `date` | Date (slash format) | `2026/05/20` |

**Response:**
```json
{
  "items": [{
    "project": "en.wikipedia",
    "access": "all-access",
    "year": "2026",
    "month": "05",
    "day": "20",
    "articles": [
      {"article": "Main_Page", "views": 7110064, "rank": 1},
      {"article": "Special:Search", "views": 1020117, "rank": 2}
    ]
  }]
}
```

### Per-Article Pageviews

```
GET /per-article/{project}/{access}/{agent}/{article}/daily/{start}/{end}
```

Returns daily pageview counts for a specific article over a date range.

| Parameter | Description | Example |
|---|---|---|
| `referer` | `all-referers`, `internal`, `external`, `unknown`, or a project domain | `all-referers` |
| `access` | Access method | `all-access`, `desktop`, `mobile-web`, `mobile-app` |
| `agent` | User agent type | `all-agents`, `user`, `spider`, `automated` |
| `article` | Page title (underscores) | `Albert_Einstein`, `Python_(programming_language)` |
| `start` | Start date (compact) | `20260101` |
| `end` | End date (compact) | `20261231` |

**Response:**
```json
{
  "items": [
    {"project": "en.wikipedia", "article": "Albert_Einstein",
     "granularity": "daily", "timestamp": "2026051600",
     "access": "all-access", "agent": "all-agents", "views": 11065}
  ]
}
```

### Media Requests (mediarequests) — file/media load counts

Sibling API for **media file loads**, not page views. Base:
`https://wikimedia.org/api/rest_v1/metrics/mediarequests/`

> **`per-file` works — but the path format is strict.**
> `mediarequests/per-file/{referer}/{agent-type}/{file-path}/{granularity}/{start}/{end}`
> where `file-path` is the upload path URL-encoded **with the leading slash**
> (`/wikipedia/commons/0/00/Crab_Nebula.jpg` → `%2Fwikipedia%2Fcommons%2F0%2F00%2FCrab_Nebula.jpg`;
> omit the slash or the `agent-type` segment and you get a 404 "invalid route",
> which previously misled a note into claiming the endpoint was removed).
> `referer` ∈ `all-referers|internal|external|unknown` or a project domain;
> `agent-type` ∈ `user|spider|all-agents` — **`automated` returns HTTP 400 on
> every route** (verified 2026-09-05 across all referer values); the AQS
> surface has no `automated` class (dumps only).

```
GET /top/{referer}/{media-type}/{year}/{month}/{day}
```

| Parameter | Description | Example |
|---|---|---|
| `referer` | `all-referers`, `internal`, `external`, `unknown`, or a project domain | `all-referers` |
| `media-type` | One of `all-media-types`, `image`, `video`, `audio`, `document`, `other` | `image` |
| `year`/`month`/`day` | Date (numeric, slash-style path) | `2024`/`01`/`01` |

**Response** — up to **1,000 files per day**:
```json
{ "items": [ { "referer": "en.wikipedia", "media_type": "image", "year": "2024",
  "month": "01", "day": "01", "files": [
    { "file_path": "/wikipedia/donate/1/14/Wikimedia_Foundation_logo_-_wordmark.svg",
      "requests": 11512041, "rank": 1 } ] } ] }
```

- `file_path` is the **hash path**, not a `File:` title — match on the basename.
- Files outside the daily top-1000 have no API-accessible count.
- **Do not confuse with `pageviews/per-article` on `File:` pages** — that
  counts description-page views (small); `mediarequests` counts actual media
  loads (large). "How many people viewed this image" is a mediarequests
  question, not a pageviews question.

### Top by Country

```
GET /top-by-country/{country}/{date}
```

Most viewed articles in a specific country on a given date.

| Parameter | Description | Example |
|---|---|---|
| `country` | ISO 3166-1 alpha-2 code | `US`, `DE`, `FR`, `IN`, `JP` |
| `date` | Date (slash format) | `2026/05/20` |

### Top by Editing Community

```
GET /top-by-ec/{project}/{access}/{year}/{month}
```

Most viewed articles by editors of a specific project in a given month.

---

## Date Format Reference

| Endpoint | Date Format | Example |
|---|---|---|
| `top/{project}/{access}/{date}` | `YYYY/MM/DD` (with slashes) | `2026/05/20` |
| `top-by-country/{country}/{date}` | `YYYY/MM/DD` (with slashes) | `2026/05/20` |
| `per-article/.../daily/{start}/{end}` | `YYYYMMDD` (compact, no slashes) | `20260101` |
| `per-article/.../monthly/{start}/{end}` | `YYYYMM` (compact, no slashes) | `202601` |
| `top-by-ec/{project}/{access}/{year}/{month}` | `YYYY` / `MM` | `2026` / `05` |

**Important:** The Top endpoint uses slashes (`2026/05/20`). The Per-Article
endpoint uses compact format (`20260101`). Using the wrong format returns 404.

---

## Common Patterns

### Last 30 days of pageviews

```bash
START=$(date -v-30d +%Y%m%d)
END=$(date +%Y%m%d)
curl "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Albert_Einstein/daily/${START}/${END}"
```

### Top 100 for today (minus 3 days for data lag)

```bash
DATE=$(date -v-3d +%Y/%m/%d)
curl "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/${DATE}"
```

### Compare desktop vs mobile for an article

```bash
URL="https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia"
for access in desktop mobile-web mobile-app; do
  curl -s "${URL}/${access}/all-agents/Albert_Einstein/daily/20260501/20260520" | \
    python3 -c "import json,sys; items=json.load(sys.stdin).get('items',[]); print(f'${access}: {sum(i[\"views\"] for i in items)}')"
done
```

### Top articles across multiple projects

```bash
for project in en.wikipedia de.wikipedia fr.wikipedia; do
  curl -s "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/${project}/all-access/2026/05/20" | \
    python3 -c "import json,sys; d=json.load(sys.stdin); items=d['items'][0]['articles'][:3]; print('${project}:'); [print(f'  #{a[\"rank\"]} {a[\"article\"]} ({a[\"views\"]})') for a in items]"
done
```

---

## Error Responses

| HTTP Code | Meaning |
|---|---|
| 200 | Success |
| 404 | No data for date (data lag ~48h) or invalid date format |
| 429 | Rate limited — back off and retry |

Common 404 causes:
- Date is too recent (data delayed ~48 hours)
- Wrong date format (slashes vs compact)
- Invalid project name (use `en.wikipedia`, not `en.wikipedia.org`)
- Article doesn't exist or has no views

---

## Rate Limiting

- No documented rate limit, but be respectful
- Use a descriptive User-Agent header
- Add 0.5s delay between batch requests
- Cache results when possible
