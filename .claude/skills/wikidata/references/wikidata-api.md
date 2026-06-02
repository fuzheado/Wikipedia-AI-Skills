# Wikidata API Reference

## Action API (Wikibase)

Base: `https://www.wikidata.org/w/api.php`

### Get entities by ID
```
action=wbgetentities&ids=Q937|Q5|Q5&props=labels|descriptions|claims|sitelinks&languages=en&format=json
```

### Search entities
```
action=wbsearchentities&search=Einstein&language=en&limit=10&format=json
```

### Get claims for an item
```
action=wbgetclaims&entity=Q937&format=json
```

### Get entity data for a property
```
action=wbgetentities&ids=P31&props=labels|descriptions|claims&format=json
```

## SPARQL Endpoint

Base: `https://query.wikidata.org/sparql`

### Common pattern: Items matching a class
```sparql
SELECT ?item ?itemLabel WHERE {
  ?item wdt:P31 wd:Q5.    # instance of human
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
```

### Transitive subclass (all subclasses recursively)
```sparql
SELECT ?item ?itemLabel WHERE {
  ?item wdt:P279* wd:Q729.   # subclass of* animal (transitive)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

### With qualifiers
```sparql
SELECT ?item ?itemLabel ?population ?pointInTime WHERE {
  ?item wdt:P31 wd:Q515;        # instance of city
         p:P1082 ?popStmt.      # population statement (property path)
  ?popStmt ps:P1082 ?population;  # population value
           pq:P585 ?pointInTime.  # point in time qualifier
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 20
```

## Common Q and P ID Reference

### Frequently used Q IDs (items)
| Q ID | Label | Note |
|------|-------|------|
| Q5 | human | Most basic item type |
| Q2 | Earth | |
| Q30 | United States of America | |
| Q90 | Paris | |
| Q727 | Titanic | |
| Q937 | Albert Einstein | |
| Q33506 | museum | |
| Q11424 | motion picture | Film |
| Q28865 | Python (programming language) | |
| Q3305213 | painting | |
| Q4167410 | Wikimedia disambiguation page | For disambiguation items |
| Q13442814 | Wikimedia list article | For list articles |

### Frequently used P IDs (properties)
| P ID | Label | Data Type | When to Use |
|------|-------|-----------|-------------|
| P31 | instance of | Item | What class this *specific thing* belongs to |
| P279 | subclass of | Item | Hierarchy: one class is a subtype of another |
| P21 | sex or gender | Item | Male/female/other |
| P106 | occupation | Item | What a person does for work |
| P569 | date of birth | Time | When someone was born |
| P570 | date of death | Time | When someone died |
| P19 | place of birth | Item | Where someone was born |
| P20 | place of death | Item | Where someone died |
| P69 | educated at | Item | School, university |
| P108 | employer | Item | Organization employing a person |
| P166 | award received | Item | Awards and honors |
| P800 | notable work | Item | Famous works by a person |
| P856 | official website | URL | Website URL |
| P625 | coordinate location | Coordinate | Lat/lon of a place |
| P18 | image | Commons Media | Representative image file name |
| P373 | Commons category | String | Category name on Commons |
| P50 | author | Item | Creator of a written work |
| P170 | creator | Item | Creator of a creative/artistic work |
| P180 | depicts | Item | What a Commons file shows |
| P571 | inception | Time | Date of creation/founding |
| P576 | dissolved, abolished or demolished date | Time | Date of dissolution |
| P1082 | population | Quantity | Population number |
| P856 | official website | URL | Website |
| P1320 | OpenAlex ID | External ID | Linked open data |
| P214 | VIAF ID | External ID | Authority control |
| P213 | ISNI | External ID | Authority control |
| P244 | Library of Congress authority ID | External ID | Authority control |
