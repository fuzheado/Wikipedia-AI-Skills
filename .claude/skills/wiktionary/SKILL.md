---
name: wiktionary
description: "Work with Wiktionary entries across languages - entry anatomy, definitions, translation tables, pronunciations, and Wikidata lexemes."
license: MIT
compatibility: opencode
last_verified: 2026-09-11
depends_on: [wikimedia-api-access, wikimedia-commons, pywikibot]
skill_discovery_hints:
  - keywords: ["Wiktionary", "dictionary entry", "definition", "translation table", "etymology"]
  - keywords: ["lexeme", "IPA", "audio pronunciation", "part of speech", "language section"]
---

> ⚠️ **Prerequisites:** This skill assumes familiarity with the MediaWiki Action API
> (see **wikimedia-api-access**), Commons file handling (**wikimedia-commons**), and
> basic Pywikibot patterns (**pywikibot**). Wikidata lexemes are covered in
> **wikidata**; language detection and fallback chains are covered in
> **wikimedia-i18n-l10n-for-tools**.

Wiktionary is the free dictionary — one of the largest Wikimedia content
projects, with **over 170 language editions** (en.wiktionary alone is one of the
biggest). It runs on the same MediaWiki platform as Wikipedia but has a
**fundamentally different content structure**: a single page holds entries for
the *same word in many languages*, and each language section contains
part-of-speech sections with numbered definitions, usage examples, translation
tables, and pronunciation data. Wikitext is the primary format — the rendered
HTML flattens the language/part-of-speech hierarchy, so almost all tooling works
against raw wikitext.

**When to use:**

- You need a definition, etymology, or example sentence for a word in a
  specific language.
- You need a word's translations into other languages (the `{{trans-top}}`
  tables).
- You need IPA or audio pronunciation files for a word.
- You need to match a dictionary entry to a Wikidata **lexeme** (L-entity) for
  structured data, or to import lexeme data back into an entry.

## API Basics

- **Base URL:** `{lang}.wiktionary.org/w/api.php` (e.g.
  `en.wiktionary.org/w/api.php`, `fr.wiktionary.org/w/api.php`). Every edition
  uses the standard MediaWiki Action API.
- **Docs:** the Action API help lives at `www.mediawiki.org/w/api.php`; for
  Wiktionary-specific templates the wiki itself is the reference (fetch the raw
  wikitext of an entry to see current template usage).
- **Primary format:** `action=parse&prop=wikitext`. Use `prop=text` only when
  you actually want rendered HTML.
- **Auth:** read-only public API; no key. A descriptive `User-Agent` is
  mandatory — see **wikimedia-api-access** for the format and rate-limit rules.

| Task | Call |
|------|------|
| Entry wikitext (primary) | `action=parse&page=word&prop=wikitext` |
| Wikitext + HTML + categories | `action=parse&page=word&prop=wikitext\|text\|categories` |
| Same word in other editions | `action=query&prop=langlinks&titles=word&lllimit=max` |
| Words in a category | `action=query&list=categorymembers&cmtitle=Category:English_nouns` |
| Prefix lookup | `action=query&list=prefixsearch&pssearch=word&pslimit=10` |
| Full-text search | `action=query&list=search&srsearch=etymology&srwhat=text` |
| Namespaces / languages | `action=query&meta=siteinfo&siprop=namespaces\|languages` |

## Quick Smoke Test

```bash
UA="WiktSkill/1.0 (https://example.org; maintainer@example.org) WiktionarySkill"

# 1) Parsed wikitext for an entry — the primary format
curl -s -G "https://en.wiktionary.org/w/api.php" \
  --data-urlencode "action=parse" \
  --data-urlencode "page=word" \
  --data-urlencode "prop=wikitext" \
  --data-urlencode "format=json" \
  -H "User-Agent: $UA"
# → {"parse":{"pageid":45,"title":"word","wikitext":{"*":"{{also|Word|worð}}\n==English==..."}}}

# 2) The same word on other editions (interwiki links)
curl -s -G "https://en.wiktionary.org/w/api.php" \
  --data-urlencode "action=query" \
  --data-urlencode "titles=word" \
  --data-urlencode "prop=langlinks" \
  --data-urlencode "lllimit=3" \
  --data-urlencode "format=json" \
  -H "User-Agent: $UA"
# → {"query":{"pages":{"45":{"title":"word","langlinks":[{"lang":"af","*":"word"}, ...]}}}}

# 3) Enumerate words in a namespace-backed category
curl -s -G "https://en.wiktionary.org/w/api.php" \
  --data-urlencode "action=query" \
  --data-urlencode "list=categorymembers" \
  --data-urlencode "cmtitle=Category:English nouns" \
  --data-urlencode "cmlimit=3" \
  --data-urlencode "format=json" \
  -H "User-Agent: $UA"
# → {"query":{"categorymembers":[{"ns":100,"title":"Appendix:English nouns"}, ...]}}
```

