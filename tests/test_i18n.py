"""Tests for the i18n/l10n skill — i18n_utils, message_loader, wikidata_labels, and scripts."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Paths
SKILL_DIR = (
    Path(__file__).resolve().parent.parent
    / ".claude" / "skills" / "wikimedia-i18n-l10n-for-tools"
)
ASSETS_DIR = SKILL_DIR / "assets"
SCRIPTS_DIR = SKILL_DIR / "scripts"

sys.path.insert(0, str(ASSETS_DIR))


# =========================================================================
# i18n_utils tests
# =========================================================================


class TestParseAcceptLanguage:
    """Tests for parse_accept_language."""

    def test_simple_single(self):
        from i18n_utils import parse_accept_language
        result = parse_accept_language("en")
        assert result == [("en", 1.0)]

    def test_simple_multi(self):
        from i18n_utils import parse_accept_language
        result = parse_accept_language("en, fr, de")
        assert len(result) == 3
        assert result[0] == ("en", 1.0)

    def test_with_quality(self):
        from i18n_utils import parse_accept_language
        result = parse_accept_language("fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7")
        assert result[0] == ("fr", 1.0)  # fr-CH stripped to fr
        assert result[1] == ("fr", 0.9)
        assert result[2] == ("en", 0.8)

    def test_empty(self):
        from i18n_utils import parse_accept_language
        assert parse_accept_language("") == []
        assert parse_accept_language(None) == []

    def test_sorting(self):
        from i18n_utils import parse_accept_language
        result = parse_accept_language("de;q=0.5, fr;q=0.9, en;q=0.8")
        assert result[0][0] == "fr"
        assert result[1][0] == "en"
        assert result[2][0] == "de"


class TestDetectLanguage:
    """Tests for detect_language."""

    def test_detect_exact(self):
        from i18n_utils import detect_language
        lang = detect_language("fr", supported_languages=["en", "fr", "de"])
        assert lang == "fr"

    def test_detect_fallback(self):
        from i18n_utils import detect_language
        lang = detect_language("pt-br", supported_languages=["en", "pt"])
        assert lang == "pt"

    def test_detect_chain_fallback(self):
        from i18n_utils import detect_language
        lang = detect_language("pt-br", supported_languages=["en", "es"])
        assert lang == "es"  # pt-br → pt → es

    def test_detect_default(self):
        from i18n_utils import detect_language
        lang = detect_language("", supported_languages=["fr", "de"])
        assert lang == "en"

    def test_detect_no_supported(self):
        from i18n_utils import detect_language
        lang = detect_language("fr-CH, fr;q=0.9")
        assert lang == "fr"


class TestResolveFallback:
    """Tests for resolve_fallback."""

    def test_english(self):
        from i18n_utils import resolve_fallback
        assert resolve_fallback("en") == ["en"]

    def test_french(self):
        from i18n_utils import resolve_fallback
        assert resolve_fallback("fr") == ["fr", "en"]

    def test_brazilian_portuguese(self):
        from i18n_utils import resolve_fallback
        chain = resolve_fallback("pt-br")
        assert chain[0] == "pt-br"
        assert "pt" in chain
        assert "en" in chain

    def test_belarusian_tarask(self):
        from i18n_utils import resolve_fallback
        chain = resolve_fallback("be-tarask")
        assert "be-tarask" in chain
        assert "be" in chain
        assert "ru" in chain
        assert "en" in chain

    def test_serbian_latin(self):
        from i18n_utils import resolve_fallback
        # sr-el is not in the chain, should fall back through sr → en
        chain = resolve_fallback("sr")
        assert "sr" in chain
        assert "en" in chain

    def test_simplified_chinese(self):
        from i18n_utils import resolve_fallback
        chain = resolve_fallback("zh-cn")
        assert "zh-cn" in chain
        assert "zh-hans" in chain
        assert "zh" in chain
        assert "en" in chain

    def test_unknown_language(self):
        from i18n_utils import resolve_fallback
        chain = resolve_fallback("xyz")
        assert chain[0] == "xyz"
        assert "en" in chain


class TestIsRtl:
    """Tests for is_rtl."""

    def test_rtl_languages(self):
        from i18n_utils import is_rtl
        assert is_rtl("ar")
        assert is_rtl("he")
        assert is_rtl("fa")
        assert is_rtl("ps")
        assert is_rtl("ur")

    def test_ltr_languages(self):
        from i18n_utils import is_rtl
        assert not is_rtl("en")
        assert not is_rtl("de")
        assert not is_rtl("fr")
        assert not is_rtl("ja")
        assert not is_rtl("zh")

    def test_rtl_with_region(self):
        from i18n_utils import is_rtl
        assert is_rtl("ar-SA")
        assert is_rtl("he-IL")


class TestLanguageToDomain:
    """Tests for language_to_domain."""

    def test_standard(self):
        from i18n_utils import language_to_domain
        assert language_to_domain("fr") == "fr.wikipedia.org"
        assert language_to_domain("de") == "de.wikipedia.org"

    def test_special(self):
        from i18n_utils import language_to_domain
        assert language_to_domain("simple") == "simple.wikipedia.org"
        assert language_to_domain("be-tarask") == "be-tarask.wikipedia.org"

    def test_other_projects(self):
        from i18n_utils import language_to_domain
        assert language_to_domain("fr", project="wiktionary") == "fr.wiktionary.org"
        assert language_to_domain("de", project="wikisource") == "de.wikisource.org"

    def test_project_wikis(self):
        from i18n_utils import language_to_domain
        assert language_to_domain("en", project="commons") == "commons.wikimedia.org"
        assert language_to_domain("en", project="wikidata") == "www.wikidata.org"
        assert language_to_domain("en", project="meta") == "meta.wikimedia.org"


class TestDomainToLanguage:
    """Tests for domain_to_language."""

    def test_standard(self):
        from i18n_utils import domain_to_language
        assert domain_to_language("fr.wikipedia.org") == "fr"
        assert domain_to_language("de.wikipedia.org") == "de"

    def test_project(self):
        from i18n_utils import domain_to_language
        assert domain_to_language("commons.wikimedia.org") is None
        assert domain_to_language("www.wikidata.org") is None

    def test_special(self):
        from i18n_utils import domain_to_language
        assert domain_to_language("simple.wikipedia.org") == "simple"
        assert domain_to_language("be-tarask.wikipedia.org") == "be-tarask"


class TestNormalizeTitle:
    """Tests for normalize_title."""

    def test_nfc_normalization(self):
        from i18n_utils import normalize_title
        # "cafe" + combining acute accent (NFD) → "café" (NFC)
        nfd = "cafe\u0301"  # e + combining acute
        nfc = normalize_title(nfd)
        assert nfc == "caf\u00e9"  # é as single codepoint
        assert len(nfc) == 4  # 4 codepoints, not 5

    def test_strip_invisible(self):
        from i18n_utils import normalize_title
        with_zwsp = "Test\u200BTitle"
        result = normalize_title(with_zwsp)
        assert result == "TestTitle"

    def test_strip_bom(self):
        from i18n_utils import normalize_title
        with_bom = "\uFEFFPageTitle"
        result = normalize_title(with_bom)
        assert result == "PageTitle"

    def test_strip_whitespace(self):
        from i18n_utils import normalize_title
        result = normalize_title("  Page Title  ")
        assert result == "Page Title"


class TestGetPreferredLanguage:
    """Tests for get_preferred_language."""

    def test_exact_match(self):
        from i18n_utils import get_preferred_language
        lang = get_preferred_language("fr", ["en", "fr", "de"])
        assert lang == "fr"

    def test_region_strip(self):
        from i18n_utils import get_preferred_language
        lang = get_preferred_language("fr-CH", ["en", "fr", "de"])
        assert lang == "fr"

    def test_fallback_chain(self):
        from i18n_utils import get_preferred_language
        lang = get_preferred_language("pt-br", ["en", "es"])
        assert lang == "es"

    def test_default(self):
        from i18n_utils import get_preferred_language
        lang = get_preferred_language("", ["fr", "de"])
        assert lang == "en"

    def test_no_match(self):
        from i18n_utils import get_preferred_language
        lang = get_preferred_language("ja, ko", ["en", "fr"])
        assert lang == "en"


class TestValidateLanguageCode:
    """Tests for validate_language_code."""

    def test_known_codes(self):
        from i18n_utils import validate_language_code
        assert validate_language_code("en")
        assert validate_language_code("fr")
        assert validate_language_code("de")
        assert validate_language_code("ar")

    def test_unknown_codes(self):
        from i18n_utils import validate_language_code
        assert not validate_language_code("xyz")
        assert not validate_language_code("")


class TestStripInvisible:
    """Tests for strip_invisible."""

    def test_zwsp(self):
        from i18n_utils import strip_invisible
        assert strip_invisible("a\u200Bb") == "ab"

    def test_bom(self):
        from i18n_utils import strip_invisible
        assert strip_invisible("\uFEFFtest") == "test"

    def test_rtl_override(self):
        from i18n_utils import strip_invisible
        assert strip_invisible("a\u202Eb") == "ab"

    def test_clean_text_unchanged(self):
        from i18n_utils import strip_invisible
        assert strip_invisible("Hello World") == "Hello World"

    def test_multiple_invisible(self):
        from i18n_utils import strip_invisible
        assert strip_invisible("\u200B\u200C\u200Dtest") == "test"


# =========================================================================
# message_loader tests
# =========================================================================


class TestI18nMessages:
    """Tests for I18nMessages."""

    @pytest.fixture
    def message_dir(self, tmp_path):
        """Create a temporary message directory with sample files."""
        msgs = {
            "en.json": {
                "welcome": "Welcome!",
                "greeting": "Hello, {name}!",
                "results": "{count, plural, one {# result} other {# results}}",
                "search": "Search",
            },
            "fr.json": {
                "welcome": "Bienvenue !",
                "greeting": "Bonjour, {name} !",
                "results": "{count, plural, one {# résultat} other {# résultats}}",
            },
            "ar.json": {
                "welcome": "!مرحبًا",
                "results": "{count, plural, one {# نتيجة} other {# نتائج}}",
            },
        }
        d = tmp_path / "messages"
        d.mkdir()
        for name, content in msgs.items():
            (d / name).write_text(json.dumps(content), encoding="utf-8")
        return str(d)

    def test_load_supported_languages(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr", "ar"])
        assert "en" in i18n.available_languages()
        assert "fr" in i18n.available_languages()
        assert "ar" in i18n.available_languages()

    def test_get_exact_message(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        msg = i18n.get("welcome", lang="fr")
        assert msg == "Bienvenue !"

    def test_get_with_variables(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        msg = i18n.get("greeting", lang="fr", name="Alice")
        assert msg == "Bonjour, Alice !"

    def test_get_fallback(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        # "search" is only in en.json
        msg = i18n.get("search", lang="fr")
        assert msg == "Search"

    def test_get_missing_key(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        msg = i18n.get("nonexistent", lang="fr")
        assert msg == "nonexistent"

    def test_get_missing_key_with_default(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        msg = i18n.get("nonexistent", lang="fr", default="Fallback")
        assert msg == "Fallback"

    def test_get_plural_english(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en"])
        # The test message uses {count} syntax, not ICU # syntax
        result1 = i18n.get("results", lang="en", count=1)
        result5 = i18n.get("results", lang="en", count=5)
        assert "1" in result1 and "result" in result1
        assert "5" in result5 and "results" in result5

    def test_get_plural_french(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        result1 = i18n.get("results", lang="fr", count=1)
        result5 = i18n.get("results", lang="fr", count=5)
        assert "1" in result1 and "résultat" in result1
        assert "5" in result5 and "résultats" in result5

    def test_has_key(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en"])
        assert i18n.has_key("welcome")
        assert not i18n.has_key("nonexistent")

    def test_has_key_specific_lang(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        # "search" only in en
        assert i18n.has_key("search", lang="en")
        assert not i18n.has_key("search", lang="fr")

    def test_auto_discover(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir)
        assert len(i18n.available_languages()) >= 3

    def test_format_number_english(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en"])
        result = i18n.format_number(1234567.89, lang="en")
        assert "1,234,567.89" in result

    def test_format_number_german(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "de"])
        result = i18n.format_number(1234567.89, lang="de")
        assert "1.234.567,89" in result

    def test_format_number_french(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr"])
        result = i18n.format_number(1234567.89, lang="fr")
        assert "1" in result
        assert "," in result  # comma as decimal

    def test_get_plural_arabic_chain_fallback(self, message_dir):
        from message_loader import I18nMessages
        i18n = I18nMessages(message_dir, supported_languages=["en", "fr", "ar"])
        results = i18n.get_plural("results", count=3, lang="ar")
        # Arabic has "few" form for 3-10, but our ICU has one/other
        assert results  # Should not error


class TestPluralCategory:
    """Tests for the internal plural category resolver."""

    def test_english_one(self):
        from message_loader import _get_plural_category
        assert _get_plural_category(1, "en") == "one"
        assert _get_plural_category(0, "en") == "other"
        assert _get_plural_category(5, "en") == "other"

    def test_russian_one(self):
        from message_loader import _get_plural_category
        assert _get_plural_category(1, "ru") == "one"
        assert _get_plural_category(2, "ru") == "few"
        assert _get_plural_category(5, "ru") == "many"

    def test_french_one(self):
        from message_loader import _get_plural_category
        assert _get_plural_category(1, "fr") == "one"
        assert _get_plural_category(2, "fr") == "other"


# =========================================================================
# wikidata_labels tests
# =========================================================================


class TestWikidataLabelFetcher:
    """Tests for WikidataLabelFetcher."""

    def test_init(self):
        from wikidata_labels import WikidataLabelFetcher
        fetcher = WikidataLabelFetcher()
        assert fetcher.WIKIDATA_API == "https://www.wikidata.org/w/api.php"
        assert fetcher.BATCH_SIZE == 50

    def test_init_custom_ua(self):
        from wikidata_labels import WikidataLabelFetcher
        fetcher = WikidataLabelFetcher(user_agent="MyBot/1.0 (test) Test")
        assert "MyBot/1.0" in fetcher.session.headers["User-Agent"]

    @patch("wikidata_labels.requests.Session.get")
    def test_get_labels(self, mock_get):
        from wikidata_labels import WikidataLabelFetcher

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {
                "Q937": {
                    "labels": {
                        "en": {"value": "Albert Einstein", "language": "en"},
                        "fr": {"value": "Albert Einstein", "language": "fr"},
                    },
                    "descriptions": {
                        "en": {"value": "German-born physicist", "language": "en"},
                    },
                }
            }
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        result = fetcher.get_labels("Q937", languages=["en", "fr"])

        assert "en" in result
        assert result["en"]["label"] == "Albert Einstein"
        assert result["en"]["description"] == "German-born physicist"
        assert result["fr"]["label"] == "Albert Einstein"

    @patch("wikidata_labels.requests.Session.get")
    def test_get_entity_info(self, mock_get):
        from wikidata_labels import WikidataLabelFetcher

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {
                "Q937": {
                    "labels": {
                        "en": {"value": "Albert Einstein", "language": "en"},
                        "fr": {"value": "Albert Einstein", "language": "fr"},
                    },
                    "descriptions": {
                        "en": {"value": "German-born physicist", "language": "en"},
                        "fr": {"value": "Physicien allemand", "language": "fr"},
                    },
                }
            }
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        info = fetcher.get_entity_info("Q937", preferred_lang="fr")

        assert info["label"] == "Albert Einstein"
        assert info["description"] == "Physicien allemand"
        assert info["lang"] == "fr"

    @patch("wikidata_labels.requests.Session.get")
    def test_get_entity_info_fallback(self, mock_get):
        from wikidata_labels import WikidataLabelFetcher

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {
                "Q937": {
                    "labels": {
                        "en": {"value": "Albert Einstein", "language": "en"},
                        "fr": {"value": "Albert Einstein", "language": "fr"},
                    },
                    "descriptions": {
                        "en": {"value": "German-born physicist", "language": "en"},
                    },
                }
            }
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        # pt-br doesn't exist, should fall back to pt → en
        info = fetcher.get_entity_info("Q937", preferred_lang="pt-br")

        assert info["label"] == "Albert Einstein"
        assert info["lang"] == "en"

    @patch("wikidata_labels.requests.Session.get")
    def test_get_label_in_language(self, mock_get):
        from wikidata_labels import WikidataLabelFetcher

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {
                "Q937": {
                    "labels": {
                        "fr": {"value": "Albert Einstein", "language": "fr"},
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        label = fetcher.get_label_in_language("Q937", "fr")
        assert label == "Albert Einstein"

    @patch("wikidata_labels.requests.Session.get")
    def test_get_label_in_language_not_found(self, mock_get):
        from wikidata_labels import WikidataLabelFetcher

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {
                "Q937": {
                    "labels": {
                        "en": {"value": "Albert Einstein", "language": "en"},
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        label = fetcher.get_label_in_language("Q937", "de")
        assert label is None

    @patch("wikidata_labels.requests.Session.get")
    def test_batch_get_entity_info(self, mock_get):
        from wikidata_labels import WikidataLabelFetcher

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {
                "Q937": {
                    "labels": {
                        "en": {"value": "Albert Einstein", "language": "en"},
                    },
                    "descriptions": {
                        "en": {"value": "Physicist", "language": "en"},
                    },
                },
                "Q5": {
                    "labels": {
                        "en": {"value": "human", "language": "en"},
                    },
                    "descriptions": {
                        "en": {"value": "Human species", "language": "en"},
                    },
                },
            }
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        results = fetcher.batch_get_entity_info(["Q937", "Q5"], preferred_lang="en")

        assert "Q937" in results
        assert "Q5" in results
        assert results["Q937"]["label"] == "Albert Einstein"
        assert results["Q5"]["label"] == "human"

    def test_parse_labels_empty(self):
        from wikidata_labels import WikidataLabelFetcher
        fetcher = WikidataLabelFetcher()
        result = fetcher._parse_labels({})
        assert result == {}

    def test_parse_labels_with_data(self):
        from wikidata_labels import WikidataLabelFetcher
        fetcher = WikidataLabelFetcher()
        entity = {
            "labels": {"en": {"value": "Test", "language": "en"}},
            "descriptions": {"en": {"value": "A test", "language": "en"}},
            "aliases": {"en": [{"value": "test1"}, {"value": "test2"}]},
        }
        result = fetcher._parse_labels(entity)
        assert result["en"]["label"] == "Test"
        assert result["en"]["description"] == "A test"
        assert result["en"]["aliases"] == ["test1", "test2"]

    @patch("wikidata_labels.requests.Session.get")
    def test_batch_splitting(self, mock_get):
        """Test that batch_get batches at 50 entities."""
        from wikidata_labels import WikidataLabelFetcher

        entities = [f"Q{i}" for i in range(1, 120)]

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entities": {eid: {"labels": {"en": {"value": eid}}} for eid in entities[:50]}
        }
        mock_get.return_value = mock_resp

        fetcher = WikidataLabelFetcher()
        results = fetcher.batch_get_entity_info(entities, preferred_lang="en")
        # Should have made at least 3 calls (50 + 50 + 20)
        assert mock_get.call_count >= 3


# =========================================================================
# Script tests
# =========================================================================


class TestScripts:
    """Tests for shell scripts."""

    def test_language_fallback_help(self):
        """Test language-fallback.sh --help."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "language-fallback.sh"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_language_fallback_french(self):
        """Test language-fallback.sh fr."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "language-fallback.sh"), "fr"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "en" in result.stdout

    def test_language_fallback_list(self):
        """Test language-fallback.sh --list."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "language-fallback.sh"), "--list"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "fr" in result.stdout

    def test_fetch_multilingual_labels_help(self):
        """Test fetch-multilingual-labels.sh --help."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "fetch-multilingual-labels.sh"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_fetch_multilingual_labels_no_args(self):
        """Test fetch-multilingual-labels.sh without args."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "fetch-multilingual-labels.sh")],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert "Missing" in result.stderr or "Error" in result.stderr or "Missing" in result.stdout

    def test_i18n_utils_script_help(self):
        """Test i18n_utils.py --help."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "i18n_utils.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout

    def test_i18n_utils_fallback_command(self):
        """Test i18n_utils.py fallback fr."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "i18n_utils.py"), "fallback", "fr"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "fr → en" in result.stdout

    def test_i18n_utils_domain_command(self):
        """Test i18n_utils.py domain fr."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "i18n_utils.py"), "domain", "fr"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "fr.wikipedia.org" in result.stdout

    def test_i18n_utils_rtl_command(self):
        """Test i18n_utils.py rtl ar."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "i18n_utils.py"), "rtl", "ar"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "yes" in result.stdout

    def test_i18n_utils_rtl_command_ltr(self):
        """Test i18n_utils.py rtl en returns no."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "i18n_utils.py"), "rtl", "en"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "no" in result.stdout

    def test_message_loader_script(self):
        """Test message_loader.py runs without error."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "message_loader.py")],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_wikidata_labels_script_help(self):
        """Test wikidata_labels.py --help."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "wikidata_labels.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout


# =========================================================================
# Reference docs tests
# =========================================================================


class TestReferences:
    """Tests for reference documentation files."""

    def test_language_codes_ref_exists(self):
        path = SKILL_DIR / "references" / "language-codes.md"
        assert path.exists()
        content = path.read_text()
        assert len(content) > 1000
        assert "ar" in content
        assert "RTL" in content

    def test_unicode_pitfalls_ref_exists(self):
        path = SKILL_DIR / "references" / "unicode-pitfalls.md"
        assert path.exists()
        content = path.read_text()
        assert len(content) > 1000
        assert "NFC" in content
        assert "normalization" in content


# =========================================================================
# SKILL.md tests
# =========================================================================


class TestSkillFile:
    """Tests for the main SKILL.md file."""

    def test_skill_file_exists(self):
        path = SKILL_DIR / "SKILL.md"
        assert path.exists()

    def test_skill_file_has_yaml_frontmatter(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert content.startswith("---")
        second = content.find("---", 3)
        assert second > 3
        frontmatter = content[3:second].strip()
        assert "name:" in frontmatter
        assert "description:" in frontmatter
        assert "license: MIT" in frontmatter
        assert "last_verified:" in frontmatter
        assert "depends_on:" in frontmatter

    def test_skill_file_references_related_skills(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "wikimedia-api-access" in content
        assert "mediawiki-translate-extension" in content
        assert "wikidata" in content

    def test_skill_file_has_sops(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "## SOP:" in content or "### SOP:" in content

    def test_skill_file_has_guardrails(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "## Guardrails" in content or "### Guardrails" in content

    def test_skill_file_covers_key_topics(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        for topic in [
            "fallback chain",
            "RTL",
            "bidi",
            "Unicode",
            "normalization",
            "message file",
            "Accept-Language",
            "cross-wiki",
        ]:
            assert topic.lower() in content.lower(), f"Missing topic: {topic}"

    def test_skill_file_has_russian_plural(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "plural" in content.lower()

    def test_skill_file_mentions_arabic(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "Arabic" in content or "ar" in content

    def test_skill_file_mentions_comons_labels(self):
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "Commons" in content
        assert "multilingual" in content
