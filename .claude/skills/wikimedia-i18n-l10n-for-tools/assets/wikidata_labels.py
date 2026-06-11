"""
Batch Wikidata label/description fetcher with language fallback support.

Fetches labels, descriptions, and aliases from Wikidata for one or more entities
in the user's preferred language, with proper fallback chain resolution.

Usage:
    from wikidata_labels import WikidataLabelFetcher

    fetcher = WikidataLabelFetcher()

    # Fetch labels for a single entity
    labels = fetcher.get_labels("Q937", languages=["en", "fr"])
    # → {"en": "Albert Einstein", "fr": "Albert Einstein"}

    # Fetch with fallback (gets best available language)
    info = fetcher.get_entity_info("Q937", preferred_lang="fr")
    # → {"label": "Albert Einstein", "description": "...", "lang": "fr"}

    # Batch fetch for multiple entities
    info = fetcher.batch_get_entity_info(
        ["Q937", "P31", "Q5"],
        preferred_lang="ar",
    )
    # → {"Q937": {"label": "...", "lang": "ar"}, ...}
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from i18n_utils import resolve_fallback

logger = logging.getLogger(__name__)


class WikidataLabelFetcher:
    """
    Fetch Wikidata labels, descriptions, and aliases with language fallback.

    Uses the `wbgetentities` Action API for single/batch lookups and SPARQL
    for more complex label retrieval patterns.
    """

    WIKIDATA_API = "https://www.wikidata.org/w/api.php"
    WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
    DEFAULT_UA = "WikidataLabelFetcher/1.0 (contact) ContentGapResearch"
    BATCH_SIZE = 50  # Max entities per wbgetentities call

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the fetcher.

        Args:
            user_agent: User-Agent header value
            timeout: Request timeout in seconds
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or self.DEFAULT_UA,
            "Accept-Encoding": "gzip, deflate",
        })
        self.timeout = timeout

    def get_labels(
        self,
        entity_id: str,
        languages: Optional[List[str]] = None,
        props: str = "labels|descriptions|aliases",
    ) -> Dict[str, Any]:
        """
        Fetch labels (and optionally descriptions/aliases) for a single entity.

        Args:
            entity_id: Wikidata entity ID (e.g., "Q937", "P31")
            languages: List of language codes to fetch (None = all available)
            props: Properties to fetch (labels, descriptions, aliases)

        Returns:
            Dict mapping language → value for each property.
            Structure: {"en": {"label": "...", "description": "..."}}
        """
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "props": props,
            "format": "json",
        }
        if languages:
            params["languages"] = "|".join(languages)

        resp = self.session.get(
            self.WIKIDATA_API,
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        entities = data.get("entities", {})
        entity = entities.get(entity_id, {})
        return self._parse_labels(entity)

    def get_entity_info(
        self,
        entity_id: str,
        preferred_lang: str = "en",
        include_aliases: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetch entity info in the user's preferred language with fallback.

        Args:
            entity_id: Wikidata entity ID
            preferred_lang: User's preferred language
            include_aliases: Whether to include aliases

        Returns:
            Dict with keys: label, description, lang (actual language used),
            aliases (optional)
        """
        # Compute which languages to ask for: preferred + fallback chain + en
        chain = resolve_fallback(preferred_lang)
        request_langs = list(dict.fromkeys(chain))  # Deduplicate preserving order

        props = "labels|descriptions"
        if include_aliases:
            props += "|aliases"

        all_labels = self.get_labels(entity_id, languages=request_langs, props=props)

        # Find best available
        for lang in request_langs:
            if lang in all_labels:
                info = all_labels[lang]
                info["lang"] = lang
                return info

        return {"label": entity_id, "description": "", "lang": "en"}

    def batch_get_entity_info(
        self,
        entity_ids: List[str],
        preferred_lang: str = "en",
        include_aliases: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch entity info for multiple entities in batch.

        Automatically splits into batches of 50 and handles rate limiting.

        Args:
            entity_ids: List of Wikidata entity IDs
            preferred_lang: User's preferred language
            include_aliases: Whether to include aliases

        Returns:
            Dict mapping entity_id → entity info dict
        """
        chain = resolve_fallback(preferred_lang)
        request_langs = list(dict.fromkeys(chain))

        props = "labels|descriptions"
        if include_aliases:
            props += "|aliases"

        results: Dict[str, Dict[str, Any]] = {}

        # Process in batches of 50
        for i in range(0, len(entity_ids), self.BATCH_SIZE):
            batch = entity_ids[i : i + self.BATCH_SIZE]
            ids_str = "|".join(batch)

            params = {
                "action": "wbgetentities",
                "ids": ids_str,
                "props": props,
                "languages": "|".join(request_langs),
                "format": "json",
            }

            resp = self.session.get(
                self.WIKIDATA_API,
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            entities = data.get("entities", {})
            for eid in batch:
                entity = entities.get(eid, {})
                parsed = self._parse_labels(entity)

                # Find best available language
                found = False
                for lang in request_langs:
                    if lang in parsed:
                        info = parsed[lang]
                        info["lang"] = lang
                        results[eid] = info
                        found = True
                        break

                if not found:
                    results[eid] = {"label": eid, "description": "", "lang": "en"}

            # Rate limiting between batches
            if i + self.BATCH_SIZE < len(entity_ids):
                time.sleep(0.5)

        return results

    def get_label_in_language(
        self,
        entity_id: str,
        language: str,
    ) -> Optional[str]:
        """
        Get a single label in a specific language (no fallback).

        Args:
            entity_id: Wikidata entity ID
            language: Language code

        Returns:
            Label string, or None if not available
        """
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "props": "labels",
            "languages": language,
            "format": "json",
        }

        resp = self.session.get(
            self.WIKIDATA_API,
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        entities = data.get("entities", {})
        entity = entities.get(entity_id, {})
        labels = entity.get("labels", {})
        if language in labels:
            return labels[language]["value"]

        return None

    def _parse_labels(self, entity: dict) -> Dict[str, Dict[str, Any]]:
        """
        Parse the entity response into a clean language-keyed dict.

        Returns:
            {"en": {"label": "...", "description": "...", "aliases": [...]}, ...}
        """
        result: Dict[str, Dict[str, Any]] = {}
        labels = entity.get("labels", {})
        descriptions = entity.get("descriptions", {})
        aliases_raw = entity.get("aliases", {})

        all_langs = set(labels.keys()) | set(descriptions.keys()) | set(aliases_raw.keys())

        for lang in all_langs:
            entry: Dict[str, Any] = {}
            if lang in labels:
                entry["label"] = labels[lang]["value"]
            if lang in descriptions:
                entry["description"] = descriptions[lang]["value"]
            if lang in aliases_raw:
                entry["aliases"] = [a["value"] for a in aliases_raw[lang]]
            result[lang] = entry

        return result


# ---- CLI ----
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Fetch Wikidata labels with language fallback"
    )
    parser.add_argument("entity_ids", nargs="+", help="Wikidata entity IDs (Q..., P...)")
    parser.add_argument("--lang", default="en", help="Preferred language")
    parser.add_argument("--all-langs", action="store_true",
                        help="Show labels in all available languages")
    parser.add_argument("--aliases", action="store_true", help="Include aliases")
    parser.add_argument("--json", action="store_true", help="Output as raw JSON")

    args = parser.parse_args()

    fetcher = WikidataLabelFetcher()

    if args.all_langs:
        ids_str = "|".join(args.entity_ids)
        for eid in args.entity_ids:
            info = fetcher.get_labels(eid)
            if args.json:
                print(json.dumps({eid: info}, indent=2))
            else:
                print(f"=== {eid} ===")
                for lang, data in sorted(info.items()):
                    label = data.get("label", "?")
                    desc = data.get("description", "")
                    print(f"  [{lang}] {label}")
                    if desc:
                        print(f"          {desc}")
                print()
    else:
        info = fetcher.batch_get_entity_info(
            args.entity_ids,
            preferred_lang=args.lang,
            include_aliases=args.aliases,
        )
        if args.json:
            print(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            for eid, data in info.items():
                label = data.get("label", "?")
                desc = data.get("description", "")
                lang = data.get("lang", "?")
                print(f"  {eid}: {label} [{lang}]")
                if desc:
                    print(f"       {desc}")
                if args.aliases and "aliases" in data:
                    print(f"       Aliases: {', '.join(data['aliases'])}")
