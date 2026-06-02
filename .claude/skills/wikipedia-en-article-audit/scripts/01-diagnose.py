#!/usr/bin/env python3
"""
01-diagnose.py — Phase 1: Article Diagnosis

Fetches a Wikipedia article and produces a structured diagnosis:
  - diagnosis.json   (structural findings, article type, NPOV flags, sources summary)
  - sentences.jsonl  (one JSON line per sentence with metadata)
  - sources/         (raw wikitext, talk page, Wikidata entity)

Usage:
  python3 scripts/01-diagnose.py "Pyrrhus Concer"
  python3 scripts/01-diagnose.py "He Tingbo" --project-dir /tmp/my-audit
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote

USER_AGENT = "WikipediaArticleAudit/1.0 (skill; contact via pi agent)"
API_URL = "https://en.wikipedia.org/w/api.php"
REST_URL = "https://en.wikipedia.org/api/rest_v1"
WIKIDATA_URL = "https://www.wikidata.org/wiki/Special:EntityData"

# ── NPOV trigger words ──────────────────────────────────────────────

NPOV_TRIGGERS = {
    "editorial_praise": [
        "undoubtedly", "unquestionably", "clearly", "obviously",
        "notably", "noteworthy", "interestingly", "importantly",
        "remarkably", "impressively", "extraordinarily",
        "incomparably", "unbeatably", "famously", "notoriously",
        "renowned", "legendary", "pioneering", "world-class",
        "visionary", "iconic", "groundbreaking", "transformative",
    ],
    "original_research": [
        "it is possible that", "it is likely that", "it is plausible that",
        "it seems that", "one can imagine that",
        "may have been", "might have been", "could have been",
        "was likely", "was probably", "appears to have been",
        "suggests that", "is suggestive of", "is indicative of",
    ],
    "essay_conclusions": [
        "a testament to", "serves as a testament",
        "speaks to his", "speaks to her", "speaks to their",
        "is a testament", "stands as a testament",
        "demonstrates his", "demonstrates her",
        "reflects his", "reflects her",
    ],
    "weasel_words": [
        "some say", "many believe", "it is said that",
        "critics claim", "it is widely regarded",
        "is considered to be", "is thought to be",
        "is often described as", "has been called",
    ],
    "blp_sensitive": [
        "controversial", "alleged", "scandal", "infamous",
        "notorious", "disgraced", "embattled",
    ],
}

SHORT_DESC_DEMONYM_PATTERNS = [
    (r'\bChina\s+(businesswoman|businessman|engineer|scientist|politician|executive|entrepreneur)', 'Chinese'),
    (r'\bAmerica\s+(businesswoman|businessman|engineer|scientist|politician|executive)', 'American'),
    (r'\bBritain\s+(businesswoman|businessman|engineer|scientist|politician|executive)', 'British'),
]

ARTICLE_TYPES = {
    "BLP": {
        "keywords": ["Living people"],
        "expected_sections": ["Early life", "Career", "Personal life", "Awards"],
    },
    "biography_general": {
        "keywords": [],
        "expected_sections": ["Early life", "Career", "Later life", "Legacy"],
    },
    "biography_executive": {
        "keywords": ["business", "executive", "chief executive", "director"],
        "expected_sections": ["Early life", "Career", "Board positions", "Awards", "Personal life"],
    },
    "biography_academic": {
        "keywords": ["scientist", "engineer", "professor", "researcher", "academic"],
        "expected_sections": ["Education", "Career", "Research", "Selected works", "Awards"],
    },
}


# ── HTTP helpers ────────────────────────────────────────────────────

def api_call(params):
    """Call the MediaWiki Action API."""
    params["format"] = "json"
    params["origin"] = "*"
    qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    url = f"{API_URL}?{qs}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def fetch_text(url):
    """Fetch a URL and return text content."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


# ── Phase 1a: Resolve title ────────────────────────────────────────

