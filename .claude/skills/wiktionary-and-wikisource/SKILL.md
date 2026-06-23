---
name: wiktionary-and-wikisource
description: Work with Wiktionary (dictionary entries, translation tables, etymologies, audio pronunciations, lexemes) and Wikisource (proofread page workflow, OCR text extraction, quality validation, compiled works) - the two largest Wikimedia content projects after Wikipedia
depends_on: [wikimedia-api-access, wikimedia-commons, pywikibot]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["Wiktionary", "Wikisource", "dictionary", "proofread", "OCR", "translation table"]
  - keywords: ["Wiktionary entry", "lexeme", "etymology", "IPA", "pronunciation", "ProofreadPage"]
last_verified: 2026-06-11
---

> ⚠️ **Prerequisites:** This skill assumes familiarity with the MediaWiki Action
> API (see **wikimedia-api-access**), Commons file handling (**wikimedia-commons**),
> and basic Pywikibot patterns (**pywikibot**). Language detection and fallback
> chains are covered in **wikimedia-i18n-l10n-for-tools**.

---

## Overview

Wiktionary (dictionary) and Wikisource (library) are Wikimedia's second- and
third-largest content projects. They run on the same MediaWiki platform as
Wikipedia but have **fundamentally different content structures**. This skill
covers both in two independent sections - jump to the one you need.

