# SDC Properties Reference

> Structured Data on Commons uses Wikidata properties on MediaInfo entities. This reference lists the most commonly used properties, their data types, constraint rules, and Commons-specific usage patterns.

---

## Item-Type Properties

These properties link a Commons file to a Wikidata item.

| Property | Label | Value Type | Single Value? | Notes |
|----------|-------|------------|:-------------:|-------|
| P180 | depicts | `wikibase-item` | No | The most-used SDC property. Can have qualifiers: P462 (color), P6022 (expression/gesture), P518 (applies to part). |
| P6243 | digital representation of | `wikibase-item` | **Yes** | A file should represent at most one Wikidata item. Use depicts (P180) for additional subjects. |
| P170 | creator | `wikibase-item` | No | Use `somevalue` + qualifier P2093 (author name string) for unknown Wikidata creators. |
| P6216 | copyright status | `wikibase-item` | No | Common values: Q50402863 (public domain), Q50402878 (copyrighted). |
| P275 | copyright license | `wikibase-item` | No | Common values: Q50829104 (CC0), Q50824428 (CC BY-SA 4.0), Q50824423 (CC BY 4.0). |
| P7482 | source of file | `wikibase-item` | No | Common values: Q74228490 (file available on internet), Q548662 (original creation). |
| P4082 | captured with | `wikibase-item` | No | Camera model as a Wikidata item (e.g., Q649631 for Canon EOS 5D). |
| P1071 | location of creation | `wikibase-item` | No | Place where the file was created (e.g., Q90 for Paris). |
| P136 | genre | `wikibase-item` | No | Genre of the work (e.g., Q615498 for documentary photography). |
| P921 | main subject | `wikibase-item` | No | Primary topic of the work. |
| P31 | instance of | `wikibase-item` | No | What type of thing the file is (e.g., Q125191 for photograph). |
| P2079 | fabrication method | `wikibase-item` | No | How the image was created (e.g., Q226881 for digital photography). |
| P180/P462 | depicts + color | qualifier | — | Color of the depicted subject (e.g., Q23444 for blue). |
| P180/P6022 | depicts + expression | qualifier | — | Expression, gesture or body pose (e.g., Q11424 for smiling). |
| P180/P518 | depicts + applies to part | qualifier | — | Specific part of the depicted item (e.g., Q7363 for nose). |
| P170/P2093 | creator + author string | qualifier | — | Text string for creator name when no Wikidata item exists. |

### Common Q IDs for Copyright Status (P6216)

| Q ID | Label | When to Use |
|------|-------|-------------|
| Q50402863 | public domain | File is in the public domain (copyright expired, not copyrighted, or government work) |
| Q50402878 | copyrighted | File is under copyright |
| Q50402887 | copyrighted, not necessarily subject to a free license | File is copyrighted but may not be freely reusable despite being on Commons |
| Q50402894 | copyright status not stated | Copyright status is unknown |

### Common Q IDs for License (P275)

| Q ID | Label | SPDX |
|------|-------|------|
| Q50829104 | Creative Commons CC0 1.0 Universal | CC0-1.0 |
| Q50824428 | Creative Commons Attribution-ShareAlike 4.0 International | CC-BY-SA-4.0 |
| Q50824423 | Creative Commons Attribution 4.0 International | CC-BY-4.0 |
| Q14946043 | Creative Commons Attribution-ShareAlike 3.0 Unported | CC-BY-SA-3.0 |
| Q19168217 | Creative Commons Attribution 2.0 Generic | CC-BY-2.0 |
| Q50825122 | Creative Commons Attribution 2.0 UK | CC-BY-2.0-UK |
| Q19169118 | Creative Commons Attribution-ShareAlike 2.0 Generic | CC-BY-SA-2.0 |
| Q20007274 | Creative Commons CC0 1.0 Universal (FAL) | Special free license |
| Q18199165 | Public Domain Mark 1.0 | PDM-1.0 (not a license, but a mark) |

### Common Q IDs for Source of File (P7482)

