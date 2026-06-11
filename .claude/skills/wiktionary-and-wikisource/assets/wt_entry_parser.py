#!/usr/bin/env python3
"""
wt_entry_parser.py — Parse Wiktionary entries into structured data.

Provides:
  - WiktionaryParser: extract language sections, POS sections, definitions,
    examples, translation tables, and audio pronunciation references
  - extract_language_section: isolate a specific language entry
  - extract_definitions: get numbered definitions with examples
  - extract_translations: get translation table data
  - extract_pronunciation_files: get audio file references

Usage:
    from wt_entry_parser import WiktionaryParser

    parser = WiktionaryParser()
    entry = parser.parse(wikitext)
    # entry == {
    #   "title": "word",
    #   "languages": {
    #     "English": {
    #       "etymology": "...",
    #       "pronunciation": [...],
    #       "pos_sections": {
    #         "Noun": {
    #           "inflection": "{{en-noun}}",
    #           "definitions": [
    #             {"definition": "A unit of language.",
    #              "examples": ["I wrote a word."]}
    #           ],
    #           "translations": {"French": ["mot"], ...}
    #         }
    #       }
    #     }
    #   }
    # }
"""

import re
from typing import Optional


class WiktionaryParser:
    """Parse Wiktionary wikitext into structured entry data."""

    def parse(self, wikitext: str, title: str = "") -> dict:
        """
        Parse a full Wiktionary page into structured entries by language.
        
        Args:
            wikitext: The raw wikitext of a Wiktionary page
            title: Optional page title for reference
        
        Returns:
            Dict with 'title' and 'languages' mapping language names to
            their structures.
        """
        result = {"title": title, "languages": {}}
        
        # Split by ---- (4 hyphens) — the language section delimiter
        raw_sections = re.split(r'^-{4,}\s*$', wikitext, flags=re.MULTILINE)
        
        for section in raw_sections:
            # Check if this section has a language heading
            lang_match = re.search(r'^==([^=]+)==', section, re.MULTILINE)
            if not lang_match:
                continue
            
            lang_name = lang_match.group(1).strip()
            lang_data = self._parse_language_section(section)
            if lang_data:
                result["languages"][lang_name] = lang_data
        
        return result

    def _parse_language_section(self, section: str) -> dict:
        """Parse a single language section (delimited by ==Language==)."""
        data = {
            "etymology": "",
            "pronunciation": [],
            "pos_sections": {},
        }
        
        # Extract etymology
        etym_match = re.search(
            r'====[Ee]tymology====\s*(.*?)(?=\n====|\n===|\Z)',
            section, re.DOTALL
        )
        if etym_match:
            data["etymology"] = etym_match.group(1).strip()
        
        # Extract pronunciation info
        data["pronunciation"] = self._extract_pronunciation(section)
        
        # Split by POS headings (===POS===)
        pos_sections = re.split(r'\n(?===)', section)
        
        for pos_section in pos_sections:
            pos_match = re.match(r'===([^=]+)===', pos_section)
            if not pos_match:
                continue
            
            pos_name = pos_match.group(1).strip()
            
            # Skip common subsections that are not POS
            if pos_name.lower() in (
                "etymology", "pronunciation", "usage notes",
                "synonyms", "antonyms", "derived terms",
                "related terms", "descendants", "translations",
                "see also", "references", "further reading",
                "anagrams", "coordinate terms",
            ):
                continue
            
            pos_data = self._parse_pos_section(pos_section)
            if pos_data:
                data["pos_sections"][pos_name] = pos_data
        
        return data

    def _parse_pos_section(self, section: str) -> dict:
        """Parse a single POS section (===Noun===, ===Verb===, etc.)."""
        # Extract inflection template (e.g., {{en-noun}}, {{fr-verb}})
        inflection = ""
        tmpl_match = re.search(r'\{\{([a-z]{2}-[a-z]+)\}\}', section)
        if tmpl_match:
            inflection = tmpl_match.group(1)
        
        # Extract definitions and examples
        definitions = self._extract_definitions(section)
        
        # Extract translation tables
        translations = self._extract_translations(section)
        
        return {
            "inflection": inflection,
            "definitions": definitions,
            "translations": translations,
        }

    def _extract_definitions(self, section: str) -> list[dict]:
        """Extract numbered definitions with their examples."""
        definitions = []
        current_def = None
        
        for line in section.split("\n"):
            # Definition line: "# text" or "#; text"
            def_match = re.match(r'^#(?!:)\s*(.*)', line)
            if def_match:
                if current_def is not None:
                    definitions.append(current_def)
                current_def = {"definition": def_match.group(1).strip(), "examples": []}
                continue
            
            # Example line: "#: text"
            example_match = re.match(r'^#:\s*(.*)', line)
            if example_match and current_def is not None:
                current_def["examples"].append(example_match.group(1).strip())
                continue
        
        if current_def is not None:
            definitions.append(current_def)
        
        return definitions

    def _extract_translations(self, section: str) -> dict[str, list[str]]:
        """Extract translation tables from a section."""
        translations = {}
        current_lang = None
        current_translations = []
        
        for line in section.split("\n"):
            trans_top = re.match(r'\{\{trans-top\|(.+?)\}\}', line)
            if trans_top:
                current_lang = trans_top.group(1).strip()
                current_translations = []
                continue
            
            if re.match(r'\{\{trans-mid\}\}', line):
                continue
            
            if re.match(r'\{\{trans-bottom\}\}', line):
                if current_lang and current_translations:
                    translations[current_lang] = current_translations
                current_lang = None
                current_translations = []
                continue
            
            if current_lang:
                # {{t|lang|word}} or {{t+|lang|word}}
                t_match = re.match(
                    r'\{\{t\+?\s*\|([a-z]{2,3})\|([^}]+?)\}\}', line
                )
                if t_match:
                    current_translations.append(t_match.group(2).strip())
        
        if current_lang and current_translations:
            translations[current_lang] = current_translations
        
        return translations

    def _extract_pronunciation(self, section: str) -> list[dict]:
        """Extract pronunciation info (IPA, audio files)."""
        results = []
        
        for line in section.split("\n"):
            # IPA: {{IPA|lang|/pron/}}
            ipa_match = re.search(
                r'\{\{IPA\|([a-z]+)\|(.+?)\}\}', line
            )
            if ipa_match:
                results.append({
                    "type": "ipa",
                    "lang": ipa_match.group(1),
                    "pron": ipa_match.group(2).strip(),
                })
                continue
            
            # Audio: {{audio|lang|file|label}}
            audio_match = re.search(
                r'\{\{audio\|([a-z]+)\|(.+?)\|(.+?)\}\}', line
            )
            if audio_match:
                results.append({
                    "type": "audio",
                    "lang": audio_match.group(1),
                    "file": audio_match.group(2),
                    "label": audio_match.group(3),
                })
        
        return results


# ── Standalone helper functions ────────────────────────────────────────────

def extract_language_section(wikitext: str, target_lang: str) -> Optional[str]:
    """Extract a single language section from a Wiktionary entry.
    
    Useful when you only need one language's data and don't want to
    parse the entire entry.
    """
    sections = re.split(r'^-{4,}\s*$', wikitext, flags=re.MULTILINE)
    for section in sections:
        lang_match = re.search(r'^==([^=]+)==', section, re.MULTILINE)
        if lang_match and lang_match.group(1).strip() == target_lang:
            return section
    return None


def count_languages(wikitext: str) -> int:
    """Count the number of language sections in a Wiktionary entry."""
    sections = re.split(r'^-{4,}\s*$', wikitext, flags=re.MULTILINE)
    count = 0
    for section in sections:
        if re.search(r'^==([^=]+)==', section, re.MULTILINE):
            count += 1
    return count
