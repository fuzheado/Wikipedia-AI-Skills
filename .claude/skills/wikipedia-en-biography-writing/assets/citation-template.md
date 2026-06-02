# Citation Templates for Wikipedia Biographies

Use these templates for inline citations. Always place `<ref>` tags immediately
after the sentence they support, before punctuation.

**Never fabricate a citation.** Every URL, author, date, and title must be real.
If you lack a source, use `{{citation needed}}` instead.

---

## Web Source

```wikitext
<ref>{{cite web
 |url        = https://example.com/article
 |title      = Article Title
 |last       = Smith
 |first      = Jane
 |date       = 2024-01-15
 |website    = Website Name
 |publisher  = Publisher (if different from website)
 |access-date = 2026-05-23
 |language   = en
}}</ref>
```

**Required fields:** `url`, `title`, `access-date`
**Recommended:** `last`, `first`, `date`, `website`

---

## News Article

```wikitext
<ref>{{cite news
 |url        = https://newspaper.com/article
 |title      = Article Title
 |last       = Doe
 |first      = John
 |date       = 2024-01-15
 |work       = The Newspaper Name
 |publisher  = Publisher
 |access-date = 2026-05-23
}}</ref>
```

**Required fields:** `url`, `title`, `work`, `access-date`
**Recommended:** `last`, `first`, `date`

---

## Book

```wikitext
<ref>{{cite book
 |title      = Book Title
 |last       = Author
 |first      = Name
 |date       = 2024
 |publisher  = Publisher Name
 |isbn       = 978-0-00-000000-0
 |pages      = 123-145
 |url        = https://... (optional if available online)
}}</ref>
```

**Required fields:** `title`, `last`, `first`, `date`, `publisher`
**Recommended:** `isbn`, `pages` (for specific citations)

---

## Journal Article

```wikitext
<ref>{{cite journal
 |title      = Article Title
 |last       = Author
 |first      = Name
 |date       = 2024
 |journal    = Journal Name
 |volume     = 10
 |issue      = 2
 |pages      = 100-120
 |doi        = 10.0000/example
 |url        = https://doi.org/10.0000/example
}}</ref>
```

**Required fields:** `title`, `last`, `first`, `journal`
**Recommended:** `volume`, `issue`, `pages`, `doi`

---

## Short Form (for repeated citations)

Use named refs when citing the same source multiple times:

```wikitext
<ref name="smith2024">{{cite web |url=... |title=... |last=Smith |date=2024}}</ref>

Text that uses the source.<ref name="smith2024" />

More text using the same source.<ref name="smith2024" />
```

---

## Citation Needed / Flag Templates

```wikitext
{{citation needed}}           <!-- Fact needs a source -->
{{better source needed}}      <!-- Current source is weak -->
{{when}}                      <!-- Missing date -->
{{where}}                     <!-- Missing location -->
{{clarify}}                   <!-- Unclear statement -->
{{failed verification}}       <!-- Source doesn't support the claim -->
{{dead link|date=May 2026}}  <!-- URL is inaccessible -->
```

---

## Quick Reference

| Source Type | Template | Required Fields |
|---|---|---|
| Website | `{{cite web}}` | url, title, access-date |
| News | `{{cite news}}` | url, title, work, access-date |
| Book | `{{cite book}}` | title, last, first, publisher |
| Journal | `{{cite journal}}` | title, last, first, journal |
| Same source reused | Named ref `<ref name="key" />` | Unique name |

## Anti-Hallucination Rules

1. **Never fabricate a URL.** Every link must be real.
2. **Never guess a DOI or ISBN.** Only include identifiers you've verified.
3. **Never assume a date.** If you don't know the publication date, omit the field.
4. **Never include a page number** unless you've seen the specific page.
5. **Every `access-date`** should be the current date or the date you last verified the link.
