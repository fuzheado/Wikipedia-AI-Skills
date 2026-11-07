---
name: citoid-publisher-diagnostics
description: This skill should be used when asked to "check if a publisher blocks Citoid", "research a domain's bot blocking", or "verify an unblock"; distinguish access, caching, WAF, and metadata failures.
license: MIT
compatibility: opencode
last_verified: 2026-11-07
depends_on: [wikimedia-api-access, wikipedia-citations]
skill_discovery_hints:
  - keywords: [citoid, publisher blocking, domain diagnosis, allowlisting, zotero translation server]
  - keywords: [user-agent differential, waf, bot blocklist, cache, wayback fallback]
---

# Citoid publisher-access diagnostics

Investigate **whether citation metadata is reachable, which layer fails, and what evidence supports a remedy**. Produce reproducible per-URL findings, not a blacklist inferred from HTTP codes. Use this skill before deciding that a publisher needs outreach or a Zotero translator.

## SOP: Diagnose a domain or publisher

### 1. Recover evidence and define the question

Read existing measurements, raw results, public issue threads, and user corrections before making new requests. Preserve original URLs, dates, endpoint formats, and network locations. Treat old publisher verdicts as historical observations, not current truth. Prefer an explicit UTC timestamp in raw evidence to a filename, filesystem modification time, conversation date, or Citoid `accessDate`.

Separate these questions:

- Does production Citoid return metadata for representative articles now?
- Is the result the requested article, a homepage, a challenge, cached metadata, or an archived fallback?
- Is failure dependent on path, host, request method, User-Agent, or source network?
- Is the content accessible but the metadata incomplete or incorrectly extracted?
- Did an intervention actually change access for the same URLs?

For an access-only request, answer access first. Keep author/date/type defects in a separate section; do not turn successful access into a blocking allegation.

### 2. Select a small, defensible sample

Start with two or three **real article URLs**, including one recently published or discovered article and, if available, a historical failing URL. Confirm that the URLs still identify articles. Obtain current links from the publisher, RSS, or a browser when necessary; do not invent slugs.

Use Wikipedia's `exturlusage` for cited examples, not as a source of necessarily current articles: results can start with very old links. Record the originating wiki and article. Treat homepage tests only as host-level controls, never as substitutes for article tests.

Keep these distinctions explicit:

- `www` versus bare host; news, regional, language, and account subdomains;
- old versus current routes, article versus section page, HTML versus PDF;
- HTTP-to-HTTPS and cross-domain redirects;
- query-bearing versus plain URLs, canonical versus `/htm` or print variants;
- original publisher URL versus an explicit Wayback URL.

Check publication ownership before extending conclusions from a domain to a publisher group. Report sample counts and exceptions instead of asserting whole-domain coverage.

### 3. Measure production Citoid first

Use the public endpoint through a Wikimedia wiki:

```text
https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/{percent-encoded-input}
https://en.wikipedia.org/api/rest_v1/data/citation/zotero/{percent-encoded-input}
```

Encode the **entire input** with `quote(url, safe="")`; preserve its query string. Use `mediawiki` for citation-facing results and `zotero` when inspecting Zotero-shaped fields. Keep the format constant in before/after comparisons and retain raw JSON: field names and response shapes differ.

Send a descriptive research User-Agent **to the Wikimedia API**. Do not assume this becomes the User-Agent Citoid sends to publishers; Citoid and the translation server have their own identities.

Pace requests sequentially, initially about one every ten seconds. Honor `Retry-After`; on repeated 429s, pause or end the run. Record service throttling separately from publisher blocking. Save each result as it arrives. See [probe protocol](references/probe-protocol.md) for runnable standard-library examples and the evidence schema.

For every response, inspect:

- HTTP status, raw error text, elapsed time, and final endpoint URL;
- returned article title, canonical URL, item type, and publication identity;
- authors/creators, date, language, and identifiers where relevant;
- `source` and any archive URL or archive date;
- whether the result actually matches the requested article.

Do not classify an HTTP 200 containing "Just a moment", "Verifying Device", "Making sure you're not a bot", or a login title as success. Conversely, do not treat Citoid HTTP 404 as the publisher's HTTP status: it can mean loading or extraction failed.

### 4. Rule out cache and archive illusions

Label results **non-Wayback metadata**, **Wayback-backed metadata**, **wrong page/challenge**, or **failure**. A `source` containing `Wayback Machine` proves an archived fallback, not a live unblock. `source: ["Zotero"]` does not prove a fresh origin fetch.

Use a genuinely new article as a stronger freshness check than repeatedly testing a popular old URL. Compare original and innocuous query-parameter variants only when useful, keeping both in the record. A cache-buster is an experiment, **not a guaranteed cache bypass**: canonicalization or internal caches may discard it, while the publisher may handle the query differently. A random fragment is not sent to the origin.

Do not infer an unblock from an old successful result while novel URLs fail. Do not infer a query-free article fails because only its query-bearing variant failed. Avoid claiming freshness from `Cache-Control: no-cache`, a response timestamp, or `accessDate` alone. Seek publisher logs or an operator-controlled endpoint when exact outgoing behavior matters.

### 5. Reproduce the access layer with controlled direct requests

Keep production results distinct from local probes. A workstation, Toolforge, and WMF production use different networks; Toolforge is **not** a proxy for production Citoid egress.

On the same URL and network, compare a browser-like baseline with the **same baseline** plus each stable service identifier:

