"""
Notability assessment engine for English Wikipedia.

Evaluates whether a subject meets Wikipedia notability guidelines (GNG or SNGs)
and produces a structured assessment report.

Usage:
    from notability_checker import NotabilityChecker

    checker = NotabilityChecker()

    # Assess a subject
    report = checker.assess(
        name="Dr. Jane Smith",
        subject_type="academic",
        description="Professor of quantum physics at MIT, named chair",
        sources=[
            {"url": "https://nature.com/article", "type": "feature", "reliable": True},
        ]
    )

    # Classify subject type
    subject_type = checker.classify_subject("A peer-reviewed study on...")
    # → "academic" (or "book", "film", "organization", "person", "event", etc.)

    # Check against a specific SNG
    result = checker.check_sng("NACADEMIC", description="Named chair at MIT")
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# =========================================================================
# Data models
# =========================================================================


@dataclass
class Source:
    """A single source for notability evaluation."""
    title: str = ""
    url: str = ""
    source_type: str = "unknown"  # "news", "academic", "book", "review", "press_release", etc.
    reliable: Optional[bool] = None
    independent: Optional[bool] = None
    significant_coverage: Optional[bool] = None
    notes: str = ""


@dataclass
class SNGResult:
    """Result of checking an SNG."""
    sng: str
    applicable: bool
    criteria_met: List[str] = field(default_factory=list)
    details: str = ""
    confidence: str = "low"  # "high", "medium", "low"


@dataclass
class GNGResult:
    """Result of checking the General Notability Guideline."""
    passed: bool = False
    significant_coverage: bool = False
    reliable_sources: bool = False
    independent_sources: bool = False
    multiple_sources: bool = False
    source_count: int = 0
    source_details: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""


@dataclass
class NotabilityReport:
    """Complete notability assessment report."""
    subject_name: str
    subject_type: str
    description: str

    overall_verdict: str = "unclear"  # "notable", "not_notable", "unclear"
    confidence: str = "low"  # "high", "medium", "low"

    gng: GNGResult = field(default_factory=GNGResult)
    sng_results: List[SNGResult] = field(default_factory=list)

    applicable_sngs: List[str] = field(default_factory=list)
    exclusion_flags: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to a serializable dict."""
        return {
            "subject": {
                "name": self.subject_name,
                "type": self.subject_type,
                "description": self.description,
            },
            "verdict": {
                "overall": self.overall_verdict,
                "confidence": self.confidence,
            },
            "gng_assessment": {
                "passed": self.gng.passed,
                "significant_coverage": self.gng.significant_coverage,
                "reliable_sources": self.gng.reliable_sources,
                "independent_sources": self.gng.independent_sources,
                "multiple_sources": self.gng.multiple_sources,
                "source_count": self.gng.source_count,
                "notes": self.gng.notes,
            },
            "sng_assessments": [
                {
                    "sng": s.sng,
                    "applicable": s.applicable,
                    "criteria_met": s.criteria_met,
                    "confidence": s.confidence,
                }
                for s in self.sng_results
            ],
            "exclusion_flags": self.exclusion_flags,
            "recommendations": self.recommendations,
        }


# =========================================================================
# Classification
# =========================================================================