| Q ID | Label | Notes |
|------|-------|-------|
| Q74228490 | file available on the internet | Used with P973 (described at URL) to link to the original source |
| Q548662 | original creation by uploader | Uploader created the file themselves |
| Q66458942 | file transferred from Flickr | Flickr was the original source |
| Q21951427 | file transferred from Wikimedia Commons | Already on Commons |
| Q21951635 | file donated by the copyright holder | Copyright holder provided the file |
| Q21010874 | file sourced from Wikimedia Commons | Migration from another Wikimedia project |

---

## Date/Time Properties

| Property | Label | Value Type | Precision | Notes |
|----------|-------|------------|:---------:|-------|
| P571 | inception | `time` | day (11) | Date of creation. Use Gregorian calendar by default. |

**Time value format:**
```json
{
  "time": "+2023-01-15T00:00:00Z",
  "timezone": 0,
  "before": 0,
  "after": 0,
  "precision": 11,
  "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
}
```

**Calendar models:**
- `http://www.wikidata.org/entity/Q1985727` — Gregorian calendar (default)
- `http://www.wikidata.org/entity/Q1985786` — Julian calendar

**Precision values:**
| Precision | Meaning | Example |
|:---------:|---------|---------|
| 9 | year | "2023" |
| 10 | month | "2023-01" |
| 11 | day | "2023-01-15" |

---

## Coordinate Properties

| Property | Label | Globe | Notes |
|----------|-------|:-----:|-------|
| P1259 | coordinates of point of view | Earth (Q2) | Where the photographer/camera was positioned |
| P914 | coordinates of depicted place | Earth (Q2) | Coordinates of the subject being photographed |

**Coordinate value format:**
```json
{
  "latitude": 48.8566,
  "longitude": 2.3522,
  "precision": 0.0001,
  "globe": "http://www.wikidata.org/entity/Q2"
}
```

---

## String/URL Properties

| Property | Label | Value Type | Notes |
|----------|-------|------------|-------|
| P973 | described at URL | `string` | URL to the source or description page for the file. Used together with P7482. |

---

## Qualifier-Only Properties

These properties are **qualifiers** — they modify a parent statement and should not be used as standalone claims on Commons.

| Property | Label | Applies To | Example |
|----------|-------|------------|---------|
| P462 | color | P180 (depicts) | `M12345 P180 Q102231` with qualifier `P462 Q23444` (rose + blue) |
| P6022 | expression, gesture or body pose | P180 (depicts) | `M12345 P180 Q5` with qualifier `P6022 Q380110` (human + smiling) |
| P518 | applies to part | P180 (depicts) | `M12345 P180 Q7725639` with qualifier `P518 Q7363` (literary work + specific part) |
| P2093 | author name string | P170 (creator) | `M12345 P170 somevalue` with qualifier `P2093 "John Smith"` |
| P580 | start time | Various | Time when something started |
| P582 | end time | Various | Time when something ended |
| P1545 | series ordinal | Various | Position in a series |
| P3831 | object has role | Various | Role of the value in the statement |

---

## Statement Ranks

| Rank | Meaning | Commons Use |
|------|---------|-------------|
| `preferred` | Most important / key statements | Mark the main subject of a file as preferred. SPARQL queries can filter by rank. |
| `normal` | Standard statements (default) | Most depicts, copyright, license statements. |
| `deprecated` | Known to be incorrect | Used when correcting errors — the incorrect statement is marked deprecated rather than deleted. |

---

## Snak Types

| Type | Meaning | JSON |
|------|---------|------|
| `value` | Normal value | `{"snaktype": "value", "datavalue": {...}}` |
| `somevalue` | Known to exist but unknown | `{"snaktype": "somevalue"}` |
| `novalue` | Does not exist | `{"snaktype": "novalue"}` |

Use `somevalue` when the value is known to exist but the specific value is unknown (e.g., "we know this file has a creator but their identity is unknown"). Use `novalue` to assert that something does not exist (e.g., "this file has no creator in the copyright sense").

---

## Constraint Rules

### Single-Value Constraints

Properties that should appear at most once on a file:
- P6243 — digital representation of

### Commons-Specific Constraints

- P462 (color) — should only be used as a qualifier on Commons, never as a main claim
- P6022 (expression/gesture) — same, qualifier-only
- P2093 (author name string) — same, qualifier-only
- P180 (depicts) — should link to valid Wikidata items only
- P6216 (copyright status) — should link to valid copyright status items only
- P571 (inception) — must use a valid date with proper calendar model
