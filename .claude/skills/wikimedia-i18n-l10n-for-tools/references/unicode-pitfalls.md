# Unicode Pitfalls for Wikimedia Tool Developers

Common Unicode issues that appear when working with Wikimedia APIs, page titles,
wikitext, and multilingual data — and how to handle them correctly.

## 1. Unicode Normalization (NFC vs. NFD)

**The problem:** The same character can be represented in multiple ways in Unicode.
For example, `é` can be a single codepoint (U+00E9, NFC) or two codepoints
(e + combining acute accent U+0301, NFD). MediaWiki **always normalizes titles to NFC**
before storing, but user input and external data may be in NFD.

**Where it bites:**
- API title comparisons: `Spielberg\u0301` ≠ `Spielberg\u00e9` without normalization
- SPARQL queries with non-NFC strings
- User-submitted search terms
- File upload filenames on Commons

**Fix:**

```python
import unicodedata

def normalize_title(title: str) -> str:
    """Normalize a wiki page title to NFC (MediaWiki standard)."""
    return unicodedata.normalize("NFC", title)

# Always normalize before comparing with API results
user_input = "Spielberg\u0301"  # NFD: e + combining acute
api_title = "Spielberg\u00e9"   # NFC: é as single codepoint
assert normalize_title(user_input) == api_title
```

## 2. Case Folding and Title Normalization

**The problem:** MediaWiki page titles are case-insensitive for the first character
but case-sensitive for the rest. Also, MediaWiki applies its own normalization:
underscores ↔ spaces, multiple spaces collapsed, Unicode NFKC normalization.

**Where it bites:**
- Comparing user-provided titles against API responses
- Building cache keys from titles
- URL construction

**Fix:** Use the Action API's `normalize` property or the `format=json&redirects=1`
parameter to let MediaWiki normalize titles for you.

```python
import unicodedata

def mediawiki_normalize(title: str) -> str:
    """Apply MediaWiki's title normalization rules."""
    # 1. Strip whitespace
    title = title.strip()
    # 2. Collapse multiple spaces
    import re
    title = re.sub(r" +", " ", title)
    # 3. Replace spaces with underscores (or keep spaces — depends on context)
    # 4. NFC normalize
    title = unicodedata.normalize("NFC", title)
    return title

# Better: let the API do it
params = {
    "action": "query",
    "titles": "user input with spaces__and underscores",
    "redirects": 1,
    "format": "json",
}
```

## 3. Zero-Width Characters and Confusables

**The problem:** Unicode contains invisible characters that can be used for
spoofing, vandalism, or simply appear in copied text:

| Character | Codepoint | Name | Risk |
|-----------|-----------|------|------|
| `\u200B` | U+200B | Zero-width space | Invisible, breaks title matching |
| `\u200C` | U+200C | Zero-width non-joiner | Invisible, appears in Persian/Arabic |
| `\u200D` | U+200D | Zero-width joiner | Invisible, appears in emoji sequences |
| `\u200E` | U+200E | Left-to-right mark | Invisible, affects bidi |
| `\u200F` | U+200F | Right-to-left mark | Invisible, affects bidi |
| `\uFEFF` | U+FEFF | BOM / Zero-width no-break space | Often at start of files |
| `\u202E` | U+202E | Right-to-left override | **Can reverse display of text** |
| `\u202D` | U+202D | Left-to-right override | Can reverse display of text |

**Where it bites:**
- Page title comparison failing because invisible characters differ
- Vandalism: inserting RTL override in infoboxes to make text appear reversed
- Content copied from PDFs or word processors often has zero-width spaces

**Fix:**

```python
import re
import unicodedata

# Strip invisible characters from user-supplied titles
INVISIBLE = re.compile(
    "[\u200B\u200C\u200D\u200E\u200F\uFEFF\u2060\u2061\u2062\u2063\u2064"
    "\u2066\u2067\u2068\u2069\u202A\u202B\u202C\u202D\u202E\u202F]"
)

def strip_invisible(text: str) -> str:
    """Remove invisible Unicode characters."""
    return INVISIBLE.sub("", text)

# Also normalize
def clean_title(title: str) -> str:
    """Clean a title for safe API use."""
    title = strip_invisible(title)
    title = unicodedata.normalize("NFC", title)
    return title.strip()
```

## 4. Combining Characters and Grapheme Clusters

**The problem:** Some scripts use combining characters that change preceding
letters. In Python, `len("नमस्ते")` returns more characters than a user expects
because of combining vowel signs. Slicing strings by codepoint can break
grapheme clusters.