1. browser-like baseline;
2. baseline + `Citoid/WMF (mailto:noc@wikimedia.org)`;
3. baseline + `ZoteroTranslationServer/WMF (mailto:noc@wikimedia.org)`;
4. optionally, the HTTP client's ordinary User-Agent.

Use clean requests without a browser session's authentication or challenge cookies. Keep headers, method, redirect behavior, and timing fixed. Repeat a small matrix in reversed order to distinguish a UA effect from time/rate effects. Compare HEAD with GET where redirect resolution or a method rule is suspected; a successful HEAD says nothing about the article body.

Record status, redirect chain, selected headers, content type, byte count, title, and article/challenge signals. Inspect the body even for 200 or unusually large 403 responses. A large HTML response can still be an error template; finding a challenge script or a word such as "login" somewhere in an article is not sufficient by itself.

Inspect raw HTML separately from a JavaScript-rendered browser. A rendered article does not prove server-side Citoid can obtain it. Identify JS challenges, soft login redirects, consent walls, explicit paywalls, and dead URLs without conflating them. Do not bypass them.

### 6. Localize the cause without overclaiming

| Observation | Defensible interpretation | Next step |
|---|---|---|
| Same-network browser baseline gets article; adding one token reliably gets denied | UA-conditioned denial on the tested route | Confirm repetition; inspect public rules or request WAF logs |
| All UAs fail locally; Citoid fails too | Access failure; trigger unresolved | Check current URL, method, network and challenge body |
| All UAs work locally; production fails | Network/client/path difference is plausible, not proven IP blocking | Seek publisher-side logs; compare another authorized location |
| Citoid returns article metadata but no author/date | Access works; extraction may be deficient | Inspect available source metadata and translator coverage |
| Only old links work, with Wayback in `source` | Archive recovery, not live access | Test a current article |
| Origin/CDN headers name a vendor | Vendor delivery evidence, not proof of the blocking rule | Request request-ID/rule correlation |
| Old routes fail; current routes succeed | Route-specific difference | Do not announce a same-URL unblock |

Citoid may contact a publisher during redirect/content-type discovery and then delegate to the translation server. A rule allowing only one service can still break the pipeline. Verify current deployment configuration or observed requests instead of assuming an upstream default is deployed.

When evidence suggests a stock UA blocklist, use [blocklist attribution](references/blocklist-attribution.md). Distinguish detection, analytics exclusion, and enforced denial; distinguish a matching fingerprint from a confirmed installed product. Test only a few controls, not a brute-force bypass search.

### 7. Choose the correct remedy

- **Confirmed access denial:** prepare focused publisher outreach with exact URLs, UTC times, observed errors, and the official allowlisting reference. Ask which rule fired.
- **One service or browser version behaves differently:** investigate both service configurations and deployment status. Match stable identifiers in long-lived rules, not a frozen full browser string.
- **Article accessible, metadata missing:** inspect HTML meta tags, JSON-LD graphs, application state and DOM bylines. Check existing translator targets, redirects, page types and generic extraction before proposing a new translator. Separate corporate authors from personal names; do not assume JSON-LD is always consumed.
- **URL path fails but DOI works:** report separate retrieval paths; DOI metadata is not proof of publisher-HTML access.
- **Dead or wrong URL:** repair the sample; do not request a WAF exception based on it.
- **Uncertain:** state the unresolved alternatives and the smallest additional measurement needed.

Use [reporting and outreach](references/reporting-and-outreach.md) for confidence labels, a compact report, and an allowlisting request. Consult [dated case studies](references/case-studies.md) for traps discovered in real investigations, not a current publisher-status list.

### 8. Verify an intervention

Retest the same original article URLs and failing variants using the same endpoint format, then add fresh articles. Record time and provenance, not merely "now works". Include controls for archive fallback and wrong-page success.

Distinguish a source-code merge, released list, site configuration update, deployment, and observed production change. None guarantees the next. Attribute causation only with an operator confirmation, correlated logs, or a controlled change; otherwise report a temporal association. Preserve contradictory results and correct earlier conclusions explicitly.

## Guardrails

- Do not equate "Citoid failed" with "publisher intentionally blocks Wikimedia".
- Do not generalize from a homepage, one URL, one host, or one network.
- Do not label missing authors/dates as an access block.
- Do not infer the exact WAF vendor or rule from HTTP 403/418 alone.
- Do not treat a successful archive, cache, browser, or DOI path as live origin proof.
- Do not assume public source configuration has already reached production.
- Do not bypass paywalls, CAPTCHAs, authentication or anti-bot controls; use low-volume diagnostics and operator cooperation.
- Keep credentials, cookies, private correspondence, full article dumps and personal network addresses out of public skill/report commits. Publish only necessary, reviewed evidence.
- Do not send outreach, file issues or submit patches without authorization. Include AI disclosure when posting AI-generated communications on behalf of a user.

## References

- [Probe protocol and runnable examples](references/probe-protocol.md)
- [Blocklist fingerprinting and provenance](references/blocklist-attribution.md)
- [Dated case studies and corrections](references/case-studies.md)
- [Reporting, allowlisting and source references](references/reporting-and-outreach.md)
- [Wikimedia API access](../wikimedia-api-access/SKILL.md) for API etiquette.
- [Wikipedia citations](../wikipedia-citations/SKILL.md) for ordinary citation generation and repair.
- [Zotero translator development](../zotero-translator-development/SKILL.md) after identifying an extraction defect that needs code.
