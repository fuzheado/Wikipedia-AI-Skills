# CS1/CS2 Parameter Reference

Complete parameter reference for all CS1 (Citation Style 1) and CS2 citation templates.

---

## Common Parameters (Available in All Templates)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `url` | Full URL of the source | `https://example.com/article` |
| `title` | Title of the source work | `The Great Breakthrough` |
| `trans-title` | English translation of foreign title | `La Grande Percée` |
| `script-title` | Non-Latin script title | `العلماء` |
| `last` / `first` | Author surname and given name | `last=Einstein`, `first=Albert` |
| `author-link` | Wikipedia article about the author | `Albert_Einstein` |
| `last2` / `first2` ... `lastN` / `firstN` | Additional authors (up to N=9 in most templates) | |
| `author-mask` | Replaces author name with em dash for repeated authors | `author-mask=1` |
| `name-list-style` | `amp` (use &), `and` (use "and"), `vanc` (Vancouver) | `amp` |
| `date` | Full publication date | `5 June 2026` |
| `year` | Publication year only | `2026` |
| `orig-date` | Original publication date (for reprints) | `1920` |
| `editor-last` / `editor-first` | Editor name(s) | |
| `edition` | Book edition | `Third` |
| `series` | Series of which this is part | `Lecture Notes in Physics` |
| `volume` | Volume number | `42` |
| `issue` | Issue number (also `number`) | `3` |
| `publisher` | Publisher name | `Oxford University Press` |
| `location` | Place of publication | `Oxford` |
| `publication-place` | Place of publication (for reprints) | `London` |
| `page` | Single page reference | `42` |
| `pages` | Page range | `123–145` |
| `at` | Precise location (section, paragraph) | `para. 5` |
| `language` | Language(s) if not English | `fr`, `de, fr` |
| `format` | File format (if not HTML) | `PDF` |
| `doi` | Digital Object Identifier | `10.1000/xyz123` |
| `pmid` | PubMed ID | `12345678` |
| `pmc` | PubMed Central ID | `PMC1234567` |
| `isbn` | ISBN (10 or 13 digits, hyphens optional) | `978-0-262-52316-5` |
| `issn` | ISSN | `0040-165X` |
| `oclc` | OCLC WorldCat ID | `123456789` |
| `jstor` | JSTOR stable URL ID | `123456` |
| `bibcode` | Astrophysics Bibcode | `1924PhRv...23..123B` |
| `arxiv` | arXiv ID | `1234.56789` |
| `s2cid` | Semantic Scholar Corpus ID | `12345678` |
| `access-date` | Date when the URL was last accessed | `5 June 2026` |
| `archive-url` | URL of an archived copy | `https://web.archive.org/web/...` |
| `archive-date` | Date of the archive snapshot | `5 June 2026` |
| `url-status` | Status of the original URL | `live`, `dead`, `unfit`, `usurped` |
| `quote` | Relevant excerpt from the source | |
| `postscript` | Punctuation after citation (CS2: default `.`) | |
| `mode` | `cs1` or `cs2` | |
| `ref` | Anchor ID for the citation (`harv` for Harvard) | `harv` |

---

## Template-Specific Parameters

### `{{cite web}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | ✅ | Full URL |
| `title` | ✅ | Page title |
| `website` | Recommended | Site name (e.g., `BBC News`) |
| `access-date` | Recommended | Date URL was accessed |

### `{{cite news}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | ✅ | Full URL |
| `title` | ✅ | Article headline |
| `newspaper` | Recommended | Publication name |
| `date` | Recommended | Publication date |
| `access-date` | Recommended | Date URL was accessed |
| `page` / `pages` | Optional | Print edition page |

### `{{cite book}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Book title |
| `last` / `first` or `author` | ✅ | Author name |
| `date` or `year` | Recommended | Publication year |
| `publisher` | Recommended | Publisher name |
| `isbn` | Recommended | ISBN |
| `edition` | Optional | Edition (e.g., `2nd`) |
| `volume` | Optional | Volume number |
| `url` | Optional | External link (e.g., Google Books) |

### `{{cite journal}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Article title |
| `last` / `first` or `author` | ✅ | Author name |
| `journal` | ✅ | Journal name |
| `date` or `year` | Recommended | Publication year |
| `volume` | Recommended | Volume number |
| `pages` | Recommended | Page range |
| `doi` | Recommended | DOI |
| `pmid` | Optional | PubMed ID |
| `pmc` | Optional | PubMed Central ID |
| `issue` | Optional | Issue number |

### `{{cite arXiv}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `eprint` | ✅ | arXiv ID (e.g., `1234.56789`) |
| `class` | ✅ | arXiv classification (e.g., `cs.AI`) |
| `title` | ✅ | Paper title |
| `author` | ✅ | Author list |
| `date` | Recommended | Publication date |

### `{{cite bioRxiv}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `biorxiv` | ✅ | bioRxiv ID |
| `title` | ✅ | Paper title |
| `author` | ✅ | Author list |
| `date` | Recommended | Publication date |

### `{{cite conference}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Paper title |
| `book-title` | ✅ | Conference proceedings title |
| `conference` | Recommended | Conference name |
| `date` | Recommended | Conference date |
| `location` | Optional | Conference location |
| `publisher` | Optional | Proceedings publisher |
| `doi` | Optional | DOI |

