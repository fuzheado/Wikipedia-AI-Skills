# CirrusSearch Syntax Reference Card

A compact, printable-style reference for all CirrusSearch syntax. All keywords are **case-sensitive and lowercase**.

## Quick Cheat Sheet

```
┌─────────────────────────────────────────────────────────────┐
│  intitle:text          — Search page titles only            │
│  incategory:"Name"     — Pages in a category (flat)         │
│  deepcategory:"Name"   — Category + subcategories (≤5)      │
│  insource:"text"       — Search raw wikitext                │
│  insource:/regex/      — Regex on wikitext                  │
│  hastemplate:"Name"    — Pages using a template             │
│  linksto:"Page"        — Pages linking TO a page            │
│  haswbstatement:P=V    — Filter by Wikidata statement       │
│  prefix:text           — Title starts with. MUST BE LAST.   │
│  subpageof:"Name"      — Subpages of a page                 │
│  morelike:X|Y|Z        — Similar-content pages              │
│  articletopic:topic    — ML topic filter (Wikipedia only)   │
│  prefer-recent:        — Boost recently edited pages        │
│  boost-templates:"T|%" — Boost by template (in ranking)     │
│  filetype:TYPE         — File media type (Commons)          │
│  filemime:MIME         — File MIME type (Commons)           │
│  filesize:N            — File size in KB (Commons)          │
│  filew:>800            — File width pixels (Commons)        │
│  fileh:>600            — File height pixels (Commons)       │
│  creationdate:>=2024   — Filter by creation date            │
│  lasteditdate:today    — Filter by last edit date           │
│  inlanguage:ja         — Page language (Translate ext)      │
│  contentmodel:json     — Content model filter               │
│  neartitle:"Place"     — Geo-search near a page             │
│  nearcoord:"37,-122"   — Geo-search by coordinates          │
│  pageid:123\|456        — Restrict to specific page IDs      │
│  hasrecommendation:img — ML recommendation filter           │
│  inlabel:text@en       — Wikidata label search (Wikibase)   │
│  hasdescription:en     — Items with description (Wikibase)  │
│  WBstatementquantity:  — Quantity-based Wikidata filter(*)  │
└─────────────────────────────────────────────────────────────┘
(*) Not enabled on any production wiki as of 2026.
```

## Modifiers

| Modifier | Syntax | Effect |
|----------|--------|--------|
| Exact phrase | `"words in quotes"` | No stemming, exact phrase match |
| Negation | `-keyword` or `!keyword` | Exclude matching pages |
| Fuzzy word | `word~` or `word~0.5` | Fuzzy match (edit distance, default 0.5) |
| Proximity phrase | `"word1 word2"~N` | Words within N positions of each other |
| Wildcard (multi) | `wor*` | Zero or more characters (never at start) |
| Wildcard (single) | `wor\?` | Exactly one character |
| Namespace | `talk:` | Search a specific namespace (first term) |
| All namespaces | `all:` | Search across all namespaces |
| Main namespace | `:` | Main (article) namespace only |
| Skip suggestions | `~` | ~query goes directly to search results |

## Namespace IDs

| ID | Namespace | Shorthand |
|----|-----------|-----------|
| 0 | Main (articles) | `:` |
| 1 | Talk | `talk:` |
| 2 | User | `user:` |
| 3 | User talk | `user talk:` |
| 4 | Wikipedia | `project:` |
| 6 | File/Media | `file:` |
| 10 | Template | `template:` |
| 14 | Category | `category:` |
| 12 | Help | `help:` |
| 8 | MediaWiki | `mediawiki:` |

## Common Combinations

```
# Category + template + keyword
incategory:"Physics" hastemplate:"Infobox scientist" quantum

# Template + title filter - exclude
hastemplate:"Unreferenced" -incategory:"Wikipedia articles in need of updating"

# Backlink analysis
linksto:"Albert Einstein" -intitle:"Albert Einstein"

# Structured data + text on Commons
haswbstatement:P180=Q5 Eiffel Tower

# Multiple category intersection with template
incategory:"Living people" incategory:"American physicists" hastemplate:"BLP unsourced"

# Date range
creationdate:>=2020-01-01 creationdate:<2021-01-01

# Regex on wikitext with index-based filter to limit scope
hastemplate:"Infobox settlement" insource:"population_total" insource:/population_total\s*=\s*\d{1,3},?\d{0,3}/

# Subpage + template audit
subpageof:"Wikipedia:WikiProject Physics" hastemplate:"WikiProject banner shell"

# Recently edited in a category (sorts by relevance, not recency)
incategory:"Physics" lasteditdate:>=today-7d

# Exact date with prefixed recency boost
incategory:"Physics" lasteditdate:>=today-7d prefer-recent:1,7
```

## Sort Orders (srsort parameter)

| srsort value | Effect |
|-------------|--------|
| `relevance` | Default. Scoring keywords active. |
| `last_edit_desc` | Most recently edited first |
| `last_edit_asc` | Least recently edited first |
| `create_timestamp_desc` | Most recently created first |
| `create_timestamp_asc` | Least recently created first |
| `incoming_links_desc` | Most linked-to first |
| `incoming_links_asc` | Least linked-to first |
| `title_natural_desc` | Title Z-A |
| `title_natural_asc` | Title A-Z |
| `just_match` | Simple text-match relevance only |
| `random` | Randomized |
| `user_random` | Randomized but stable per user |
| `none` | Unsorted (fastest for large sets) |

**⚠️ Using any sort order other than `relevance` disables scoring keywords like `prefer-recent:`, `boost-templates:`, and `articletopic:`.**

## When CirrusSearch Can't Do It

| Task | Fallback Tool |
|------|---------------|
| Category intersection (AND) across large sets | PetScan or SPARQL |
| Numerical comparisons on WikiBase quantities | SPARQL (`wbstatementquantity:` not deployed) |
| Date ranges on WikiBase statements | SPARQL |
| Recursive category search >5 levels deep | PetScan or SQL replicas |
| Bulk export with structured metadata | SQL replicas or SPARQL |
| Real-time monitoring | EventStreams |
| Semantic/vector search when labels unknown | Wikidata Vector Search |
