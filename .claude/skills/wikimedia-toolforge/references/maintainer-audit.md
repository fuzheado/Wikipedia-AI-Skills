# Auditing Toolforge tool maintainers (ecosystem health / bus factor)

Goal: measure how many Toolforge tools have N maintainers (solo vs shared), and
enumerate unique maintainers — the "bus factor" distribution of the whole tool
ecosystem. Used when someone asks "how many people maintain Toolforge tools" or
"how many tools have >1 maintainer".

## Where the authoritative data lives

- **Striker / toolsadmin** (`https://toolsadmin.wikimedia.org/`) is the source of
  truth. Its "Maintainers" list on each tool page is read directly from the LDAP
  membership that gates `become` / service-account access. This is the *real*
  maintainer concept (who can actually touch the tool).
- **There is no public API** for "list all tools + maintainers". Striker's
  `/tools/api/` endpoints are auth-gated autocomplete/availability lookups only
  (confirmed in `wikimedia/labs-striker` → `striker/tools/urls.py`).
- **LDAP is internal-only.** `ldap.tools.wmflabs.org` / `ldap-labs.eqiad.wikimedia.org`
  do not answer on port 389 from the public internet (refused / DNS not found).
  Don't try to `ldapsearch` from outside Toolforge.
- **Toolhub is NOT authoritative for maintainers.** Its `author` field comes from each
  tool's self-reported `toolinfo.json`, not from Toolforge LDAP membership. Toolhub's
  count (~4,484) also includes non-Toolforge tools, so it can't be used for this audit.

## Crawl recipe (what works)

1. **Index** — `GET https://toolsadmin.wikimedia.org/tools/?p=N`, paginated at
   **10 tools/page**. Tool names appear in `href="/tools/id/<name>"`. Total page count
   is discoverable from the pagination `?p=N` links on page 1.
2. **Tool page** — `GET https://toolsadmin.wikimedia.org/tools/id/<name>` — **no
   trailing slash** (a trailing slash returns 404; the URL pattern is
   `id/<slug:tool>` with no `/`).
3. **Extract maintainers** — find `<caption>Maintainers</caption>`, then each
   `<td>...</td>` in that `<tbody>` is one maintainer (strip tags + HTML-unescape).

Run it with `scripts/count-maintainers.py --all` (stdlib only). The full crawl is
~4,600 requests, so it is deliberate rather than a default: without `--all` (or a
`--max-page` bound) the script prints its usage and exits instead of starting.

**Pacing.** Striker is Wikimedia infrastructure, a *non-wiki* resource, so the
[Robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy) applies: at most
**1 concurrent request** and at least **1 second between requests**. The defaults
follow that (`--workers 1 --delay 1.0`), which puts a full crawl at roughly **80
minutes** — budget for it rather than reaching for `--workers`.

`--delay` is enforced *globally across threads*: raising `--workers` does not raise
the average request rate, it only removes idle time between paced requests. Feeding
this crawl 12 threads to finish in a couple of minutes is exactly the burst pattern
that gets a client rate-limited (see the measured 101 × 429 case in the
`wikimedia-commons-thumbnails` skill) — and a 429 here is not the URL being bad, it
is the client asking too fast.

## Pitfalls

- **Trailing slash 404s** on tool detail pages — always drop it.
- A "maintainer" can itself be a **tool/service account** (e.g. `tools.xtools`,
  `tools.admin`), not a person. ~63 tools are held *only* by tool-accounts. Don't
  assume every maintainer is a human.
- Some tools **302 to a renamed/disabled target**; follow redirects and re-parse the
  final page.
- A few tools legitimately have **zero maintainers** (orphaned) — the Maintainers
  `<tbody>` is empty.
- The high end of the distribution is skewed by **WMF-run infrastructure tools**
  (`admin`, `stewardbots`, `wikibugs`, etc. with 12–18 maintainers). For a "community
  tool" solo rate, exclude those.
- Use a descriptive User-Agent (`$WIKIMEDIA_USER_AGENT` when set) and the paced
defaults above. The crawl is ~4,600 requests; at `--delay 1.0` that is ~80 minutes.
- On **HTTP 429** the script honours `Retry-After` and **stops the run** after 2
consecutive 429s rather than retrying through the throttle; on repeated **5xx** it
stops too, because the policy asks for a 15-minute pause after a 5xx.

## Baseline snapshot (2026-08-16)

- **4,205** Toolforge tools total (Striker).
- **3,145 (74.8%)** have exactly **1** maintainer; **1,059 (25.2%)** have 2+; 1 has 0.
- Median 1, mean 1.52 maintainers/tool.
- **2,092** unique maintainer accounts (mostly individuals; some tool-accounts).
- Most prolific maintainers (heavy concentration): BryanDavis (91 tools), Legoktm (89),
  Magnus Manske (87), Ladsgroup (55), MusikAnimal (49) — mostly WMF Cloud Services staff.