def resolve_title(title):
    """Resolve redirects and check for disambiguation."""
    data = api_call({"action": "query", "titles": title, "redirects": 1})
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if pid == "-1":
            return {"error": f"Page '{title}' does not exist."}
        if "missing" in page:
            return {"error": f"Page '{title}' is missing."}
        return {
            "pageid": page["pageid"],
            "title": page["title"],
            "canonical_title": page["title"],
        }
    return {"error": f"Could not resolve '{title}'."}


# ── Phase 1b: Fetch components ─────────────────────────────────────

def fetch_article_components(title, project_dir):
    """Fetch wikitext, talk page, page info, categories, templates, Wikidata."""
    sources_dir = project_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Wikitext
    wt = fetch_text(
        f"https://en.wikipedia.org/w/index.php?title={quote(title)}&action=raw"
    )
    (sources_dir / "article.wikitext").write_text(wt)

    # Talk page
    talk_wt = fetch_text(
        f"https://en.wikipedia.org/w/index.php?title=Talk:{quote(title)}&action=raw"
    )
    (sources_dir / "talk.wikitext").write_text(talk_wt)

    # Page info
    info = api_call({
        "action": "query", "prop": "info|pageprops|categories|templates",
        "titles": title,
        "inprop": "protection",
        "cllimit": 100,
        "tllimit": 500,
    })
    pages = info.get("query", {}).get("pages", {})
    page_data = {}
    for pid, p in pages.items():
        page_data = p
        break

    # Wikidata
    wd_id = page_data.get("pageprops", {}).get("wikibase_item", "")
    if wd_id:
        try:
            wd = fetch_text(f"{WIKIDATA_URL}/{wd_id}.json")
            (sources_dir / "wikidata.json").write_text(wd)
        except Exception:
            pass

    return wt, talk_wt, page_data


# ── Phase 1c: Structural audit ─────────────────────────────────────

def classify_article(categories, infobox_type, blp_status):
    """Determine article type from categories and infobox."""
    cat_text = " ".join(c.lower() for c in categories)

    if blp_status or "living people" in cat_text:
        return "BLP"
    if any("births" in c for c in categories):
        for atype, info in ARTICLE_TYPES.items():
            if atype == "BLP":
                continue
            if info["keywords"] and any(kw in cat_text for kw in info["keywords"]):
                return atype
        return "biography_general"
    return "topic_article"


