---
name: wikimedia-commons-pdf
description: Work with PDF and DjVu documents on Wikimedia Commons — multi-page document model, page selection for thumbnails (page1- prefix), page dimensions, uploading large documents, Wikisource proofread integration, OCR text extraction, document metadata (pagecount, PDF version), and editing/versioning multi-page files
depends_on: [wikimedia-api-access, wikimedia-commons, wikimedia-commons-thumbnails]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["PDF", "PDF file", "DjVu", "document", "multipage", "page", "pagecount", "proofread"]
  - keywords: ["page1-", "page selection", "page rendering", "PDF thumbnail", "DjVu thumbnail", "scan"]
  - keywords: ["Wikisource", "Page namespace", "OCR", "text extraction", "proofread page", "book scanning"]
  - keywords: ["PDF metadata", "pdf_version", "pdf_encrypted", "DjVu metadata", "document rendering"]
  - keywords: ["Commons document", "Commons PDF", "Commons DjVu", "upload PDF", "upload DjVu"]
  - keywords: ["iiurlparam", "page selector", "page dimension"]
last_verified: 2026-06-16
---

> ⚠️ **User-Agent required:** All curl and code examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

---

## 1. PDF/DjVu on Commons: Document Model

PDF and DjVu files on Commons are treated as **multi-page documents**, not single images. This affects everything from how metadata is reported to how thumbnails work.

### Key Differences from Image Files

| Aspect | Image (JPEG, PNG, etc.) | Document (PDF, DjVu) |
|--------|------------------------|----------------------|
| API width/height | Native pixel dimensions | **Page dimensions** (typically the first page) |
| `mediatype` | `BITMAP`, `DRAWING` | `OFFICE` or `TEXT` |
| `pagecount` | Not present | **Present** — number of pages |
| Thumbnail | One per file | **One per page** — page selector prefix in URL |
| Resolution | Fixed (native pixels) | Unlimited (page renders at any size) |

### Format Comparison

| Format | MIME Type | Typical Use | Notes |
|--------|-----------|-------------|-------|
| PDF | `application/pdf` | Scanned books, documents, forms | Most common document format on Commons |
| DjVu | `image/vnd.djvu` | Scanned books, especially on Wikisource | Better compression for scanned text pages |

> 💡 DjVu is less common on Commons overall, but **very common on Wikisource** because of its superior compression for scanned text (black-and-white or limited-color pages). Many older Wikisource works use DjVu.

### API: Checking If a File Is a Document

```python
import requests

resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "size|mime|metadata|mediatype",
    "titles": "File:The Three Hostages (1924).pdf",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

page = next(iter(resp.json()["query"]["pages"].values()))
info = page.get("imageinfo", [{}])[0]

print(f"MIME:       {info.get('mime')}")
print(f"Mediatype:  {info.get('mediatype')}")
print(f"Dimensions: {info.get('width')}×{info.get('height')} (page 1)")
print(f"File size:  {info.get('size')} bytes")

# Extract pagecount from metadata
for meta in info.get("metadata", []):
    if meta["name"] == "pagecount":
        print(f"Pages:      {meta['value']}")
```

---

## 2. Page Selection and Thumbnails

### Thumb URL Pattern for Documents

Document thumbnails include a **page selector** in the URL:

```
https://upload.wikimedia.org/wikipedia/commons/thumb/{hash}/{filename}/page{N}-{width}px-{filename}.jpg
```

Where `{N}` is the **1-indexed page number**.

**Real example (PDF, page 1, 960px):**
```
https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/PDF_metadata.pdf/page1-960px-PDF_metadata.pdf.jpg
```

### Requesting Thumbnails via the Action API

Use `iiurlwidth` to request a thumbnail — it defaults to **page 1**:

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|thumbmime",
    "iiurlwidth": 800,
    "titles": "File:PDF_metadata.pdf",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

