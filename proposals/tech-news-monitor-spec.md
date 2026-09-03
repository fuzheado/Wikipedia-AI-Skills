# Tech News Monitor — Skill Impact Watcher

**Date:** 2026-09-03
**Author:** Hermes agent spec for Andrew Lih (User:Fuzheado)
**Status:** Proposed — spec for a persistent (Hermes 24×7) watcher process; not yet implemented
**Related:** PR #26 (thumbnails skill update), T427465 / T402792 / Tech News 2026 week 05 + Issue 36 (motivating incidents)

---

## 1. Motivation

In September 2026, CommonsVibe debugging traced an image-loading regression to a
Wikimedia thumbnail infrastructure migration (`thumb.wikimedia.org`, standard-size
enforcement). Every part of that change was **announced in advance** in
**Tech News** — the Wikimedia technical community's weekly bulletin:

- **2026-01-26 (week 05):** non-standard thumbnail sizes "will stop working in the
  near future … Tool-authors, will need to update their code to use standard
  thumbnail sizes" — **8 months of lead time**.
- **2026-08-31 (Issue 36):** the domain change itself, 3 days before the bug
  surfaced. The same issue also announced the deepcat search fix (observed
  live during that debugging) and the Math API deprecation.

Nothing in the skills catalog caught these announcements. A catalog of 40+ skills
each pinned to moving Wikimedia API surfaces has exactly one weekly, structured,
archived channel that reports changes to those surfaces — and nobody is listening
to it systematically. This spec defines a watcher that listens.

## 2. What it is / is not

**Is:** a persistent, low-volume process that (a) ingests each new Tech News issue,
(b) matches announcement items against the skills catalog's API-surface inventory,
and (c) publishes a **review report** listing likely-affected skills with the
specific evidence — opened as a GitHub issue for human triage.

