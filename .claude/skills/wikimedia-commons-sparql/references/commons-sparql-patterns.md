# Commons SPARQL Query Patterns Reference

> This reference covers Commons-specific SPARQL patterns. For general SPARQL syntax and Wikidata Query Service patterns, see the [wikidata skill](../wikidata/SKILL.md) and its [references](../wikidata/references/).

---

## Quick Reference: Commons Properties and Their SPARQL Usage

| Property | Label | SPARQL Pattern | Value Type |
|----------|-------|----------------|------------|
| P180 | depicts | `?file wdt:P180 wd:Q42` | Wikidata item URI |
| P6243 | digital representation of | `?file wdt:P6243 wd:Q179900` | Wikidata item URI |
| P170 | creator | `?file wdt:P170 wd:Q5582` | Wikidata item URI (or text via qualifier) |
| P571 | inception | `?file wdt:P571 ?date . FILTER(YEAR(?date) > 2000)` | dateTime |
| P7482 | source of file | `?file wdt:P7482 wd:Q74228490` | Wikidata item URI |
| P6216 | copyright status | `?file wdt:P6216 wd:Q50402863` | Wikidata item URI |
| P275 | copyright license | `?file wdt:P275 wd:Q50829104` | Wikidata item URI |
| P4082 | captured with | `?file wdt:P4082 wd:Q649631` | Wikidata item URI |
| P1259 | coordinates of point of view | `?file wdt:P1259 ?coords` | WKT literal |
| P2079 | fabrication method | `?file wdt:P2079 wd:Q226881` | Wikidata item URI |
| P973 | described at URL | `?file wdt:P973 ?url` | string/URI |
| P180/P462 | depicts → color (qualifier) | `?file p:P180 [ ps:P180 wd:Q42 ; pq:P462 ?color ]` | Qualifier chain |
| P180/P6022 | depicts → expression/gesture | `?file p:P180/pq:P6022 ?gesture` | Qualifier path |

### Common Wikidata Values for Copyright / License Queries

| Q ID | Label | Meaning for Commons |
|------|-------|-------------------|
| Q50402863 | public domain | File is in the public domain |
| Q50402878 | copyrighted | File is under copyright |
| Q50829104 | Creative Commons CC0 1.0 Universal | CC0 (public domain dedication) |
| Q50824428 | Creative Commons Attribution-ShareAlike 4.0 International | CC BY-SA 4.0 |
| Q50824423 | Creative Commons Attribution 4.0 International | CC BY 4.0 |
| Q14946043 | Creative Commons Attribution-ShareAlike 3.0 Unported | CC BY-SA 3.0 |
| Q19168217 | Creative Commons Attribution 2.0 Generic | CC BY 2.0 |

### Common Values for Source of File (P7482)

| Q ID | Label |
|------|-------|
| Q74228490 | file available on the internet |
| Q548662 | original creation by uploader |
| Q66458942 | file transferred from Flickr |
| Q21951427 | file transferred from Wikimedia Commons |
| Q21951635 | file donated by the copyright holder |

---

## Schema.org Predicates Reference

These predicates from the Schema.org vocabulary are available for every MediaInfo entity:

| Predicate | Type | Example | Use Case |
|-----------|------|---------|----------|
| `schema:url` | URI | File page on Commons | **Required for ImageGrid display** |
| `schema:contentUrl` | URI | Direct download URL | Getting actual file bytes |
| `schema:thumbnailUrl` | URI | Thumbnail URL | Preview (300px wide) |
| `schema:width` | Integer | 1920 | Filtering by image size |
| `schema:height` | Integer | 1080 | Filtering by image size |
| `schema:encodingFormat` | String | "image/jpeg" | Filtering by file type |
| `schema:datePublished` | Date | 2023-01-15 | Filtering by publication date |
| `schema:name` | String | Multilingual file name | File name search |
| `schema:description` | String | Multilingual description | Description text |

---

## Performance Patterns: Sampling

For large result sets, use random sampling to avoid timeouts (especially on WCQS):

```sparql
# Random sample of 100,000 files with depicts statements
SELECT (COUNT(DISTINCT(?file)) AS ?count) ?source WHERE {
  SERVICE bd:sample {
    ?file wdt:P7482 ?source .
    bd:serviceParam bd:sample.limit 100000 .
    bd:serviceParam bd:sample.sampleType "RANDOM" .
  }
}
GROUP BY ?source
```

> **Note:** The `bd:sample` SERVICE is a Blazegraph feature and may not be available on QLever. On QLever, use `LIMIT` with `ORDER BY RAND()` or accept results from a LIMIT query.

---

## Construction of M IDs from Page IDs

When using `wikibase:mwapi` or working with PetScan data, you often get numeric page IDs and need to construct M ID URIs:

```sparql
BIND(URI(CONCAT('https://commons.wikimedia.org/entity/M', ?pageid)) AS ?file)
```

To convert back from an M ID URI to a numeric page ID for use with Pywikibot:

```python
# In Python
m_id = "M37200540"
page_id = int(m_id.replace("M", ""))
# Use site.load_pages_from_pageids([page_id])
```

---

## Common Federation Patterns

### Find files for Wikidata items not yet illustrated

```sparql
# Find Wikidata items that have no image (P18) but have Commons files depicting them
SELECT ?item ?itemLabel ?image WHERE {
  SERVICE <https://query.wikidata.org/sparql> {
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31 wd:Q5 ;            # instance of human
             wdt:P106 wd:Q36180 .       # occupation = writer
      FILTER NOT EXISTS { ?item wdt:P18 ?image . }  # no image yet
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
      }
    }
    LIMIT 100
  }
  ?file wdt:P180 ?item ;               # file depicts this writer
         schema:url ?image .
}
```

### Constraint violation detection

```sparql
# Files with multiple "digital representation of" statements (should have only one)
SELECT ?file (COUNT(?value) AS ?count) WHERE {
  ?file wdt:P6243 ?value .
}
GROUP BY ?file
HAVING (?count > 1)
ORDER BY DESC(?count)
LIMIT 100
```

---

## File Discoverability by Known Upload/Date Patterns

### Find files by uploader's camera model

```sparql
SELECT ?file ?image WHERE {
  ?file wdt:P4082 wd:Q649631 ;   # captured with Canon EOS 5D Mark IV
         schema:url ?image .
}
LIMIT 50
```

### Find recently uploaded public domain images

```sparql
SELECT ?file ?date ?image WHERE {
  ?file wdt:P6216 wd:Q50402863 ;   # public domain
         schema:datePublished ?date ;
         schema:url ?image .
  FILTER(?date > "2025-01-01"^^xsd:dateTime)
}
ORDER BY DESC(?date)
LIMIT 100
```
