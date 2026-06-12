"""
i18n utilities for Wikimedia tool builders — language detection, fallback,
title normalization, language→domain mapping, and Accept-Language parsing.

Usage:
    from i18n_utils import (
        detect_language,
        resolve_fallback,
        normalize_language_code,
        language_code_to_bcp47,
        normalize_title,
        language_to_domain,
        domain_to_language,
        parse_accept_language,
        get_preferred_language,
    )

    # Detect user's language
    lang = detect_language("fr-CH, fr;q=0.9, en;q=0.8")
    # → "fr"

    # Resolve fallback chain
    chain = resolve_fallback("pt-br")
    # → ["pt-br", "pt", "es", "en"]

    # Normalize a language code (handles aliases like zh-yue→yue, no→nb)
    code = normalize_language_code("zh-yue")
    # → "yue"

    # Convert to BCP 47 tag
    tag = language_code_to_bcp47("simple")
    # → "en-simple"

    # Normalize a page title to MediaWiki standard (NFC)
    title = normalize_title("Spielberg\\u0301")
    # → "Spielberg\\u00e9"

    # Get wiki domain for a language
    domain = language_to_domain("fr")
    # → "fr.wikipedia.org"
"""

import logging
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

# Wikimedia language fallback chains (source: MediaWiki i18n)
# Maps language code → ordered fallback list (last = ultimate fallback)
FALLBACK_CHAINS: Dict[str, List[str]] = {
    # Romance
    "fr": ["en"], "es": ["en"], "it": ["en"],
    "pt": ["es", "en"], "pt-br": ["pt", "es", "en"],
    "ro": ["en"], "ca": ["en"],
    "gl": ["pt", "es", "en"], "oc": ["fr", "en"],
    "ast": ["es", "en"], "ext": ["es", "en"],
    "mwl": ["pt", "es", "en"],
    "pms": ["it", "fr", "en"], "fur": ["it", "en"],
    "lmo": ["it", "en"], "nap": ["it", "en"],
    "scn": ["it", "en"], "vec": ["it", "en"],
    "co": ["fr", "it", "en"],
    # Germanic
    "de": ["en"], "nl": ["en"],
    "sv": ["en"], "da": ["en"],
    "no": ["nb"], "nb": ["nn", "en"], "nn": ["nb", "no", "en"],
    "is": ["en"], "fo": ["da", "en"],
    "fy": ["nl", "en"], "nds": ["de", "en"],
    "nds-nl": ["nds", "nl", "en"],
    "li": ["nl", "en"], "zea": ["nl", "en"],
    # Slavic
    "ru": ["en"], "pl": ["en"],
    "uk": ["ru", "en"], "cs": ["en"],
    "sk": ["cs", "en"], "bg": ["en"],
    "sr": ["en"], "sh": ["sr", "hr", "bs", "en"],
    "hr": ["en"], "bs": ["hr", "en"],
    "sl": ["en"], "mk": ["en"],
    "be": ["ru", "en"], "be-tarask": ["be", "ru", "en"],
    "rue": ["uk", "ru", "en"], "szl": ["pl", "en"],
    "dsb": ["de", "en"], "hsb": ["dsb", "de", "en"],
    "cu": ["ru", "en"],
    # Uralic
    "fi": ["en"], "et": ["en"], "hu": ["en"],
    "se": ["nb", "fi", "en"], "smn": ["fi", "en"],
    # Baltic
    "lt": ["en"], "lv": ["en"], "sgs": ["lt", "en"],
    # Hellenic
    "el": ["en"],
    # Celtic
    "ga": ["en"], "gd": ["en"], "cy": ["en"],
    "br": ["fr", "en"], "kw": ["en"], "gv": ["en"],
    # Semitic
    "ar": ["en"], "he": ["en"], "fa": ["en"],
    "ps": ["en"], "ur": ["en"],
    "ckb": ["ar", "en"],
    "am": ["en"],
    # Turkic
    "tr": ["en"], "az": ["en"],
    "azb": ["az", "tr", "en"],
    "uz": ["en"], "kk": ["ru", "en"],
    "ky": ["ru", "en"], "crh": ["tr", "en"],
    "tk": ["en"], "tt": ["ru", "en"],
    "ba": ["ru", "en"], "sah": ["ru", "en"],
    # East Asian
    "ja": ["en"], "ko": ["en"],
    "zh": ["en"], "yue": ["zh-hant", "zh", "en"],
    "zh-hans": ["zh", "en"], "zh-hant": ["zh", "en"],
    "zh-cn": ["zh-hans", "zh", "en"],
    "zh-tw": ["zh-hant", "zh", "en"],
    "zh-hk": ["zh-hant", "zh", "en"],
    # Southeast Asian
    "th": ["en"], "vi": ["en"],
    "lo": ["th", "en"], "km": ["en"],
    "my": ["en"], "mn": ["ru", "en"],
    "bo": ["zh", "en"],
    # South Asian
    "hi": ["en"], "bn": ["en"],
    "ta": ["en"], "te": ["en"], "kn": ["en"],
    "ml": ["en"], "mr": ["en"], "gu": ["en"],
    "pa": ["en"], "or": ["en"],
    "as": ["bn", "en"], "ne": ["hi", "en"],
    "si": ["en"], "sd": ["en"],
    "ks": ["ur", "en"], "pi": ["hi", "en"],
    "sa": ["hi", "en"],
    "dty": ["ne", "hi", "en"],
    "mai": ["hi", "en"], "gom": ["hi", "en"],
    # African
    "af": ["nl", "en"], "sw": ["en"],
    "xh": ["af", "en"], "zu": ["af", "en"],
    "st": ["af", "en"], "tn": ["af", "en"],
    "nso": ["af", "en"], "ss": ["af", "en"],
    "rw": ["en"], "rn": ["en"], "sn": ["en"],
    "mg": ["fr", "en"], "mt": ["en"],
    "eu": ["es", "en"], "ht": ["fr", "en"],
    "jv": ["id", "en"], "su": ["id", "en"],
    "min": ["id", "en"], "ace": ["id", "en"],
    "bug": ["id", "en"], "bjn": ["id", "en"],
    "map-bms": ["jv", "id", "en"],
    "sg": ["fr", "en"], "ln": ["fr", "en"],
    "lg": ["en"],
}

