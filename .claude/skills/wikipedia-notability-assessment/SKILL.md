---
name: wikipedia-notability-assessment
description: Evaluate whether a subject meets Wikipedia notability guidelines — the General Notability Guideline (GNG), all 13 subject-specific SNGs with decision trees, source quality evaluation, structured report generation, AfD-ready summaries, and common invalid arguments
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["notability", "notable", "WP:GNG", "WP:N", "article deletion", "AfD", "should this exist"]
  - keywords: ["SNG", "NACADEMIC", "NCORP", "NMUSIC", "NGEO", "BIO", "notability guideline"]
  - keywords: ["source evaluation", "reliable source", "independent source", "significant coverage"]
  - keywords: ["article creation", "notability assessment", "subject-specific notability"]
last_verified: 2026-06-11
depends_on: [wikimedia-api-access]
---

> ⚠️ **User-Agent required:** API examples in this skill access Wikipedia. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for User-Agent format and rate limiting.

> 💡 **Related skills:** For *how to write* an article once notability is confirmed, see **[wikipedia-en-biography-writing](../wikipedia-en-biography-writing/SKILL.md)** and the general article drafting guidance. For *how to delete* a non-notable article, see the proposed deletion-processes skill. For *how to patrol* new pages, see **[wikipedia-pagetriage-api](../wikipedia-pagetriage-api/SKILL.md)**.

---

## Table of Contents

