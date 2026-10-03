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

Run it with `scripts/count-maintainers.py` (stdlib only, threaded, ~4,200 tools in a
few minutes).

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
- Use a descriptive User-Agent and polite concurrency (~12 threads). The full crawl is
  ~4,200 requests; a couple minutes.

## Baseline snapshot (2026-08-16)

- **4,205** Toolforge tools total (Striker).
- **3,145 (74.8%)** have exactly **1** maintainer; **1,059 (25.2%)** have 2+; 1 has 0.
- Median 1, mean 1.52 maintainers/tool.
- **2,092** unique maintainer accounts (mostly individuals; some tool-accounts).
- Most prolific maintainers (heavy concentration): BryanDavis (91 tools), Legoktm (89),
  Magnus Manske (87), Ladsgroup (55), MusikAnimal (49) — mostly WMF Cloud Services staff.