info = next(iter(resp.json()["query"]["pages"].values()))["imageinfo"][0]
print(f"Page 1 thumb: {info['thumburl']}")     # → .../page1-960px-....jpg
print(f"Thumb MIME:   {info['thumbmime']}")    # → image/jpeg
print(f"Dimensions:   {info['thumbwidth']}×{info['thumbheight']}")
```

### Selecting a Specific Page via `iiurlparam`

To get a thumbnail for a different page, use `iiurlparam`:

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|thumbmime",
    "iiurlwidth": 800,
    "iiurlparam": "page3",          # request page 3
    "titles": "File:100-page-document.pdf",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})
```

> 💡 **`iiurlparam` syntax:** `page{N}` where N is the 1-indexed page number. This works for both PDF and DjVu.

### Constructing Thumb URLs for Arbitrary Pages

If you have the page 1 thumb URL, you can construct URLs for other pages by replacing the page number:

```python
import re

page1_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Doc.pdf/page1-960px-Doc.pdf.jpg"
page_n_url = re.sub(r"/page\d+-", f"/page{page_number}-", page1_url)
```

> ⚠️ This pattern works 99% of the time, but the safest approach is always to use `iiurlparam` with the API.

### Thumbnail Format

Document page thumbnails are always **JPEG** (`thumbmime: image/jpeg`), regardless of whether the source is PDF or DjVu.

---

## 3. Page Dimensions Across a Document

### What the API Reports

The `width` and `height` fields in `prop=imageinfo` report the dimensions of **page 1 only**. In a multi-page document, different pages may have different dimensions.

### Getting Dimensions for All Pages

Commons does not expose per-page dimensions directly through the Action API. To get them:

**Option 1: Parse the PDF metadata** (for locally accessible files)

```bash
# Using pdfinfo (part of poppler-utils)
pdfinfo document.pdf | grep -E "Pages|Page size"
```

**Option 2: Render each page and check dimensions** (slow but works via API)

```python
for page_num in range(1, pagecount + 1):
    resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "size",
        "iiurlwidth": 100,  # small width to minimize bandwidth
        "iiurlparam": f"page{page_num}",
        "titles": "File:Doc.pdf",
        "format": "json",
    }, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})
    info = next(iter(resp.json()["query"]["pages"].values()))["imageinfo"][0]
    print(f"Page {page_num}: {info['thumbwidth']}×{info['thumbheight']}")
```

> 💡 This is slow for large documents. Consider fetching the PDF locally and using PyPDF2 or similar to extract per-page dimensions.

### DjVu vs PDF Page Structure

| Aspect | PDF | DjVu |
|--------|-----|------|
| Page dimensions | Can vary per page | Can vary per page |
| Compression | Per-page content streams | Single file with layered pages |
| Page count metadata | `pdf_pagecount` field | `pagecount` field |
| Page numbering | 1-indexed | 1-indexed |

---

## 4. Uploading Documents

### Allowed Formats

| Format | Accepted? | Notes |
|--------|:---------:|-------|
| PDF | ✅ | Most common document format |
| DjVu | ✅ | Preferred for Wikisource scanned texts |
| EPUB | ❌ | Not supported by Commons |
| MOBI | ❌ | Not supported |
| DOC/DOCX | ❌ | Not supported — convert to PDF first |
| ODT | ❌ | Not supported — convert to PDF first |

### Converting to PDF for Upload

```bash
# Convert DOCX to PDF (LibreOffice)
libreoffice --headless --convert-to pdf input.docx

# Convert EPUB to PDF
pandoc input.epub -o output.pdf

# Combine multiple images into a PDF
convert page-*.jpg combined.pdf
```

### File Size Considerations

- Documents can be **hundreds of megabytes** (scanned books at high resolution)
- Commons has a per-file size limit (typically 100 MB for standard upload, larger may require chunked upload or special handling)
- DjVu tends to be **smaller** than PDF for scanned text pages

### Upload Tools

