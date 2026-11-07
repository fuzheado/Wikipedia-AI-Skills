---
name: zotero-translator-development
description: This skill should be used when asked to "write a Zotero translator", "fix a translator's bylines", "add translator tests", or "address translator PR review"; covers implementation, fixtures, lint, and submission.
license: MIT
compatibility: opencode
last_verified: 2026-11-07
depends_on: [citoid-publisher-diagnostics]
skill_discovery_hints:
  - keywords: [zotero translator development, web translator, embedded metadata delegation, translator fixtures]
  - keywords: [translator review, translator lint, scaffold, byline extraction]
---
# Zotero web translator development
Build or repair a web translator after deciding that extraction code is needed. Use [Citoid publisher diagnostics](../citoid-publisher-diagnostics/SKILL.md) for access failures, archive/cache checks, and publisher triage; do not build a scraper to solve a WAF denial.
Scope this skill to **web translators**. A website's search-results page is still a web-translator task; Zotero search translators resolve identifiers such as DOI/ISBN. Ask about scope if the request could instead mean import, export, or identifier lookup.
## SOP: Research, implement, verify, submit
### 1. Inspect the checkout and preserve existing work
Locate the intended Zotero translators checkout; read its current contributor instructions, `index.d.ts`, web template, and available development tools. Inspect git status, remotes, branch history and any existing PR. Do not assume remote names, push permissions, paths, tools or credentials match another machine.
For a new topic, branch from current upstream `master`; for an existing open PR, build on its current head. Keep one PR per topic. Preserve dirty files and unrelated local tooling patches; do not blindly reset, overwrite a translator, or switch branches under active work. Verify a PR is still open before pushing to its branch.
Read the official [translator documentation](https://www.zotero.org/support/dev/translators) and [coding guide](https://www.zotero.org/support/dev/translators/coding). Prefer current templates and recently maintained translators over legacy Framework examples.
### 2. Inspect representative real pages before coding
Map single-article, search/section, legacy, and supported language-edition layouts. Record canonical URL, title, type, publication date, all author channels, publication identity, language, tags, and attachments. Distinguish datePublished from dateModified and the article from recommendations further down the page.
Use the checkout's browser inspection tools when present:
```text
node .bin/inspect-page.mjs "ARTICLE_URL" --meta
node .bin/capture-har.mjs "ARTICLE_URL"
```
Read `--help` first; these helpers may not exist in every revision. Otherwise use Scaffold or authorized browser inspection. Prefer inspecting rendered metadata/API traffic over dumping minified HTML. Compare raw response and rendered DOM when investigating server-side extraction. A browser success does not establish Citoid access. Stop at authentication/challenges and seek user/operator assistance; do not spoof or automate a bypass.
Check existing translators, their target regexes, redirected hosts, and Embedded Metadata (EM) behavior before adding a new file. Prefer a focused repair or shared-extractor correction over redundant site code. Do not assume deployed Citoid has the checkout's current translators.
### 3. Implement the smallest reliable extraction
Create new metadata with Scaffold or the checkout's initializer; preserve translator ID, existing author credit and license when repairing a file. Bump `lastUpdated` using current UTC on substantive changes. Scope `target` to supported hosts/routes without excluding their current canonical redirects.
Start with EM delegation when it already extracts most fields. Correct the missing/wrong fields in `itemDone`, then call `item.complete()` once. Select another approach only when needed: documented page API with `requestJSON`, identifier delegation, DOM scraping, or a small hybrid. See [EM delegation](references/em-delegation.md).
Use promise-based sandbox APIs: `request`, `requestText`, `requestJSON`, `requestDocument`, and `Zotero.selectItems`. Do not introduce deprecated `ZU.processDocuments`, `ZU.doGet` or `ZU.doPost`; avoid new Framework code. Do not use browser-page `fetch`, click handlers, or Node APIs in translator code.
For multiple-item pages, present actual choices, respect cancellation, then fetch only selected documents:
```js
async function doWeb(doc, url) {
	if (detectWeb(doc, url) == 'multiple') {
		let selected = await Zotero.selectItems(getSearchResults(doc, false));
		if (!selected) return;
		for (let selectedURL of Object.keys(selected)) {
			await scrape(await requestDocument(selectedURL));
		}
	}
	else {
		await scrape(doc, url);
	}
}
```
Follow the checkout's formatting conventions (normally tabs). Treat this as a control-flow example; supply the site's detector, result mapping and scraper. Use existing global `attr`/`text` helpers where appropriate rather than shadowing them. See [structure and style](references/style.md).
### 4. Enforce field semantics
- Inspect **all author channels** before declaring no byline. Prefer article-scoped personal credits over generic site metadata. Do not replace valid creators with a weaker fallback, or fabricate a person from a numeric profile ID.
- Keep personal names personal regardless of word count. Use single-field creators for genuine organizations/collective credits when appropriate; distinguish publisher branding, agencies, contributors and job titles using evidence rather than a universal blacklist.
- Set `place` to the publication's city where applicable, not a story's dateline. Keep a meaningful dateline in tags if consistent with the translator's model.
- Use the right item type and publication field; an NGO page is not automatically a newspaper article. Preserve publication versus modification dates and reviewed-book versus review dates.
- Add tags as `{ tag: value }` objects and deduplicate case-insensitively. Exclude navigation, unrelated articles and advertising.
- Preserve accents, particles and initials. Normalize malformed all-caps bylines only when justified; avoid English-only casing or name splitting.
- Support language editions explicitly. Prefer a reliable declared language; use a constant only for demonstrably single-language scope. Test regional/script casing, not just `en`.
Read [bylines and localization](references/bylines-and-localization.md) for detailed precedence, organizations, JSON-LD and application-state pitfalls.
### 5. Generate fixtures and test real paths
Add tests **inside the translator file** with Scaffold or, where available:
```text
node .bin/create-test.mjs "Site Name.js" --url "ARTICLE_URL"
```
Include representative supported page types, meaningful layout/language variants, author/date edge cases, and a multiple-item test if selection is supported. Inspect every expected field against source evidence; auto-generation records current output, including bugs. Add a regression fixture before a bug fix when practical, and demonstrate it passes afterward.
Run the repository linter and actual browser fixture harness:
```text
npm run lint -- "Site Name.js"
node .bin/run-tests.mjs "Site Name.js"
```
Use Scaffold tests when checkout helpers are unavailable. Lint alone does not detect deprecated API usage or guarantee correct metadata. Run existing fixtures too, not just the new example. See [tests and troubleshooting](references/tests.md).
Do not assume an earlier broken browser installation remains broken. Diagnose the actual failure. Helper-level checks against real documents can supplement browser tests but do not replace detection, delegation, selection and completion in the real sandbox. If fixtures cannot run, report exactly what is blocked; never claim CI passed before checking it.
### 6. Review, commit and submit only when authorized
Review a focused diff: translator, justified fixtures and retirement metadata only. Preserve UTF-8/LF and license/creator credit. Exclude downloaded pages, HAR files, profiles/cookies, dependency trees, generated builds, and unrelated helper patches.
Retire an unused translator ID in `deleted.txt` and increment its version when removing/replacing that ID; do not retire an ID retained through a rename or rewrite. Confirm the current file format before editing it.
Push to the contributor's authorized fork and create/update a PR only when requested. State the defect, evidence, supported scope and exact lint/test results. Do not hardcode historical credentials or PR numbers into reusable guidance. Evaluate reviewer suggestions, implement valid feedback, retest, then reply with the pushed commit and resolve addressed threads. See [PR workflow](references/pr-workflow.md).
## Guardrails
- Do not generalize from a single article, language, or successful browser session.
- Do not treat JSON-LD availability as proof EM or production Citoid consumes it.
- Do not confuse publishers, personal authors, organizational credits and role labels.
- Do not solve a fixture mismatch by deleting the assertion or copying wrong output.
- Do not rewrite a header, replace an ID, discard dirty work, or force-push without a justified, authorized workflow.
- Do not include credentials, personal paths, browser profiles or publisher-page dumps in a submission.
- Do not claim local helper checks are end-to-end browser or deployed-Citoid verification.
## Tooling and references
No custom executables are shipped; use the current Zotero checkout's tools or Scaffold.
- [EM delegation and structured metadata](references/em-delegation.md)
- [Bylines, tags and localization](references/bylines-and-localization.md)
- [Translator structure and style](references/style.md)
- [Fixture tests and environment troubleshooting](references/tests.md)
- [Branch, PR and review workflow](references/pr-workflow.md)