1. [What Notability Is and Why It Matters](#what-notability-is-and-why-it-matters)
2. [SOP: The GNG — The Four-Element Test](#sop-the-gng--the-four-element-test)
3. [SOP: The 13 Subject-Specific Notability Guidelines](#sop-the-13-subject-specific-notability-guidelines)
4. [SOP: WP:BIO Sub-Criteria (8 Paths)](#sop-wpbio-sub-criteria-8-paths)
5. [SOP: Source Quality Assessment](#sop-source-quality-assessment)
6. [SOP: What Never Counts](#sop-what-never-counts)
7. [SOP: Producing a Structured Notability Report](#sop-producing-a-structured-notability-report)
8. [SOP: Special Topics](#sop-special-topics)
9. [Guardrails](#guardrails)
10. [Cross-References](#cross-references)

---

## What Notability Is and Why It Matters

Notability is Wikipedia's test for whether a topic warrants **its own article**. It is defined by the [General Notability Guideline](https://en.wikipedia.org/wiki/Wikipedia:Notability) (WP:GNG) and elaborated by [Subject-Specific Notability Guidelines](https://en.wikipedia.org/wiki/Wikipedia:Notability#Subject-specific_notability_guidelines) (SNGs).

**Key principles:**

| Principle | Shortcut | Meaning |
|-----------|----------|---------|
| Notability ≠ fame | WP:NFAME | Someone can be famous but not notable; someone can be notable but not famous. Notability is about *coverage*, not *popularity*. |
| Notability ≠ article quality | WP:CONTN | A beautifully written article makes a subject no more notable. A poorly sourced article makes a subject no less notable. Notability is about the *subject*, not the *article*. |
| Notability is not inherited | WP:NOTINHERITED | Being Elon Musk's child does not make you notable. The child must have independent coverage. |
| Notability is based on existing sources, not in-article citations | WP:NEXIST | If sources exist in the real world, the subject is notable even if no one has cited them yet. |
| Notability is not temporary | WP:NTEMP | Once a subject has significant coverage, it doesn't need ongoing coverage to remain notable. |
| Notability is presumed, not guaranteed | WP:GNG | Meeting GNG or an SNG creates a *presumption* of notability. Deletion discussions may still determine against inclusion (e.g., due to WP:NOT). |

### What notability is NOT

```
Notability ≠ Famous, Important, Well-known, Popular, Google hits, YouTube views
Notability ≠ Well-written article, Lots of blue links, Exists on other Wikipedias
Notability ≠ Published by major publisher, Has IMDb page, Has LinkedIn profile
```

### The notability decision tree (simplified)

```
Does the subject have significant coverage in multiple
reliable, independent sources (GNG)?
├── Yes → Likely notable (subject may have its own article)
├── No → Does it meet any Subject-Specific Notability Guideline (SNG)?
│   ├── Yes → Presumed notable
│   └── No → Does it fail any exclusion criteria (BLP1E, NOTNEWS, etc.)?
│       └── Likely not notable → Merge, redirect, or delete
```

---

## SOP: The GNG — The Four-Element Test

The GNG has four elements. ALL four must be present:

### 1. Significant Coverage (WP:SIGCOV)

The source must address the subject **directly and in detail**, not just mention it in passing.

```python
# What counts as significant coverage:
- Feature-length newspaper or magazine profile
- In-depth academic analysis (journal article, book chapter)
- Book-length treatment or dedicated biography
- Documentary film focused on the subject
- Multiple paragraphs in a major reference work

# What does NOT count:
- "He was born in Boston and attended Harvard" (two sentences in a larger article)
- "The company was founded in 2010" (routine announcement)
- "Also appearing was..." (passing mention in event coverage)
- Trivial directory listing, database entry, or search result
```

**Test:** Could you write 3+ substantial paragraphs about the subject using ONLY this source? If no, it's not significant coverage.

### 2. Reliable Sources (WP:RS)

The source must have editorial oversight, fact-checking, and a reputation for accuracy.

| Tier | Examples | Contributes to Notability? |
|------|----------|---------------------------|
| **High** | Peer-reviewed journals, major newspapers (NYT, Guardian, Reuters), books from academic presses | ✅ Yes |
| **Medium** | Trade publications, reputable magazines (Wired, The Atlantic), local newspapers | ✅ Yes, but weight accordingly |
| **Low** | Personal blogs, self-published books, company websites, press releases | ❌ No |
| **Never** | Wikipedia, IMDb, Social media, forums, user-generated content | ❌ No |

### 3. Independent of the Subject (WP:INDY)

The source must not be produced by, paid by, or affiliated with the subject.

```
Independent:      Newspaper article by a journalist who doesn't work for the subject
Not independent:  Press release from the subject's PR firm
Not independent:  The subject's autobiography or memoir
Not independent:  The subject's company website or annual report
Not independent:  An interview (the subject's own words are primary, not independent)
```

### 4. Multiple Sources

Multiple **independent** sources are required. Note that:
- Multiple articles from the **same wire service** (AP, Reuters) count as ONE source
- Multiple articles by the **same author** (re-reporting same information) count as ONE source
- Multiple articles **from the same press release** (churnalism) count as ONE source

**The four-element test in code:**

```python
from notability_checker import NotabilityChecker

checker = NotabilityChecker()
report = checker.assess(
    name="Jane Smith",
    subject_type="academic",
    description="Professor of quantum physics at MIT",
    sources=[
        {"title": "Nature profile", "type": "news_feature",
         "reliable": True, "independent": True, "significant": True},
        {"title": "NYT article about her research",
         "type": "news_article", "reliable": True,
         "independent": True, "significant": True},
    ],
)
print(report.overall_verdict)  # "notable" or "not_notable" or "unclear"
```

---

## SOP: The 13 Subject-Specific Notability Guidelines

Each SNG is a specialized test for a specific topic area. Meeting **any one** SNG creates a presumption of notability, even if the GNG is not met.

See **[references/sng-decision-trees.md](references/sng-decision-trees.md)** for detailed decision tree cards for each SNG.

### Quick Reference Table

| # | SNG | Shortcut | Who | Key Test |
|---|-----|----------|-----|----------|
| 1 | Academics | WP:NACADEMIC | Scholars, researchers | Named chair, major award, highly cited, learned society fellow (8 criteria, any 1) |
| 2 | Astronomical objects | WP:NASTRO | Celestial objects | Confirmed exoplanet, numbered asteroid, NGC object |
| 3 | Books | WP:NBOOK | Published works | Multiple independent reviews OR major literary award OR verified bestseller |
| 4 | Events | WP:NEVENT | Occurrences | Persistent coverage beyond news cycle, lasting impact |
| 5 | Films | WP:NFILM | Movies | Publicly released, multiple reviews (WP:NFF for unreleased) |
| 6 | Geographic features | WP:NGEO | Places, natural features | Named populated place or natural feature → notable |
| 7 | Music | WP:NMUSIC | Musicians, bands, albums | Charted, certified, major label, major award (12 criteria, any 1) |
| 8 | Numbers | WP:NNUMBER | Integers, constants | Only 1–99 and mathematically significant numbers |
| 9 | Organizations & companies | WP:NCORP | Businesses, non-profits | Strictest SNG — significant independent coverage required |
| 10 | People | WP:BIO | All biographical subjects | Umbrella — see sub-criteria below |
| 11 | Species | WP:NSPECIES | Biological taxa | All described species presumed notable |
| 12 | Sports | WP:NSPORT | Athletes, teams | Competed at highest professional or major international level |
| 13 | Web content | WP:NWEB | Websites, podcasts, influencers | Very strict — significant independent coverage required |

### Using the SNG Checker

```python
from notability_checker import NotabilityChecker

checker = NotabilityChecker()

# Auto-classify subject type from description
subject_type = checker.classify_subject(
    "A peer-reviewed study on quantum entanglement published in Nature"
)
# → "academic"

# Check a specific SNG
result = checker.check_sng("NPOL", 
    "Senator from California, served 2000-2010")
print(result.criteria_met)  # ["Held notable political office"]
print(result.confidence)    # "high"
```

### Key SNG Details

**WP:NACADEMIC** — 8 criteria, any ONE sufficient:
1. Named chair or distinguished professorship
2. Highly cited (field-dependent)
3. Major academic award (Fields, Nobel, Turing, MacArthur, etc.)
4. Editorial role at top journal
5. Fellow of prestigious learned society (NAS, Royal Society, etc.)
6. Highly influential monograph/textbook
7. Research with major impact on policy/practice
8. Substantial entry in major reference work

**WP:NCORP** — The strictest SNG. Requires:
- Multiple independent reliable sources with **significant** coverage
- Press releases, product announcements, and routine business coverage do NOT count
- Being a public company or Fortune 500 does NOT guarantee notability
- See also: most K-12 schools are not notable; universities generally are

**WP:NMUSIC** — 12 criteria, any ONE sufficient:
- Charted on national/international chart
- Gold record or higher certification
- Album on major or notable independent label
- Major music award nomination/win
- Multiple independent reviews in notable publications
- Significant national radio airplay

---

## SOP: WP:BIO Sub-Criteria (8 Paths)

The People guideline (WP:BIO) contains 8 distinct paths. Check ANYBIO first (quickest pass).

### Quick Decision Tree

```
ANYBIO → Quick check:
  ├── Major award/honor? → Notable
  ├── Enduring historical record? → Notable
  ├── National biographical dictionary entry? → Notable
  └── None → Check specific sub-path:

1. NACADEMIC → Scholars, researchers (8 criteria)
2. NCREATIVE → Authors, artists, architects, journalists (4 criteria)
3. NENTERTAINER → Actors, comedians, models, voice actors (2 criteria)
4. NPOL → Politicians, judges (elected or high-level appointed office)
5. NSPORT → Athletes (professional or international competition)
6. NCRIME → Victims, perpetrators (very high bar)
7. BIO1E → Single-event notability (default: cover the event, not the person)
```

### Notable Exceptions

| Case | Rule | Example |
|------|------|---------|
| Mayor of a small town | Not inherently notable | Must pass GNG |
| US Senator | NPOL → Notable | Officeholder |
| City council member | Not inherently notable | Must pass GNG |
| Olympic athlete (competed) | NSPORT → Notable | Even if no medal |
| NCAA athlete | Not inherently notable | Must pass GNG |
| Professor at community college | Not inherently notable | Must check NACADEMIC criteria |
| Nobel laureate | ANYBIO → Notable | Any field |
| Child of celebrity | NOTINHERITED → Not notable | Unless independent coverage |
| Victim of crime | NCRIME → Very high bar | Default: mention in event article |
| Person known for one news event | BIO1E → Redirect to event | Default: not standalone article |

---

## SOP: Source Quality Assessment

Notability is determined by **what sources exist**, not by what's cited in the article.
The skill includes a `SourceEvaluator` for rating sources.

```python
from source_evaluator import SourceEvaluator

evaluator = SourceEvaluator()

# Evaluate a source by URL and description
result = evaluator.evaluate(
    title="Nature profile of Dr. Smith",
    source_type="news_feature",
    url="https://nature.com/articles/profile",
)

print(result["reliable"])     # True
print(result["significant"])  # True
print(result["score"])        # 9/10

# Classify an unknown source
source_type = evaluator.classify_source(
    url="https://en.wikipedia.org/wiki/Albert_Einstein"
)
# → "self_published" (Wikipedia doesn't count for notability)
```

### Source Hierarchy

```
┌─────────────────────────────────────────────────────┐
│              Source Quality Hierarchy                │
├─────────────────────────────────────────────────────┤
│  10  Peer-reviewed journal articles                  │
│   9  Books from academic presses                     │
│   8  Major newspapers (NYT, Guardian, Reuters)       │
│   7  Reputable magazines (Wired, New Yorker)         │
│   6  Trade publications                              │
│   5  Local newspapers (for local topics)             │
│   4  Company blogs, press releases                   │
│   3  Personal blogs, social media                    │
│   2  IMDb, Wikipedia, user-generated content         │
│   1  Self-published, anonymous sources               │
└─────────────────────────────────────────────────────┘
Only sources at 5+ count toward establishing notability.
```

### Churnalism Detection

When multiple sources have identical or near-identical content, they may all
derive from the same press release:

```python
# If 10 news articles all say the same thing and attribute it to "a press release",
# they count as ONE source for notability purposes.
sources = [
    "Company X announces new product — PR Newswire",
    "Company X announces new product — Reuters (same PR)",
    "Company X announces new product — Local News (same PR)",
]
# → 0 independent sources. These are all churnalism.
```

---

## SOP: What Never Counts

See **[references/invalid-arguments.md](references/invalid-arguments.md)** for a complete reference.

### Quick Reference: Arguments That Always Fail

| Argument | Why |
|----------|-----|
| "Spouse of notable person" | WP:NOTINHERITED |
| "High Google ranking" | WP:GOOGLEHITS |
| "Has an IMDb page" | WP:NOTDATABASE |
| "Popular on YouTube" | WP:NWEB |
| "Article X exists, so should this" | WP:WAX (whataboutism) |
| "It's well-written" | WP:CONTN |
| "It exists" | Existence ≠ notability |
| "Sources exist (but I won't name them)" | WP:NEXIST — name them |
| "Delete because it's poorly written" | WP:IMPERFECT — fixable |
| "Keep because I like it" | WP:ILIKEIT |
| "Has an article on fr.wikipedia" | Different standards per language |

---

## SOP: Producing a Structured Notability Report

### Using the NotabilityChecker

```python
from notability_checker import NotabilityChecker
from notability_templates import format_report, generate_afd_summary

checker = NotabilityChecker()

# Assess a subject
report = checker.assess(
    name="Dr. Jane Smith",
    subject_type="academic",
    description="Professor of quantum physics at MIT, named chair holder",
    sources=[
        {"title": "Nature profile of Smith", "type": "news_feature",
         "reliable": True, "independent": True, "significant": True},
        {"title": "NYT: Smith wins major award",
         "type": "news_article", "reliable": True,
         "independent": True, "significant": True},
        {"title": "Smith's MIT faculty page",
         "type": "self_published", "reliable": False,
         "independent": False, "significant": False},
    ],
)

# Get structured output
report_dict = report.to_dict()
# → {"verdict": {"overall": "notable", "confidence": "high"}, ...}

# Full formatted report
print(format_report(report))

# AfD-ready summary
print(generate_afd_summary(report))
```

### CLI Usage

```bash
# Quick assessment
python3 assets/notability_checker.py "Jane Smith" \
    --description "Professor of quantum physics at MIT, named chair" \
    --type academic

# With sources
python3 assets/notability_checker.py "Jane Smith" \
    --description "Professor of quantum physics at MIT" \
    --type academic \
    --source "Nature profile|news_feature|yes|yes|yes" \
    --source "NYT article|news_article|yes|yes|yes"

# Shell script
bash scripts/notability-check.sh "Jane Smith" \
    --type academic \
    --desc "Professor of quantum physics at MIT" \
    --source "Nature profile|news|yes|yes|yes" \
    --json

# Evaluate a specific source
python3 assets/source_evaluator.py \
    --title "Nature profile of Smith" \
    --type news_feature \
    --url "https://nature.com/articles/profile"
```

### What the Report Looks Like

```
==================================================
NOTABILITY ASSESSMENT REPORT
==================================================

Subject: Dr. Jane Smith
Type:    academic
Desc:    Professor of quantum physics at MIT, named chair

✅  Verdict: NOTABLE
   Confidence: HIGH

📋 SUBJECT-SPECIFIC GUIDELINES (SNGs):
   ✅ NACADEMIC: Named chair or distinguished professorship

📊 GENERAL NOTABILITY GUIDELINE (GNG):
   ✅ Overall: PASS
   ✅ Significant coverage
   ✅ Reliable sources
   ✅ Independent sources
   ✅ Multiple sources
   Sources evaluated: 3

💡 RECOMMENDATIONS:
   → Subject likely meets Wikipedia notability guidelines. Proceed with article creation.
```

### Report Types

| Format | Use Case | Command |
|--------|----------|---------|
| Full report | Detailed assessment | `format_report(report)` |
| One-line summary | Quick reference | `format_short(report)` |
| AfD summary | Deletion discussion | `generate_afd_summary(report)` |
| Maintenance tag | Flagging an article | `generate_notability_tag(report)` → `{{notability|date=June 2026}}` |

---

## SOP: Special Topics

### Notability of Lists (WP:NLIST)

Standalone lists have their own notability rules:
- Lists can exist if the **list topic** is notable (not each individual entry)
- Entry in a list does NOT need to be independently notable (list criteria determine inclusion)
- Common list types: discographies, bibliographies, filmographies, awards lists

### Notability Is Not Temporary (WP:NTEMP)

Once a topic has significant coverage, it **retains** notability even if coverage stops.
- A 1990s band with significant coverage in the 90s is still notable today
- A historical event with significant coverage is permanently notable
- Exception: Living persons may need reassessment if sources become unavailable

### Sustained Coverage (WP:SUSTAINED)

For currently-developing topics (news events, new companies), look for **sustained** coverage:
- Brief burst of news coverage → not enough (WP:NOTNEWS)
- Coverage that persists for months/years → strong signal
- New organizations need time to demonstrate notability

### Future Events (WP:CRYSTAL)

- Do not create articles for events that haven't happened yet
- Exception: Planned events where notability is reasonably assured (Olympics, major elections)
- Films: Create article only after principal photography has started (WP:NFF)
- Albums: Must have confirmed release date and verifiable content

### Redirects vs. Articles

When a subject is notable mainly for a single event:
- Default: Create redirect to the event article
- Only create standalone biography if the person's role is historically significant
- Example: Assassin of a major political leader → standalone article likely appropriate
- Example: Witness to a crime → redirect to crime article

---

## Guardrails

### 1. Never Assess Notability by Article Quality

A well-written article about a non-notable subject is still non-notable (WP:CONTN).
Notability is about the *subject*, not the *Wikipedia article*.

### 2. Never Cite Wikipedia Itself as a Source

Wikipedia articles, other language Wikipedias, and Wikidata entries do not
demonstrate notability. They are derivative sources.

### 3. Distinguish "Notable" from "Famous"

"Famous" people can fail notability if they lack significant coverage in
reliable independent sources. "Obscure" scholars can pass notability through
NACADEMIC criteria (named chair, major awards, etc.).

### 4. SNGs Are Guidelines, Not Policies

Meeting an SNG creates a *presumption* of notability, not a guarantee.
Reasons to still exclude: WP:NOT (not an encyclopedia topic), WP:BLP1E
(single-event person), WP:NOTNEWS (routine coverage).

### 5. BLP Subjects Require Extra Care

For living people:
- Apply notability standards strictly
- Sources must be reliable (BLP policy)
- The bar for deletion is lower if sources are weak
- Default: no article for people notable only for one event (BLP1E)

### 6. Don't Count Press Releases

Press releases, even when reproduced verbatim by multiple news outlets,
count as ZERO independent sources. This is called **churnalism** — identify
it and exclude it.

### 7. Local Notability vs. Global Notability

- Local politician with only local newspaper coverage: fails GNG
- Local business with only local business journal coverage: fails NCORP
- Exception: Local topics of clear encyclopedic value (historic buildings, significant local events)

### 8. NOTINHERITED Applies Broadly

- Spouse of notable person → not notable (unless own coverage)
- Child of notable person → not notable (unless own coverage)
- Student of notable teacher → not notable (unless own coverage)
- Employee of notable company → not notable (unless own coverage)

### 9. Multiple Same-Source Articles Count as One

If 50 newspapers carry the same AP story about a subject, that counts as
ONE source, not 50. Identify the original source.

### 10. When Unsure, Flag It

If notability is unclear:
- Add `{{notability|date=June 2026}}` tag
- Suggest the user provide more sources
- Do not create the article — better to wait for clarity

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikipedia-en-biography-writing](../wikipedia-en-biography-writing/SKILL.md)** | Drafting an article AFTER notability is confirmed |
| **[wikipedia-pagetriage-api](../wikipedia-pagetriage-api/SKILL.md)** | New page patrol — assessing notability of recently created pages |
| **[wikipedia-citations](../wikipedia-citations/SKILL.md)** | Formatting the sources that demonstrate notability |
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | Searching for sources to evaluate notability |
| **[wikimedia-search-cirrussearch](../wikimedia-search-cirrussearch/SKILL.md)** | Finding sources using CirrusSearch (`hastemplate:"notability"`) |
| **[wikimedia-ml-services](../wikimedia-ml-services/SKILL.md)** | Article quality scoring (complementary to notability) |
| **[wikipedia-error-handling](../wikipedia-error-handling/SKILL.md)** | API error handling when searching for sources |