# RTL languages
RTL_LANGUAGES = {"ar", "he", "fa", "ps", "ur", "sd", "ckb", "yi", "dv", "arc"}

# Language → Wikimedia wiki domain
# Non-Wikipedia: wiktionary, wikisource, wikiquote, wikibooks, wikinews, wikiversity, wikivoyage
WIKI_PROJECTS = ["wikipedia", "wiktionary", "wikisource", "wikiquote",
                 "wikibooks", "wikinews", "wikiversity", "wikivoyage"]

# Languages whose domain differs from the language code
SPECIAL_DOMAINS = {
    "simple": "simple.wikipedia.org",
    "be-tarask": "be-tarask.wikipedia.org",
    "cbk-zam": "cbk-zam.wikipedia.org",
    "roa-rup": "roa-rup.wikipedia.org",
    "bat-smg": "bat-smg.wikipedia.org",
    "srn": "srn.wikipedia.org",
}

# Deprecated/alias language codes → canonical Wikimedia internal code
# Source: MediaWiki $wgDummyLanguageCodes
# These are codes that were renamed or never corresponded to a real interface language.
# When you receive one of these codes from any source, normalize to the canonical value.
DUMMY_LANGUAGE_CODES: Dict[str, str] = {
    "als": "gsw",              # Alemannic (was wrongly using ISO code for Tosk Albanian)
    "bat-smg": "sgs",          # Samogitian (deprecated code → ISO 639-3)
    "be-x-old": "be-tarask",   # Belarusian old orthography (renamed)
    "bh": "bho",               # Bihari → Bhojpuri
    "fiu-vro": "vro",          # Võro (deprecated code → ISO 639-3)
    "no": "nb",                # Norwegian macrolanguage → Bokmål
    "roa-rup": "rup",          # Aromanian (deprecated code → ISO 639-3)
    "simple": "en",            # Simple English → English (for internal API use)
    "zh-classical": "lzh",     # Classical Chinese (deprecated code → ISO 639-3)
    "zh-min-nan": "nan",       # Min Nan (deprecated code → ISO 639-3)
    "zh-yue": "yue",           # Cantonese (deprecated code → ISO 639-3)
}