**Where it bites:**
- Truncating text in the middle of a grapheme cluster
- Counting "characters" for display limits
- Regex patterns that assume one codepoint = one character

**Fix:**

```python
# Python 3.14+ has grapheme cluster support via re and unicodedata
# For older versions, use the `grapheme` library

def grapheme_length(text: str) -> int:
    """Count visible grapheme clusters, not codepoints."""
    # Simple approximation (not perfect for all scripts):
    # Count base characters, ignoring combining marks
    import unicodedata
    count = 0
    for char in text:
        if unicodedata.combining(char) == 0:
            count += 1
    return count


def safe_truncate(text: str, max_graphemes: int) -> str:
    """Truncate at grapheme cluster boundary."""
    result = []
    count = 0
    for char in text:
        if unicodedata.combining(char) == 0:
            if count >= max_graphemes:
                break
            count += 1
        result.append(char)
    return "".join(result)
```

## 5. Right-to-Left Override Characters

**The problem:** U+202E (RIGHT-TO-LEFT OVERRIDE) and U+202D (LEFT-TO-RIGHT OVERRIDE)
force text direction regardless of the surrounding context. Malicious users can
insert these to make text display in reverse order.

**Where it bites:**
- Wikipedia infobox vandalism
- User-generated content that includes these characters
- Log output that looks correct in plain text but reverses in a browser

**Example of spoofing:**
```python
# This would make "harmless.exe" display as "exe.esselmrah"
spoofed = "harmless.exe\u202E"  # The RTL override reverses following text
```

**Fix:** Always strip U+202A–U+202F and U+2066–U+2069 from user-supplied text
before sending to the API or displaying in a tool.

## 6. URL Encoding vs. UTF-8 vs. Percent Encoding

**The problem:** Wikimedia APIs use different encoding conventions depending on
the endpoint. Page titles with special characters need careful handling.

| Encoding | Example | API Context |
|----------|---------|-------------|
| Percent-encoded UTF-8 | `Caf%C3%A9` | REST API URLs, MediaWiki API query strings |
| Raw UTF-8 | `Café` | Action API `titles=` parameter (API handles encoding) |
| Punycode (IDN) | `xn--caf-dma` | Interwiki links to non-ASCII domains |

**Where it bites:**
- Mixing up percent-encoded and raw titles when chaining APIs
- Constructing URLs manually instead of using `urllib.parse.urlencode`
- Comparing titles from different API responses that use different encoding

**Fix:**

```python
from urllib.parse import quote, unquote, urlencode

# Action API: pass raw Unicode, the API handles encoding
params = {"action": "query", "titles": "Café", "format": "json"}

# REST API: percent-encode manually
title = "Café"
safe_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"

# For comparison, always decode percent-encoding first
title_from_url = unquote("Caf%C3%A9")  # → "Café"
```

## 7. Punycode/IDN in Interwiki Links

**The problem:** Some Wikimedia wikis have non-ASCII domain names that use
Punycode encoding. For example, the Cyrillic Wikipedia subdomain
`https://ру.wikipedia.org` is also accessible as `https://xn--h1ayg.wikipedia.org`.

**Where it bites:**
- Constructing URLs from language codes programmatically
- Parsing interwiki links that use internationalized domain names
- Comparing domain names from different sources

**Fix:**
```python
# Use the simple ASCII domain when possible
# Non-ASCII subdomains may not resolve in all environments
domain = f"https://{lang}.wikipedia.org"  # lang = "ru" → https://ru.wikipedia.org

# For scripts that need IDN support, use Python's idna module
import idna
domain_idn = idna.encode("ру.wikipedia.org").decode("ascii")
# → "xn--h1ayg.wikipedia.org"
```

## 8. Bidi in JSON and API Responses

**The problem:** When viewing JSON responses containing RTL text in a terminal or
log, characters can appear in unexpected order because of the Unicode bidi
algorithm combined with the LTR context of JSON.

**Where it bites:**
- Debugging API responses with mixed RTL/LTR content
- Log file analysis
- Test assertions on text containing RTL characters

**Fix:**
```python
import json

def debug_json(data: dict) -> str:
    """Print JSON with RTL markers for debugging."""
    text = json.dumps(data, indent=2, ensure_ascii=False)
    # Wrap RTL segments with Unicode bidi markers for clarity
    return text

# Better: isolate RTL values during debugging
for key, value in data.items():
    if isinstance(value, str) and any('\u0600' <= c <= '\u06FF' for c in value):
        print(f"{key}: <RTL> {value!r} </RTL>")
    else:
        print(f"{key}: {value!r}")
```