### `{{cite encyclopedia}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Entry title |
| `encyclopedia` | ✅ | Encyclopedia name |
| `author` | Recommended | Entry author |
| `date` or `year` | Recommended | Publication year |
| `publisher` | Recommended | Publisher |
| `location` | Optional | Place of publication |
| `isbn` | Optional | ISBN of the encyclopedia set |

### `{{cite thesis}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Thesis title |
| `type` | ✅ | Type (e.g., `PhD thesis`, `MA thesis`) |
| `publisher` | ✅ | University/institution |
| `author` | ✅ | Author |
| `date` or `year` | Recommended | Year awarded |
| `url` | Optional | Link to thesis |
| `degree` | Optional | Degree abbreviation |

### `{{cite report}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Report title |
| `author` | Recommended | Author(s) |
| `date` or `year` | Recommended | Publication year |
| `publisher` or `institution` | Recommended | Publishing body |
| `number` | Optional | Report number |
| `url` | Optional | Link to report |

### `{{cite patent}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `country` | ✅ | Patent country code (e.g., `US`, `EP`) |
| `number` | ✅ | Patent number |
| `title` | ✅ | Patent title |
| `pubdate` | ✅ | Publication date |
| `inventor` | Recommended | Inventor name(s) |
| `assignee` | Optional | Assignee/owner |
| `status` | Optional | `patent` or `application` |
| `url` | Optional | Link to patent |

### `{{cite AV media}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Title of the media |
| `people` | Recommended | Creator/director |
| `date` | Recommended | Release date |
| `medium` | Recommended | Format (e.g., `DVD`, `Film`, `Television`) |
| `publisher` | Recommended | Distributor/network |
| `url` | Optional | Link to media |

### `{{cite episode}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Episode title |
| `series` | ✅ | Series name |
| `network` | Recommended | Broadcast network |
| `station` | Recommended | Local station |
| `date` | Recommended | Airdate |
| `season` | Recommended | Season number |
| `number` | Recommended | Episode number |
| `url` | Optional | Link to episode summary |

### `{{cite podcast}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | ✅ | Link to episode |
| `title` | ✅ | Episode title |
| `series` | ✅ | Podcast series name |
| `host` | Recommended | Host name(s) |
| `date` | Recommended | Release date |
| `time` | Optional | Timestamp of cited content |

### `{{cite interview}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `last` / `first` | ✅ | Interviewee |
| `interviewer` | Recommended | Interviewer name |
| `title` | Recommended | Interview title |
| `date` | Recommended | Interview date |
| `work` | Recommended | Publication where interview appeared |
| `url` | Optional | Link to interview |

### `{{cite map}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Map title |
| `publisher` | Recommended | Cartographic publisher |
| `date` or `year` | Recommended | Publication year |
| `url` | Optional | Link to map |
| `scale` | Optional | Map scale (e.g., `1:25000`) |
| `edition` | Optional | Edition |
| `section` | Optional | Section/quadrant |

### `{{cite press release}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Press release title |
| `publisher` | Recommended | Issuing organization |
| `date` | Recommended | Release date |
| `url` | Optional | Link to release |

### `{{cite court}}`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `litigants` | ✅ | Party names (e.g., `Brown v. Board of Education`) |
| `vol` | ✅ | Reporter volume |
| `reporter` | ✅ | Reporter series (e.g., `U.S.`) |
| `opinion` | ✅ | First page of the opinion |
| `court` | ✅ | Court name |
| `date` | ✅ | Decision date |
| `url` | Optional | Link to opinion |
| `pinpoint` | Optional | Specific page cited |

---

## CS2 (Citation Style 2)

CS2 uses a single `{{citation}}` template. It accepts all parameters listed
above. The key difference is that CS2 does not generate a descriptive label
(e.g., "Web", "News", "Book") — it renders all citations uniformly.

```wikitext
<!-- CS2: no template type label -->
<ref>{{citation |url= |title= |last= |first= |date= |publisher= |isbn=}}</ref>
```

**When to use CS2:**
- All citations are the same type (e.g., all books)
- You want a uniform look
- You are using a citation management tool that exports CS2

**When to use CS1:**
- Citation types vary (web vs book vs journal)
- Readers benefit from knowing the format at a glance
- You want type-specific error checking and metadata extraction

---

## Date Formatting

Wikipedia uses two date formats. Use one consistently per article:

| Format | Example | Where Common |
|--------|---------|--------------|
| **DMY** (day month year) | `5 June 2026` | British/Australian articles |
| **MDY** (month day, year) | `June 5, 2026` | US articles |

**ISO format** (`2026-06-05`) is accepted in `|date=` and `|access-date=`
parameters but will be auto-formatted to the article's date style.

---

## Common Parameter Gotchas

| Gotcha | Explanation |
|--------|-------------|
| `publisher` vs `work` | `publisher` is the company; `work`/`website`/`journal`/`newspaper` is the publication name. A book has a publisher, not a work. |
| `page` vs `pages` | `page` for single page; `pages` for range. Never both. |
| `last`/`first` vs `author` | Use `last`/`first` for individual authors; `author` for corporate authors or when you cannot separate names. |
| `date` vs `year` | Prefer `date` when you have the full date. Use `year` only for books with known year only. |
| Missing `access-date` | Without it, readers cannot tell if the link was verified. Always include for online sources. |
| `|` in URLs | Must be escaped as `%7C` or the template breaks. |
| `=` in URLs | Must be escaped as `%3D` or the template confuses `=` for a parameter separator. |