| Section | Project | Key Skill |
|---------|---------|-----------|
| [Part 1 - Wiktionary](#part-1--wiktionary) | `*.wiktionary.org` | Parsing entry structure, translation tables, lexemes |
| [Part 2 - Wikisource](#part-2--wikisource) | `*.wikisource.org` | ProofreadPage workflow, text extraction, quality |

---

## Part 1 - Wiktionary

### Reference: Entry Anatomy

Every Wiktionary page can contain entries for the **same word in multiple
languages**, separated by `----` (4 hyphens) section dividers:

```wikitext
==English==
===Etymology===
From Latin ''verbum''.

===Pronunciation===
* {{a|UK}} {{IPA|en|/wɜːd/}}
* {{audio|en|en-uk-word.ogg|Audio (UK)}}

===Noun===
{{en-noun}}
# A unit of language.
#: {{ux|en|I wrote a '''word'''.}}

===Verb===
{{en-verb}}
# To phrase a certain way.
#: {{ux|en|How would you '''word''' that?}}

----

==French==
===Etymology===
From Latin ''verbum''.

===Noun===
{{fr-noun|m}}
# {{l|en|word}}
```

**Heading hierarchy:**

| Level | Marker | Content |
|-------|--------|---------|
| 1 | `==Language name==` | Language section (English, French, etc.) |
| 2 | `===Part of speech===` | Noun, Verb, Adjective, etc. |
| 3 | `====Subsection====` | Etymology, Pronunciation, Usage notes |
| 4 | `#` Definition | Numbered definitions |
| 5 | `#:` Example | Example sentence under a definition |

### SOP: Parse a Wiktionary Entry by Language

When you need definitions for a specific word in a specific language, you must
first isolate the correct language section:

```python
import mwparserfromhell

def extract_language_section(wikitext: str, target_lang: str) -> str | None:
    """Extract a single language section from a Wiktionary entry.

    Wiktionary entries are delimited by '----' (5 hyphens). Each section
    starts with '==Language name==' and runs until the next '----' or EOF.

    Args:
        wikitext: Raw page content
        target_lang: e.g. 'English', 'French', 'Spanish'

    Returns:
        The language section wikitext, or None if not found.
    """
    parsed = mwparserfromhell.parse(wikitext)

    # The '----' is not a heading - we need to split by top-level headings
    # that match '==Language=='
    for section in parsed.get_sections(flat=True):
        # Filter to top-level headings only (level 2 = ==Heading==)
        headings = section.filter_headings()
        if not headings:
            continue
        # Check if the first heading matches the target language
        first_heading = str(headings[0].title).strip()
        if first_heading == target_lang:
            return str(section)

    return None
```

### SOP: Extract Definitions and Examples

Once you have a language section, extract definitions with their examples:

```python
def extract_definitions(lang_section: str) -> list[dict]:
    """Extract numbered definitions and examples from a language section.

    Returns:
        [{"definition": "...", "examples": ["...", ...]}, ...]
    """
    import re
    definitions = []
    current_def = None

    for line in lang_section.split("\n"):
        # Definition line: "# text" or "#; text" for sub-definitions
        def_match = re.match(r"^#(?:;)?\s*(.*)", line)
        if def_match:
            if current_def is not None:
                definitions.append(current_def)
            current_def = {"definition": def_match.group(1).strip(), "examples": []}
            continue

        # Example line: "#: text"
        example_match = re.match(r"^#:\s*(.*)", line)
        if example_match and current_def is not None:
            current_def["examples"].append(example_match.group(1).strip())
            continue

        # Definition continues if it's a clear continuation (no other marker)
    if current_def is not None:
        definitions.append(current_def)

    return definitions
```

### SOP: Query Wiktionary via the API

```python
def fetch_entry(word: str, lang: str = "en") -> dict | None:
    """Fetch a Wiktionary entry via the Action API.

    The Wiktionary Action API is at en.wiktionary.org, fr.wiktionary.org, etc.
    """
    import requests
    WIKTIONARY = f"https://{lang}.wiktionary.org/w/api.php"

    resp = requests.get(WIKTIONARY, params={
        "action": "parse",
        "page": word,
        "prop": "wikitext|text|categories",
        "format": "json",
    }, timeout=30, headers={
        "User-Agent": "WiktTool/1.0 (https://example.com; user@example.com)"
    })
    resp.raise_for_status()
    return resp.json()["parse"] if "parse" in resp.json() else None
```

### SOP: Translation Table Lookup

Translation tables use the `{{trans-top}}` / `{{trans-mid}}` / `{{trans-bottom}}`
template family. Extract them with a template parser:

```python
def extract_translations(wikitext: str) -> dict[str, list[str]]:
    """Extract translation tables from a Wiktionary entry.

    Returns:
        {"French": ["mot"], "Spanish": ["palabra"], ...}
    """
    import mwparserfromhell
    parsed = mwparserfromhell.parse(wikitext)
    translations = {}
    current_lang = None

    for template in parsed.filter_templates():
        name = str(template.name).strip().lower()

        if name == "trans-top":
            current_lang = str(template.get(1).value).strip()
            if current_lang not in translations:
                translations[current_lang] = []
        elif name == "trans-mid":
            pass  # Separator between LTR and RTL languages
        elif name in ("trans-bottom",):
            current_lang = None
        elif name in ("t", "t+", "tt", "tt+") and current_lang:
            # {{t|fr|mot}}, {{t+|es|palabra}}, {{tt|en|small}}, {{tt+|en|tiny}}
            try:
                word = str(template.get(2).value).strip()
                translations[current_lang].append(word)
            except (IndexError, ValueError):
                pass

    return translations
```

### SOP: Audio Pronunciation Files

Pronunciation audio files are stored on Commons and referenced via `{{audio}}`:

```wikitext
{{audio|en|en-uk-word.ogg|Audio (UK)}}
```

```python
def get_pronunciation_files(lang_section: str) -> list[dict]:
    """Extract audio pronunciation file references.

    Returns:
        [{"lang": "en", "file": "en-uk-word.ogg", "label": "Audio (UK)"}, ...]
    """
    import mwparserfromhell, re
    parsed = mwparserfromhell.parse(lang_section)
    files = []

    for template in parsed.filter_templates():
        name = str(template.name).strip().lower()
        if name == "audio":
            try:
                lang = str(template.get(1).value).strip()
                file = str(template.get(2).value).strip()
                label = str(template.get(3).value).strip() if template.params[3] else ""
                files.append({"lang": lang, "file": file, "label": label})
            except (IndexError, ValueError):
                pass

    return files
```

### SOP: Wikidata Lexemes (L-entities)

Wiktionary entries are linked to Wikidata **lexemes** (L-entities), which provide
structured data about the word (part of speech, gender, inflections, etc.):

```python
def fetch_lexeme(lexeme_id: str) -> dict:
    """Fetch a Wikidata lexeme by L-ID.

    Lexemes are Wikidata entities with ID format L12345.
    They contain: lemma, language, lexical category, forms, senses.
    """
    import requests
    resp = requests.get(
        f"https://www.wikidata.org/wiki/Special:EntityData/{lexeme_id}.json",
        headers={"User-Agent": "WiktTool/1.0 (user@example.com) LexemeLookup"}
    )
    resp.raise_for_status()
    return resp.json()["entities"][lexeme_id]


# Use with Pywikibot for batch operations:
# import pywikibot
# site = pywikibot.Site("en", "wiktionary")
# repo = site.data_repository()
# lexeme = repo.get_lexeme("L12345")
# print(lexeme.lemma)  # The word itself
# print(lexeme.lexical_category)  # e.g. Q1084 (noun)
```

---

## Part 2 - Wikisource

### Reference: ProofreadPage Workflow

Wikisource uses the **ProofreadPage extension** to manage the process of turning
scanned page images into validated text. Three namespaces work together:

```
Index:Work Title            # Metadata about the publication
    │                         (author, year, publisher, scanner)
    │
    ▼
Page:Work Title/1          # One page = one scanned image + its OCR text
Page:Work Title/2             Each has a quality level:
Page:Work Title/3               - 0 = Without text
    │                           - 1 = Problematic
    │                           - 2 = Proofread
    ▼                           - 3 = Validated
Work Title                  # Compiled text - transcludes Page: pages
```

The main namespace page (e.g., `Work Title`) is built by transcluding
individual `Page:` pages:

```wikitext
<pages index="Work Title" from=1 to=100 header=1 />
```

This single tag transcludes all pages 1-100 with their headers.

### Quality Levels

| Code | Level | Meaning | What's Needed |
|------|-------|---------|---------------|
| 0 | Without text | Raw image only | OCR or manual transcription |
| 1 | Problematic | Text has issues | Needs human review |
| 2 | Proofread | Read by one person | Second reader validation |
| 3 | Validated | Read by two people | Complete - ready for inclusion |

### SOP: Check Proofreading Progress

```python
def get_work_stats(wiki: str, index_title: str) -> dict:
    """Get proofreading statistics for a work on Wikisource.

    Args:
        wiki: Language code (e.g., 'en', 'fr', 'de')
        index_title: Index page title (e.g., 'Index:Example Book.pdf')

    Returns:
        {"total": N, "without_text": N, "problematic": N,
         "proofread": N, "validated": N, "percent_done": 0-100}
    """
    import requests
    API = f"https://{wiki}.wikisource.org/w/api.php"

    # Step 1: Get the list of pages in the Index
    resp = requests.get(API, params={
        "action": "query",
        "titles": index_title,
        "prop": "proofreadinfo",
        "piprop": "quality",
        "format": "json",
    }, timeout=30, headers={
        "User-Agent": "WskTool/1.0 (https://example.com; user@example.com)"
    })
    resp.raise_for_status()
    data = resp.json()

    # Step 2: Count pages by quality level
    # The proofreadinfo API returns quality data per page
    pages = data.get("query", {}).get("pages", {})
    stats = {"without_text": 0, "problematic": 0,
             "proofread": 0, "validated": 0, "total": 0}

    for page_id, page_data in pages.items():
        if page_id == "-1":
            continue
        quality = page_data.get("pagequality", 0)
        quality_map = {0: "without_text", 1: "problematic",
                       2: "proofread", 3: "validated"}
        key = quality_map.get(quality)
        if key:
            stats[key] += 1
        stats["total"] += 1

    if stats["total"] > 0:
        done = stats["proofread"] + stats["validated"]
        stats["percent_done"] = round(done / stats["total"] * 100)

    return stats
```

### SOP: Extract OCR Text for Proofreading

```python
def get_page_text(wiki: str, page_title: str) -> str | None:
    """Get the raw OCR text from a Wikisource Page: namespace page.

    The text layer is stored as the wikitext of the Page: page.
    An empty page (or one with only {{blank}} template) means
    no text has been entered yet.
    """
    import requests
    API = f"https://{wiki}.wikisource.org/w/api.php"

    resp = requests.get(API, params={
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
    }, timeout=30, headers={
        "User-Agent": "WskTool/1.0 (https://example.com; user@example.com)"
    })
    resp.raise_for_status()
    data = resp.json()

    if "parse" in data and "wikitext" in data["parse"]:
        wikitext = data["parse"]["wikitext"]["*"]
        # Strip out header/footer templates to get just the text layer
        import re
        text = re.sub(r"\{\{header\|.*?\}\}", "", wikitext)
        text = re.sub(r"\{\{footer\|.*?\}\}", "", text)
        text = re.sub(r"\{\{c\|.*?\}\}", "", text)  # {{c|...}} center template
        return text.strip()
    return None
```

### SOP: Query Wikisource via the API

Wikisource uses standard MediaWiki Action API but has project-specific modules:

```python
def get_page_status(wiki: str, page_title: str) -> dict:
    """Get the proofread status of a specific Page: page."""
    import requests
    API = f"https://{wiki}.wikisource.org/w/api.php"

    resp = requests.get(API, params={
        "action": "query",
        "titles": page_title,
        "prop": "proofread",
        "format": "json",
    }, timeout=30, headers={
        "User-Agent": "WskTool/1.0 (https://example.com; user@example.com)"
    })
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    for pid, pdata in pages.items():
        if pid != "-1":
            quality = pdata.get("pagequality", 0)
            quality_labels = {0: "Without text", 1: "Problematic",
                              2: "Proofread", 3: "Validated"}
            return {
                "title": pdata.get("title", page_title),
                "quality": quality,
                "quality_label": quality_labels.get(quality, "Unknown"),
            }
    return {"title": page_title, "quality": None, "quality_label": "Not found"}
```

### SOP: Author Pages

Author pages live in the `Author:` namespace and use the `{{author}}` template:

```wikitext
{{author
| firstname = Jane
| lastname  = Austen
| last_initial = Au
| birthyear = 1775
| deathyear = 1817
| description = English novelist known for ...
}}
==Works==
* [[Pride and Prejudice]] (1813)
* [[Sense and Sensibility]] (1811)
```

```python
def get_author_works(wiki: str, author_name: str) -> list[str]:
    """Get a list of works by an author on Wikisource.

    Args:
        wiki: Language code (e.g., 'en')
        author_name: Author page title (without 'Author:' prefix)
    """
    import requests
    API = f"https://{wiki}.wikisource.org/w/api.php"

    resp = requests.get(API, params={
        "action": "query",
        "list": "embeddedin",
        "eititle": f"Author:{author_name}",
        "eilimit": "max",
        "format": "json",
    }, headers={
        "User-Agent": "WskTool/1.0 (https://example.com; user@example.com)"
    })
    resp.raise_for_status()
    data = resp.json()

    return [p["title"] for p in data.get("query", {}).get("embeddedin", [])]
```

---

## Guardrails

### ❌ Don't Assume English Wiktionary or Wikisource
Both projects have 150+ language editions with different template conventions.
Always specify the language code when querying.

### ❌ Don't Confuse `----` with Section Headings
In Wiktionary, `----` (4 hyphens) is NOT a heading - it's a raw divider between
language sections. Parsing by headings alone will miss this.

### ❌ Don't Try to Edit Page: Pages on Wikisource Directly
Wikisource `Page:` pages hold image + text pairs. Edits should update the text
layer, not replace the image. Use the ProofreadPage UI or the `proofread` API
module.

### ❌ Don't Overwrite Translation Tables
Translation tables on Wiktionary are maintained by many editors. Appending is
safer than replacing.

### ❌ Don't Ignore Quality Levels
Wikisource's quality system is central to its workflow. Treating a "Without text"
page the same as a "Validated" page defeats the purpose.

---

## Tooling

### 🔧 Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`scripts/wt-entry-summary.sh`](./scripts/wt-entry-summary.sh) | Fetch a Wiktionary entry and show its structure (languages, POS, definitions) | `./wt-entry-summary.sh word en` |
| [`scripts/ws-page-status.sh`](./scripts/ws-page-status.sh) | Show proofreading progress for a Wikisource work | `./ws-page-status.sh en "Index:Example.pdf"` |
| [`scripts/ws-text-extract.sh`](./scripts/ws-text-extract.sh) | Extract OCR text from a Wikisource Page: page | `./ws-text-extract.sh en "Page:Example/1"` |

### 🐍 Python Assets

| Asset | Purpose | Usage |
|-------|---------|-------|
| [`assets/wt_entry_parser.py`](./assets/wt_entry_parser.py) | Importable module: parse Wiktionary entries into structured language/POS/definition data | `from wt_entry_parser import WiktionaryParser` |
| [`assets/ws_proofread_checker.py`](./assets/ws_proofread_checker.py) | Importable module: query Wikisource proofreading status, quality distribution, and page-level status | `from ws_proofread_checker import ProofreadChecker` |
| [`assets/ws_text_extractor.py`](./assets/ws_text_extractor.py) | Importable module: extract text layer from Wikisource pages with header/footer stripping | `from ws_text_extractor import TextExtractor` |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/wiktionary-entry-structure.md`](./references/wiktionary-entry-structure.md) | Full entry anatomy: heading hierarchy, section types, template families, language codes |
| [`references/wikisource-proofread-workflow.md`](./references/wikisource-proofread-workflow.md) | Three-namespace system, quality levels, proofreading lifecycle, API modules |
| [`references/sister-project-api.md`](./references/sister-project-api.md) | API differences between Wikipedia, Wiktionary, and Wikisource - endpoint URLs, prop modules, list modules |

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | Commons hosts audio pronunciations and scanned documents used by both projects |
| **[wikimedia-commons-pdf](../wikimedia-commons-pdf/SKILL.md)** | PDF/DjVu handling for Wikisource OCR and proofreading |
| **[pywikibot](../pywikibot/SKILL.md)** | Bot operations for bulk Wiktionary/Wikisource tasks |
| **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** | Parsing entry/page wikitext with mwparserfromhell |
| **[wikimedia-i18n-l10n-for-tools](../wikimedia-i18n-l10n-for-tools/SKILL.md)** | Language detection and fallback for multilingual entries |
