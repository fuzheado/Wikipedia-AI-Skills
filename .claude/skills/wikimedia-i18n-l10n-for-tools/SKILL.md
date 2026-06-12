---
name: wikimedia-i18n-l10n-for-tools
description: Design multilingual Toolforge tools — message files and ICU plurals, language detection and fallback chains, RTL/bidi layout, Unicode normalization and pitfalls, cross-wiki domain mapping, batch Wikidata label fetching, and avoiding English Wikipedia assumptions
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["i18n", "l10n", "internationalization", "localization", "multilingual", "translation", "toolforge"]
  - keywords: ["RTL", "bidi", "right-to-left", "Arabic", "Hebrew", "Persian"]
  - keywords: ["Unicode", "Unicode normalization", "NFC", "page title", "cross-wiki"]
  - keywords: ["message file", "ICU", "pluralization", "language fallback", "gettext"]
  - keywords: ["Wikidata label", "multilingual label", "wbgetentities", "language detection"]
last_verified: 2026-06-11
depends_on: [wikimedia-api-access, wikidata]
---

> ⚠️ **User-Agent required:** All API examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

> 💡 **Related skills:** This skill covers *app-level* i18n for tool developers. For *on-wiki content translation* using the Translate extension, see **[mediawiki-translate-extension](../mediawiki-translate-extension/SKILL.md)**. For Wikidata SPARQL queries with multilingual labels, see **[wikidata](../wikidata/SKILL.md)**.

---

## Table of Contents

