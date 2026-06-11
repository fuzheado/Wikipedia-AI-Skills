# Common Search Scenarios

Real-world scenarios with executable queries, organized by workflow.

---

## 1. Page Discovery and Research

### Find comprehensive pages on a topic
```cirrus
# Articles about quantum computing
quantum computing

# More specific: articles about the physics concept, not the technology
intitle:"quantum" incategory:Physics
```

### Find all pages about a place with a specific feature
```cirrus
# Bridges in New York (category intersection)
incategory:"Suspension bridges" incategory:"Bridges in New York City"

# Museums in Paris with a Wikipedia article
incategory:"Museums in Paris"
```

### Find pages with similar content to a known page
```cirrus
# Equivalent to "find more pages like this one"
morelike:quantum|mechanics

# With template constraints
morelikethis:bee hastemplate:"Featured article"
```

---

## 2. News and Current Events

### Find recently-updated pages on a topic
```cirrus
# Pages about climate change edited today
climate change lasteditdate:today

# Pages edited in the last week about a specific topic
incategory:"Current events" lasteditdate:>=today-7d

# Pages created this year on a topic
intitle:election creationdate:>=2026
```

### Find breaking news coverage (pages created very recently)
```cirrus
# Pages created in the last 24 hours
creationdate:>=today-1d

# Combined with "prefer-recent" for recency-biased ranking
prefer-recent:1,0.04 incategory:"2026"
```

---

## 3. Patrolling and New Page Reviewer

### Find new unreviewed pages in a specific area
```cirrus
# Recently created articles in a WikiProject's scope
incategory:"WikiProject Physics articles" creationdate:>=today-7d
```

### Find articles that need immediate attention
```cirrus
# Unsourced BLPs
hastemplate:"BLP sources" incategory:"Living people"
hastemplate:"BLP unsourced" incategory:"Living people"

# Recently created articles with no categories
incategory:"Uncategorized pages" creationdate:>=today-7d
```

### Find potentially promotional pages
```cirrus
# Pages with promotional language patterns
# (cirrus can't detect tone, but can find common promotional template patterns)
hastemplate:"Advert" incategory:"All articles with unsourced statements"
```

---

## 4. Citation and Reference Audits

### Find articles with bare URLs in citations
```cirrus
# Pages with no cite template but containing URLs
insource:"http://" -hastemplate:"cite web" -hastemplate:"cite news" -hastemplate:"cite journal"
```

### Find articles with dead link tags
```cirrus
hastemplate:"Dead link" incategory:"All articles with dead external links"
```

### Find articles with insufficient citations
```cirrus
# Articles with the "refimprove" template
hastemplate:"Refimprove"
hastemplate:"More citations needed"
```

---

## 5. Template and Infobox Audits

### Find all pages using a specific infobox
```cirrus
hastemplate:"Infobox scientist"
hastemplate:"Infobox settlement" incategory:"Populated places in France"
```

### Find infobox misuse
```cirrus
# Pages with an infobox but missing key parameter (example: no image)
hastemplate:"Infobox person" -insource:"|image =" -insource:"|image ="
```

### Find pages using deprecated templates
```cirrus
hastemplate:"Deprecated template"
# Or more directly (deprecated templates usually have tracking categories)
incategory:"Pages using deprecated templates"
```

### Find template documentation problems
```cirrus
# Template pages missing documentation
hastemplate:"Template documentation" -insource:"{{Documentation"
incategory:"Template documentation"
```

---

## 6. Category Maintenance

### Find uncategorized pages
```cirrus
incategory:"All uncategorized pages"
# Or more specifically
incategory:"Wikipedia uncategorized articles"
```

### Find overcategorized pages (parent + child)
```cirrus
incategory:"Physics" incategory:"Subfields of physics"
```

### Find categories with few members (near-empty)
```cirrus
# Uses pageid filter with known IDs — better done via API
# API: list=categorymembers&cmtitle=Category:Name&cmlimit=1
```

### Find category redirects that should be bypassed
```cirrus
incategory:"Wikipedia category redirects"
```

---

## 7. WikiProject Quality Drives

### Find unassessed articles in a WikiProject
```cirrus
incategory:"Unassessed Wikipedia articles" incategory:"WikiProject Physics articles"
```

### Find stub articles in a specific area
```cirrus
incategory:"Physics stubs"
incategory:"Biography stubs" incategory:"WikiProject Physics articles"
```

### Find articles needing expansion
```cirrus
# Articles tagged as stubs in a specific category (via intersection)
# Direct: search in stub category
incategory:"Physics stubs"
```

### Find articles with specific maintenance tags
```cirrus
# Articles needing copy editing
hastemplate:"Copy edit" incategory:"All articles with unsourced statements"

# Articles needing expert attention
hastemplate:"Expert needed"
```

---

## 8. File and Commons Audits

### Find files without structured data
```cirrus
# On Commons: files with no "depicts" statement
-haswbstatement:P180

# Files without a Wikimedia Commons category (on Commons)
-haswbstatement:P373
```

### Find unused files
```cirrus
# On Commons (approximation — use Special:UnusedFiles for accuracy)
incategory:"Unused files"
```

### Find files by type and criteria
```cirrus
# All video files
filetype:video

# PDF documents larger than 10MB
filemime:application/pdf filesize:>10240

# Images at least 1920×1080
filew:>=1920 fileh:>=1080
```

---

## 9. Cross-Wiki and Cross-Language

### Find articles in a specific language
```cirrus
# On a wiki with Translate extension
inlanguage:fr
inlanguage:ja incategory:Physics
```

### Find items without a label in a specific language (Wikidata)
```cirrus
# Items with no English label
hascaption:en -hascaption:ja
```

### Find items with a description in one language but not another
```cirrus
hasdescription:en -hasdescription:fr
```

---

## 10. Administrative and Policy Enforcement

### Find possible copyright violations
```cirrus
# Pages tagged for copyright review
hastemplate:"Copyright violation"
hastemplate:"Copyrighted free use"
```

### Find pages with POV issues
```cirrus
# Pages tagged for NPOV review
hastemplate:"POV"
hastemplate:"NPOV"
hastemplate:"Neutrality"
```

### Find pages needing splitting or merging
```cirrus
hastemplate:"Split"
hastemplate:"Merge"
hastemplate:"Merge to"
```

### Find redirects to non-existent pages
```cirrus
# This is tricky via search alone — use the API or a tool like WMF's broken redirects report
# Approximate: search for redirect pages
incategory:"Articles with redirect hatnotes"
```
