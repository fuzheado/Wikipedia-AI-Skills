"""
Source evaluator — classify and evaluate sources for notability assessment.

Determines whether a given source (URL or description) counts as:
- Significant coverage vs. trivial mention
- Reliable vs. unreliable source
- Independent vs. affiliated with the subject

Usage:
    from source_evaluator import SourceEvaluator

    evaluator = SourceEvaluator()

    result = evaluator.evaluate(
        title="Nature profile of Dr. Smith",
        source_type="news_feature",
        url="https://nature.com/articles/profile",
    )
    # → {"reliable": True, "independent": True, "significant": True, "score": 9/10}
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from notability_checker import Source


# Reliable domains (news/academic)
RELIABLE_DOMAINS: Dict[str, int] = {
    # Major academic publishers
    "nature.com": 10, "science.org": 10, "springer.com": 9,
    "wiley.com": 9, "taylorandfrancis.com": 8, "sagepub.com": 8,
    "oxfordjournals.org": 10, "cambridge.org": 9, "ieee.org": 8,
    "acm.org": 8, "arxiv.org": 7, "pubmed.ncbi.nlm.nih.gov": 10,
    "doi.org": 8, "jstor.org": 9,
    # Major newspapers
    "nytimes.com": 9, "washingtonpost.com": 9, "theguardian.com": 9,
    "wsj.com": 9, "ft.com": 9, "reuters.com": 9, "apnews.com": 9,
    "bbc.com": 9, "bbc.co.uk": 9, "bloomberg.com": 8,
    "economist.com": 9, "newyorker.com": 9, "theatlantic.com": 8,
    "latimes.com": 8, "chicagotribune.com": 8, "bostonglobe.com": 8,
    "lemonde.fr": 8, "elpais.com": 8, "spiegel.de": 8,
    "zeit.de": 8, "thetimes.co.uk": 8,
    # Major magazines
    "nationalgeographic.com": 8, "scientificamerican.com": 8,
    "forbes.com": 6, "wired.com": 7, "arstechnica.com": 7,
    "theverge.com": 6,
}

# Unreliable domains / sources that don't contribute to notability
UNRELIABLE_PATTERNS: List[str] = [
    r"imdb\.com", r"linkedin\.com", r"facebook\.com", r"twitter\.com",
    r"instagram\.com", r"youtube\.com", r"tiktok\.com",
    r"reddit\.com", r"quora\.com", r"medium\.com",
    r"goodreads\.com", r"discogs\.com", r"musicbrainz\.org",
    r"crunchbase\.com", r"angel\.co", r"zoominfo\.com",
    r"wikipedia\.org", r"wikidata\.org", r"fandom\.com",
    r"blogspot\.com", r"wordpress\.com", r"tumblr\.com",
    r"britannica\.com", r"whoswho\.com", r"marquiswhoswho\.com",
]

# Source types and their typical characteristics
SOURCE_TYPE_RATINGS: Dict[str, Dict[str, Any]] = {
    "academic_journal": {"reliable": True, "significant_possible": True, "type": "academic"},
    "news_feature": {"reliable": True, "significant_possible": True, "type": "news"},
    "news_article": {"reliable": True, "significant_possible": False, "type": "news"},
    "book": {"reliable": True, "significant_possible": True, "type": "book"},
    "book_review": {"reliable": True, "significant_possible": True, "type": "review"},
    "documentary": {"reliable": True, "significant_possible": True, "type": "documentary"},
    "press_release": {"reliable": False, "significant_possible": False, "type": "press_release"},
    "blog": {"reliable": False, "significant_possible": False, "type": "blog"},
    "social_media": {"reliable": False, "significant_possible": False, "type": "social_media"},
    "self_published": {"reliable": False, "significant_possible": False, "type": "self_published"},
    "company_website": {"reliable": False, "significant_possible": False, "type": "company_website"},
    "database": {"reliable": False, "significant_possible": False, "type": "database"},
    "directory": {"reliable": False, "significant_possible": False, "type": "directory"},
}

# Keywords suggesting significant coverage
SIGNIFICANCE_POSITIVE = [
    "profile", "feature", "in-depth", "investigation", "biography",
    "book-length", "documentary", "retrospective", "analysis",
    "review of", "examination", "study of", "history of",
    "portrait", "interview with", "conversation with",
]

# Keywords suggesting trivial/routine coverage
SIGNIFICANCE_NEGATIVE = [
    "press release", "announces", "launches", "partnership",
    "appoints", "hires", "promoted", "named",
    "briefly", "mentions", "in passing", "roundup",
    "earnings", "quarterly", "financial results",
    "match report", "game recap", "score",
    "obituary", "death notice",
]


class SourceEvaluator:
    """Evaluate sources for notability assessment."""

    def evaluate(
        self,
        title: str = "",
        source_type: str = "",
        url: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluate a single source for notability.

        Args:
            title: Source title or headline
            source_type: Type of source (news_feature, press_release, etc.)
            url: Source URL (used for domain checking)
            description: Free-form description of the source

        Returns:
            Dict with: reliable, independent, significant, score, confidence
        """
        result = {
            "reliable": None,
            "independent": None,
            "significant": None,
            "score": 0,
            "confidence": "low",
            "notes": [],
        }

        # Check domain reliability
        if url:
            domain_result = self._check_domain(url)
            if domain_result is not None:
                result["reliable"] = domain_result >= 6
                result["score"] += domain_result / 10 * 5
                result["notes"].append(
                    f"Domain: {'reliable' if result['reliable'] else 'unreliable'} "
                    f"(score: {domain_result}/10)"
                )

        # Check source type
        if source_type in SOURCE_TYPE_RATINGS:
            rating = SOURCE_TYPE_RATINGS[source_type]
            if result["reliable"] is None:
                result["reliable"] = rating["reliable"]
            result["significant"] = rating["significant_possible"]
            result["notes"].append(f"Type: {source_type}")
            if not rating["reliable"]:
                result["notes"].append(
                    "This source type does not contribute to notability."
                )

        # Check title/description for significance signals
        combined = f"{title} {description}".lower()
        significance_signals = self._evaluate_significance(combined)

        if significance_signals["has_positive"]:
            result["significant"] = True
            result["score"] += 3
            result["notes"].append(
                f"Signals: {', '.join(significance_signals['positives'][:3])}"
            )
        if significance_signals["has_negative"]:
            if result["significant"] is None:
                result["significant"] = False
            result["score"] -= 2
            result["notes"].append(
                f"Routine signals: {', '.join(significance_signals['negatives'][:3])}"
            )

        # Default independence (most external sources are independent)
        if result["independent"] is None:
            if source_type in ("press_release", "self_published", "company_website", "autobiography"):
                result["independent"] = False
                result["notes"].append("Not independent (self-published or affiliated)")
            else:
                result["independent"] = True

        # Normalize score to 0–10
        result["score"] = max(0, min(10, result["score"]))

        # Confidence
        score = result["score"]
        if score >= 7:
            result["confidence"] = "high"
        elif score >= 4:
            result["confidence"] = "medium"
        else:
            result["confidence"] = "low"

        return result

    def _check_domain(self, url: str) -> Optional[int]:
        """Check domain against reliability database. Returns score 1-10 or None."""
        domain_match = re.search(r"https?://([^/]+)", url.lower())
        if not domain_match:
            return None

        domain = domain_match.group(1)

        # Check exact matches
        for reliable_domain, score in RELIABLE_DOMAINS.items():
            if domain == reliable_domain or domain.endswith("." + reliable_domain):
                return score

        # Check unreliable patterns
        for pattern in UNRELIABLE_PATTERNS:
            if re.search(pattern, domain):
                return 1

        # Unknown domain — neutral
        return 5

    def _evaluate_significance(self, text: str) -> Dict[str, Any]:
        """Check if text suggests significant or routine coverage."""
        result = {"has_positive": False, "has_negative": False,
                   "positives": [], "negatives": []}

        for keyword in SIGNIFICANCE_POSITIVE:
            if keyword in text:
                result["has_positive"] = True
                result["positives"].append(keyword)

        for keyword in SIGNIFICANCE_NEGATIVE:
            if keyword in text:
                result["has_negative"] = True
                result["negatives"].append(keyword)

        return result

    def classify_source(self, url: str = "", title: str = "") -> str:
        """Classify a source by its likely type."""
        combined = f"{url} {title}".lower()

        if any(d in combined for d in ["nature.com", "science.org", "springer",
                                         "wiley", "ieee", "acm", "arxiv"]):
            return "academic_journal"
        if any(d in combined for d in ["imdb", "discogs", "musicbrainz",
                                        "goodreads", "worldcat"]):
            return "database"
        if any(d in combined for d in ["linkedin", "facebook", "twitter",
                                        "instagram", "youtube", "tiktok"]):
            return "social_media"
        if any(d in combined for d in ["blogspot", "wordpress", "medium",
                                        "substack", "patreon"]):
            return "blog"
        if "press release" in title.lower():
            return "press_release"
        if any(d in combined for d in ["wikipedia", "fandom"]):
            return "self_published"
        if "review" in title.lower():
            return "book_review" if "book" in title.lower() else "review"
        if any(w in combined for w in ["profile", "feature", "in-depth"]):
            return "news_feature"
        if any(d in combined for d in ["nytimes", "guardian", "bbc", "reuters",
                                        "apnews", "washingtonpost", "wsj"]):
            return "news_article"
        if any(d in combined for d in ["crunchbase", "zoominfo", "bloomberg"]):
            return "directory"

        return "unknown"


# ---- CLI ----
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Evaluate a source for Wikipedia notability"
    )
    parser.add_argument("--title", help="Source title or headline")
    parser.add_argument("--type", help="Source type (news_feature, press_release, etc.)")
    parser.add_argument("--url", help="Source URL")
    parser.add_argument("--desc", help="Free-form description")

    args = parser.parse_args()

    evaluator = SourceEvaluator()
    result = evaluator.evaluate(
        title=args.title or "",
        source_type=args.type or "",
        url=args.url or "",
        description=args.desc or "",
    )

    print(json.dumps(result, indent=2))
