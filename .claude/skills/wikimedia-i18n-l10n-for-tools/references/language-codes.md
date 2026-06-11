# Language Code Reference for Wikimedia Tools

A quick reference for language codes, script codes, and region codes used across
Wikimedia projects. All Wikimedia wikis use [BCP 47](https://tools.ietf.org/html/bcp47)
language tags, which combine ISO 639 language codes with ISO 15924 scripts and
ISO 3166 regions.

## Wikimedia Language Codes

Wikimedia uses **mostly ISO 639-1** (two-letter) codes, with ISO 639-3 (three-letter)
codes for languages that don't have a two-letter code.

### Top 20 Wikimedia Languages by Article Count

| Code | Language | Script | RTL | Wiki Domain |
|------|----------|--------|-----|-------------|
| `en` | English | Latin | No | `en.wikipedia.org` |
| `de` | German | Latin | No | `de.wikipedia.org` |
| `fr` | French | Latin | No | `fr.wikipedia.org` |
| `ja` | Japanese | Japanese | No | `ja.wikipedia.org` |
| `zh` | Chinese | Han | No | `zh.wikipedia.org` |
| `ru` | Russian | Cyrillic | No | `ru.wikipedia.org` |
| `es` | Spanish | Latin | No | `es.wikipedia.org` |
| `it` | Italian | Latin | No | `it.wikipedia.org` |
| `pt` | Portuguese | Latin | No | `pt.wikipedia.org` |
| `ar` | Arabic | Arabic | **Yes** | `ar.wikipedia.org` |
| `pl` | Polish | Latin | No | `pl.wikipedia.org` |
| `nl` | Dutch | Latin | No | `nl.wikipedia.org` |
| `he` | Hebrew | Hebrew | **Yes** | `he.wikipedia.org` |
| `fa` | Persian | Arabic | **Yes** | `fa.wikipedia.org` |
| `vi` | Vietnamese | Latin | No | `vi.wikipedia.org` |
| `ko` | Korean | Hangul | No | `ko.wikipedia.org` |
| `tr` | Turkish | Latin | No | `tr.wikipedia.org` |
| `id` | Indonesian | Latin | No | `id.wikipedia.org` |
| `sv` | Swedish | Latin | No | `sv.wikipedia.org` |
| `th` | Thai | Thai | No | `th.wikipedia.org` |

### RTL Languages (common)

| Code | Language | Script | Tool Considerations |
|------|----------|--------|-------------------|
| `ar` | Arabic | Arabic | Full RTL, cursive, contextual letter forms |
| `he` | Hebrew | Hebrew | RTL, numbers are LTR within RTL text |
| `fa` | Persian (Farsi) | Arabic | RTL, uses modified Arabic script |
| `ps` | Pashto | Arabic | RTL |
| `ur` | Urdu | Arabic | RTL, uses Nastaliq script |
| `sd` | Sindhi | Arabic | RTL |
| `ckb` | Central Kurdish | Arabic | RTL |
| `yi` | Yiddish | Hebrew | RTL |
| `dv` | Dhivehi | Thaana | RTL |
| `arc` | Aramaic | Syriac | RTL |

### Script Variants (zh, sr, etc.)

Some languages have multiple script variants with separate wikis:

| Code | Language | Script | Domain |
|------|----------|--------|--------|
| `zh` | Chinese | Simplified | `zh.wikipedia.org` |
| `zh-hans` | Chinese (Simplified) | Simplified | (redirects to zh) |
| `zh-hant` | Chinese (Traditional) | Traditional | `zh.wikipedia.org` (via zh converter) |
| `zh-cn` | Chinese (China) | Simplified | (zh variant) |
| `zh-tw` | Chinese (Taiwan) | Traditional | (zh variant) |
| `sr` | Serbian | Cyrillic | `sr.wikipedia.org` |
| `sr-ec` | Serbian (Cyrillic) | Cyrillic | (sr variant) |
| `sr-el` | Serbian (Latin) | Latin | (sr variant) |
| `sh` | Serbo-Croatian | Latin | `sh.wikipedia.org` |

### Three-Letter Codes (ISO 639-3)

When a language has no ISO 639-1 code, Wikimedia uses the ISO 639-3 code:

| Code | Language | Wiki Domain |
|------|----------|-------------|
| `cdo` | Min Dong Chinese | `cdo.wikipedia.org` |
| `gan` | Gan Chinese | `gan.wikipedia.org` |
| `wuu` | Wu Chinese | `wuu.wikipedia.org` |
| `hak` | Hakka Chinese | `hak.wikipedia.org` |
| `nan` | Min Nan Chinese | `nan.wikipedia.org` |
| `vep` | Veps | `vep.wikipedia.org` |
| `ady` | Adyghe | `ady.wikipedia.org` |

### Special Wikimedia Language Codes

| Code | Purpose | Example |
|------|---------|---------|
| `simple` | Simple English | `simple.wikipedia.org` |
| `be-tarask` | Belarusian (Taraškievica) | `be-tarask.wikipedia.org` |
| `cbk-zam` | Chavacano (Zamboangueño) | `cbk-zam.wikipedia.org` |
| `roa-rup` | Aromanian | `roa-rup.wikipedia.org` |
| `bat-smg` | Samogitian | `bat-smg.wikipedia.org` |

These are **not** BCP 47 valid — they are Wikimedia-specific identifiers.
Always treat them as opaque identifiers.

## How to Determine If a Language Code Exists

```python
import requests

def language_has_wikipedia(lang_code: str) -> bool:
    """Check if a language code has a Wikipedia edition."""
    resp = requests.get(
        f"https://{lang_code}.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "meta": "siteinfo",
            "siprop": "general",
            "format": "json",
        },
        headers={"User-Agent": "LangCheck/1.0 (contact) ContentGapResearch"},
        timeout=10,
    )
    return resp.status_code == 200


def get_all_wikipedia_languages() -> dict:
    """Fetch all Wikipedia language editions from the API."""
    resp = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "sitematrix",
            "format": "json",
        },
        headers={"User-Agent": "LangCheck/1.0 (contact) ContentGapResearch"},
        timeout=30,
    )
    data = resp.json()
    languages = {}
    for site_group in data.get("sitematrix", {}).values():
        if isinstance(site_group, dict) and "site" in site_group:
            for site in site_group["site"]:
                if site.get("code") == "wiki":
                    lang = site_group.get("code", "")
                    domain = site.get("dbname", "").replace("_", ".")
                    languages[lang] = domain
    return languages
```

## Language-to-Domain Mapping

The general rule: `https://{lang}.wikipedia.org`

**Exceptions** (languages where the domain differs from the code):

| Code | Actual Domain |
|------|---------------|
| `simple` | `simple.wikipedia.org` |
| `be-tarask` | `be-tarask.wikipedia.org` |
| `cbk-zam` | `cbk-zam.wikipedia.org` |
| `roa-rup` | `roa-rup.wikipedia.org` |
| `bat-smg` | `bat-smg.wikipedia.org` |
| `srn` | `srn.wikipedia.org` |

For non-Wikipedia projects, the pattern is:
- `https://{lang}.wiktionary.org`
- `https://{lang}.wikisource.org`
- `https://{lang}.wikiquote.org`
- `https://{lang}.wikibooks.org`
- `https://{lang}.wikinews.org`
- `https://{lang}.wikiversity.org`
- `https://{lang}.wikivoyage.org`

Special cases:
- Commons: `https://commons.wikimedia.org` (no language subdomain)
- Wikidata: `https://www.wikidata.org` (no language subdomain)
- Meta: `https://meta.wikimedia.org` (no language subdomain)
- MediaWiki: `https://www.mediawiki.org` (no language subdomain)
- Incubator: `https://incubator.wikimedia.org`

## Accept-Language Header Format

```python
# Parsing Accept-Language from browser
accept_lang = "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5"

def parse_accept_language(header: str) -> list[tuple[str, float]]:
    """Parse Accept-Language header into sorted list of (code, quality)."""
    languages = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            code, q = part.split(";q=")
            languages.append((code.strip(), float(q)))
        else:
            languages.append((part, 1.0))
    return sorted(languages, key=lambda x: -x[1])
```
