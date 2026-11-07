# Probe protocol

Use this reference for evidence capture, reproducible requests, and controlled comparisons. Keep requests low-volume and never use the matrix to evade an access control.

## 1. Establish request identity

Read [Citoid/Allowlisting](https://wikitech.wikimedia.org/wiki/Citoid/Allowlisting) at investigation time. As reviewed on **7 November 2026**, it documents these stable identifiers:

- `Citoid/WMF (mailto:noc@wikimedia.org)`
- `ZoteroTranslationServer/WMF (mailto:noc@wikimedia.org)`

The documented browser prefix for **both** is then:

```text
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36
```

Do not freeze this version in future investigations or outreach. Earlier October 2026 measurements used Chrome/110; after a translation-server update the two services temporarily differed. By 7 November the public allowlisting page and the Citoid chart both show Chrome/156. Configuration is not independent proof of the bytes every running replica sends.

Distinguish three identities:

1. Research client -> Wikimedia API: use the researcher's descriptive UA and real contact information.
2. Citoid -> publisher: configured in the Citoid service/deployment, including redirect discovery.
3. Zotero translation server -> publisher: configured independently; not necessarily identical to Citoid.

When the actual deployed identity is critical, ask operators to capture a request to an endpoint they control, or correlate publisher logs. Avoid sending confidential tokens or private URLs to third-party echo services. Record source network, HEAD/GET, full UA and time. Do not guess egress IPs from DNS names such as `citoid.wikimedia.org`.

## 2. Capture production Citoid results

Save this example as a single Python file, replace the public article URLs and contact UA, then run it with Python 3. Use an output location outside the skill repository for raw evidence. The example uses the standard library only, makes sequential requests, and preserves error bodies. It deliberately does **not** issue a verdict from field presence alone.

```python
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


USER_AGENT = "CitationAccessResearch/1.0 (https://example.org/contact)"
URLS = ["https://example.org/news/current-article"]
ENDPOINT = "https://en.wikipedia.org/api/rest_v1/data/citation/{format}/".format(
    format="mediawiki"
)
OUTPUT = Path("citoid-evidence.json")


def fetch(url):
    for attempt in range(3):
        started = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        request = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT, "Accept": "application/json"
        })
        try:
            response = urllib.request.urlopen(request, timeout=90)
        except urllib.error.HTTPError as error:
            response = error
        except (OSError, TimeoutError) as error:
            return {"started_utc": started, "transport_error": str(error)}
        with response:
            status = response.code
            headers = {key.lower(): value for key, value in response.headers.items()}
            body = response.read().decode("utf-8", errors="replace")
            result = {
                "started_utc": started, "http": status,
                "elapsed_seconds": round(time.monotonic() - tick, 3),
                "final_endpoint": response.geturl(), "headers": headers,
                "raw_body": body,
            }
        if status != 429 or attempt == 2:
            try:
                result["json"] = json.loads(body)
            except ValueError:
                pass
            return result
        retry = headers.get("retry-after", "")
        try:
            delay = float(retry)
        except ValueError:
            try:
                until = parsedate_to_datetime(retry)
                delay = (until - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                delay = 60 * (attempt + 1)
        time.sleep(max(60, delay))


if __name__ == "__main__":
    results = []
    for article in URLS:
        endpoint = ENDPOINT + urllib.parse.quote(article, safe="")
        results.append({"input_url": article, "endpoint": endpoint,
                        "response": fetch(endpoint)})
        OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        if results[-1]["response"].get("http") == 429:
            break
        time.sleep(10)
```

Stop a batch if the last response is still 429 instead of continuing across the publisher list. For a large audit, retain resumable per-URL results, bounded retries and a shared rate limiter. Treat timeouts as observations, not proof of denial. Do not disable TLS verification to make a measurement pass.

Inspect the full result. Different endpoint formats use different date and author fields. Do not silently discard all but the first item of a multi-item response. A positive author count can be a numeric Facebook page ID, a site name split as a person, or an organization; it does not establish correct extraction.

## 3. Direct-fetch comparison

Use an HTTP client with TLS verification on, no login/challenge cookies, fixed `Accept`/`Accept-Language`, and consistent redirect handling. Compare the same browser prefix alone, with the Citoid suffix, and with the translation-server suffix. Change **only** the UA first. Use a new clean client/session per matrix cell to avoid cookies contaminating comparisons.

Run one small forward-order matrix and one reverse-order matrix, with a few seconds between requests; stop on throttling or challenges rather than escalating. Repeat on another authorized network only if network discrimination is the unresolved question. Label it by location, not "WMF" unless it really is production egress.

For curl on Windows, invoke `curl.exe`, not PowerShell's historical `curl` alias. A single GET example, with an illustrative article:

```powershell
$article = 'https://example.org/news/current-article'
$ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Citoid/WMF (mailto:noc@wikimedia.org)'
curl.exe --location --max-redirs 10 --connect-timeout 20 --max-time 60 --user-agent $ua --header 'Accept: text/html,application/xhtml+xml' --dump-header headers.txt --output body.html --write-out '%{http_code} %{url_effective} %{size_download}\n' $article
```

Keep `headers.txt` and `body.html` local; they may contain cookies and copyrighted material. Inspect and redact before sharing. Use separate labels/output locations for each matrix cell rather than overwriting evidence accidentally.

To compare HEAD, issue a separate `--head` request and retain its redirect headers. Do not call it a body test. Keep the original GET evidence: some sites deny HEAD, others permit HEAD but deny GET, and redirects may be discovered differently.

### Inspect more than status and size

Capture each redirect's status and `Location`; inspect the final body and canonical link. Useful headers include `Server`, `Via`, `Content-Type`, `Content-Length`, `Retry-After`, cache headers, CDN request IDs and challenge headers. None alone identifies the precise WAF rule.

Look for the requested article's heading/title, byline, publication date, canonical URL and content signals. Distinguish:

- small hard-deny pages, empty 418 responses, and connection closures;
- a 200 challenge or login page;
- a large branded error page;
- real article HTML carrying incidental login links or challenge-library references;
- JavaScript shells whose metadata appears only after rendering;
- real article metadata behind a subscription body gate.

Use an HTML parser for extraction, not a title regex as a definitive classifier. `Content-Length` can describe compressed transfer bytes, while client body length is decompressed; do not compare them as if identical.

## 4. Cache, archive and canonicalization controls

Retain original URLs and provenance. Compare a new article, an original old URL and (only if needed) a query-bearing variant separately. Adding `?cb=...` can change routing, signatures or WAF evaluation. Do not use it on signed URLs. Fragments never reach the origin.

Read Citoid `source`, archive URL/date and returned URL. A result sourced from Wayback for a publisher URL is archived fallback. An explicit Wayback input tests the archive, not the publisher. Even a non-Wayback source may reflect service caching. Response freshness requires more than a fresh HTTP timestamp.

When repeated cached success contradicts new-article failures, report both. For a claimed before/after transition, retest the **exact failing URLs** and endpoint format; current-route successes cannot substitute for failed legacy paths.

## 5. Evidence fields

For each request retain:

```text
run_id; started_utc; network_label; input_url; original_or_variant;
method; endpoint_format; request_ua; selected_request_headers;
http_status; elapsed_seconds; redirect_chain; final_url;
selected_response_headers; body_bytes; body_title; body_classification;
raw_citoid_json; source; returned_url; item_type;
authors; publication_date; archive_url; archive_date;
interpretation; confidence; evidence_artifact
```

Keep response metadata and raw bodies privately; publish only a reviewed subset. Record transport failures rather than substituting status 0 for every failure kind. Explicitly mark unknown values. Do not include access tokens, authorization headers, session cookies, or personal IPs in a public report.