# Canonical language code → valid BCP 47 tag
# Source: MediaWiki $wgExtraLanguageCodes
# Use these for HTML lang attributes, Accept-Language headers, and BCP 47 contexts.
EXTRA_LANGUAGE_CODES: Dict[str, str] = {
    "als": "gsw",
    "crh-cyrl": "crh-Cyrl",
    "crh-latn": "crh-Latn",
    "de-ch": "de-CH",
    "de-formal": "de-x-formal",
    "en-gb": "en-GB",
    "hu-formal": "hu-x-formal",
    "kk-arab": "kk-Arab",
    "kk-cyrl": "kk-Cyrl",
    "kk-latn": "kk-Latn",
    "kk-cn": "kk-Arab-CN",
    "kk-kz": "kk-Cyrl-KZ",
    "kk-tr": "kk-Latn-TR",
    "ku-arab": "ckb",         # Kurdish (Arabic script) → Central Kurdish
    "ku-latn": "ku-Latn",
    "nl-informal": "nl-x-informal",
    "simple": "en-simple",
    "sr-ec": "sr-Cyrl",
    "sr-el": "sr-Latn",
    "tg-cyrl": "tg-Cyrl",
    "tg-latn": "tg-Latn",
    "uz-cyrl": "uz-Cyrl",
    "uz-latn": "uz-Latn",
    "zh-hans": "zh-Hans",
    "zh-hant": "zh-Hant",
    "zh-cn": "zh-Hans-CN",
    "zh-hk": "zh-Hant-HK",
    "zh-mo": "zh-Hant-MO",
    "zh-my": "zh-Hans-MY",
    "zh-sg": "zh-Hans-SG",
    "zh-tw": "zh-Hant-TW",
}

# Non-standard Wikipedia subdomains — codes that exist as wiki URLs but differ
# from canonical ISO/BCP 47 codes. Includes codes still in active use.
# Source: https://meta.wikimedia.org/wiki/Special_language_codes
NON_STANDARD_WIKI_CODES: Dict[str, str] = {
    "als": "gsw",              # alemannische Wikipedia (uses ISO 639-3 gsw)
    "bat-smg": "sgs",          # Žemaitėška Wikipedia (Samogitian)
    "cbk-zam": "cbk-zam",      # Chavacano de Zamboanga (no ISO code)
    "eml": "egl",              # Emiliàn e rumagnòl (retired ISO, split to egl/rgn)
    "fiu-vro": "vro",          # Võro Wikipedia
    "iu": "iu",                # Inuktitut (ISO macrolanguage)
    "ksh": "ksh",              # Ripoarisch (ISO code is for Kölsch subset)
    "map-bms": "map-bms",       # Basa Banyumasan (no ISO code)
    "nds-nl": "nds-nl",         # Nedersaksies (Dutch Low Saxon)
    "nrm": "nrf",              # Nouormand (ISO code conflicts with Narom)
    "roa-rup": "rup",          # Armãneashti Wikipedia (Aromanian)
    "roa-tara": "roa-tara",     # Tarandíne (Tarantino, no ISO code)
    "sh": "sh",                # Srpskohrvatski (deprecated ISO 639-1, still valid BCP 47)
    "simple": "simple",         # Simple English (subdomain is the code)
    "srn": "srn",              # Sranan Tongo
    "zh-classical": "lzh",      # Classical Chinese (Wikipedia subdomain)
    "zh-min-nan": "nan",        # Min Nan (Wikipedia subdomain)
    "zh-yue": "yue",           # Cantonese (Wikipedia subdomain)
}

