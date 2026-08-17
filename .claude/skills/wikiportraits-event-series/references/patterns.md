# Event edition patterns - worked examples and edge cases

## Worked example: Crossing Europe (Linz)

Crossing Europe is an annual film festival in Linz, Austria, running since
2004. It is a fully-wired real example of the pattern in this skill (all QIDs
and categories live, wired by 1Veertje).

### Facts

- **Series item**: Q1141279 `Crossing Europe` - P31 `film festival` (Q220505),
  P571 = 2004, P373 = `Crossing Europe`. Commons parents:
  `Category:Events in Linz`, `Category:Film festivals in Austria`.
- **Edition type**: Q27787439 `film festival edition`.
- **Location / country**: Q41329 Linz, Q40 Austria.
- **First edition**: 4-9 May 2004. **2020 cancelled** (COVID-19).
- **Edition numbering**: 2004=1 ... 2019=16, then **2021=17, 2022=18,
  2023=19, 2024=20, 2025=21, 2026=22**. The 2017 item already carried
  P393=`14`, which pins the unbroken part to `year - 2003`; after the 2020
  gap the formula becomes `year - 2004`.

### The edition items

Each edition item (Q140965327 = 2004 ... Q140965125 = 2026) carries:

- label (en) `Crossing Europe <YYYY>`, description (en) `film festival edition`
- P31 = Q27787439, P179 = Q1141279, P276 = Q41329, P17 = Q40,
  P393 = <edition number>, P585 = <year> (precision 9) as the anchor,
  P373 = `Crossing Europe <YYYY>`
- one-day editions set `P585` to the exact date (day precision); multi-day
  editions add `P580` start time + `P582` end time (day precision) and keep
  the year on P585 (pattern used by `Q61654036` 47th IFFR)
- sitelink `commonswiki` → `Category:Crossing Europe <YYYY>`
- P155/P156 chaining consecutive editions; **2019 ↔ 2021 bridge the cancelled
  2020** (2019.P156 = 2021 item, 2021.P155 = 2019 item). No 2020 item exists.

### The Commons categories

Bare event category `Category:Crossing Europe`:

```text
{{Wikidata Infobox}}
'''Crossing Europe''' is an annual film festival held in Linz, Austria, since 2004.

[[Category:Film festivals in Austria]]
[[Category:Events in Linz]]
```

Year category `Category:Crossing Europe 2005` (real wikitext):

```text
{{Wikidata Infobox}}
{{Decade years navbox
|header={{C|Crossing Europe}}
|decade=200
|cat_prefix=Crossing Europe
|cat_suffix=
}}

[[Category:Crossing Europe]]
[[Category:2005 film festivals]]
[[Category:2005 events in Linz]]
[[Category:April 2005 in Linz]]
```

Parents used across the series: `<YYYY> film festivals` (the "20xx film
festivals" category), `<YYYY> events in Linz`, and `April <YYYY> in Linz` for
the April editions. The 2004 edition (4-9 May) has **no month category**,
because `May 2004 in Linz` does not exist - always probe before linking.

### Lessons learned while wiring this series

1. **The existing items were inconsistent**: early ones had
   P31+P179+P585+P373, later ones only P31+P373. Bring the whole series to one
   claim set instead of matching the least complete item.
2. **Descriptions were mixed** (`film festival edition` vs
   `2015 film festival edition`) - normalize to the dominant style.
3. **P276 and P17 were missing on every existing item**; P393 existed only on
   2017 (=14), which is what pinned the edition formula.
4. **The 2020 gap shifted the numbering**: naively computing `year - 2003`
   for 2021 gives 18, but the correct value is 17. Always check for cancelled
   years.
5. **Commons pageprops lag** after adding a sitelink; the infobox briefly
   shows "Uses of Wikidata Infobox with no item" until the job runs. A null
   edit (`page.touch()`) fixes it immediately.
6. **Wikidata replication lag (maxlag)** can reject rapid edits; retry with
   backoff. pywikibot's built-in handling gives up after a while - wrap edits
   in an explicit retry loop for batch work.
7. **The navbox breaks silently when the separator space is missing.**
   `{{Decade years navbox}}` builds titles as `cat_prefix + padding + year +
   padding + cat_suffix`. MediaWiki trims trailing whitespace from
   `cat_prefix`/`cat_suffix`, and an **empty `|padding=` is honored as "no
   separator"** (it does NOT fall back to the template default), so with
   `displayredlinks=no` the navbox checks `Event2007` and renders blank. Omit
   `padding` (default = space) or pass `|padding=&#32;` for an explicit space;
   empty `padding=` is only for tight affixes like `Collision (2014)`. Also
   set `decade = year//10` (199 for the 1990s) - `decade=190` probes
   1900-1909. (Riverwalk Blues Festival 1996/2006/2007 hit exactly this.)

## Naming and renames

- Check the existing category name before creating; event names may need
  spaces between words (`24HBC 2011` → `24 HBC 2011`).
- Renames leave `{{Category redirect|NewName}}` on the old title (no
  `Category:` prefix in the parameter). Search the category tree first so you
  update the existing page instead of creating a duplicate.
- Photographer categories are person categories, not event children. Files
  showing a named person can additionally carry `[[Category:<Person>]]` after
  the event category, but only for categories that already exist (probe
  first).

## Media and extras

- Add **P18** (representative image) and **P10** (video) from files already
  inside the year category.
- The year category can carry extra topic/region parents that exist for that
  event (e.g. `<YYYY> music festivals in <country>`, region categories).

## Edge cases

- **First edition**: no P155 (nothing precedes it).
- **Cancelled editions**: no item, the chain bridges the gap, and P393 still
  counts the slot.
- **Unmodeled held editions - leave the chain open.** A link means "directly
  consecutive editions, nothing held in between". If the series is modeled only
  at some years (e.g. 1989, 1996, 2006, 2007 of an annual festival) and the
  in-between editions were held but have no items yet, do **not** link
  1996→2006 or 2006→1996; that would falsely claim 1997-2005 never happened.
  Chain only truly adjacent editions. Backfill the intermediate items later
  and then extend the chain.
- **Parallel series** (international series plus a national edition): chain
  within each series only, never across.
- **Biennials**: `edition = (year - Y0) / 2 + 1`; still one category/item per
  held edition.
- **Event moved to a new city**: keep the current location on recent editions,
  the old location on historical ones; put the current location on the series
  item (with a P582 qualifier on P276 for the range when it changed).

## Chain-verification SPARQL

```sparql
SELECT ?item ?itemLabel ?prev ?prevLabel ?next ?nextLabel WHERE {
  ?item wdt:P179 wd:Q1141279.
  OPTIONAL { ?item wdt:P155 ?prev. }
  OPTIONAL { ?item wdt:P156 ?next. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

Check that every P155 has a matching reverse P156 (and vice versa) and that
the ordering matches the years. A partially modeled series legitimately has
open chain ends at the boundaries of an unmodeled run of held editions - those
are expected, not errors; do not bridge them.