1. [Why Tool i18n Is Different from Wiki Translation](#why-tool-i18n-is-different-from-wiki-translation)
2. [Two Layers of i18n for Wikimedia Tools](#two-layers-of-i18n-for-wikimedia-tools)
3. [SOP: Message Files and UI Translation](#sop-message-files-and-ui-translation)
4. [SOP: Language Detection and Switching](#sop-language-detection-and-switching)
5. [SOP: RTL and Bidi Layout](#sop-rtl-and-bidi-layout)
6. [SOP: Language Fallback Chains](#sop-language-fallback-chains)
7. [SOP: Wikidata and Commons Multilingual Labels](#sop-wikidata-and-commons-multilingual-labels)
8. [SOP: Page Title Normalization Across Scripts](#sop-page-title-normalization-across-scripts)
9. [SOP: Cross-Wiki Domain and Language Handling](#sop-cross-wiki-domain-and-language-handling)
10. [SOP: Avoiding English Wikipedia Assumptions](#sop-avoiding-english-wikipedia-assumptions)
11. [SOP: Unicode Pitfalls](#sop-unicode-pitfalls)
12. [Guardrails](#guardrails)
13. [Cross-References](#cross-references)

---

## Why Tool i18n Is Different from Wiki Translation

The repo already has a skill for the **MediaWiki Translate extension** (`mediawiki-translate-extension`), which covers on-wiki content translation using `<translate>` tags and the `Special:Translate` workflow. That skill is for **wiki editors** translating page content.

This skill is for **tool developers** building applications (web apps, bots, scripts) that need to:

| Concern | Wiki Translation (Translate ext) | Tool i18n (this skill) |
|---------|-------------------------------|----------------------|
| **Translation format** | `<translate>` tags in wikitext | `.json`/`.po`/`.properties` files |
| **Translation workflow** | Special:Translate, translation admins | Crowdin/translatewiki.net or manual PRs |
| **Language detection** | User preference on wiki | `Accept-Language` header, cookie, URL prefix |
| **Fallback** | Built into Translate extension | Developer implements via fallback chains |
| **Plural rules** | `{{PLURAL:}}` parser function | ICU MessageFormat `{x, plural, ...}` |
| **RTL/Bidi** | Handled by MediaWiki skin CSS | Developer implements with CSS `direction`, flexbox |
| **Title normalization** | Handled by MediaWiki | Developer handles NFC, case folding, percent-encoding |
| **Wikidata labels** | Not directly relevant | Batch-fetching with language fallback |

---

## Two Layers of i18n for Wikimedia Tools

### Layer 1: App UI i18n

Translating your tool's user interface — buttons, labels, messages, error text.

```json
{
    "welcome": "Welcome to my tool!",
    "search": "Search",
    "results": "{count, plural, one {# result} other {# results}}",
    "error_loading": "Error loading data: {error}"
}
```

### Layer 2: Wikimedia-Specific i18n

Interfacing with Wikimedia APIs in a language-aware way — fetching labels in the user's language, handling cross-wiki requests, normalizing titles.

```python
# Fetch Wikidata label in user's language
label = fetch_label("Q937", user_lang="fr")
# → "Albert Einstein"

# Make an API call to the user's wiki
wiki = language_to_domain(user_lang)
resp = requests.get(f"https://{wiki}/w/api.php?action=query&...")
```

Both layers are needed for a truly multilingual tool. Most tools focus only on Layer 1 and forget Layer 2.

---

## SOP: Message Files and UI Translation

### 1. Message File Structure

Organize translations as JSON files, one per language:

```
messages/
├── en.json        # Source language (English)
├── fr.json        # French
├── de.json        # German
├── ar.json        # Arabic
└── zh-hans.json   # Simplified Chinese
```

Each file is a flat key-value map:

```json
{
    "app_title": "Wikimedia Category Analyzer",
    "search_placeholder": "Search categories...",
    "results_count": "{count, plural, one {# category} other {# categories}}",
    "loading": "Loading...",
    "error_network": "Could not connect. Please try again.",
    "welcome_user": "Welcome back, {username}!"
}
```

### 2. ICU MessageFormat for Plurals, Gender, Select

Use ICU MessageFormat syntax for messages that vary by count, gender, or other variables.

**Plurals:**
```
{count, plural,
    one {# result}
    other {# results}
}
```

**Select (for gender-aware messages):**
```
{gender, select,
    male {He submitted}
    female {She submitted}
    other {They submitted}
}
```

**Nested:**
```
{count, plural,
    one {{gender, select,
        male {His # result}
        female {Her # result}
        other {Their # result}
    }}
    other {{gender, select,
        male {His # results}
        female {Her # results}
        other {Their # results}
    }}
}
```

### 3. Loading Messages in Python

```python
from message_loader import I18nMessages

i18n = I18nMessages("messages/", supported_languages=["en", "fr", "de", "ar"])

# Get a simple message
msg = i18n.get("app_title", lang="fr")
# → "Analyseur de catégories Wikimedia"

# Message with variable substitution
msg = i18n.get("welcome_user", lang="de", username="Alice")
# → "Willkommen zurück, Alice!"

# Message with pluralization
msg = i18n.get_plural("results_count", count=5, lang="fr")
# → "5 catégories"

msg = i18n.get_plural("results_count", count=1, lang="fr")
# → "1 catégorie"

# Fallback when translation is missing
msg = i18n.get("app_title", lang="ja")
# → "Wikimedia Category Analyzer"  (falls back to en)
```

### 4. Translation Workflow for Toolforge Tools

**Option A: Manual with PRs**
1. Keep `en.json` as the source of truth
2. Developers/volunteers submit translations via pull requests
3. Review and merge

**Option B: translatewiki.net**
[translatewiki.net](https://translatewiki.net) is the Wikimedia community's translation platform for software. It supports:
- `.json` (flat key-value)
- `.properties` (Java-style)
- `.yaml`
- `.po` (gettext)

**To use translatewiki.net:**
1. Register your tool as a project
2. Push your `en.json` as the source file
3. Translators contribute through the web interface
4. Pull translated files back into your repo

### 5. Locale-Aware Number and Date Formatting

```python
# Using the message_loader's built-in formatter
i18n = I18nMessages("messages/")

# Numbers
num = i18n.format_number(1234567.89, lang="de")
# → "1.234.567,89"

num = i18n.format_number(1234567.89, lang="en")
# → "1,234,567.89"

# For full CLDR support, use the `babel` library:
from babel.numbers import format_number, format_currency
from babel.dates import format_date, format_time

formatted = format_number(1234567.89, locale="de_DE")
# → "1.234.567,89"

date_formatted = format_date(today, locale="ar_SA")
# → "١٩ ربيع الأول ١٤٤٦ هـ"
```

---

## SOP: Language Detection and Switching

### 1. Detect Language from Browser

```python
from i18n_utils import detect_language, parse_accept_language

# From HTTP header
accept = request.headers.get("Accept-Language", "")
user_lang = detect_language(accept, supported_languages=["en", "fr", "de"])
# → e.g., "fr"

# Parse for debugging
parsed = parse_accept_language("fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7")
# → [("fr", 1.0), ("en", 0.9), ("de", 0.8)]
```

### 2. Complete Language Resolution Strategy

For a Flask web tool, implement this layered strategy:

```python
from i18n_utils import detect_language, is_rtl
from message_loader import I18nMessages

def get_user_language(request, supported_languages, default="en"):
    """
    Resolve user language from multiple sources, in priority order:
    1. URL prefix (example.com/fr/page)
    2. User cookie (language preference)
    3. Accept-Language header (browser preference)
    4. Default
    """
    # 1. URL prefix
    lang_from_url = extract_lang_from_path(request.path)
    if lang_from_url in supported_languages:
        return lang_from_url

    # 2. Cookie
    lang_from_cookie = request.cookies.get("lang")
    if lang_from_cookie in supported_languages:
        return lang_from_cookie

    # 3. Accept-Language header
    accept = request.headers.get("Accept-Language", "")
    lang_from_header = detect_language(accept, supported_languages)
    if lang_from_header != default:
        return lang_from_header

    return default
```

### 3. Flask Blueprint Example

```python
from flask import Blueprint, request, session, redirect, url_for

i18n_bp = Blueprint("i18n", __name__)

@i18n_bp.route("/set-language/<lang>")
def set_language(lang):
    """Set language preference via URL."""
    resp = redirect(request.referrer or "/")
    resp.set_cookie("lang", lang, max_age=365*24*3600)
    return resp


# Template context processor
def inject_i18n():
    """Inject i18n messages and RTL direction into all templates."""
    from flask import g, request
    from i18n_utils import detect_language, is_rtl

    supported = ["en", "fr", "de", "ar", "ja", "zh-hans"]
    lang = get_user_language(request, supported)
    i18n = I18nMessages("messages/", supported_languages=supported)

    g.lang = lang
    g.i18n = i18n
    g.dir = "rtl" if is_rtl(lang) else "ltr"
```

### 4. HTML Template with Language Attributes

```html
<!DOCTYPE html>
<html lang="{{ g.lang }}" dir="{{ g.dir }}">
<head>
    <meta charset="utf-8">
    {% if g.dir == "rtl" %}
    <link rel="stylesheet" href="/static/css/rtl.css">
    {% endif %}
</head>
<body>
    <h1>{{ g.i18n.get("app_title", lang=g.lang) }}</h1>
    <p>{{ g.i18n.get_plural("results_count", count=results|length, lang=g.lang) }}</p>
</body>
</html>
```

---

## SOP: RTL and Bidi Layout

### 1. HTML Fundamentals

Always set `dir` and `lang` attributes on the `<html>` element:

```html
<html lang="ar" dir="rtl">
```

CSS will automatically mirror most layout:
- `text-align: start` / `end` works correctly (no need for LTR/RTL variants)
- Flexbox with `flex-start` / `flex-end` adapts to direction
- Grid auto-placement adapts

### 2. CSS for RTL Support

```css
/* Use logical properties instead of physical ones */
/* ❌ Avoid: */
.element {
    margin-left: 1em;
    padding-right: 0.5em;
    border-left: 1px solid #ccc;
    text-align: left;
}

/* ✅ Use: */
.element {
    margin-inline-start: 1em;
    padding-inline-end: 0.5em;
    border-inline-start: 1px solid #ccc;
    text-align: start;
}
```

### 3. Common RTL Challenges

| Challenge | Solution |
|-----------|----------|
| **Mixed LTR/RTL text** (e.g., English name in Arabic article) | Unicode bidi algorithm handles most cases automatically. Use `<bdi>` element to isolate. |
| **Numbers in RTL text** | Numbers are LTR within RTL text by default. This is correct for most cases. |
| **Icons/arrows** | Flip icons that imply direction (← →) in RTL mode: `transform: scaleX(-1)` for CSS, or use directional icon variants. |
| **Form input alignment** | Use `text-align: start;` — inputs in RTL will have cursor on the right. |
| **Time/date in RTL** | Numbers and Latin text within dates should remain LTR. Use `<bdi>` wrappers. |

### 4. Python Direction Helper

```python
from i18n_utils import is_rtl

# Set direction in templates
dir_attr = "rtl" if is_rtl(user_lang) else "ltr"

# Bidi-isolate user-generated content
user_text = f"<bdi>{user_text}</bdi>"  # Prevents RTL/LTR from leaking
```

### 5. Testing RTL Layout

- Test with real Arabic/Hebrew/Persian content, not just lorem ipsum
- Check that navigation menus, buttons, and forms are reversed
- Verify that mixed LTR/RTL content (e.g., English Wikidata labels in Arabic interface) displays correctly
- Test with `dir="auto"` on user-generated content

---

## SOP: Language Fallback Chains

### 1. What Fallback Chains Are

When a message isn't available in the user's requested language, the tool should try progressively broader languages. Wikimedia has well-defined fallback chains. For example:

```
pt-br → pt → es → en       (Brazilian Portuguese → Portuguese → Spanish → English)
zh-cn → zh-hans → zh → en  (Chinese China → Simplified Chinese → Chinese → English)
be-tarask → be → ru → en   (Belarusian Taraškievica → Belarusian → Russian → English)
```

### 2. Using the Fallback Resolver

```python
from i18n_utils import resolve_fallback

chain = resolve_fallback("pt-br")
# → ["pt-br", "pt", "es", "en"]

chain = resolve_fallback("be-tarask")
# → ["be-tarask", "be", "ru", "en"]

chain = resolve_fallback("en")
# → ["en"]
```

### 3. Fetching Wikidata Labels with Fallback

```python
from wikidata_labels import WikidataLabelFetcher

fetcher = WikidataLabelFetcher()

# Automatically tries fallback chain
info = fetcher.get_entity_info("Q937", preferred_lang="pt-br")
# → {"label": "Albert Einstein", "description": "...", "lang": "pt"}

# Actual language used:
info["lang"]  # → "pt" (Portuguese — falls back from pt-br)
```

### 4. Fallback in Message Files

The `I18nMessages` class automatically applies fallback chains:

```python
from message_loader import I18nMessages

i18n = I18nMessages("messages/", supported_languages=["en", "fr", "de"])

# If "pt-br" is requested but only "pt" and "en" exist:
msg = i18n.get("app_title", lang="pt-br")
# Falls back through: pt-br → pt → en
```

### 5. Implementing Fallback in SPARQL Queries

```python
# SPARQL with language fallback
sparql = """
SELECT ?item ?itemLabel ?itemDescription WHERE {
    VALUES ?item { wd:Q937 wd:Q5 wd:P31 }
    SERVICE wikibase:label {
        bd:serviceParam wikibase:language "%s", "en".
    }
}
""" % (user_lang,)
# The wikibase:label service handles fallback internally!
```

---

## SOP: Wikidata and Commons Multilingual Labels

### 1. Batch-Fetching Labels with Fallback

```python
from wikidata_labels import WikidataLabelFetcher

fetcher = WikidataLabelFetcher()

# Fetch for multiple entities at once (batched in 50s)
entities = ["Q937", "Q5", "P31", "P279", "Q42"]
info = fetcher.batch_get_entity_info(
    entities,
    preferred_lang="ar",
    include_aliases=True,
)

for eid, data in info.items():
    print(f"{eid}: {data['label']} [{data['lang']}]")
    # → Q937: ألبرت أينشتاين [ar]
    # → Q5: إنسان [ar]
    if "aliases" in data:
        print(f"       Aliases: {', '.join(data['aliases'])}")
```

### 2. Action API with Language Parameters

```python
import requests

# Fetch Wikidata entity with specific languages
resp = requests.get(
    "https://www.wikidata.org/w/api.php",
    params={
        "action": "wbgetentities",
        "ids": "Q937|Q5|P31",
        "props": "labels|descriptions",
        "languages": "en|fr|de|ar",
        "format": "json",
    },
    headers={"User-Agent": "MyTool/1.0 (contact) ContentGapResearch"},
    timeout=30,
)
```

### 3. Commons Multilingual File Descriptions

Commons file pages have multilingual captions and descriptions stored as Wikibase statements:

```python
# Fetch Commons file captions
resp = requests.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "wbgetentities",
        "sites": "commonswiki",
        "titles": "File:Example.jpg",
        "props": "labels|descriptions",
        "languages": "en|fr|de|ar",
        "format": "json",
    },
    headers={"User-Agent": "MyTool/1.0 (contact) ContentGapResearch"},
    timeout=30,
)
```

### 4. The `uselang` Parameter

Many MediaWiki API endpoints accept a `uselang` parameter that controls the language of interface messages:

```python
params = {
    "action": "query",
    "meta": "siteinfo",
    "uselang": "fr",  # Interface messages in French
    "format": "json",
}
```

The `uselang` parameter also affects:
- Error messages returned by the API
- `prop=extracts` snippet language (on multilingual wikis like Commons)
- Content language in `prop=pageprops`

---

## SOP: Page Title Normalization Across Scripts

### 1. MediaWiki Title Normalization

MediaWiki applies these normalization rules to all page titles:

1. **NFC Unicode normalization** — characters like `é` are stored as single codepoints
2. **First letter capitalized** — `albert einstein` → `Albert Einstein`
3. **Underscores for spaces** — or spaces for underscores (both are equivalent)
4. **Multiple spaces collapsed** — `  spaces  ` → `spaces`
5. **Invisible characters stripped** — zero-width spaces, direction markers removed

### 2. Normalizing Before API Calls

```python
from i18n_utils import normalize_title

user_input = "Spielberg\u0301"  # NFD: e + combining accent
safe_title = normalize_title(user_input)
# → "Spielberg\u00e9"  # NFC: é as one codepoint

# Now safe for API use
params = {"action": "query", "titles": safe_title}
```

### 3. Cross-API Title Format Differences

| API | Title Format | Example |
|-----|-------------|---------|
| Action API | Spaces (raw or encoded) | `Albert Einstein` |
| REST API | Percent-encoded spaces | `Albert%20Einstein` |
| SQL replicas | Underscores | `Albert_Einstein` |
| Wikidata (wbgetentities) via sitelinks | Underscores | `Albert_Einstein` |
| URL path | Underscores or percent-encoded | `/wiki/Albert_Einstein` |

**Converting between formats:**

```python
from urllib.parse import quote, unquote

# Spaces ← → underscores
title_with_spaces = "Albert_Einstein".replace("_", " ")
title_with_underscores = "Albert Einstein".replace(" ", "_")

# For REST API URLs
safe_path = quote("Albert Einstein", safe="")
# → "Albert%20Einstein"

# SQL format
sql_format = "Albert_Einstein"
```

### 4. Case Folding Across Scripts

Different scripts have different case rules. The MediaWiki `ucfirst` behavior is well-defined for Latin but complex for other scripts:

```python
# MediaWiki-style first-letter capitalization
def mw_ucfirst(title: str) -> str:
    """Apply MediaWiki-style first-letter capitalization."""
    if not title:
        return title
    # For Latin scripts: simple capitalize
    # For other scripts: may be more complex
    return title[0].upper() + title[1:]

# But for Japanese, capitalization doesn't apply:
# "東京" stays "東京" (no uppercase concept)
```

**Best practice:** Don't manually capitalize — let the API's `normalize` property handle it:

```python
params = {
    "action": "query",
    "titles": "user entered title",
    "redirects": 1,  # Follow redirects
    "format": "json",
}
# The response will contain the normalized title
```

### 5. The `normalize` Property in Action API Responses

```json
{
    "query": {
        "normalized": [
            {
                "from": "user entered title",
                "to": "User entered title"
            }
        ],
        "pages": {...}
    }
}
```

Always use the `normalized` and `redirects` properties in API responses to get the canonical title.

---

## SOP: Cross-Wiki Domain and Language Handling

### 1. Language-to-Domain Mapping

> **⚠️ Important:** The Action API's `prop=langlinks` returns **CLDR/BCP 47 language codes**
> which sometimes differ from Wikipedia domain names. For example, `yue` (Cantonese)
> resolves to `zh-yue.wikipedia.org`, not `yue.wikipedia.org`. A static mapping works
> for common cases, but the **Site Matrix API** (`action=sitematrix`) is the canonical
> source for the correct domain of every Wikipedia language edition.

#### Quick approach — static mapping (covers 95% of cases)

```python
from i18n_utils import language_to_domain

# Standard mapping
domain = language_to_domain("fr")
# → "fr.wikipedia.org"

domain = language_to_domain("de", project="wiktionary")
# → "de.wiktionary.org"

# Special codes
domain = language_to_domain("simple")
# → "simple.wikipedia.org"

domain = language_to_domain("be-tarask")
# → "be-tarask.wikipedia.org"

# Known code/domain mismatches (not covered by static mapping):
#   yue → zh-yue.wikipedia.org  (Cantonese)
#   nan → zh-min-nan.wikipedia.org  (Min Nan Chinese)
#   nb  → no.wikipedia.org  (Norwegian Bokmål → Norwegian)

# Project wikis
domain = language_to_domain("en", project="commons")
# → "commons.wikimedia.org"

domain = language_to_domain("en", project="wikidata")
# → "www.wikidata.org"
```

#### Authoritative approach — Site Matrix API (covers 100%, self-updating)

For tools that fetch interlanguage links and need the correct domain every time,
calling the Site Matrix API once at startup builds an authoritative mapping:

```python
import requests

def build_domain_map() -> dict:
    """Build {language_code: domain} from the Wikimedia Site Matrix."""
    resp = requests.get("https://en.wikipedia.org/w/api.php", params={
        "action": "sitematrix",
        "format": "json",
        "smtype": "language",
    }, headers={"User-Agent": "MyBot/1.0 (contact)"}, timeout=15)
    data = resp.json()
    domain_map = {}
    for smkey, smval in data.get("sitematrix", {}).items():
        if smkey == "count" or not isinstance(smval, dict):
            continue
        lang_code = smval.get("code")
        for site in smval.get("site", []):
            if site.get("code") == "wiki" and "wikipedia.org" in site.get("url", ""):
                # Extract domain from URL: "https://fr.wikipedia.org/w/" → "fr.wikipedia.org"
                domain = site["url"].replace("https://", "").replace("/w/", "")
                domain_map[lang_code] = domain
    # Static fallbacks for edge cases not covered by the matrix
    domain_map.update({
        "yue": "zh-yue.wikipedia.org",
        "nan": "zh-min-nan.wikipedia.org",
        "nb": "no.wikipedia.org",
    })
    return domain_map

# Usage
domain_map = build_domain_map()
domain = domain_map.get("yue", f"{lang}.wikipedia.org")
# → "zh-yue.wikipedia.org"
```

This handles all ~362 language editions automatically, including edge cases
like `yue`→`zh-yue`, `nan`→`zh-min-nan`, and `nb`→`no`. The API call takes
~1 second and the result can be cached in memory for the lifetime of the tool.

### 2. Domain-to-Language Extraction

```python
from i18n_utils import domain_to_language

lang = domain_to_language("fr.wikipedia.org")
# → "fr"

lang = domain_to_language("commons.wikimedia.org")
# → None (no language)

lang = domain_to_language("be-tarask.wikipedia.org")
# → "be-tarask"
```

### 3. Cross-Wiki API Patterns

```python
import requests

def fetch_page_from_wiki(title: str, lang: str) -> dict:
    """Fetch a page from a specific language Wikipedia."""
    from i18n_utils import language_to_domain

    domain = language_to_domain(lang)
    url = f"https://{domain}/w/api.php"

    resp = requests.get(
        url,
        params={
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
        },
        headers={"User-Agent": "MyTool/1.0 (contact) ContentGapResearch"},
        timeout=30,
    )
    return resp.json()


# Fetch the same topic across multiple languages
for lang in ["en", "fr", "de", "ar"]:
    data = fetch_page_from_wiki("Albert Einstein", lang)
    # Process each language version
```

### 4. Interlanguage Links via the API

```python
# Fetch page links to other language editions
resp = requests.get(
    "https://en.wikipedia.org/w/api.php",
    params={
        "action": "query",
        "titles": "Albert Einstein",
        "prop": "langlinks",
        "lllimit": 500,
        "format": "json",
    },
    headers={"User-Agent": "MyTool/1.0 (contact) ContentGapResearch"},
    timeout=30,
)
data = resp.json()

# Extract language → title mappings
pages = data.get("query", {}).get("pages", {})
for page_id, page in pages.items():
    langlinks = page.get("langlinks", [])
    for link in langlinks:
        lang = link["lang"]
        title = link["title"]
        print(f"{lang}: {title}")
```

---

## SOP: Avoiding English Wikipedia Assumptions

### 1. Bad Patterns vs. Good Patterns

```python
# ❌ BAD: Hardcoded English Wikipedia
resp = requests.get("https://en.wikipedia.org/w/api.php?...")

# ✅ GOOD: Parameterized wiki domain
def fetch_wiki(title: str, lang: str = "en"):
    from i18n_utils import language_to_domain
    domain = language_to_domain(lang)
    url = f"https://{domain}/w/api.php"
    ...


# ❌ BAD: Assuming English labels exist on Wikidata
# (they almost always do, but when they don't, your tool breaks)

# ✅ GOOD: Use fallback chains to find any available language
from wikidata_labels import WikidataLabelFetcher

fetcher = WikidataLabelFetcher()
info = fetcher.get_entity_info("Q937", preferred_lang=user_lang)
# Falls back: user_lang → ... → en


# ❌ BAD: Assuming LTR layout
html = f"<html><body><p>{message}</p></body></html>"

# ✅ GOOD: Set dir and lang attributes
dir_attr = "rtl" if is_rtl(user_lang) else "ltr"
html = f'<html lang="{user_lang}" dir="{dir_attr}">...</html>'


# ❌ BAD: Assuming Latin script
title_length = len(page_title)  # Counts codepoints, not graphemes

# ✅ GOOD: Handle all scripts gracefully
# (Devanagari, CJK, Arabic all have different character widths)


# ❌ BAD: Hardcoded "en" in SPARQL
SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }

# ✅ GOOD: Use user's language with en fallback
SERVICE wikibase:label {
    bd:serviceParam wikibase:language "{user_lang}", "en".
}
```

### 2. Checklist for Multilingual Tool Design

- [ ] All API calls parameterize the wiki domain (not hardcoded `en.wikipedia.org`)
- [ ] Wikidata queries use the user's language with English fallback
- [ ] HTML templates set `lang` and `dir` attributes
- [ ] CSS uses logical properties (`margin-inline-start`, `text-align: start`)
- [ ] Message files exist for at least one non-English language
- [ ] `Accept-Language` header is parsed for language detection
- [ ] User-facing numbers use locale-aware formatting
- [ ] Page titles are NFC-normalized before comparison
- [ ] Invisible Unicode characters are stripped from user input
- [ ] Language fallback chains are implemented (not just "en" fallback)
- [ ] SPARQL `SERVICE wikibase:label` uses the user's language
- [ ] RTL layout is tested with real Arabic/Hebrew/Persian content
- [ ] Plural rules are correct for the target languages
- [ ] `uselang` parameter is passed to API calls where appropriate

### 3. Testing Multilingual Tools

```python
"""Test your tool with multiple languages in CI."""

TEST_LANGUAGES = ["en", "fr", "de", "ar", "ja", "zh-hans", "ru"]

def test_message_coverage():
    """Verify all supported languages have all required keys."""
    from message_loader import I18nMessages

    i18n = I18nMessages("messages/", supported_languages=TEST_LANGUAGES)
    required_keys = ["app_title", "search", "results", "error_network"]

    for lang in TEST_LANGUAGES:
        for key in required_keys:
            msg = i18n.get(key, lang=lang)
            assert msg != key, f"Missing translation: {lang}.{key}"
            assert msg != "", f"Empty translation: {lang}.{key}"

def test_rtl_languages_handled():
    """Verify RTL languages return correct direction."""
    from i18n_utils import is_rtl

    assert is_rtl("ar")
    assert is_rtl("he")
    assert is_rtl("fa")
    assert not is_rtl("en")
    assert not is_rtl("de")
```

---

## SOP: Unicode Pitfalls

See **[references/unicode-pitfalls.md](references/unicode-pitfalls.md)** for a complete reference.

Key takeaways:

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| NFC vs NFD | Title comparison fails | `unicodedata.normalize("NFC", title)` |
| Zero-width characters | API returns "page not found" | Strip `\u200B-\u200F`, `\uFEFF` |
| RTL override characters | Text displays in reverse order | Strip `\u202A-\u202F` |
| Combining characters | `len()` gives wrong count | Use grapheme cluster counting |
| Percent-encoding mismatch | REST API returns 404 | Use `urllib.parse.quote` for REST URLs |
| Punycode domains | Interwiki link fails | Use ASCII domain names where possible |

---

## Guardrails

### 1. Never Hardcode `en.wikipedia.org`

Every API call should parameterize the wiki domain. Use `language_to_domain()` from `i18n_utils.py`.

### 2. Always Normalize Page Titles

Before comparing, storing, or using page titles from user input, always:
1. Strip invisible characters
2. NFC normalize
3. Strip whitespace

### 3. Set `dir` and `lang` on Every HTML Page

Even if you only support English. This ensures browser tools, screen readers, and CSS frameworks work correctly.

### 4. Don't Assume Latin Script for Truncation

`text[:100]` may cut in the middle of a CJK character, a Devanagari conjunct, or an emoji. Use grapheme-aware truncation or set CSS `text-overflow: ellipsis` instead.

### 5. Always Pass `uselang` to the API

When calling Wikimedia APIs, pass `uselang` to get error messages and interface text in the user's language:

```python
params = {
    "action": "query",
    "uselang": user_lang,
    "format": "json",
}
```

### 6. Wikidata Labels May Not Exist in English

While rare, some Wikidata items lack English labels. Always use the fallback chain rather than hardcoding `"en"`.

### 7. Test RTL with Real Content

Testing RTL layout with Latin lorem ipsum is useless. Use real Arabic, Hebrew, or Persian text:

```
مرحبًا بكم في أداة تحليل الويكي
ברוכים הבאים לכלי ניתוח ויקי
به ابزار تحلیل ویکی خوش آمدید
```

### 8. Plural Rules Vary Significantly

Don't apply English plural rules (one/other) to all languages:
- Arabic has 6 plural forms (zero, one, two, few, many, other)
- Russian has 4 forms (one, few, many, other)
- Japanese has 2 forms but they work differently
- Some languages have no plural forms at all

Use ICU MessageFormat or the `babel` library instead of simple `if count == 1` checks.

### 9. Language Code Normalization: Aliases, Renames, and Non-Standard Codes

Wikimedia has a complex history of language code usage. The same language can
be referred to by multiple codes depending on the source:

| Context | Example Codes |
|---------|--------------|
| Wikipedia subdomain | `yue.wikipedia.org`, `nb.wikipedia.org` |
| ISO 639-1/3 standard | `yue`, `nb` (canonical) |
| Deprecated alias | `zh-yue` (old MediaWiki code → `yue`) |
| Deprecated alias | `no` (ISO macrolanguage → `nb`) |
| BCP 47 tag | `en-simple` (Simple English as English variant) |

**The critical mappings** (from MediaWiki `$wgDummyLanguageCodes`):

| Alias | Canonical | Why |
|-------|-----------|-----|
| `zh-yue` → | `yue` | Cantonese Wikipedia subdomain was renamed |
| `no` → | `nb` | ISO macrolanguage code redirects to Bokmål |
| `zh-classical` → | `lzh` | Classical Chinese uses ISO 639-3 |
| `zh-min-nan` → | `nan` | Min Nan uses ISO 639-3 |
| `bat-smg` → | `sgs` | Samogitian (deprecated code) |
| `roa-rup` → | `rup` | Aromanian (deprecated code) |
| `als` → | `gsw` | Alemannic (was wrongly using Tosk Albanian's ISO code) |
| `fiu-vro` → | `vro` | Võro (deprecated code) |
| `be-x-old` → | `be-tarask` | Belarusian old orthography (renamed) |
| `simple` → | `en` | Simple English uses English message files |

**How to handle this in your code:**

```python
from i18n_utils import normalize_language_code, language_code_to_bcp47

# User passes an old/alias code — normalize it
lang = normalize_language_code("zh-yue")   # → "yue"
lang = normalize_language_code("no")       # → "nb"
lang = normalize_language_code("zh-yue")   # → "yue"

# For HTML output, convert to BCP 47
tag = language_code_to_bcp47("simple")     # → "en-simple"
tag = language_code_to_bcp47("zh-cn")     # → "zh-Hans-CN"

# Always normalize before building API URLs or making cross-system comparisons
```

**Full reference:** See the [language-codes.md](references/language-codes.md) reference doc
for the complete mapping tables including BCP 47 conversion, non-standard Wikipedia
subdomains, and all `$wgExtraLanguageCodes` mappings.

### 10. Cross-Wiki API Calls Have Different Rate Limits

Different language Wikipedias are separate API endpoints with separate rate limits. You cannot assume the same limits apply to `fr.wikipedia.org` and `de.wikipedia.org`.

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent headers, rate limiting, base API patterns |
| **[wikidata](../wikidata/SKILL.md)** | SPARQL with `SERVICE wikibase:label`, entity queries |
| **[mediawiki-translate-extension](../mediawiki-translate-extension/SKILL.md)** | On-wiki content translation (different from tool i18n) |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | Commons multilingual file descriptions and captions |
| **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** | Unicode handling in wikitext parsing |
| **[wikipedia-error-handling](../wikipedia-error-handling/SKILL.md)** | 429 handling per wiki domain |
| **[pywikibot](../pywikibot/SKILL.md)** | Pywikibot's `mylang` config, cross-wiki `-interwiki:` generator |
| **[wikimedia-database](../wikimedia-database/SKILL.md)** | `langlinks` table for interlanguage lookups via SQL |