# Invisible characters that cause problems in Wikimedia APIs
INVISIBLE_CHARS = re.compile(
    "["
    "\u200B"  # Zero-width space
    "\u200C"  # Zero-width non-joiner
    "\u200D"  # Zero-width joiner
    "\u200E"  # Left-to-right mark
    "\u200F"  # Right-to-left mark
    "\uFEFF"  # BOM / Zero-width no-break space
    "\u2060"  # Word joiner
    "\u2061"  # Function application
    "\u2062"  # Invisible times
    "\u2063"  # Invisible separator
    "\u2064"  # Invisible plus
    "\u2066"  # Left-to-right isolate
    "\u2067"  # Right-to-left isolate
    "\u2068"  # First strong isolate
    "\u2069"  # Pop directional isolate
    "\u202A"  # Left-to-right embedding
    "\u202B"  # Right-to-left embedding
    "\u202C"  # Pop directional formatting
    "\u202D"  # Left-to-right override
    "\u202E"  # Right-to-left override
    "\u202F"  # Narrow no-break space
    "]"
)


def parse_accept_language(header: str) -> List[Tuple[str, float]]:
    """
    Parse an Accept-Language header into a sorted list of (code, quality).

    Args:
        header: The Accept-Language header value (e.g., "fr-CH, fr;q=0.9, en;q=0.8")

    Returns:
        List of (language_code, quality) sorted by quality descending
    """
    if not header:
        return []

    languages = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            code, q_str = part.split(";q=", 1)
            code = code.strip()
            try:
                q = float(q_str)
            except ValueError:
                q = 1.0
        else:
            code = part
            q = 1.0

        # Strip region subtag: "fr-CH" → "fr"
        lang = code.split("-")[0].lower() if "-" in code else code.lower()
        languages.append((lang, q))

    return sorted(languages, key=lambda x: -x[1])


def detect_language(
    accept_header: str,
    supported_languages: Optional[List[str]] = None,
) -> str:
    """
    Detect the best language from an Accept-Language header.

    Args:
        accept_header: Accept-Language header value
        supported_languages: List of languages your tool supports (or None for all)

    Returns:
        Best matching language code (defaults to "en")
    """
    parsed = parse_accept_language(accept_header)
    if not parsed:
        return "en"

    # Try each language in priority order (with fallback)
    for lang, _ in parsed:
        # Try exact match first
        if supported_languages is None or lang in supported_languages:
            return lang

        # Try fallback chain
        chain = resolve_fallback(lang)
        for fallback in chain:
            if supported_languages is None or fallback in supported_languages:
                return fallback

    return "en"


def resolve_fallback(lang: str) -> List[str]:
    """
    Resolve the full fallback chain for a language.

    Args:
        lang: Language code (e.g., "pt-br", "zh-cn", "fr")

    Returns:
        Ordered list: [lang, fallback1, fallback2, ..., "en"]
    """
    if lang == "en":
        return ["en"]

    chain = [lang]
    seen = {lang}
    current = lang

    while current != "en":
        fallbacks = FALLBACK_CHAINS.get(current, ["en"])
        found = False
        for fb in fallbacks:
            if fb not in seen:
                chain.append(fb)
                seen.add(fb)
                current = fb
                found = True
                break
            # If all fallbacks are already in chain, try the first one
            if not found:
                chain.append("en")
                current = "en"
        if not found:
            chain.append("en")
            break

    return chain


def is_rtl(lang: str) -> bool:
    """Check if a language is right-to-left."""
    return lang.split("-")[0].lower() in RTL_LANGUAGES


