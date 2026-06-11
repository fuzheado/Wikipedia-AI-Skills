# Sister Project API Differences

Quick reference for API differences between Wikipedia, Wiktionary, and Wikisource.
All use the same `w/api.php` Action API endpoint — the differences are in available
module parameters and response structures.

---

## Base URLs

| Project | API URL Pattern |
|---------|----------------|
| Wikipedia | `https://{lang}.wikipedia.org/w/api.php` |
| Wiktionary | `https://{lang}.wiktionary.org/w/api.php` |
| Wikisource | `https://{lang}.wikisource.org/w/api.php` |

---

## Page Content Retrieval

### Wikipedia: `action=parse` → `text.*`
```json
{
  "parse": {
    "title": "Word",
    "text": { "*": "<div class=\"mw-parser-output\">..." }
  }
}
```
HTML is the primary output. Wikitext is available but less commonly used.

### Wiktionary: `action=parse` → `wikitext.*`
```json
{
  "parse": {
    "title": "word",
    "wikitext": { "*": "==English==\n===Noun===\n{{en-noun}}\n# A unit..." }
  }
}
```
**Wikitext is the primary format.** Wiktionary entries are complex wikitext with
template-heavy structures. The HTML rendering loses the section-delineator (`----`)
structure.

### Wikisource: `action=parse` → `wikitext.*` (for Page: pages)
```json
{
  "parse": {
    "title": "Page:Example/1",
    "wikitext": { "*": "<pages index=\"...\" from=1 to=1 />" }
  }
}
```
For compiled works, use `action=parse&page=Work_Title` to get the assembled text.
For individual scanned pages, use the `Page:` namespace to get the raw text layer.

---

## Project-Specific API Modules

### Wiktionary

| Module | Purpose | Key Parameters |
|--------|---------|----------------|
| `list=categorymembers` | List words in a category | Same as Wikipedia — `cmtitle=Category:English_nouns` |
| `prop=langlinks` | Get interwiki links (same word in other languages) | `lllimit=max` |
| `list=prefixsearch` | Search words by prefix | `pssearch=word*` |
| `list=search` | Full-text search | `srwhat=text` |
| `meta=siteinfo` | Get project info (language codes, namespaces) | `siprop=namespaces|languages` |

### Wikisource

| Module | Purpose | Key Parameters |
|--------|---------|----------------|
| `prop=proofread` | Get proofread quality status of a Page: page | `gap=...` (page ID or title) |
| `prop=proofreadinfo` | Get proofreading info for an Index: page | `piprop=quality` — returns per-page quality |
| `list=proofreadpages` | List pages in an Index: by quality | `pipqual=2` (filter by quality level) |
| `prop=pageprops` | Get Index: page properties | `ppprop=index-authors|index-publisher` |

---

## Namespaces

| # | Wikipedia | Wiktionary | Wikisource |
|---|-----------|------------|------------|
| 0 | Article | Entry | Compiled work |
| 1 | Talk | Talk | Talk |
| 2 | User | User | User |
| 4 | Project (WP:) | Project (WT:) | Project (WS:) |
| 6 | File | File | File |
| 10 | Template | Template | Template |
| 14 | Category | Category | Category |
| 100 | Portal | Appendix | Page |
| 102 | — | Concise | Index |
| 104 | — | Rhymes | Author |
| 106 | — | Thesaurus | Translation |
| 108 | — | Citations | — |
| 110 | — | Sign gloss | — |

### Key Wikisource Namespaces

| Namespace | Prefix | Content |
|-----------|--------|---------|
| Page | `Page:Example.djvu/1` | Scanned page image + text layer |
| Index | `Index:Example.djvu` | Work metadata (author, year, scanner) |
| Author | `Author:Pliny the Elder` | Author biography and work list |

### Key Wiktionary Namespaces

| Namespace | Prefix | Content |
|-----------|--------|---------|
| Appendix | `Appendix:English irregular verbs` | Reference lists |
| Concise | `Concise:word` | Simplified definitions |
| Rhymes | `Rhymes:English:-ɜː(r)d` | Rhyme groupings |
| Thesaurus | `Thesaurus:word` | Synonym lists |
| Citations | `Citations:word` | Quotations supporting usage |
| Sign gloss | `Sign gloss:WORD` | Sign language glosses |

---

## Important Parameter Differences

### `list=search`

| Parameter | Wikipedia | Wiktionary | Wikisource |
|-----------|-----------|------------|------------|
| `srwhat` | `text`, `title`, `nearmatch` | `text`, `title`, `nearmatch` | Same |
| `srnamespace` | `0` (default) | `0` (default) | `0` for compiled; `102` for Index; `100` for Page |

### `prop=info`

On Wikisource, `prop=info&inprop=protection` works normally (page protection is
used to lock validated pages). On Wiktionary, protection is less common — most
pages are open to editing.

---

## Rate Limits

All sister projects share the same rate limit infrastructure as Wikipedia.
The same User-Agent requirements and Retry-After handling apply. See
**wikimedia-api-access** for details.
