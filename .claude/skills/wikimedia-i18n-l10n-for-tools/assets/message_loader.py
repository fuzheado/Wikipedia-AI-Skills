"""
Message file loader with language fallback for Wikimedia tool builders.

Supports JSON message files (.json), ICU MessageFormat, and MediaWiki-style
i18n with full fallback chain resolution.

Usage:
    from message_loader import I18nMessages

    # Load messages for all supported languages
    i18n = I18nMessages("messages/", supported_languages=["en", "fr", "de", "ar"])

    # Get a message in the user's language (with fallback)
    msg = i18n.get("welcome", lang="fr")
    # → "Bienvenue sur notre outil"

    # Message with variables
    msg = i18n.get("greeting", lang="de", name="Alice")
    # → "Hallo, Alice!"

    # Plural forms
    msg = i18n.get_plural("results", count=5, lang="fr")
    # → "5 résultats"

    # Format numbers per locale
    num = i18n.format_number(1234567.89, lang="de")
    # → "1.234.567,89"
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from i18n_utils import resolve_fallback, is_rtl

logger = logging.getLogger(__name__)


# Simple ICU MessageFormat-style pattern compiler
# Supports: {variable}, {variable, plural, one {...} other {...}}
# This is a minimal implementation. For full ICU support, use the `icu` package.
_ICU_PLURAL = re.compile(
    r"\{(\w+),\s*plural,\s*(.+?)\}",
    re.DOTALL,
)
_ICU_OPTIONS = re.compile(r"(\w+)\s*\{(.*?)\}", re.DOTALL)


def _format_plural(count: int, pattern: str, lang: str) -> str:
    """Format an ICU plural pattern with the given count."""
    def _choose_plural(match: re.Match) -> str:
        var_name = match.group(1)
        options_text = match.group(2)

        # Parse options: "one {text} other {text}"
        options = {}
        for opt_match in _ICU_OPTIONS.finditer(options_text):
            key = opt_match.group(1).strip()
            value = opt_match.group(2).strip()
            options[key] = value

        # Determine plural category
        plural = _get_plural_category(count, lang)
        # Fallback: other → one → (nothing)
        for cat in [plural, "other", "one"]:
            if cat in options:
                result = options[cat]
                # Replace {var_name} placeholder (e.g., {count})
                result = result.replace("{" + var_name + "}", str(count))
                # Replace ICU # placeholder (standard ICU syntax for count)
                result = result.replace("#", str(count))
                return result
        return str(count)

    return _ICU_PLURAL.sub(_choose_plural, pattern)


def _get_plural_category(count: int, lang: str) -> str:
    """
    Get the plural category for a count in a given language.

    Simplified plural rules for common languages. Wikimedia CLDR-based rules
    are more complex; this covers the most common cases.
    """
    # Languages with one/other (most common)
    one_other = {
        "en", "de", "nl", "da", "sv", "nb", "nn", "fo",
        "es", "pt", "it", "ca", "gl",
        "el",
        "he",
        "ar",  # Arabic actually has 6 forms, simplified here
        "fa",
        "tr",
        "az",
        "et", "fi",
        "hu",
        "id",
        "ja",
        "ko",
        "th",
        "vi",
        "zh",
        "ms",
    }

    # Languages with one/few/many/other (Slavic)
    slavic = {"ru", "uk", "be", "sr", "hr", "bs", "mk", "bg"}

    # Languages with one/two/few/many/other (Celtic)
    celtic = {"ga", "gd", "cy", "br"}

    if lang.split("-")[0] in slavic:
        mod10 = count % 10
        mod100 = count % 100
        if mod10 == 1 and mod100 != 11:
            return "one"
        if 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
            return "few"
        return "many" if mod10 in (0, 5, 6, 7, 8, 9) or 11 <= mod100 <= 14 else "other"

    if lang in celtic:
        if count == 1:
            return "one"
        if count == 2:
            return "two"
        if 3 <= count <= 6:
            return "few"
        if 7 <= count <= 10:
            return "many"
        return "other"

    if lang.split("-")[0] in one_other:
        return "one" if count == 1 else "other"

    # Default: one/other
    return "one" if count == 1 else "other"


class I18nMessages:
    """
    Load and access translated messages with full fallback support.

    Message files should be structured as:
        messages/en.json
        messages/fr.json
        messages/de.json
        messages/ar.json

    Each file is a flat JSON object of message keys to message values.
    Values can use ICU MessageFormat-style {variable} and {x, plural, ...} syntax.
    """

    def __init__(
        self,
        messages_dir: str,
        supported_languages: Optional[List[str]] = None,
        default_language: str = "en",
    ):
        """
        Initialize the message loader.

        Args:
            messages_dir: Directory containing language JSON files
            supported_languages: List of language codes your tool supports
            default_language: Fallback language when nothing matches
        """
        self.messages_dir = Path(messages_dir)
        self.default_language = default_language
        self._messages: Dict[str, Dict[str, str]] = {}
        self._loaded_languages: List[str] = []

        if supported_languages:
            for lang in supported_languages:
                self.load_language(lang)
        else:
            # Auto-discover available languages
            self._discover_languages()

    def _discover_languages(self) -> None:
        """Auto-discover available message files."""
        if not self.messages_dir.exists():
            logger.warning(f"Messages directory not found: {self.messages_dir}")
            return
        for fpath in sorted(self.messages_dir.glob("*.json")):
            lang = fpath.stem
            self.load_language(lang)

    def load_language(self, lang: str) -> bool:
        """
        Load messages for a specific language from a JSON file.

        Args:
            lang: Language code

        Returns:
            True if messages were loaded
        """
        path = self.messages_dir / f"{lang}.json"
        if not path.exists():
            logger.debug(f"No message file for {lang}: {path}")
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                messages = json.load(f)
            self._messages[lang] = messages
            if lang not in self._loaded_languages:
                self._loaded_languages.append(lang)
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading messages for {lang}: {e}")
            return False

    def get(
        self,
        key: str,
        lang: Optional[str] = None,
        default: Optional[str] = None,
        **variables,
    ) -> str:
        """
        Get a message in the best available language.

        Resolves through the full fallback chain: requested language →
        fallback chain → default language → key itself as fallback.

        Args:
            key: Message key
            lang: Requested language (or None for default)
            default: Fallback text if key is not found
            **variables: Variables to substitute into the message

        Returns:
            The formatted message string
        """
        lang = lang or self.default_language
        chain = resolve_fallback(lang)

        # Try each language in the fallback chain
        for fb_lang in chain:
            if fb_lang in self._messages and key in self._messages[fb_lang]:
                pattern = self._messages[fb_lang][key]
                return self._format(pattern, variables, fb_lang)

        # Try default language
        if self.default_language in self._messages and key in self._messages[self.default_language]:
            pattern = self._messages[self.default_language][key]
            return self._format(pattern, variables, self.default_language)

        # Ultimate fallback: use the key itself or the provided default
        fallback = default if default is not None else key
        if variables:
            return self._simple_format(fallback, variables)
        return fallback

    def get_plural(
        self,
        key: str,
        count: int,
        lang: Optional[str] = None,
        **variables,
    ) -> str:
        """
        Get a message with pluralization support.

        The message value should use ICU MessageFormat plural syntax:
            "{count, plural, one {# result} other {# results}}"

        Args:
            key: Message key
            count: The count for pluralization
            lang: Requested language
            **variables: Additional variables

        Returns:
            The formatted message with plural resolved
        """
        variables["count"] = count
        msg = self.get(key, lang=lang, **variables)

        # Handle ICU plural patterns in the result
        if "{count, plural," in msg or "{count,plural," in msg:
            msg = _format_plural(count, msg, lang or self.default_language)

        return msg

    def _format(self, pattern: str, variables: dict, lang: str) -> str:
        """Format a message pattern with variables and ICU plural support."""
        if not variables:
            return pattern

        # Handle ICU plural patterns
        if re.search(r"\{\w+,\s*plural,\s*", pattern):
            # Find and process each plural pattern
            pattern = _ICU_PLURAL.sub(
                lambda m: _format_plural(
                    int(variables.get(m.group(1), 0)),
                    m.group(0),
                    lang,
                ),
                pattern,
            )

        # Simple {variable} substitution (for remaining variables)
        return self._simple_format(pattern, variables)

    @staticmethod
    def _simple_format(text: str, variables: dict) -> str:
        """Simple {variable} substitution."""
        for key, value in variables.items():
            text = text.replace("{" + key + "}", str(value))
        return text

    def format_number(
        self,
        number: float,
        lang: Optional[str] = None,
        decimals: int = 2,
    ) -> str:
        """
        Format a number according to a language's locale conventions.

        This is a simplified formatter. For full CLDR support, use
        Python's `locale` module or the `babel` library.

        Args:
            number: Number to format
            lang: Language for formatting
            decimals: Number of decimal places

        Returns:
            Locale-formatted number string
        """
        lang = lang or self.default_language
        formatted = f"{number:,.{decimals}f}"

        # Language-specific formatting
        lang_base = lang.split("-")[0]

        # Languages using comma as decimal separator and period as thousands sep
        european = {"de", "fr", "it", "es", "nl", "pt", "ro", "sv", "no",
                     "da", "fi", "pl", "cs", "sk", "hu", "ru", "uk", "bg",
                     "sr", "hr", "sl", "el", "tr", "is"}

        if lang_base in european:
            formatted = (
                formatted
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        return formatted

    def available_languages(self) -> List[str]:
        """Get list of loaded languages."""
        return list(self._loaded_languages)

    def has_key(self, key: str, lang: Optional[str] = None) -> bool:
        """Check if a message key exists (in any loaded language or specific one)."""
        if lang:
            return lang in self._messages and key in self._messages[lang]
        return any(key in msgs for msgs in self._messages.values())


# ---- CLI Example ----
if __name__ == "__main__":
    import sys

    # Create a demo message directory
    demo_dir = Path("/tmp/i18n_demo_messages")
    demo_dir.mkdir(exist_ok=True)

    # Write demo message files
    samples = {
        "en": {
            "welcome": "Welcome to our tool!",
            "greeting": "Hello, {name}!",
            "results": "{count, plural, one {# result} other {# results}}",
            "searching": "Searching...",
        },
        "fr": {
            "welcome": "Bienvenue sur notre outil !",
            "greeting": "Bonjour, {name} !",
            "results": "{count, plural, one {# résultat} other {# résultats}}",
        },
        "de": {
            "welcome": "Willkommen bei unserem Tool!",
            "greeting": "Hallo, {name}!",
            "results": "{count, plural, one {# Ergebnis} other {# Ergebnisse}}",
        },
        "ar": {
            "welcome": "!مرحبًا بك في أدائنا",
            "results": "{count, plural, one {# نتيجة} other {# نتائج}}",
        },
    }

    for lang, msgs in samples.items():
        path = demo_dir / f"{lang}.json"
        path.write_text(json.dumps(msgs, indent=2), encoding="utf-8")

    # Demo
    i18n = I18nMessages(str(demo_dir),
                        supported_languages=["en", "fr", "de", "ar"])

    print("=== Message Loading Demo ===\n")
    for lang in ["en", "fr", "de", "ar", "ja"]:
        welcome = i18n.get("welcome", lang=lang)
        greeting = i18n.get("greeting", lang=lang, name="Alice")
        results = i18n.get_plural("results", count=5, lang=lang)
        results1 = i18n.get_plural("results", count=1, lang=lang)
        print(f"[{lang}] {welcome}")
        print(f"[{lang}] {greeting}")
        print(f"[{lang}] {results} (count=5)")
        print(f"[{lang}] {results1} (count=1)")
        rtl = "RTL" if is_rtl(lang) else "LTR"
        print(f"[{lang}] Direction: {rtl}")
        print()

    # Number formatting demo
    print("=== Number Formatting Demo ===\n")
    number = 1234567.89
    for lang in ["en", "de", "fr", "ar"]:
        formatted = i18n.format_number(number, lang=lang)
        print(f"[{lang}] {formatted}")

    # Cleanup
    import shutil
    shutil.rmtree(demo_dir)
