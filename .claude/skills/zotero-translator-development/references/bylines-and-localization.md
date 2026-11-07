# Bylines, tags, dates and language editions
## Inventory first, then select and clean
Inspect article-scoped meta tags (`author`, `article:author`), JSON-LD author nodes/references, DOM bylines, profile links/microdata and relevant application state. Record the actual human credit and role on several pages before concluding an author is absent.
Prefer a source supported by the article itself. A nonempty meta author can be a site owner or numeric ID; JSON-LD can describe an organization even when the DOM names reporters. Replacing all creators unconditionally can also erase a good author. Define precedence from observed channel quality and test missing-channel and conflicting-channel cases.
Apply only justified cleaning:
- Strip a localized byline prefix and split co-authors with site-specific delimiters. Do not split every comma: it can separate surname/given name or a role.
- Keep job titles out of creator names. Preserve relevant contributor roles separately, using supported creator types or a concise `extra` field when appropriate.
- Separate publisher branding from true corporate or agency credits. Do not universally discard AP/Reuters or replace them with an invented person. Follow site semantics and reviewer conventions; genuine organizations can use `{ lastName: name, creatorType: 'author', fieldMode: 1 }`.
- Filter a known newsroom/service label with a precise, tested list if evidence supports it; do not reject every name containing words like "news".
- Preserve accents, apostrophes, particles, initials and multiword surnames. Long names are not organizations. Avoid blanket title-casing: it damages deliberate casing, and English particle rules do not generalize globally.
- Deduplicate equivalent credits without merging distinct people. Unicode NFC/case normalization can help comparison; do not strip meaningful characters from saved names.
Never infer a person's name from a profile slug when the displayed credit is available. Avoid adding role text, a numeric page ID or a publication's Facebook account as a personal author.
## Tags and publication fields
Scope tags to the current article: `article:tag`, keywords, article tag links and documented categories. A shared extractor may already have filled some tags and skipped another channel. Inspect the current code/output before adding a fallback. Use `{ tag: value }` and compare normalized values case-insensitively; exclude empty strings and global navigation.
Set the newspaper's `place` to its city of publication when known, never the story's filing location. A supported dateline-as-tag convention may retain that location without corrupting `place`. Do not guess publication city, ISSN or regional language from the reporter's dateline.
Use the field appropriate to the item type (`publicationTitle`, `websiteTitle`, publisher, etc.). Institutional web publications are not automatically newspapers. Check title suffixes, section labels and reviewed-book publication dates rather than trusting a generic extractor's first nonempty value.
## Dates
Choose the article's publication date, not a modification timestamp, recommendation-card date, page build time or access date. Preserve a supplied timezone; do not invent missing precision. For reviews, distinguish review publication from the work's publication. When multiple structured nodes exist, select the current article before extracting a date.
## Languages and variants
Inspect the editions actually claimed by the translator's scope, not just an English page. Different locales can have different paths, byline vocabulary, CSS and metadata completeness. Add representative fixtures for supported language/layout variants, and state untested scope instead of claiming universal coverage.
Prefer a trustworthy page language (`inLanguage`, `lang`, `og:locale` with underscores normalized) and canonical BCP-47 casing: `en-US`, `pt-BR`, `zh-Hant`. If scope is genuinely single-language, a constant is simpler than a general normalizer. Do not use one constant across a multilingual target.
Keep script and region distinctions and respect non-Latin names. Distinguish an untranslated organization label from a missing personal author. Verify both output values and the actual item type through the sandbox, not just a helper function.