## SOP 1: Fetch an Entry's Wikitext

```python
import requests

def fetch_wikitext(word: str, lang: str = "en") -> str | None:
    """Return the raw wikitext of a Wiktionary entry, or None if missing.

    The parse module's `wikitext` field is a dict with a single `*` key
    (formatversion=1, the default) — not a bare string.
    """
    api = f"https://{lang}.wiktionary.org/w/api.php"
    resp = requests.get(api, params={
        "action": "parse",
        "page": word,
        "prop": "wikitext",
        "format": "json",
    }, headers={
        "User-Agent": "WiktSkill/1.0 (https://example.org; maintainer@example.org) WiktionarySkill",
    }, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "parse" not in data:
        return None
    return data["parse"]["wikitext"]["*"]
```

## SOP 2: Isolate One Language Section

A page can hold dozens of languages. Isolate the target before parsing, or you
will mix French definitions into the English entry. Split on the legacy `----`
divider **and** on level-2 `==Language==` headings (many current entries have no
divider at all):

```python
import re

SPLIT_RE = re.compile(r"(?m)^(?=(?:-{4,}\s*$|==[^=]))")

def split_language_sections(wikitext: str) -> list[str]:
    """Return one chunk per level-2 language heading (divider optional)."""
    chunks = SPLIT_RE.split(wikitext)
    return [c for c in chunks if re.search(r"^==([^=]+)==", c, re.MULTILINE)]

def extract_language_section(wikitext: str, target_lang: str) -> str | None:
    """Return the `==English==` / `==French==` … section, or None."""
    for section in split_language_sections(wikitext):
        first = re.search(r"^==([^=]+)==", section, re.MULTILINE)
        if first and first.group(1).strip() == target_lang:
            return section
    return None
```

`extract_language_section` and `count_languages` are provided ready-made in
[`assets/wt_entry_parser.py`](./assets/wt_entry_parser.py).

## SOP 3: Extract Definitions and Examples

```python
import re

def extract_definitions(lang_section: str) -> list[dict]:
    """Extract numbered definitions with their `#:` example sentences."""
    definitions = []
    current = None
    for line in lang_section.split("\n"):
        m = re.match(r"^#(?!:)\s*(.*)", line)          # "# definition"
        if m:
            if current is not None:
                definitions.append(current)
            current = {"definition": m.group(1).strip(), "examples": []}
            continue
        m = re.match(r"^#:\s*(.*)", line)              # "#: example"
        if m and current is not None:
            current["examples"].append(m.group(1).strip())
    if current is not None:
        definitions.append(current)
    return definitions
```

Definitions are raw wikitext — internal wiki links (`[[` `…` `]]` markup),
`'''bold'''`, and templates such as
`{{l|en|…}}` are still present. Clean them yourself or hand the section to
**wikimedia-wikitext** for a proper `mwparserfromhell` pass.

## SOP 4: Translation Tables

Translations live in `{{trans-top}} … {{trans-bottom}}` blocks, with `{{t}}` /
`{{t+}}` rows. `{{trans-mid}}` separates left-to-right from right-to-left
languages and carries no data of its own — skip it.

```python
import re

def extract_translations(lang_section: str) -> dict[str, list[str]]:
    """Return {'French': ['mot'], 'Spanish': ['palabra'], ...} for a section."""
    translations = {}
    current_lang = None
    for line in lang_section.split("\n"):
        top = re.match(r"\{\{trans-top\|(.+?)\}\}", line)
        if top:
            current_lang = top.group(1).strip()
            translations.setdefault(current_lang, [])
            continue
        if line.startswith("{{trans-bottom"):
            current_lang = None
            continue
        if line.startswith("{{trans-mid"):
            continue
        if current_lang:
            row = re.match(r"\{\{t\+?\|([a-z]{2,3})\|([^}|]+)", line)
            if row:
                translations[current_lang].append(row.group(2).strip())
    return translations
```

⚠️ Append to translation tables; never replace them (see Guardrails).

## SOP 5: Pronunciation — IPA and Audio

IPA is inline (`{{IPA|en|/wɜːd/}}`); audio files live on Commons and are
referenced by name. Current entries pass the qualifier as a named parameter
(`{{audio|en|En-us-word.ogg|a=GA}}`); older ones use a positional label
(`{{audio|en|en-uk-word.ogg|Audio (UK)}}`).

```python
import re