def structural_audit(wt, talk_wt, page_data):
    """Run structural checks and return findings."""
    findings = {}

    # Short description
    sd_match = re.search(r'\{\{Short description\|(.+?)\}\}', wt)
    findings["short_description"] = sd_match.group(1) if sd_match else None
    findings["short_description_issues"] = []
    if sd_match:
        sd = sd_match.group(1)
        for pattern, correct in SHORT_DESC_DEMONYM_PATTERNS:
            if re.search(pattern, sd, re.IGNORECASE):
                findings["short_description_issues"].append(
                    f"'{sd}' uses '{pattern.pattern.split(chr(92)+'b')[0].strip(chr(92))}' "
                    f"as a modifier — should be '{correct}'"
                )

    # Infobox
    infobox_match = re.search(r'\{\{(Infobox[^}]*)\}\}', wt, re.DOTALL)
    findings["has_infobox"] = infobox_match is not None
    infobox_type = None
    if infobox_match:
        infobox_type = infobox_match.group(1).split("|")[0].strip()
    findings["infobox_type"] = infobox_type

    # Sections
    sections = re.findall(r'^==\s*(.+?)\s*==$', wt, re.MULTILINE)
    findings["sections"] = sections
    findings["section_count"] = len(sections)

    # Categories
    categories = re.findall(r'\[\[Category:(.+?)\]\]', wt)
    findings["categories"] = categories
    findings["category_count"] = len(categories)

    # Article type
    blp_status = "blp=yes" in talk_wt.lower()
    findings["blp"] = blp_status
    article_type = classify_article(categories, infobox_type, blp_status)
    findings["article_type"] = article_type

    # Expected sections check
    expected = ARTICLE_TYPES.get(article_type, {}).get("expected_sections", [])
    section_names = [s.strip().lower() for s in sections]
    missing_sections = [
        e for e in expected
        if not any(e.lower() in sn or sn.startswith(e.lower().split()[0]) for sn in section_names)
    ]
    findings["missing_expected_sections"] = missing_sections

    # Protection
    protection = page_data.get("protection", [])
    findings["protection"] = [p.get("type") for p in protection] if protection else "none"

    # Length
    findings["length_bytes"] = len(wt)

    # Images
    findings["has_lead_image"] = "[[File:" in wt[:2000] or "[[Image:" in wt[:2000]
    findings["current_images"] = re.findall(r'\[\[(?:File|Image):(.+?)\]\]', wt)
    findings["commons_category"] = None
    cc = re.search(r'\[\[Category:Pyrrhus_Concer\]\]', wt)
    if not cc:
        cc = re.findall(r'Commons category', wt)
    # Approximate Commons check
    findings["image_notes"] = "Check Commons: https://commons.wikimedia.org/wiki/Category:{PAGENAME}"

    # Assessment
    assessment_match = re.search(r'class=(\w+)', talk_wt)
    findings["current_assessment"] = assessment_match.group(1) if assessment_match else "unknown"

    # References
    ref_count = len(re.findall(r'<ref[ >]', wt))
    cite_count = len(re.findall(r'\{\{cite ', wt, re.IGNORECASE))
    findings["reference_count"] = max(ref_count, cite_count)
    findings["citation_templates"] = list(set(re.findall(r'\{\{(cite\w+)', wt, re.IGNORECASE)))

    # Maintenance templates
    maintenance = []
    for mt in ["citation needed", "POV", "expand section", "dead link", "Orphan", "stub"]:
        if mt.lower() in wt.lower():
            maintenance.append(mt)
    findings["maintenance_templates"] = maintenance

    return findings


# ── Phase 1d: NPOV scan ────────────────────────────────────────────

def npov_scan(wt):
    """Scan article text for NPOV trigger words and phrases."""
    # Strip refs, templates, wikilinks for plain text scan
    text = wt
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*/>', '', text)
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]|]*)\]\]', r'\1', text)
    text = re.sub(r"'''?", '', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'^==+.*?==+\s*$', '', text, flags=re.MULTILINE)

    flags = []
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z\"\'])', text.strip())
    for i, s in enumerate(sentences, 1):
        s_clean = s.strip()
        if len(s_clean) < 15:
            continue
        for category, triggers in NPOV_TRIGGERS.items():
            for trigger in triggers:
                if trigger.lower() in s_clean.lower():
                    flags.append({
                        "sentence_index": i,
                        "text": s_clean[:200],
                        "trigger": trigger,
                        "category": category,
                    })
                    break  # one flag per sentence per category

    return flags


# ── Phase 1e: Extract sentences ────────────────────────────────────

def extract_sentences(wt):
    """Split article body into individual sentences with metadata."""
    text = wt
    # Remove infobox block
    text = re.sub(r'\{\{Infobox[^}]*\}\}', '', text)
    # Remove all templates iteratively (handles nesting)
    for _ in range(10):
        new_text = re.sub(r'\{\{[^{}]*\}\}', '', text)
        if new_text == text:
            break
        text = new_text
    # Remove ref tags
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*/>', '', text)
    # Extract wikilink display text
    text = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]|]*)\]\]', r'\1', text)
    text = re.sub(r"'''?", '', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'^==+.*?==+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\s*\n', '\n', text).strip()

    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    sentences = []
    for i, s in enumerate(raw, 1):
        s = s.strip()
        if len(s) < 20 or s.startswith('|') or '|' in s[:5]:
            continue
        section = "lead" if i <= 4 else "body"
        sentences.append({
            "index": i,
            "text": s,
            "section": section,
            "verdict": None,
        })
    return sentences


# ── Phase 1f: Extract citations ────────────────────────────────────

