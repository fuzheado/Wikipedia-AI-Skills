# Assessment Ratings Reference

Wikipedia articles are assessed on **quality** and **importance** for each WikiProject that covers them. This data is stored in WikiProject banners on talk pages.

## Quality Ratings (ascending)

```
Stub → Start → C → B → GA → FA
```

| Rating | Abbrev. | Description | Criteria Summary |
|--------|---------|-------------|------------------|
| **Featured Article** | FA | The best articles Wikipedia has to offer | Comprehensive, well-researched, neutral, stable, well-written, well-illustrated. Passed a formal peer review (FAC). |
| **Featured List** | FL | The best lists on Wikipedia | Similar to FA but for list articles. Passed a formal review (FLC). |
| **Good Article** | GA | Good, but not yet featured | Passed a Good Article review (GAN). Meets the GA criteria: well-written, verifiable, broad coverage, neutral, stable, illustrated. |
| **B-class** | B | Mostly complete | Article is mostly complete but has some gaps or issues. No formal review required. |
| **C-class** | C | Substantial but incomplete | Article has substantial content but significant gaps or quality issues remain. No formal review. |
| **Start** | Start | Basic, incomplete | Article has some meaningful content but is not yet substantial. |
| **Stub** | Stub | Very brief | A very short article — just enough to define the topic. Usually a few sentences or a paragraph. |
| **List** | List | List article | The page is a list (not a prose article). Assessed separately from the prose quality scale. |
| **NA** | N/A | Non-article | Disambiguation pages, templates, categories, portals, project pages — anything that isn't a standard article. |

### What Each Rating Looks Like in Practice

| Rating | Typical Length | Typical Sections | Typical Citations |
|--------|---------------|-----------------|-------------------|
| FA | 15,000+ words | 8+ well-developed sections | 100+ citations from multiple high-quality sources |
| GA | 5,000–15,000 words | 5–8 sections with decent depth | 30–100 citations from reliable sources |
| B | 3,000–10,000 words | 4–6 sections, some may be underdeveloped | 20–60 citations |
| C | 1,500–5,000 words | 3–5 sections, some may be short | 10–30 citations |
| Start | 500–2,000 words | 2–3 sections, often short | 0–10 citations |
| Stub | <500 words | No sections, or just 1–2 | Usually 0–3 citations |

### How Ratings Are Determined

- **FA, FL, GA** are determined through formal community review processes (FAC, FLC, GAN).
- **B, C, Start, Stub** are assigned by WikiProject editors based on their subjective assessment against the project's quality scale.
- Ratings can become outdated — an article assessed as B five years ago might now be C or Stub if it hasn't been maintained.

## Importance Ratings

| Rating | Meaning | Example |
|--------|---------|---------|
| **Top** | Core topic — essential for the project | Physics → "Albert Einstein" |
| **High** | Major topic — covers a significant area | Physics → "Quantum mechanics" |
| **Mid** | Notable topic — within the project's scope | Physics → "Thermodynamics" |
| **Low** | Peripheral topic — of limited interest | Physics → "History of the barometer" |
| **NA** | Not applicable (non-article pages) | Templates, categories, disambiguation |
| **Unknown** | Importance has not been assigned | Default when omitted from the banner |

### Importance is Project-Specific

An article's importance rating depends on which WikiProject is assessing it:

| Article | WikiProject Biography | WikiProject Physics | WikiProject Germany |
|---------|----------------------|--------------------|--------------------|
| Albert Einstein | Top | Top | Top |
| Max Planck | High | Top | High |
| Berlin | NA (not a biography) | Mid | Top |

## Assessment Distribution

Approximate distribution of assessments across English Wikipedia (as of 2026):

| Quality | Approx. Count | % of Articles |
|---------|--------------|---------------|
| FA | ~6,500 | 0.1% |
| GA | ~40,000 | 0.6% |
| B | ~140,000 | 2.1% |
| C | ~350,000 | 5.3% |
| Start | ~1,600,000 | 24.3% |
| Stub | ~3,200,000 | 48.6% |
| List/NA/etc. | ~1,200,000 | 18.2% |

Most articles are Start-class or Stub — there is a massive quality gap between the average article and the encyclopedia's best content.

## Assessment Banners Template Reference

Standard WikiProject banner format:

```wikitext
{{WikiProject ProjectName
| class      = B
| importance = High
| listas     = Einstein, Albert    ← Sort key for category listings
}}
```

Common parameters:
- `class` — Quality rating (FA, GA, B, C, Start, Stub, List, NA)
- `importance` — Importance within the project (Top, High, Mid, Low, NA, Unknown)
- `listas` — Sort key for category pages (e.g., "Einstein, Albert" sorts under E)
- `living` — `yes`/`no` for biographies of living people (BLP)

## How to Access Assessment Data

**Method 1 — Manual (this skill):**
Parse the talk page wikitext for `{{WikiProject...|class=...|importance=...}}`.

```bash
./scripts/get-assessment.sh "Albert Einstein"
```

**Method 2 — Database (for bulk queries):**
Use the `wikimedia-page-assessment` skill, which queries the `page_assessments` table directly.

```sql
SELECT pa_class, pa_importance, pap_project_title
FROM page_assessments
JOIN page_assessments_projects ON pa_project_id = pap_project_id
JOIN page ON pa_page_id = page_id
WHERE page_title = 'Albert_Einstein' AND page_namespace = 0;
```