def normalize_language_code(code: str) -> str:
    """
    Normalize a language code to the canonical Wikimedia internal code.

    Resolves deprecated aliases, legacy codes, and common alternate codes
    to the canonical code that Wikimedia APIs expect.

    Based on MediaWiki's $wgDummyLanguageCodes configuration, which captures
    all historical renames and code reassignments.

    Args:
        code: A language code from any source (e.g., "zh-yue", "no", "bat-smg")

    Returns:
        Canonical Wikimedia language code (e.g., "yue", "nb", "sgs")

    Examples:
        >>> normalize_language_code("zh-yue")
        "yue"
        >>> normalize_language_code("yue")
        "yue"
        >>> normalize_language_code("no")
        "nb"
        >>> normalize_language_code("nb")
        "nb"
        >>> normalize_language_code("bat-smg")
        "sgs"
        >>> normalize_language_code("simple")
        "en"
        >>> normalize_language_code("en")
        "en"
        >>> normalize_language_code("zh-classical")
        "lzh"
    """
    if not code:
        return code

    lower = code.lower().strip()

    # 1. Direct alias lookup (handles zh-yue→yue, no→nb, etc.)
    if lower in DUMMY_LANGUAGE_CODES:
        return DUMMY_LANGUAGE_CODES[lower]

    # 2. Already canonical
    return lower


def language_code_to_bcp47(code: str) -> str:
    """
    Convert a Wikimedia language code to a valid BCP 47 language tag.

    BCP 47 tags are used for HTML lang attributes, Accept-Language headers,
    and other standards-compliant contexts. Wikimedia uses mostly ISO 639
    codes internally, but some codes need BCP 47 formatting (e.g., script
    variants like sr-ec → sr-Cyrl, region variants like zh-cn → zh-Hans-CN).

    Based on MediaWiki's $wgExtraLanguageCodes and LanguageCode::bcp47().

    Args:
        code: A Wikimedia language code (e.g., "simple", "zh-cn", "sr-ec")

    Returns:
        BCP 47 language tag (e.g., "en-simple", "zh-Hans-CN", "sr-Cyrl")

    Examples:
        >>> language_code_to_bcp47("simple")
        "en-simple"
        >>> language_code_to_bcp47("zh-cn")
        "zh-Hans-CN"
        >>> language_code_to_bcp47("zh-tw")
        "zh-Hant-TW"
        >>> language_code_to_bcp47("sr-ec")
        "sr-Cyrl"
        >>> language_code_to_bcp47("sr")
        "sr"
        >>> language_code_to_bcp47("en")
        "en"
        >>> language_code_to_bcp47("yue")
        "yue"
    """
    if not code:
        return code

    lower = code.lower().strip()

    # 1. Check the original code against EXTRA_LANGUAGE_CODES first
    #    (e.g., "simple" has BCP 47 "en-simple" but normalizes to "en")
    if lower in EXTRA_LANGUAGE_CODES:
        return EXTRA_LANGUAGE_CODES[lower]

    # 2. Normalize to canonical internal code (e.g., zh-yue → yue)
    canonical = normalize_language_code(lower)

    # 3. Look up BCP 47 mapping for the canonical code
    if canonical in EXTRA_LANGUAGE_CODES:
        return EXTRA_LANGUAGE_CODES[canonical]

    # 4. BCP 47 casing rules:
    #    - First subtag (language): lowercase
    #    - Second subtag (script, 4 chars): title case
    #    - Second subtag (region, 2 chars): uppercase
    #    - All other subtags: lowercase
    parts = canonical.split("-")
    bcp47_parts = []
    for i, part in enumerate(parts):
        if i == 0:
            bcp47_parts.append(part.lower())
        elif len(part) == 4:
            bcp47_parts.append(part[0].upper() + part[1:].lower())
        elif len(part) == 2:
            bcp47_parts.append(part.upper())
        else:
            bcp47_parts.append(part.lower())

    return "-".join(bcp47_parts)


