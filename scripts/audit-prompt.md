# Skill Audit Prompt

> Copy-paste this entire prompt into Pi to run a comprehensive audit of all
> skills in `.claude/skills/`. Best used after adding new skills or making
> batch changes.

---

**Task:** Run a comprehensive audit of all skills in `.claude/skills/`.

## Phase 1: Generate Metrics (Bash)

First run:
```bash
bash scripts/audit-skills.sh
```

This produces a table of word counts, line counts, internal references, dependencies,
and missing YAML fields for every skill. Review this for anomalies.

## Phase 2: Deep Analysis (Subagents)

Run **6 parallel subagents** using the `worker` agent, each analyzing one domain:

| Batch | Skills | Output File |
|-------|--------|-------------|
| APIs & Auth | wikimedia-api-access, wikimedia-api-strategy, wikimedia-auth-oauth, wikimedia-security-and-privacy, wikipedia-error-handling, wikimedia-diffs, wikipedia-edit-history | `reports/audit-apis-auth.json` |
| Wikidata & Search | wikidata, wikidata-vector-search, wikimedia-search-cirrussearch, wikimedia-pageviews, wikimedia-page-assessment | `reports/audit-wikidata-search.json` |
| Commons | wikimedia-commons, commons-file-resolution, wikimedia-commons-audio-video, wikimedia-commons-pdf, wikimedia-commons-sdc, wikimedia-commons-sparql, wikimedia-commons-svg, wikimedia-commons-thumbnails | `reports/audit-commons.json` |
| Content | wikipedia-categories, wikipedia-citations, wikipedia-page-anatomy, wikipedia-talk-page, wikipedia-templates, wikipedia-wikitables, wikipedia-en-article-audit, wikipedia-en-biography-writing, wikipedia-notability-assessment, wikipedia-reference-verifiability | `reports/audit-content.json` |
| Toolforge | wikimedia-toolforge, toolforge-nodejs, wikimedia-database, wikimedia-eventstreams, wikimedia-i18n-l10n-for-tools, wikimedia-ml-services, wikimedia-cdn-assets, wikimedia-phabricator | `reports/audit-toolforge.json` |
| Tools | pywikibot, mediawiki-page-navigation, mediawiki-translate-extension, wikimedia-page-styling, wikimedia-wikitext, wikipedia-pagetriage-api, wiktionary-and-wikisource | `reports/audit-tools.json` |

For **each** skill in your batch, produce this JSON structure:
```json
{
  "name": "skill-name",
  "yaml_description": "the description from frontmatter",
  "description_issues": ["problems with description"],
  "word_count": 0,
  "structure": "assessment of structure",
  "cross_references": {
    "internal": ["skills referenced"],
    "external": ["URLs referenced"],
    "issues": ["missing/broken links"]
  },
  "completeness": {
    "score": "poor|fair|good|excellent",
    "missing_topics": ["gaps"],
    "redundant_content": ["duplicates"]
  },
  "correctness_issues": ["factual errors, outdated APIs, wrong URLs"],
  "conciseness": {
    "score": "poor|fair|good|excellent",
    "issues": ["verbose sections"]
  },
  "overall_score": "poor|fair|good|excellent",
  "top_3_improvements": ["actionable fixes"]
}
```

Also produce a **cross-reference matrix** showing which skills reference which within
your batch, using ✓ for existing links, ✗ for missing, and ← for "should reference".

**IMPORTANT:** Read each file with the read tool. Don't guess. Produce valid JSON.

## Phase 3: Synthesize Report

After all 6 batches complete, read the JSON outputs and produce a markdown report in
`reports/skill-audit-{date}.md` covering:
1. Executive summary with score distribution
2. Deep-dive on any new skills
3. Cross-reference gaps (bidirectional missing links, duplicated content)
4. YAML frontmatter quality (description length, missing fields)
5. Correctness issues (bugs, outdated URLs, description/body mismatches)
6. Completeness gaps by domain
7. Conciseness issues (candidates for splitting, offload recommendations)
8. Cross-reference density matrices
9. Prioritized action plan (P0 bugs → P1 cross-refs → P2 descriptions → P3 duplicates → P4 structural)
10. Complete skill inventory with scores

## Tips

- **New skills:** Focus especially on skills that were added since the last audit.
  They won't appear in hub skill cross-reference tables and may need back-linking.
- **Recently modified files:** Check `git diff --name-only HEAD~10` to see what's
  changed recently and focus extra attention there.
- **Cross-ref patterns:** Look for `[[skill-name]]→` wikilinks AND
  `[text](../skill-name/SKILL.md)` markdown links.