| Tool | Best For |
|------|----------|
| **[UploadWizard](https://commons.wikimedia.org/wiki/Special:UploadWizard)** | Single documents, step-by-step metadata entry |
| **[Pattypan](https://commons.wikimedia.org/wiki/Commons:Pattypan)** | Batch uploads with spreadsheet-based metadata |
| **Action API** (`action=upload`) | Automated uploads with authentication |

> ⚠️ **`video2commons` does NOT handle PDF or DjVu.** Use UploadWizard, Pattypan, or direct API upload instead.

### Converting DjVu ↔ PDF

```bash
# DjVu → PDF
ddjvu -format=pdf input.djvu output.pdf

# PDF → DjVu (for Wikisource — better compression for text pages)
pdf2djvu input.pdf -o output.djvu  # preserves OCR text layer when present
```

---

## 5. Wikisource Integration (Critical)

The primary use of PDF and DjVu files on Commons is as **backing documents** for Wikisource — the free-content digital library.

### The Proofread Page Workflow

Wikisource uses a **[proofread](https://en.wikisource.org/wiki/Help:Proofread)** workflow where:

1. A scanned document (PDF or DjVu) is uploaded to Commons
2. Wikisource creates one `Page:` namespace page per document page
3. Editors proofread the OCR text against the scan image
4. Once validated, pages are transcluded into the final work in the main namespace

### Linking Pattern

The linking between a Commons document and its Wikisource pages uses the `{{ProofreadPage}}` template:

```
https://en.wikisource.org/w/index.php?title=Page:Book_Title.djvu/1
```

Each `Page:Namespace` page (NS 104 on Wikisource) contains:
- The OCR text extracted from that page
- The scan image of that page (referenced to the Commons file)
- Proofreading status (Proofread, Problematic, Validated)

### Checking If a Document Is Used on Wikisource

Use `prop=globalusage` to check if a document is linked to Wikisource:

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "globalusage",
    "titles": "File:My_Document.pdf",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

usage = next(iter(resp.json()["query"]["pages"].values())).get("globalusage", [])
wikisource_usage = [u for u in usage if "wikisource" in u.get("wiki", "")]
print(f"Used on {len(wikisource_usage)} Wikisource(s)")
```

### Marking Documents for Wikisource

| Template | Purpose |
|----------|---------|
| `{{PDF}}` | General PDF marker |
| `{{DjVu}}` | General DjVu marker |
| `{{Book}}` | Full book description template (author, title, year, pages) |
| `{{ProofreadPage}}` | Links the file to its Wikisource work |

> 🔗 **Detailed Wikisource workflow:** See the **[wiktionary-and-wikisource](../wiktionary-and-wikisource/SKILL.md)** skill for complete coverage of the proofread page lifecycle, including validation levels, progress tracking, and transclusion.

---

## 6. Document Metadata

### PDF-Specific Metadata

The Action API `iiprop=metadata` returns PDF-specific fields:

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "metadata",
    "titles": "File:Document.pdf",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

info = next(iter(resp.json()["query"]["pages"].values()))["imageinfo"][0]
for meta in info.get("metadata", []):
    print(f"{meta['name']}: {meta['value']}")
```

Common PDF metadata fields:

| Field | Type | Example |
|-------|------|---------|
| `pagecount` | Integer | `324` |
| `pdf_version` | String | `1.7` |
| `pdf_encrypted` | Boolean | `false` |
| `pdf_created` | Timestamp | `2020-01-15T10:30:00` |
| `pdf_modified` | Timestamp | `2020-06-01T14:22:00` |
| `pdf_pagecount` | Integer | Same as `pagecount` |
| `pdf_has_xfa` | Boolean | Whether the PDF uses XFA forms |

### DjVu-Specific Metadata

DjVu files expose different metadata:

| Field | Description |
|-------|-------------|
| `pagecount` | Number of pages |
| `djvu_page_width` | Width of each page (comma-separated if varying) |
| `djvu_page_height` | Height of each page |
| `djvu_resolution` | Scan resolution in DPI |

### Shared Metadata

Both PDF and DjVu may expose:
- `playtime_seconds` — Not standard for documents, but may be populated for some PDF/DjVu files
- `mediatype` — `OFFICE` or `TEXT`

---

## 7. OCR and Text Extraction

Commons runs **automatic OCR** on uploaded PDF and DjVu files using **Tesseract**.

### How OCR Works

1. File is uploaded to Commons
2. The OCR pipeline detects the language(s) present
3. Tesseract extracts text from each page
4. The extracted text is made available on the corresponding Wikisource `Page:` namespace

### Checking OCR Status

OCR status is not directly exposed by the Commons API. To check if OCR has been run:

- Check the file's Wikisource Page: namespace entries — if they contain text, OCR ran
- Manual validation: the `{{PDFOCR}}` template on the file page indicates OCR was applied

### When OCR May Fail

| Situation | Result |
|-----------|--------|
| Language not supported by Tesseract | No OCR |
| Handwritten text | Poor quality or no OCR |
| Image-only pages (no text) | No OCR |
| Very poor scan quality | Garbled OCR |
| Scan resolution too low (<150 DPI) | Poor OCR quality |

### Uploading a Text Layer

If the automatic OCR is insufficient, you can upload a PDF or DjVu that already contains an embedded text layer. Tools like `pdf2djvu` preserve existing text layers during conversion.

---

## 8. PDF/DjVu-Specific Templates and Categories

### Templates

| Template | Usage |
|----------|-------|
| `{{PDF}}` | Marks file as a PDF, adds to `Category:PDF files` |
| `{{DjVu}}` | Marks file as a DjVu, adds to `Category:DjVu files` |
| `{{Book}}` | Descriptive template for multi-page documents with title, author, year, pages, source, and other bibliographic fields |
| `{{Proofread}}` | Links to the corresponding Wikisource work |
| `{{PDFOCR}}` | Indicates OCR text has been extracted |
| `{{Scanned}}` | Marks as a scanned document (as opposed to born-digital PDF) |

### Category Hierarchy

```
Category:PDF files
├── PDF files by language
│   ├── PDF files in English
│   ├── PDF files in French
│   └── ...
├── PDF files by topic
│   ├── PDF books
│   ├── PDF journals
│   └── ...
└── PDF files by size

Category:DjVu files
├── DjVu files by language
├── DjVu files by topic
└── DjVu files by size

Category:Scan pages
├── Proofread
├── Not proofread
└── Problematic
```

---

## 9. Editing and Versioning Documents

### Uploading a New Version

The same `action=upload` pattern used for images applies to documents:

```python
with open("corrected-ocr.pdf", "rb") as f:
    resp = SESSION.post("https://commons.wikimedia.org/w/api.php", data={
        "action": "upload",
        "filename": "Existing_Document.pdf",
        "comment": "Replaced page 47 scan, fixed OCR layer",
        "token": csrf_token,
        "format": "json",
    }, files={"file": f})
```

> 🔗 **Authentication setup:** See **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** for bot passwords and CSRF token handling.

### ⚠️ Page Range Replacement

Commons does **not support** partial page replacement within a document. To replace a single page:

1. Download the full document locally
2. Extract all pages
3. Replace the specific page(s)
4. Recombine and re-upload the entire document

```bash
# Extract all pages from PDF
pdfseparate -f 1 -l 500 input.pdf page-%d.pdf

# Replace page 47
# ... edit page-47.pdf ...

# Recombine
pdfunite page-*.pdf output.pdf

# Upload output.pdf as new version of the original
```

### Replacing DjVu with PDF (or Vice Versa)

If you need to change the format of an existing document (e.g., replace a DjVu with a better-quality PDF), you cannot "re-upload" to the same filename with a different MIME type. You must:

1. Upload the new file as a **new filename** (e.g., `Document (PDF).pdf`)
2. Update Wikisource Page: namespace links to point to the new file
3. Request deletion of the old file (if appropriate)

### File History for Documents

All previous versions of a document are retained in the file history, just like images:

```python
resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|timestamp|user|size|comment",
    "titles": "File:Document.pdf",
    "format": "json",
})
```

Each archived version includes a timestamped URL to download that version.

---

## Related Skills

| Skill | Relevance |
|-------|-----------|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, rate limiting, error handling |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | File search, categories, upload basics |
| **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** | Document page rendering, thumb URL scheme, `thumbmime` |
| **[wiktionary-and-wikisource](../wiktionary-and-wikisource/SKILL.md)** | Wikisource proofread workflow, Page: namespace, transclusion |
| **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** | Authentication for uploading new document versions |