**Is not:** an auto-editor. Tech News items are prose; matching is probabilistic.
The bot **recommends, never commits** to skill files. Human reviews each report
and decides whether a skill needs updating (as PR #26 did for thumbnails).

## 3. Inputs

| Input | Source | Notes |
|---|---|---|
| Tech News issues | Diff posts (e.g. `diff.wikimedia.org/2026/08/31/tech-news-2026-issue-36/`) and/or meta.wikimedia.org `Tech/News/*` transclusions; RSS/Atom available | Published weekly (Mondays); occasional special editions |
| `scripts/api-surface.json` | checked into the skills repo, refreshed by `scripts/refresh-api-surface.py` | machine-readable inventory: which API domains/endpoints each skill touches — **the matching substrate** |
| Skill files | `.claude/skills/*/SKILL.md` (+ `references/`) | for evidence citation (file + line) |
| Ledger | watcher-local state (see §7) | what has already been processed |

## 4. Pipeline (per new issue)

1. **Detect.** Poll the Diff RSS feed and/or the meta Tech/News index 2–4×/day
   (issues publish Mondays ~18:00 UTC). Dedupe by issue slug
   (`tech-news-2026-issue-36`).
2. **Extract items.** Split the issue into announcement items (bullet/section
   boundaries under "Latest tech news" / "Updates for technical contributors").
   Each item: {id, title, body, links[], phab-ids[]}.
3. **Match** each item against the inventory, in tiers:
   - **T1 — entity/domain (highest confidence):** item mentions a domain or
     endpoint literal that appears in `api-surface.json` or skill files
     (`upload.wikimedia.org`, `thumb.wikimedia.org`, `incategory`, `imageinfo`,
     `api.wikimedia.org`, …). The thumbnail case matches at T1 on 7
     `upload.wikimedia.org` references in `wikimedia-commons-thumbnails`.
   - **T2 — keyword:** API/product names (`deepcat`, `CirrusSearch`, `EventStreams`,
     `MinT`, `OAuth`, `Math`…) matched against skill names/descriptions/keywords
     from SKILL.md frontmatter.
   - **T3 — advisory (report-only, lower confidence):** deprecation/sunset
     language (`deprecated`, `sunset`, `stop working`, `will be removed`) with no
     entity match — include as "manual review" items.
   - **Skip-list:** maintenance-window, browser-release, and other generic items
     match nothing → silently ignored.
4. **Score & dedupe.** Confidence = tier + match count + phab-reference boost
   (a named Phab task linked from a skill is strong evidence). Never re-report an
   (issue, skill) pair already in the ledger.
5. **Report.** If ≥1 item matched at T1/T2: open a **GitHub issue** in
   `fuzheado/Wikipedia-AI-Skills` (dedupe by issue slug in the title), containing:
   - the announcement item(s), quoted, with link and date
   - per matched skill: name, matched entity, the SKILL.md lines referencing it
   - a suggested first check ("grep the skill for `<domain>`; review section X")
   - explicit note: **review required — the bot does not update skills**
   If only T3 items matched: append to a rolling monthly digest instead of filing
   an issue (keeps noise down).

## 5. Runtime: Hermes 24×7 placement

Designed for a persistent Hermes process, runtime-agnostic requirements:

- **Scheduler:** in-process timer or cron — poll 2–4×/day is sufficient; weekly
  output.
- **Network:** outbound HTTPS to diff.wikimedia.org / meta.wikimedia.org (read)
  and api.github.com (issue creation). GitHub token via env/secret.
- **Git:** **not required** — the watcher reads the catalog via the GitHub API
  (raw file fetch) or a periodic `git pull` of the skills repo into a scratch
  clone. Ledger lives in watcher-local storage (§7), not committed to the repo.
- **State:** small JSON ledger, durable across restarts (Hermes state dir).
- **Politeness:** descriptive User-Agent (`tech-news-monitor/0.1 (Hermes; contact:
  User:Fuzheado)`), honor caching headers, ≤1 fetch/hour per feed.

**CI fallback (optional):** the same matcher runnable as a weekly GitHub Actions
job in the skills repo for environments without a persistent process — loses the
prompt "day-of" notice but keeps the report. The matcher must be a pure function
of (issue text, catalog snapshot) to support both modes.

## 6. Matching substrate — keep `api-surface.json` honest

The watcher is only as good as the inventory. Requirements:
- `refresh-api-surface.py` must keep covering: domains referenced per skill,
  Action-API params/keywords, REST endpoints, external services.
- New skills must add their surface at registration time (extend the
  skill-registration check to warn if a skill has no api-surface entry).

## 7. Ledger (state)

```json
{
  "issues": {
    "tech-news-2026-issue-36": {
      "processedAt": "2026-09-04T06:00:00Z",
      "url": "https://diff.wikimedia.org/2026/08/31/tech-news-2026-issue-36/",
      "reported": true,
      "githubIssue": 27,
      "matches": ["wikimedia-commons-thumbnails", "wikimedia-api-access"]
    }
  },
  "lastFeedCheck": "2026-09-04T06:00:00Z"
}
```

## 8. Failure modes & observability

- **Feed format drift** (Diff redesign): item extraction returns 0 items for 2
  consecutive issues → alarm (Hermes notification / GitHub issue) — silence is
  the enemy; a dead watcher must be visible.
- **Heartbeat:** write `lastFeedCheck` on every poll; external alarm if stale
  >72h (misses >2 issues).
- **Feed unavailable:** back off exponentially; do not alert on a single failed
  poll; alert at 48h.
- **GitHub API failures:** retry ×3, then carry forward unreported matches into
  the next successful run (ledger only marks `reported` after issue creation).
- **Rate limits:** trivially low volume; standard UA + pacing suffices.

## 9. Testing — historical replay as ground truth

Ship two fixture issues with known-correct expected output:

| fixture | must flag | must NOT flag |
|---|---|---|
| Tech News 2026 week 05 (2026-01-26) | `wikimedia-commons-thumbnails`, `wikimedia-api-access`, `pattypan` (thumbnail sizes/tool-author language) | skills with no media/API surface |
| Tech News 2026 Issue 36 (2026-08-31) | `wikimedia-commons-thumbnails` (domain change, T1), `wikimedia-api-access` | Math API deprecation item → **no skill match** (correct silence) |

Golden tests assert: flagged set, match tier, and evidence lines. CI runs the
replay on every matcher change. This is the cheapest way to keep the matcher
honest as it evolves.

## 10. Non-goals (v1)

- No automatic skill edits or PRs (human triage only).
- No Phabricator task watching (T427465 was never in Tech News until after the
  fact — a **future extension**: watch a subscribed-task list via the Phab API
  `maniphest.search` and feed results into the same matcher).
- No non-Wikimedia feeds (reuse the pipeline later for WMF Bulletins, wikitech-l).

## 11. Effort estimate

- Matcher + ledger + report: ~150–200 lines Python (reuses
  `api-surface.json` + existing CI patterns).
- Hermes wiring (scheduler, storage, GitHub issue creation): ~50–100 lines.
- Fixtures + golden tests: ~100 lines.
- **Total ≈ 1–2 sessions.** Highest-leverage part is keeping `api-surface.json`
  current — one existing refresh script already does that.

## 12. Open questions

1. GitHub issues vs. a `reports/tech-news/` file in the repo as the report
   surface (issues are more actionable; files are greppable — could do both).
2. Should the ledger be committed under `reports/tech-news/ledger.json` for
   auditability (low-churn, ~1 commit/week) or stay Hermes-local?
3. T3 advisory language list — start conservative (`deprecated`, `sunset`,
   `stop working`, `removed`, `breaking`) and grow from observed misses.