def extract_citations(wt, sentences):
    """Extract citation metadata from <ref> blocks."""
    refs = re.findall(r'<ref[^>]*>(.*?)</ref>', wt, re.DOTALL)
    citations = []
    for i, ref_content in enumerate(refs):
        content = ref_content.strip()
        if not content:
            continue
        # Get a readable label: prefer title, then first 80 chars
        title_m = re.search(r'title\s*=\s*([^|}"]+)', content, re.IGNORECASE)
        label = title_m.group(1).strip()[:70] if title_m else content[:70].replace('\n', ' ')
        # Extract URL if present
        url_m = re.search(r'url\s*=\s*([^\s|}"]+)', content, re.IGNORECASE)
        url = url_m.group(1) if url_m else None
        citations.append({
            "ref_index": i,
            "short_ref": label,
            "url": url,
            "accessible": None,
            "sentences_supported": [],
        })
    return citations


# ── Output ──────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 01-diagnose.py 'Article Title' [--project-dir DIR]")
        sys.exit(1)

    title = sys.argv[1]
    project_dir = Path(sys.argv[3]) if len(sys.argv) > 2 and sys.argv[2] == "--project-dir" else Path.cwd()

    print(f"🔍 Diagnosing: {title}")
    print(f"📁 Project dir: {project_dir}")

    # 1a. Resolve
    resolved = resolve_title(title)
    if "error" in resolved:
        print(f"❌ {resolved['error']}")
        sys.exit(1)
    print(f"   Resolved to: {resolved['title']} (page ID {resolved['pageid']})")

    # 1b. Fetch components
    wt, talk_wt, page_data = fetch_article_components(title, project_dir)
    print(f"   Wikitext: {len(wt)} bytes")

    # 1c. Article-type + structural audit
    findings = structural_audit(wt, talk_wt, page_data)
    print(f"   Type: {findings['article_type']}")
    print(f"   Infobox: {'✅' if findings['has_infobox'] else '❌'} ({findings['infobox_type'] or 'missing'})")
    print(f"   Assessment: {findings['current_assessment']}")
    print(f"   Sections: {findings['section_count']} ({findings['sections']})")
    print(f"   Categories: {findings['category_count']}")
    print(f"   References: ~{findings['reference_count']}")

    if findings["short_description_issues"]:
        for issue in findings["short_description_issues"]:
            print(f"   ⚠️ Short description: {issue}")

    if findings["missing_expected_sections"]:
        print(f"   ⚠️ Missing expected sections: {', '.join(findings['missing_expected_sections'])}")

    # 1d. NPOV scan
    npov_flags = npov_scan(wt)
    if npov_flags:
        print(f"   ⚠️ NPOV flags: {len(npov_flags)}")
        for f in npov_flags[:5]:
            print(f"      S{f['sentence_index']}: [{f['category']}] '{f['trigger']}'")
        if len(npov_flags) > 5:
            print(f"      ... and {len(npov_flags) - 5} more")

    # 1e. Extract sentences
    sentences = extract_sentences(wt)
    print(f"   Sentences: {len(sentences)}")

    # 1f. Extract citations
    citations = extract_citations(wt, sentences)

    # Build diagnosis
    diagnosis = {
        "article_title": resolved["title"],
        "page_id": resolved["pageid"],
        "article_type": findings["article_type"],
        "blp": findings["blp"],
        "structural": findings,
        "npov_flags": npov_flags,
        "citations": citations,
        "sources_summary": citations,
    }

    # Write outputs
    (project_dir / "diagnosis.json").write_text(json.dumps(diagnosis, indent=2))
    with open(project_dir / "sentences.jsonl", "w") as f:
        for s in sentences:
            f.write(json.dumps(s) + "\n")

    print(f"\n✅ Diagnosis written to:")
    print(f"   {project_dir / 'diagnosis.json'}")
    print(f"   {project_dir / 'sentences.jsonl'}")
    print(f"   {project_dir / 'sources/'}")

    return diagnosis


if __name__ == "__main__":
    main()
