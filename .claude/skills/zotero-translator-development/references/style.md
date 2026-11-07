# Translator structure and style
## Metadata, identity and licensing
Use Scaffold's web template or a verified checkout initializer for new translators. The header is a JSON metadata object followed by JavaScript, not an ordinary executable JS module. A naive `node --check` on the whole translator file does not validate Zotero's format.
Retain an existing translator ID across fixes/rewrites and preserve author credits. For new files, generate a UUID, use `translatorType: 4`, select a supported minimum version, scope `target` precisely, and follow the current header/template conventions. Set `lastUpdated` to current UTC (`YYYY-MM-DD HH:MM:SS`) when changing functional code. Do not replace it with a historical example timestamp.
Preserve the source license. Zotero recommends AGPLv3-or-later for new translators; use the current template's license statement. This WAIS instructional skill is MIT; that does not relicense existing translator source. Use the actual contributor identity, not an author copied from an example.
## Control flow and sandbox
Implement `detectWeb`, `getSearchResults`, `doWeb` and `scrape` for supported page types. `getSearchResults(doc, true)` should return early once one selectable result exists; full mode returns a URL/title map or false. Exclude navigation, category pages and unrelated cards; use URL patterns plus page evidence rather than obfuscated presentation classes.
Use current promise APIs and await them. For multiple pages call `Zotero.selectItems`, return on cancellation, then `requestDocument` and `scrape` for selected URLs. `ZU.selectItems` is not the selection API. Do not add deprecated `ZU.processDocuments`, `ZU.doGet` or `ZU.doPost` just because legacy translators contain them.
The sandbox provides `attr`, `text` and related helpers: check `index.d.ts` before defining a conflicting helper. Use `ZU.cleanAuthor` for personal names with the appropriate comma-order setting, not as an organization detector. Keep a multiword personal surname personal; word count does not establish corporate authorship.
Do not use Node/file-system APIs or browser-page functions in translator code. Requests use `request`, `requestText`, `requestJSON`, or `requestDocument`, which accept relative URLs. A static document is not an interactive tab; reconstruct a documented API call where justified rather than clicking buttons.
## Formatting and lint
Match the current file and repository style, normally tab indentation. Avoid unnecessary rewrites, unused callback arguments, repeated fallback plumbing, and speculative abstractions. Use optional chaining/existence checks where markup is optional. Add English comments only for genuinely non-obvious extraction decisions.
Use the repository's ESLint processor, which understands the header and embedded fixtures:
```text
npm run lint -- "Site Name.js"
```
Check UTF-8 without BOM and LF line endings before staging. If a formatter/editor converts the whole file to CRLF, normalize the edited file instead of committing a whole-file diff or dismissing all lint errors as harmless. Inspect the diff again. Do not assume lint catches deprecated request APIs, incorrect author semantics, or untested page types.