# Keywords that hint at subject type for auto-classification
TYPE_KEYWORDS: Dict[str, List[str]] = {
    "academic": [
        "professor", "researcher", "scientist", "scholar", "ph.d.", "phd",
        "university", "institute", "laboratory", "research", "academic",
        "dean", "chair", "fellow", "lecturer", "postdoc",
    ],
    "artist": [
        "painter", "sculptor", "photographer", "artist", "exhibition",
        "gallery", "museum", "artwork",
    ],
    "author": [
        "author", "writer", "novelist", "poet", "playwright", "book",
        "published", "bestseller", "literary",
    ],
    "company": [
        "company", "corporation", "inc.", "ltd.", "llc", "startup",
        "business", "firm", "enterprise", "organization", "nonprofit",
        "non-profit", "foundation", "ceo", "founder",
    ],
    "entertainer": [
        "actor", "actress", "comedian", "musician", "band", "singer",
        "film", "television", "tv", "movie", "performance", "stage",
        "director", "producer",
    ],
    "event": [
        "conference", "festival", "disaster", "election", "protest",
        "competition", "tournament", "incident", "attack",
    ],
    "film": [
        "film", "movie", "documentary", "short film", "feature film",
    ],
    "geographic": [
        "city", "town", "village", "mountain", "river", "lake", "island",
        "region", "state", "province", "county", "park",
    ],
    "music": [
        "album", "song", "single", "band", "musician", "singer",
        "composer", "record", "label", "concert",
    ],
    "politician": [
        "senator", "congressman", "congresswoman", "representative",
        "governor", "mayor", "minister", "president", "prime minister",
        "chancellor", "mep", "legislator", "councilor",
    ],
    "sports": [
        "athlete", "player", "footballer", "basketball", "baseball",
        "soccer", "tennis", "olympic", "champion", "coach", "manager",
    ],
    "web": [
        "website", "blog", "podcast", "youtube", "streamer", "influencer",
        "online", "app", "platform", "social media",
    ],
}

# Subject type → applicable SNGs
TYPE_TO_SNGS: Dict[str, List[str]] = {
    "academic": ["NACADEMIC", "ANYBIO"],
    "artist": ["NCREATIVE", "ANYBIO"],
    "author": ["NCREATIVE", "NBOOK", "ANYBIO"],
    "company": ["NCORP"],
    "entertainer": ["NACTOR", "NENTERTAINER", "ANYBIO"],
    "event": ["NEVENT"],
    "film": ["NFILM"],
    "geographic": ["NGEO"],
    "music": ["NMUSIC"],
    "person": ["ANYBIO"],
    "politician": ["NPOL", "ANYBIO"],
    "sports": ["NSPORT", "ANYBIO"],
    "web": ["NWEB"],
}


