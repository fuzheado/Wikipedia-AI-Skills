# Wikisource ProofreadPage Workflow

## The Three-Namespace System

Wikisource uses three interconnected namespaces to manage proofreading:

```
Index:     Metadata about the publication
  │         (title, author, year, publisher, scanner,
  │          progress, pages)
  │
  ├──→ Page:  One per scanned image
  │            Image + text layer
  │            Quality level: 0-3
  │
  └──→ Main:  Compiled text
               Transcludes Page: pages
               What the reader sees
```

### Index: Namespace

The `Index:` page stores metadata and defines the page range:

```wikitext
{{:MediaWiki:Proofreadpage_index_template
|Title=[[Pride and Prejudice]]
|Language=en
|Author=[[Author:Jane Austen]]
|Year=1813
|Publisher=T. Egerton
|Pages=<pagelist from=1 to=400 />
}}
```

**API access:** `prop=pageprops&titles=Index:Work.djvu`

### Page: Namespace

Each `Page:` page represents a single scanned image. The wikitext contains the
extracted text layer:

```wikitext
{{header|1=1|2=Pride and Prejudice|3=Chapter 1}}
<pages index="Pride and Prejudice" from=1 to=1 />
It is a truth universally acknowledged, that a single man in possession
of a good fortune, must be in want of a wife.
{{c|{{smaller|CHAP. I.}}}}
{{nop}}
{{footer|1=1|2=Pride and Prejudice|3=Chapter 1}}
```

The actual text to proofread is between `{{header}}` and `{{footer}}`. The
`{{nop}}` template ensures paragraph breaks carry over correctly.

### Main Namespace (Compiled Work)

The main namespace page transcludes all Page: pages into a single flowing text:

```wikitext
<pages index="Pride and Prejudice" from=1 to=400 header=1 />
```

Additional content like a table of contents or notes may appear before or after
the `<pages>` tag.

---

## Quality Levels in Detail

| Level | Code | Color | Meaning | Requirements |
|-------|------|-------|---------|-------------|
| 0 | Without text | ⬜ | Raw image only | OCR or manual transcription needed |
| 1 | Problematic | 🟡 | Text entered but has issues | Needs human review; may have OCR errors |
| 2 | Proofread | 🟢 | Read by one person | Second reader should validate |
| 3 | Validated | 🔵 | Read by two people | Complete; pages are usually protected |

### Setting Quality via API

```python
import requests

def set_page_quality(wiki: str, page_title: str, quality: int,
                     token: str, access_token: str) -> dict:
    """Set the proofread quality level for a Page: page.
    
    Requires proofread or validate rights. Quality values: 0-3.
    """
    api_url = f"https://{wiki}.wikisource.org/w/api.php"
    resp = requests.post(api_url, data={
        "action": "proofread",
        "page": page_title,
        "quality": quality,
        "token": token,
        "format": "json",
    }, headers={
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "WskTool/1.0 (user@example.com)",
    })
    resp.raise_for_status()
    return resp.json()
```

---

## The Proofreading Lifecycle

```
          ┌─────────────┐
          │ DjVu/PDF    │
          │ uploaded to │
          │ Commons     │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │ Index: page │
          │ created on  │
          │ Wikisource  │
          └──────┬──────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │ Page: pages auto-created│
    │ with OCR text layer     │
    │ Quality: 0 (Without)    │
    └─────────────────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │ Proofreader corrects    │
    │ text against scan       │
    │ Quality → 2 (Proofread) │
    └─────────────────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │ Validator re-reads text │
    │ against scan            │
    │ Quality → 3 (Validated) │
    └─────────────────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │ Pages transcluded into  │
    │ main namespace work     │
    │ Page protected          │
    └─────────────────────────┘
```

---

## Key Templates

| Template | Purpose | Placement |
|----------|---------|-----------|
| `{{header}}` | Page header with chapter/number | Top of each Page: page |
| `{{footer}}` | Page footer | Bottom of each Page: page |
| `{{nop}}` | No paragraph break (preserve spacing) | After paragraphs |
| `{{c|text}}` | Centered text | For chapter headings, centered text |
| `{{larger|text}}` | Larger font | Chapter titles |
| `{{smaller|text}}` | Smaller font | Footnotes, attributions |
| `{{gap}}` | Horizontal spacing | Poetry, indented text |
| `{{raw image}}` | Image that should not be cropped | Illustrations, diagrams |
| `{{missing image}}` | Placeholder for missing image | Illustrations not yet uploaded |
| `{{eh}}` | End of hyphenation | Words split across page breaks |

---

## API Examples

### Get Quality Distribution for an Index

```
GET https://en.wikisource.org/w/api.php
  ?action=query
  &titles=Index:Pride_and_Prejudice.djvu
  &prop=proofreadinfo
  &piprop=quality
  &format=json
```

### Get All Pages of a Specific Quality

```
GET https://en.wikisource.org/w/api.php
  ?action=query
  &list=proofreadpages
  &pipqual=2
  &pipindex=Index:Pride_and_Prejudice.djvu
  &format=json
```

### Get the Text of a Specific Page

```
GET https://en.wikisource.org/w/api.php
  ?action=parse
  &page=Page:Pride_and_Prejudice/1
  &prop=wikitext
  &format=json
```
