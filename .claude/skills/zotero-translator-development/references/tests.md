# Fixture tests and environment troubleshooting
## Create and inspect embedded fixtures
Tests live in the translator file between `/** BEGIN TEST CASES **/` and `/** END TEST CASES **/` as a `testCases` array. Generate with Scaffold's recorder or, if present:
```text
node .bin/create-test.mjs "Site Name.js" --url "ARTICLE_URL"
```
Read `--help` for the current CLI. The recorder captures output, not truth: inspect title, all creators, publication date/type, canonical URL, language, publication, tags, attachments and expected empty fields against the article. Do not manufacture an expected item by copying another site's fixture.
Cover each supported page type and meaningful variant: modern/legacy layouts, multiple authors, no author, organization versus person, optional fields, supported languages, and selection pages. Preserve existing regression coverage. An archived page may test a legacy layout, but says nothing about current origin access.
For a multiple-item test, use the recorder's `"items": "multiple"` output. The harness observes whether `Zotero.selectItems` was called; feeding all URLs directly to a scraper can fetch multiple articles yet fail the selection test. Respect cancellation and scrape only the returned selection. `ZU.selectItems` is not a substitute.
## Run the real workflow
```text
npm run lint -- "Site Name.js"
node .bin/run-tests.mjs "Site Name.js"
```
Use the current checkout's tools or Scaffold if those scripts are absent. Test detection, request/delegation, item completion, fixtures and dependent translators where shared extraction changes. Lint is necessary but not semantic or deprecation coverage.
Retain real page evidence for the assertions; helper-level tests against actual DOM/strings are useful supplements. They are not proof the translator target matches or that EM calls the completion handler correctly. Do not mock the entire sandbox and call that end-to-end verification.
## Diagnose environment failures without normalizing them into policy
Separate errors before fixing code:
- Invalid translator/header/target or expected-output mismatch: inspect the source and emitted item.
- Browser launch or missing dependencies: inspect actual executable/version and the checkout's dependency files. Do not assume a months-old broken installation still applies.
- Windows ESM drive-path error: Node dynamic imports need file URLs; a tool using `import(path.join(...))` may need `pathToFileURL(...).href`. Confirm whether already fixed; keep tooling changes separate from translator PRs.
- Challenge/login/timeout: inspect the document actually loaded. A challenge page causes misleading detection failures. Seek authorized user assistance rather than automating evasion. Protect reused browser profiles and never publish their cookies.
- Server/port/profile conflict: identify the exact owning process; do not kill all Node/Chrome processes or delete profiles indiscriminately.
- CRLF lint flood: restore LF in the edited file, rerun, and verify a minimal diff.
If full tests cannot run, give the exact blocker, commands and narrower checks completed. Do not mark the work fully verified. If CI fails, inspect accessible logs and annotations; access varies with repository settings. Do not assume every failure is a stale fixture or that all CI tests use cached HTML. Check the current harness's network and cache behavior.