class NotabilityChecker:
    """Main notability assessment engine."""

    def classify_subject(self, description: str) -> str:
        """
        Auto-classify a subject based on description text.

        Returns the most likely subject type as a string key.
        """
        desc_lower = description.lower()

        scores: Dict[str, int] = {}
        for type_name, keywords in TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > 0:
                scores[type_name] = score

        if not scores:
            return "person"  # Default fallback

        # Return the type with the highest keyword score
        return max(scores, key=scores.get)

    def assess(
        self,
        name: str,
        subject_type: Optional[str] = None,
        description: str = "",
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> NotabilityReport:
        """
        Produce a complete notability assessment.

        Args:
            name: Subject name
            subject_type: Type hint (auto-classified if not provided)
            description: Subject description
            sources: List of source dicts with url, title, type, etc.

        Returns:
            Complete NotabilityReport
        """
        if subject_type is None:
            subject_type = self.classify_subject(description)

        report = NotabilityReport(
            subject_name=name,
            subject_type=subject_type,
            description=description,
        )

        # Determine applicable SNGs
        report.applicable_sngs = TYPE_TO_SNGS.get(subject_type, ["ANYBIO"])

        # Check SNGs
        for sng in report.applicable_sngs:
            result = self.check_sng(sng, description)
            report.sng_results.append(result)
            if result.applicable and result.confidence in ("high", "medium"):
                report.overall_verdict = "notable"
                report.confidence = result.confidence

        # Check GNG (if not already notable via SNG)
        if report.overall_verdict != "notable" or report.confidence == "low":
            gng_result = self.check_gng(sources or [], description)
            report.gng = gng_result
            if gng_result.passed:
                report.overall_verdict = "notable"
                report.confidence = "medium" if gng_result.source_count >= 3 else "low"

        # Check exclusion rules
        report.exclusion_flags = self.check_exclusions(
            subject_type, description, report
        )

        # Generate recommendations
        if report.overall_verdict == "notable":
            if report.exclusion_flags:
                report.recommendations.append(
                    "Subject appears notable but has exclusion flags that need review."
                )
            else:
                report.recommendations.append(
                    "Subject likely meets Wikipedia notability guidelines. "
                    "Proceed with article creation."
                )
        elif report.overall_verdict == "not_notable":
            report.recommendations.append(
                "Subject does not appear to meet notability guidelines. "
                "Consider merging into a broader article or listing for deletion."
            )
        else:
            if not sources:
                report.recommendations.append(
                    "No sources provided for evaluation. "
                    "Please provide at least 2-3 independent reliable sources "
                    "with significant coverage of the subject."
                )
            else:
                report.recommendations.append(
                    "Notability is unclear. Additional sources may be needed, "
                    "or the subject may fit under a different SNG."
                )

        return report

    def check_gng(
        self,
        sources: List[Dict[str, Any]],
        description: str,
    ) -> GNGResult:
        """
        Evaluate sources against the General Notability Guideline.

        GNG test: Significant coverage + Reliable sources + Independent of subject
        + Multiple sources.
        """
        result = GNGResult()

        if not sources:
            result.notes = "No sources provided for evaluation."
            return result

        reliable_count = 0
        independent_count = 0
        significant_count = 0
        unknown_significant_count = 0  # reliable+independent but significance unknown

        for src in sources:
            src_type = src.get("type", "unknown")
            reliable = src.get("reliable", False)
            independent = src.get("independent", True)
            significant = src.get("significant", False)

            # Source type heuristics
            if src_type in ("press_release", "self_published", "blog", "social_media"):
                independent = False
                significant = False
            elif src_type in (
                "academic", "news", "news_article", "news_feature",
                "book", "review", "book_review", "documentary",
            ):
                reliable = reliable if reliable is not None else True

            if reliable:
                reliable_count += 1
            if independent:
                independent_count += 1
            if significant is True:
                significant_count += 1
            elif significant is None and reliable and independent:
                # Reliable+independent source with unknown significance —
                # could be significant, depends on article content
                unknown_significant_count += 1

            result.source_details.append({
                "title": src.get("title", ""),
                "type": src_type,
                "reliable": reliable,
                "independent": independent,
                "significant": significant,
            })

        result.source_count = len(sources)
        result.reliable_sources = reliable_count >= 2
        result.independent_sources = independent_count >= 2
        # Significant coverage can be explicit (True) or implied (reliable+independent
        # from a source type that reasonably could provide significant coverage)
        result.significant_coverage = (
            significant_count >= 1
            or (unknown_significant_count >= 2 and significant_count >= 0)
        )
        # "Multiple sources" means at least 2 sources that are both reliable AND independent
        qualifying = sum(
            1 for sd in result.source_details
            if sd.get("reliable") and sd.get("independent")
        )
        result.multiple_sources = qualifying >= 2

        # Passes GNG if all four conditions met
        result.passed = (
            result.significant_coverage
            and result.reliable_sources
            and result.independent_sources
            and result.multiple_sources
        )

        if result.passed:
            details = []
            if significant_count > 0:
                details.append(f"{significant_count} confirmed significant coverage")
            if unknown_significant_count > 0:
                details.append(f"{unknown_significant_count} additional from reliable+independent sources")
            details.append(f"{reliable_count} reliable")
            details.append(f"{independent_count} independent")
            result.notes = "Passes GNG: " + ", ".join(details) + "."
        else:
            failures = []
            if not result.significant_coverage:
                failures.append("no source with significant coverage")
            if not result.reliable_sources:
                failures.append("fewer than 2 reliable sources")
            if not result.independent_sources:
                failures.append("sources not independent (press releases, self-published)")
            if not result.multiple_sources:
                failures.append("only 1 source")
            result.notes = f"Fails GNG: {', '.join(failures)}."

        return result

    def check_sng(self, sng: str, description: str) -> SNGResult:
        """
        Check a subject against a specific SNG.

        Returns an SNGResult indicating if the SNG applies and which criteria are met.
        """
        desc_lower = description.lower()
        result = SNGResult(sng=sng, applicable=False)

        if sng == "NACADEMIC":
            criteria = []
            # Criterion 1: Named chair
            if "named chair" in desc_lower or "distinguished professor" in desc_lower:
                criteria.append("Named chair or distinguished professorship")
            # Criterion 3: Major award
            if any(award in desc_lower for award in [
                "nobel", "fields medal", "turing", "macarthur", "pulitzer",
                "wolf prize", "abbott", "kyoto prize", "crafoord",
                "national medal of science", "breakthrough prize",
            ]):
                criteria.append("Major academic award")
            # Criterion 5: Learned society
            if any(society in desc_lower for society in [
                "fellow of the royal society", "national academy",
                "american academy", "aaas fellow", "academia europaea",
                "fellow of", "member of the national academy",
            ]):
                criteria.append("Fellow of prestigious learned society")
            # Criterion 4: Editorial role
            if "editor-in-chief" in desc_lower or "editorial board" in desc_lower:
                criteria.append("Editorial role at top journal")

            if criteria:
                result.applicable = True
                result.criteria_met = criteria
                result.confidence = "high"
                result.details = f"Meets NACADEMIC: {'; '.join(criteria)}"
            else:
                # NACADEMIC may still apply but no criteria found in description
                result.applicable = True  # Still applicable type
                result.confidence = "low"
                result.details = "Subject is an academic but no specific NACADEMIC criteria found in description."

        elif sng == "ANYBIO":
            criteria = []
            if any(award in desc_lower for award in [
                "nobel", "pulitzer", "oscar", "academy award", "grammy",
                "emmy", "tony", "booker", "fields medal", "turing",
                "national medal", "presidential", "medal of honor",
                "knight", "dame", "order of",
            ]):
                criteria.append("Major award or honor")
            if "biographical dictionary" in desc_lower or "dnb" in desc_lower:
                criteria.append("Entry in national biographical dictionary")

            if criteria:
                result.applicable = True
                result.criteria_met = criteria
                result.confidence = "high"
                result.details = f"Meets ANYBIO: {'; '.join(criteria)}"

        elif sng == "NCREATIVE":
            criteria = []
            if any(word in desc_lower for word in [
                "exhibition at", "museum", "gallery", "biennale",
                "retrospective", "permanent collection",
            ]):
                criteria.append("Major exhibition or museum representation")
            if "review" in desc_lower and any(
                w in desc_lower for w in ["critically", "acclaim", "best-selling", "bestseller"]
            ):
                criteria.append("Independent critical attention")

            if criteria:
                result.applicable = True
                result.criteria_met = criteria
                result.confidence = "medium"
                result.details = f"Meets NCREATIVE: {'; '.join(criteria)}"

        elif sng == "NPOL":
            criteria = []
            if any(office in desc_lower for office in [
                "senator", "congressman", "congresswoman", "member of parliament",
                "governor", "minister", "president", "prime minister",
                "chief justice", "justice", "judge", "mayor",
                "lieutenant governor", "attorney general", "secretary of",
                "ambassador", "speaker", "mep", "mp for",
            ]):
                criteria.append("Held notable political office")

            if criteria:
                result.applicable = True
                result.criteria_met = criteria
                result.confidence = "high" if any(
                    office in desc_lower for office in [
                        "senator", "congressman", "governor", "minister",
                        "president", "prime minister", "chief justice",
                    ]
                ) else "medium"
                result.details = f"Meets NPOL: {'; '.join(criteria)}"

        elif sng == "NSPORT":
            criteria = []
            if any(level in desc_lower for level in [
                "olympic", "world champion", "world cup", "professional",
                "nba", "nfl", "mlb", "nhl", "epl", "la liga",
                "grand slam", "tour de france", "formula one",
                "ufc", "world series", "super bowl", "stanley cup",
            ]):
                criteria.append("Competed at highest professional or international level")

            if criteria:
                result.applicable = True
                result.criteria_met = criteria
                result.confidence = "high"
                result.details = f"Meets NSPORT: {'; '.join(criteria)}"

        elif sng == "NCORP":
            result.applicable = True
            # NCORP is hard to auto-evaluate from description alone
            result.confidence = "low"
            result.details = (
                "NCORP requires significant coverage in reliable independent sources. "
                "Specific descriptions of coverage needed for assessment."
            )

        elif sng == "NGEO":
            result.applicable = True
            if any(place in desc_lower for place in [
                "city", "town", "village", "mountain", "river", "lake",
                "island", "county", "state", "province", "national park",
            ]):
                result.criteria_met = ["Named geographic feature"]
                result.confidence = "high"
                result.details = "Named populated place or natural feature — generally notable per NGEO."
            else:
                result.confidence = "low"
                result.details = "Geographic feature but type unclear."

        elif sng == "NMUSIC":
            criteria = []
            if any(term in desc_lower for term in [
                "chart", "billboard", "gold record", "platinum",
                "grammy", "mtv award", "major label",
            ]):
                criteria.append("Charted or certified or major award")
            if "review" in desc_lower:
                criteria.append("Multiple independent reviews")

            if criteria:
                result.applicable = True
                result.criteria_met = criteria
                result.confidence = "medium"
                result.details = f"Meets NMUSIC: {'; '.join(criteria)}"

        elif sng == "NFILM":
            result.applicable = True
            if "released" in desc_lower or "premiered" in desc_lower:
                if "review" in desc_lower:
                    result.criteria_met = ["Released film with reviews"]
                    result.confidence = "medium"
                    result.details = "Film appears to meet NFILM criteria."
                else:
                    result.confidence = "low"
                    result.details = "Film released but no review information provided."
            elif "not yet released" in desc_lower or "pre-production" in desc_lower:
                result.confidence = "low"
                result.details = "Unreleased film — WP:NFF applies."

        elif sng == "NEVENT":
            result.applicable = True
            result.confidence = "low"
            result.details = (
                "NEVENT requires persistent coverage beyond the news cycle. "
                "Cannot assess without source timeline data."
            )

        elif sng == "NWEB":
            result.applicable = True
            result.confidence = "low"
            result.details = (
                "NWEB is very strict. Requires significant coverage in "
                "independent reliable sources. Social media metrics are not evidence."
            )

        elif sng == "NBOOK":
            result.applicable = True
            if "review" in desc_lower and (
                "book" in desc_lower or "novel" in desc_lower or "published" in desc_lower
            ):
                result.criteria_met = ["Multiple independent reviews"]
                result.confidence = "medium"
                result.details = "Book has reviews in independent sources — likely meets NBOOK."

        elif sng == "NASTRO":
            result.applicable = True
            if any(term in desc_lower for term in [
                "exoplanet", "confirmed exoplanet", "numbered asteroid",
                "ngc ", "ic ", "messier", "named comet", "periodic comet",
                "supernova",
            ]):
                result.criteria_met = ["Confirmed or cataloged astronomical object"]
                result.confidence = "high"
                result.details = "Confirmed astronomical object — generally notable per NASTRO."
            else:
                result.confidence = "low"
                result.details = "Astronomical object type unclear. Confirmed exoplanets, numbered asteroids, NGC/IC objects, and named comets are notable."

        elif sng == "NNUMBER":
            # Numbers 1-99 are generally notable. Others need mathematical significance.
            result.applicable = True
            desc_number = desc_lower.strip()
            # Simple check: is the description a number or about a number?
            import re as _re
            number_match = _re.search(r'\b([1-9][0-9]?)\b', desc_number)
            if number_match:
                n = int(number_match.group(1))
                if 1 <= n <= 99:
                    result.criteria_met = [f"Number between 1 and 99 — per NNUMBER"]
                    result.confidence = "high"
                    result.details = f"Number {n} is generally notable per NNUMBER."
                    return result
            if any(term in desc_lower for term in ["constant", "π", "pi", "euler", "fibonacci"]):
                result.criteria_met = ["Mathematically significant number"]
                result.confidence = "medium"
                result.details = "Mathematically significant — likely meets NNUMBER."
            else:
                result.confidence = "low"
                result.details = "Most numbers beyond 99 are not notable. Only 1-99 and mathematically significant numbers have articles."

        elif sng == "NSPECIES":
            result.applicable = True
            if any(term in desc_lower for term in [
                "species", "subspecies", "taxon", "described",
                "genus", "family", "order", "class", "phylum",
            ]):
                result.criteria_met = ["Described species or higher taxon"]
                result.confidence = "high"
                result.details = "All described species are presumed notable per NSPECIES."
            else:
                result.confidence = "low"
                result.details = "NSPECIES: All described species are notable. Undescribed or hypothetical species are not."

        # Default for unhandled SNGs
        if not result.criteria_met and result.applicable and result.details:
            pass  # Keep as-is

        return result

    def check_exclusions(
        self,
        subject_type: str,
        description: str,
        report: NotabilityReport,
    ) -> List[str]:
        """
        Check for common exclusion rules that might override notability.

        Returns a list of exclusion flags found.
        """
        flags = []
        desc_lower = description.lower()

        # BLP1E: Person notable for only one event
        if subject_type == "person" and any(
            term in desc_lower for term in [
                "survivor of", "witness to", "victim of", "only known for",
            ]
        ):
            flags.append(
                "WP:BIO1E: Subject may be notable only for a single event. "
                "Consider merging into event article."
            )

        # NOTINHERITED: Notable by association
        if any(term in desc_lower for term in [
            "spouse of", "child of", "parent of", "sibling of", "wife of",
            "husband of", "daughter of", "son of",
        ]):
            flags.append(
                "WP:NOTINHERITED: Notability is not inherited. "
                "Subject must have independent notability."
            )

        # SPIP: Self-promotion / publicity
        if any(term in desc_lower for term in [
            "press release", "self-published", "autobiography", "pr campaign",
        ]):
            flags.append(
                "WP:SPIP: Sources may be promotional or non-independent."
            )

        # NOTNEWS: Routine coverage
        if any(term in desc_lower for term in [
            "announced", "launched", "opened", "appointed",
            "hired", "promoted", "routine",
        ]):
            if subject_type in ("event", "company", "person"):
                flags.append(
                    "WP:NOTNEWS: Verify that coverage is not routine. "
                    "Routine announcements do not establish notability."
                )

        return flags


# ---- CLI ----
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Assess Wikipedia notability of a subject"
    )
    parser.add_argument("name", help="Subject name")
    parser.add_argument("--type", help="Subject type (academic, artist, company, etc.)")
    parser.add_argument("--description", "-d", required=True, help="Subject description")
    parser.add_argument("--source", "-s", action="append",
                        help="Source URL or pipe-delimited metadata. "
                             "Bare URLs are auto-classified. "
                             "Pipe format: title|type|reliable|independent|significant "
                             "(e.g., 'Nature article|academic|yes|yes|yes'). "
                             "Can be repeated.")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--afd", action="store_true", help="Output AfD-ready summary")
    parser.add_argument("--short", action="store_true", help="One-line summary")

    args = parser.parse_args()

    checker = NotabilityChecker()
    sources = []

    # Import SourceEvaluator for auto-classification of raw URLs
    from source_evaluator import SourceEvaluator
    source_eval = SourceEvaluator()

    if args.source:
        for s in args.source:
            parts = s.split("|")
            has_pipes = len(parts) > 1

            if has_pipes:
                # Pipe-delimited format: title|type|reliable|independent|significant
                src = {"title": parts[0] if len(parts) > 0 else ""}
                if len(parts) > 1:
                    src["type"] = parts[1]
                if len(parts) > 2:
                    src["reliable"] = parts[2].lower() in ("yes", "true", "1")
                if len(parts) > 3:
                    src["independent"] = parts[3].lower() in ("yes", "true", "1")
                if len(parts) > 4:
                    src["significant"] = parts[4].lower() in ("yes", "true", "1")
            else:
                # Bare URL — auto-classify using SourceEvaluator
                url = parts[0]
                cls = source_eval.classify_source(url=url)
                ev = source_eval.evaluate(url=url, source_type=cls)
                src = {
                    "title": url,
                    "url": url,
                    "type": cls,
                    "reliable": ev["reliable"],
                    "independent": ev["independent"],
                    "significant": ev["significant"],
                }
            sources.append(src)

    report = checker.assess(
        name=args.name,
        subject_type=args.type,
        description=args.description,
        sources=sources,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    elif args.afd:
        from notability_templates import generate_afd_summary
        print(generate_afd_summary(report))
    elif args.short:
        from notability_templates import format_short
        print(format_short(report))
    else:
        from notability_templates import format_report
        print(format_report(report))