def language_to_domain(lang: str, project: str = "wikipedia") -> str:
    """
    Convert a language code to a Wikimedia wiki domain.

    Handles the full chain:
    1. Normalizes alias codes (zh-yue → yue, no → nb)
    2. Checks SPECIAL_DOMAINS for non-standard subdomains
    3. Falls back to the standard {code}.{project}.org pattern

    Args:
        lang: Language code (e.g., "fr", "de", "simple", "zh-yue")
        project: Project type (wikipedia, wiktionary, wikisource, etc.)

    Returns:
        Full domain (e.g., "fr.wikipedia.org")
    """
    if project == "commons":
        return "commons.wikimedia.org"
    if project == "wikidata":
        return "www.wikidata.org"
    if project == "meta":
        return "meta.wikimedia.org"
    if project == "mediawiki":
        return "www.mediawiki.org"

    # Normalize the language code first
    normalized = normalize_language_code(lang)

    # Check for special domains (non-standard Wikipedia subdomains)
    if normalized in SPECIAL_DOMAINS and project == "wikipedia":
        return SPECIAL_DOMAINS[normalized]

    # Check if the original code (before normalization) maps to a special domain
    low_lang = lang.lower().strip()
    if low_lang != normalized and low_lang in SPECIAL_DOMAINS and project == "wikipedia":
        return SPECIAL_DOMAINS[low_lang]

    return f"{normalized}.{project}.org"


def domain_to_language(domain: str) -> Optional[str]:
    """
    Extract the language code from a Wikimedia wiki domain.

    Args:
        domain: Wiki domain (e.g., "fr.wikipedia.org", "commons.wikimedia.org")

    Returns:
        Language code or None for project wikis (Commons, Wikidata, Meta)
    """
    project_domains = {
        "commons.wikimedia.org": None,
        "www.wikidata.org": None,
        "meta.wikimedia.org": None,
        "www.mediawiki.org": None,
        "incubator.wikimedia.org": None,
    }

    if domain in project_domains:
        return None

    # Reverse lookup for special domains
    for lang, special_domain in SPECIAL_DOMAINS.items():
        if domain == special_domain:
            return lang

    # General pattern: {lang}.{project}.org
    match = re.match(r"^([a-z0-9-]+)\.", domain)
    if match:
        return match.group(1)

    return None


def normalize_title(title: str) -> str:
    """
    Normalize a page title to MediaWiki standard.

    MediaWiki stores titles in NFC Unicode normalization, with underscores
    representing spaces and the first letter capitalized.

    Args:
        title: Raw title (may have spaces, invisible chars, non-NFC)

    Returns:
        NFC-normalized title with invisible characters stripped
    """
    # Strip invisible characters
    title = INVISIBLE_CHARS.sub("", title)
    # NFC normalize
    title = unicodedata.normalize("NFC", title)
    # Strip leading/trailing whitespace
    title = title.strip()
    return title


def strip_invisible(text: str) -> str:
    """Remove invisible Unicode characters from text."""
    return INVISIBLE_CHARS.sub("", text)


def get_preferred_language(
    accept_header: str,
    supported_languages: List[str],
    default: str = "en",
) -> str:
    """
    Get the user's preferred language with fallback support.

    This handles the full resolution: user preference → region code →
    language without region → fallback chain → supported languages → default.

    Args:
        accept_header: Accept-Language header
        supported_languages: Languages your tool supports
        default: Fallback language (default "en")

    Returns:
        Best matching supported language
    """
    if not accept_header:
        return default

    parsed = parse_accept_language(accept_header)

    # 1. Try exact match
    for lang, _ in parsed:
        if lang in supported_languages:
            return lang

    # 2. Try base language (fr-CH → fr)
    for lang, _ in parsed:
        base = lang.split("-")[0]
        if base in supported_languages:
            return base

    # 3. Try fallback chain for each
    for lang, _ in parsed:
        chain = resolve_fallback(lang.split("-")[0])
        for fb in chain:
            if fb in supported_languages:
                return fb

    return default


