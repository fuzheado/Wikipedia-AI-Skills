# Citation Maintenance Templates — Full Reference

Templates that flag citation issues for human reviewers.

---

## Inline Templates (Placed After the Issue)

| Template | What It Signals | Parameters | When to Use |
|----------|----------------|------------|-------------|
| `{{citation needed}}` / `{{cn}}` | A claim needs a reliable source | `date=` | A factual statement has no citation at all |
| `{{dead link}}` | A cited URL no longer works | `date=`, `bot=` | URL returns 404 or connection fails |
| `{{failed verification}}` | Cited source does not support the claim | `date=` | Source exists but says something different |
| `{{full citation needed}}` | Key bibliographic details missing | `date=` | Citation lacks publisher, page, date, etc. |
| `{{page needed}}` / `{{pn}}` | No specific page number given | `date=` | Book or long article cited without page |
| `{{better source needed}}` | Source is weak, unreliable, or primary | `date=`, `reason=` | Source is blog, forum, or primary |
| `{{verification needed}}` | Claim may not match the cited source | `date=` | Suspicious but not certain it's wrong |
| `{{self-published source}}` | Source is self-published | `date=` | Blog, personal website, self-published book |
| `{{primary source inline}}` | Source is primary, secondary preferred | `date=` | Original research paper when review is available |
| `{{medical citation needed}}` | Medical claim needs medical source | `date=` | Health/medical claims |
| `{{third-party inline}}` | Source is too close to the subject | `date=` | Company website cited for company facts |
| `{{bare URL}}` / `{{bare URL inline}}` | URL not wrapped in a citation template | `date=` | Bare `<ref>https://...</ref>` |
| `{{unreliable source?}}` | Source may not be reliable | `date=`, `reason=` | Questionable but not certain |
| `{{bsn}}` | Alias for `{{better source needed}}` | | |
| `{{dubious}}` | Fact is likely incorrect | `date=` | Claim contradicts common knowledge |
| `{{original research inline}}` | Claim appears to be original research | `date=` | Synthesis or original analysis |
| `{{promotion inline}}` | Text reads like promotion | `date=` | Peacock language, puffery |

## Article-Level Templates (Placed at Top of Article or Section)

| Template | What It Signals | Parameters |
|----------|----------------|------------|
| `{{refimprove}}` | Article needs more references | `date=` |
| `{{more citations needed}}` | Alias for `{{refimprove}}` | `date=` |
| `{{one source}}` | Article relies on a single source | `date=` |
| `{{primary sources}}` | Article relies too heavily on primary sources | `date=` |
| `{{third-party}}` | Article lacks independent sources | `date=` |
| `{{no footnotes}}` | No inline citations (only general references) | `date=` |
| `{{citation style}}` | Citation formatting needs cleanup | `date=`, `details=` |
| `{{more footnotes}}` | Inline citations exist but are insufficient | `date=` |
| `{{cleanup bare URLs}}` | Many bare URLs need expanding | `date=` |
| `{{linkrot}}` | Large number of bare URLs | `date=` |

## Section Templates (Placed at Top of Section)

| Template | What It Signals | Parameters |
|----------|----------------|------------|
| `{{unreferenced section}}` | Entire section has no citations | `date=` |
| `{{refimprove section}}` | Section needs more citations | `date=` |
| `{{one source section}}` | Section relies on one source | `date=` |

## Detecting Templates via API

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}

def find_templates(wikitext: str, template_name: str) -> list[str]:
    """Find all instances of a template in wikitext."""
    import re
    return re.findall(r"\{\{" + template_name + r"[^}]*\}\}", wikitext, re.IGNORECASE)

def count_maintenance_tags(page_title: str, lang: str = "en") -> dict:
    """Count all maintenance templates on a page."""
    domain = f"{lang}.wikipedia.org"
    params = {"action": "parse", "page": page_title, "prop": "wikitext", "format": "json"}
    resp = requests.get(f"https://{domain}/w/api.php", params=params, headers=headers)
    wikitext = resp.json()["parse"]["wikitext"]["*"]
    
    templates = [
        "citation needed", "dead link", "failed verification", "full citation needed",
        "page needed", "better source needed", "bare URL", "bare URL inline",
        "unreliable source", "dubious", "self-published source", "primary source inline",
        "medical citation needed", "third-party inline", "refimprove", "more citations needed",
        "one source", "primary sources", "no footnotes", "more footnotes", "cleanup bare URLs",
    ]
    
    counts = {}
    for tmpl in templates:
        count = len(find_templates(wikitext, tmpl))
        if count > 0:
            counts[tmpl] = count
    
    return counts
```
