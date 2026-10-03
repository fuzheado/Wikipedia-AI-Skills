# Researching a Wikimedia Extension's History — Worked Example

## Case Study: Special:PersonalDashboard (2025–2026)

### Sources Consulted

| Source | What It Provided |
|--------|-----------------|
| [T404439](https://phabricator.wikimedia.org/T404439) — Gerrit repo request | Earliest date: Sep 12, 2025 |
| [T402647](https://phabricator.wikimedia.org/T402647) — MVP launch epic | Pilot wikis (id, tr, simple, th), user criteria (100+ edits), MVP scope |
| [T418367](https://phabricator.wikimedia.org/T418367) — Deploy to enwiki | Silent rollout date: Mar 19, 2026 |
| [T421415](https://phabricator.wikimedia.org/T421415) — Live config on enwiki | Go-live date: Apr 6, 2026 |
| [T419358](https://phabricator.wikimedia.org/T419358) — FY26-27 epic | Current status, active work Jul–Dec 2026 |
| GitHub API (`mediawiki-extensions-PersonalDashboard`, page 254) | First commit: Sep 19, 2025 by "jsn" (Jason Sherman). Forked from GrowthExperiments Homepage |
| [Extension:PersonalDashboard](https://www.mediawiki.org/wiki/Extension:PersonalDashboard) | Release status: experimental, Author: Jason Sherman / WMF Growth Team, MW 1.45+ |

### Key Technique: GitHub API for First Commit

```
# Get total page count
curl -sI "https://api.github.com/repos/wikimedia/mediawiki-extensions-PersonalDashboard/commits?per_page=1" | grep link
# → rel="last" shows page=254

# Get first commit (oldest)
curl -s "https://api.github.com/repos/wikimedia/mediawiki-extensions-PersonalDashboard/commits?per_page=1&page=254" | python3 -c "
import json,sys
c=json.load(sys.stdin)[0]
print(f\"Date: {c['commit']['author']['date']}\")
print(f\"Author: {c['commit']['author']['name']}\")
print(f\"Message: {c['commit']['message'][:300]}\")
"
```

### Key Technique: Extracting Phabricator Timelines

Instead of scrolling and snapshotting repeatedly:
```js
// Get full timeline as text
document.querySelector('.phui-timeline-view').innerText

// For long timelines, chunk it
document.querySelector('.phui-timeline-view').innerText.substring(0, 5000)
document.querySelector('.phui-timeline-view').innerText.substring(5000, 10000)
```

### Pitfalls

- **Don't assume `browser_navigate` to Gerrit JSON endpoints will work** — Gerrit may reject non-browser requests. Use GitHub mirror API instead.
- **Phabricator task snapshots get truncated** at ~8000 chars. `browser_console` with `innerText` bypasses this limit.
- **The initial commit is often not the first code commit** — look at commits on pages 250+; the first few commits are often `.gitreview`, CI config, etc. Read the messages; the real "Initial commit" is usually explicit.
- **Deployment ≠ visible to users** — many extensions deploy silently first ("configured to not display anything to users"), then get a separate config-change task to go live. Always look for the config task.

---

## Case Study: Special:ReadingLists (2017–2026)

### Sources Consulted

| Source | What It Provided |
|--------|-----------------|
| [T181107](https://phabricator.wikimedia.org/T181107) — Deploy to production | Scheduled Dec 7, 2017; deployed with MW 1.31.0-wmf.17 (Jan 2018) |
| [Wikimedia Apps/Synced Reading Lists](https://www.mediawiki.org/wiki/Wikimedia_Apps/Synced_Reading_Lists) | Design doc with "Why Not Watchlist" rationale, personas, usage stats |
| [Extension:ReadingLists](https://www.mediawiki.org/wiki/Extension:ReadingLists) | Release status: beta; Author: Tgr (WMF) / Reader Experience Team; v1.0.0-beta.1 (Oct 2025) |
| GitHub API (`mediawiki-extensions-ReadingLists`, page 1264) | First code commit: Jun 24, 2017 by Gergő Tisza |
| `operations/mediawiki-config/InitialiseSettings.php` | `wgReadingListsBetaDefaultForNewAccountsAfter` — enwiki set to Apr 21, 2026 |

### Key Technique: Config Scraping for Deployment Status

The WMF's `operations/mediawiki-config` repo on GitHub mirrors production config. Querying `InitialiseSettings.php` and `CommonSettings.php` reveals:

- **Which wikis have an extension enabled**: `wmgUse<Extension>` setting
- **Beta feature rollout dates**: `wg<Extension>BetaDefaultForNewAccountsAfter`
- **Wiki-specific overrides**: e.g. survey links, preview settings, edit count thresholds

```bash
# Check extension enablement
curl -s "https://raw.githubusercontent.com/wikimedia/operations-mediawiki-config/master/wmf-config/InitialiseSettings.php" | grep -B2 -A5 "wmgUseReadingLists"

# Check for beta/default-on dates
curl -s "https://raw.githubusercontent.com/wikimedia/operations-mediawiki-config/master/wmf-config/InitialiseSettings.php" | grep -B1 -A10 "BetaDefaultForNewAccountsAfter"

# Check extension loading logic
curl -s "https://raw.githubusercontent.com/wikimedia/operations-mediawiki-config/master/wmf-config/CommonSettings.php" | grep -B2 -A10 -i "readinglist"
```

Note: `'sul' => true` in WMF config means "all SUL wikis" (~1010 wikis in `dblists/sul.dblist`), not just the login wiki. This is how extensions like ReadingLists are deployed wiki-wide.

### Origin Pattern: App-First vs. Web-First

ReadingLists originated in the mobile apps (Android 2016, iOS earlier), with the web `Special:` page as a secondary interface. This is the reverse of PersonalDashboard, which started as a web extension. When researching a feature, check whether it began as:
- **Web-first**: Extension → Special page → maybe app integration
- **App-first**: App feature → backend API → web Special page added later
- **Clue**: App-first features often have REST API documentation predating the Special page

### When Design Docs Exist

Some features have dedicated design/planning pages on mediawiki.org (e.g. `Wikimedia Apps/Synced Reading Lists`). These are gold for understanding *why* a feature was built a certain way — they often contain explicit rationale sections like "Why Not Watchlist." Search for: `site:mediawiki.org "<feature name>" AND (design OR plan OR rationale OR "why not")`.

### Community Communications Audit

When asked "how would existing editors have known about this?", systematically check each channel:

1. **Tech News** — search enwiki Project namespace:
   ```
   api.php?action=query&list=search&srsearch="<FeatureName>" prefix:Wikipedia:Tech+news&srnamespace=4
   ```
   Tech News is the highest-reach channel — delivered to Village Pumps on every wiki in 20+ languages. The Meta-Wiki delivery pages (e.g. `meta:Tech/News/2026/13`) show exactly which languages received the announcement.

2. **The Signpost** — search for `<FeatureName>` in Signpost namespace:
   ```
   api.php?action=query&list=search&srsearch="<FeatureName>" prefix:"Wikipedia:Wikipedia Signpost"&srnamespace=4
   ```
   The Signpost is enwiki's community newspaper and reaches dedicated editors. Zero coverage means the feature had no independent editorial attention.

3. **Village Pumps** — search VP(WMF), VP(technical), VP(miscellaneous) archives. VP(WMF) cross-posts WMF Bulletin. VP(misc) sometimes hosts pre-launch community discussions.

4. **WMF Bulletin** — monthly digest delivered to VP(WMF). Check for mentions by searching the raw wikitext of Archive pages.

5. **Help pages** — check if `Help:<FeatureName>` or `Wikipedia:<FeatureName>` exists on enwiki. A redlink means no user-facing documentation was ever written.

6. **Wikimania/Diff** — check wikimania.wikimedia.org and diff.wikimedia.org. Conference presentations and blog posts are signals of intentional community engagement.

7. **Community discussion before launch** — check if there was a VP(Misc) discussion or RfC *before* deployment. ReadingLists had one in 2017 (initiated by CKoerner/WMF); PersonalDashboard had none.

**Gap pattern to watch for:** Features built for one audience (new editors, mobile app users) and announced in channels those audiences don't read, then extended to existing users with no dedicated re-announcement. This is the most common discoverability failure.