def validate_language_code(code: str) -> bool:
    """
    Validate that a language code is a known Wikimedia language code.

    Checks against ISO 639-1, ISO 639-3, known special codes, and
    deprecated/alias codes (which are valid inputs even if they resolve
    to a different canonical code).

    Args:
        code: Language code to validate

    Returns:
        True if the code is known or can be normalized to a known code
    """
    if not code:
        return False

    # Normalize first — if the alias itself maps somewhere, it's valid
    normalized = normalize_language_code(code)

    # English is always valid
    if normalized == "en":
        return True

    # Check if it's a known dummy/alias code (valid even before normalization)
    # e.g., "zh-yue", "no", "bat-smg" are valid inputs even though they resolve away
    low_code = code.lower().strip()
    if low_code in DUMMY_LANGUAGE_CODES:
        return True

    # Check special non-standard Wikimedia wiki codes
    special_codes = {
        "simple", "be-tarask", "cbk-zam", "roa-rup", "roa-tara",
        "bat-smg", "srn", "eml", "map-bms", "nds-nl", "nrm", "sh",
    }
    if normalized in special_codes or low_code in special_codes:
        return True

    # Check if it has a known fallback chain (covers most major languages)
    if normalized in FALLBACK_CHAINS:
        return True

    # Check base code
    base = normalized.split("-")[0]
    if base in FALLBACK_CHAINS:
        return True

    # Check non-standard wiki codes with fallback chains
    if normalized in {"gsw", "vro", "rup", "lzh", "nan", "sgs"}:
        return True
    if low_code in {"gsw", "vro", "rup", "lzh", "nan", "sgs"}:
        return True

    return False


# ---- CLI ----
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Wikimedia i18n utilities")
    sub = parser.add_subparsers(dest="command")

    # detect
    detect_p = sub.add_parser("detect", help="Detect language from Accept-Language header")
    detect_p.add_argument("header", help="Accept-Language header value")

    # fallback
    fb_p = sub.add_parser("fallback", help="Resolve language fallback chain")
    fb_p.add_argument("lang", help="Language code")

    # domain
    dom_p = sub.add_parser("domain", help="Convert language code to wiki domain")
    dom_p.add_argument("lang", help="Language code")
    dom_p.add_argument("--project", default="wikipedia",
                       choices=["wikipedia", "wiktionary", "wikisource",
                                "wikiquote", "wikibooks", "wikinews"])

    # normalize-code
    normc_p = sub.add_parser("normalize-code", help="Normalize a language code")
    normc_p.add_argument("code", help="Language code to normalize (e.g., zh-yue, no)")

    # bcp47
    bcp_p = sub.add_parser("bcp47", help="Convert language code to BCP 47 tag")
    bcp_p.add_argument("code", help="Language code (e.g., simple, zh-cn)")

    # normalize
    norm_p = sub.add_parser("normalize", help="Normalize a page title")
    norm_p.add_argument("title", help="Raw page title")

    # rtl
    rtl_p = sub.add_parser("rtl", help="Check if language is RTL")
    rtl_p.add_argument("lang", help="Language code")

    args = parser.parse_args()

    if args.command == "detect":
        result = detect_language(args.header)
        print(result)
    elif args.command == "fallback":
        chain = resolve_fallback(args.lang)
        print(" → ".join(chain))
    elif args.command == "domain":
        domain = language_to_domain(args.lang, args.project)
        print(domain)
    elif args.command == "normalize-code":
        canonical = normalize_language_code(args.code)
        bcp47 = language_code_to_bcp47(args.code)
        print(f"Canonical: {canonical}")
        print(f"BCP 47:    {bcp47}")
    elif args.command == "bcp47":
        tag = language_code_to_bcp47(args.code)
        print(tag)
    elif args.command == "normalize":
        normalized = normalize_title(args.title)
        print(normalized)
    elif args.command == "rtl":
        print("yes" if is_rtl(args.lang) else "no")
    else:
        parser.print_help()