def extract_pronunciation(lang_section: str) -> list[dict]:
    """Extract IPA values and audio file references from a language section."""
    found = []
    for line in lang_section.split("\n"):
        for m in re.finditer(r"\{\{IPA\|([a-z-]+)\|([^}|]+)", line):
            found.append({"type": "ipa", "lang": m.group(1),
                          "value": m.group(2).strip()})
        for m in re.finditer(
            r"\{\{audio\|([a-z-]+)\|([^}|]+)(?:\|a=([^}|]+))?", line
        ):
            found.append({"type": "audio", "lang": m.group(1),
                          "file": m.group(2).strip(), "qualifier": m.group(3)})
    return found
```

Resolve the `file` field against Commons to build a playable URL — see
**wikimedia-commons** for the file-path and thumbnail patterns.

## SOP 6: Wikidata Lexemes (L-entities)

Every word-sense can have a structured Wikidata **lexeme**: lemma, language,
lexical category (e.g. noun = Q1084), forms (inflections), and senses.
Lexeme IDs look like `L1`, `L12345`.

```python
import requests

def get_lexeme(lexeme_id: str) -> dict:
    """Fetch a Wikidata lexeme (lemma, language, lexical category, forms, senses)."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{lexeme_id}.json"
    resp = requests.get(url, headers={
        "User-Agent": "WiktSkill/1.0 (https://example.org; maintainer@example.org) WiktionarySkill",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["entities"][lexeme_id]

# Batch work via Pywikibot's data repository:
# import pywikibot
# site = pywikibot.Site("en", "wiktionary")
# repo = site.data_repository()
# lexeme = repo.get_lexeme("L1")
# print(lexeme.lemma)
```

## Guardrails

### ❌ Don't assume English Wiktionary
Wiktionary has **over 170 language editions**, each with its own template
conventions and its own sense of what a "section" contains. Always pass the
language code explicitly; never hard-code `en`.

### ❌ Don't confuse `----` with a section heading
`----` is **four** hyphens, a raw divider between language sections — not a
heading, and **not required**. Verified live on en.wiktionary (2026-09-11):
`word`, `water`, and `cat` contain *no* `----` line at all; sections are
delimited purely by level-2 `==Language==` headings. Split on both, and key on
the headings.

### ❌ Don't overwrite translation tables
Translation tables are maintained by many editors and are easy to corrupt.
**Append** new rows rather than replacing a `{{trans-top}} … {{trans-bottom}}`
block, and preserve the `{{trans-mid}}` separator.

### ❌ Don't trust stale namespace numbers
Older references list `104`=Rhymes, `106`=Thesaurus, `108`=Citations. The live
en.wiktionary layout (verified via `meta=siteinfo&siprop=namespaces`) is
`100`=Appendix, `106`=Rhymes, `108`=Transwiki, `110`=Thesaurus, `114`=Citations,
`116`=Sign gloss, `118`=Reconstruction. Re-query `siteinfo` rather than guessing.

### ❌ Don't mix section-header language names with template language codes
Section headers use the **English name** (`==French==`); template parameters use
the **ISO 639 code** (`{{t|fr|mot}}`). Comparing the two directly never matches.

### ❌ Don't forget the User-Agent
Every request needs a descriptive `User-Agent`; outside Toolforge/WMCS, pace
requests at ≥1 s and handle 429/403. See **wikimedia-api-access**.

## Tooling

### 🔧 Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`scripts/wt-entry-summary.sh`](./scripts/wt-entry-summary.sh) | Fetch an entry and print its language sections, parts of speech, definitions, templates, and interwiki links | `./wt-entry-summary.sh word en` |

### 🐍 Python Assets

| Asset | Purpose | Usage |
|-------|---------|-------|
| [`assets/wt_entry_parser.py`](./assets/wt_entry_parser.py) | Importable parser: language sections, definitions + examples, translation tables, IPA/audio, inflection templates | `from wt_entry_parser import WiktionaryParser` |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/wiktionary-entry-structure.md`](./references/wiktionary-entry-structure.md) | Entry anatomy: heading hierarchy, POS and subsection tables, template families, language codes, API modules, namespaces |

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent format, rate limits, and Action API request patterns for every call above |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | Audio pronunciation files referenced by `{{audio}}` are hosted on Commons |
| **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** | Parsing entry wikitext with `mwparserfromhell` — templates, links, `<ref>` tags |
| **[pywikibot](../pywikibot/SKILL.md)** | Batch entry edits and lexeme operations via the bot framework |
| **[wikidata](../wikidata/SKILL.md)** | Lexemes, senses, and structured data behind each entry |
| **[wikimedia-i18n-l10n-for-tools](../wikimedia-i18n-l10n-for-tools/SKILL.md)** | Language detection and fallback for multilingual entries |
