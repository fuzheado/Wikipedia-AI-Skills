---
name: wikiportraits-event-series
description: Create Wikidata edition items and Commons year categories for recurring events (festivals, conferences) — P155/P156 follows/followed-by chains, cancelled-year numbering, edition claims, and the <Event> <YYYY> category scheme
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikidata, pywikibot, wikimedia-commons-categories]
skill_discovery_hints:
  - keywords: ["event category", "year category", "festival edition", "conference edition", "event series"]
  - keywords: ["P155", "P156", "follows", "followed by", "previous edition", "next edition", "edition chain"]
  - keywords: ["Crossing Europe", "IFFR", "Internetdagarna", "film festival year category", "annual conference category"]
  - keywords: ["edition number", "P393", "cancelled edition", "gap in editions"]
  - keywords: ["Decade years navbox", "events in Linz", "events in Stockholm"]
  - keywords: ["P856 official website", "P973 described at URL", "edition references", "Wayback snapshot"]
  - keywords: ["WikiPortraits event", "WikiPortraits edition", "portrait event series"]
last_verified: 2026-06-24
---

> **User-Agent required:** All API calls hit Wikimedia endpoints; requests without a descriptive `User-Agent` are blocked. See **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)**.
> **Prerequisites:** For reading/writing Wikidata entities and claims see **[wikidata](../wikidata/SKILL.md)**. For general Commons category naming conventions see **[wikimedia-commons-categories](../wikimedia-commons-categories/SKILL.md)** (this skill contains the event-specific year-category shape). For running the shipped script see **[pywikibot](../pywikibot/SKILL.md)**.

## What this skill is

Recurring events (film festivals, conferences, competitions, biennials) are modelled as a **series of edition items** on Wikidata and a **series of year categories** on Commons. This skill covers the complete workflow in one place:

1. one **Wikidata item per edition**, carrying event type, series, year, location, country, edition number, official website, references, aliases, and **P155/P156 follows / followed-by** links that chain consecutive editions;
2. one **Commons category per year** (`<Event> <YYYY>`) mirroring the edition items and linked back to them.

Worked examples (Crossing Europe 2004-2026, Internetdagarna, International Film Festival Rotterdam) and every edge case live in `references/patterns.md` and `references/event-editions-workflow.md`. The shipped `scripts/create_edition.py` automates the repeatable parts.

## The two linked data models

| Model | Per event | Per year |
|---|---|---|
| Wikidata | one **event/series item** (P31 = event class, e.g. `film festival` Q220505) | one **edition item** (P31 = `<type> edition`, e.g. `film festival edition` Q27787439) |
| Commons | one bare **`<Event>`** category | one **`<Event> <YYYY>`** year category |

The two models are joined by the edition item's **P373** (Commons category string) and a **`commonswiki` sitelink** pointing at the year category. The bare event category links to the series item.

## Wikidata edition items (memorize)

Each year-edition item gets this claim set:

| Property | Target | Notes |
|---|---|---|
| label (en) | `<Event> <YYYY>` | e.g. `Crossing Europe 2004`, `43rd International Film Festival Rotterdam` |
| description (en) | `<YYYY> edition of ...` or `film festival edition` | use the style already established in the series |
| P31 | `<type> edition` | `Q27787439` film festival edition, `Q108095628` conference edition, `Q41582469` music festival edition |
| P179 | series item | the parent event item |
| P585 | point in time | **one-day event:** the exact date (day precision). **Multi-day event:** keep the year (precision 9) as the anchor - see P580/P582 |
| P580 | start time | multi-day events only: exact start date (day precision) |
| P582 | end time | multi-day events only: exact end date (day precision) |
| P276 | location item | the city where it is held |
| P17 | country item | |
| P393 | edition number | datatype **string**; see numbering section |
| P373 | `<Event> <YYYY>` | Commons category string, only when the category exists |
| P856 | official website | edition page URL, qualifiers `P407` English (Q1860) + `P813` retrieved |
| P973 | described at URL | same canonical URL when P856 is not used |
| P155 | previous edition item | chain, see below |
| P156 | next edition item | chain, see below |
| P18 / P10 | representative image / video | optional, when media exist |
| sitelink | `commonswiki` → `<Event> <YYYY>` | |

**Dates.** A one-day edition carries `P585` = the exact date (day precision). A multi-day edition keeps `P585` = the year as the anchor and adds `P580` start time + `P582` end time at day precision - e.g. `Q61654036` 47th International Film Festival Rotterdam has `P585` 2018, `P580` 2018-01-24, `P582` 2018-02-04. In `scripts/create_edition.py` pass `--date YYYY-MM-DD` for one-day events or `--start/--end` for multi-day events; with neither, `P585` falls back to the year.

**Labels, aliases and descriptions** follow the series convention: `Internetdagarna 2013`, `43rd International Film Festival Rotterdam`, alias `IFFR 2014`. Reuse the series item's existing conventions (P31 class, P276, P17, P373).

**Match the series' existing conventions first.** Read a few existing edition items before creating or editing - a series is often internally inconsistent (early items carry P31+P179+P585+P373, later ones only P31+P373). Bring the whole series to one claim set and one description style rather than matching the least complete item. Upgrade items that still carry the plain event type (e.g. Q625994 convention) to the `<type> edition` class.

## Edition numbers (P393) and cancelled gaps

P393 is the ordinal edition number as the organizers count it ("17th edition"), and its datatype is **string**. Derive it, do not guess - **numbering does not equal `year - start_year + 1`** (Internetdagarna 2012 is the *13th* edition):

- **Unbroken annual series** starting in year Y0: `edition = year - Y0 + 1`, confirmed against sources.
- **Cancelled years**: a cancelled year consumes an ordinal even though no edition is held, so `edition = year - Y0 + 1 - (number of cancelled editions in [Y0, year])`.
- **Verify against sources**: organizer press pages or local news state the ordinal (e.g. "feiert seine 20. Ausgabe" → 20th edition). Confirm the formula with at least one independently numbered year before applying it to the whole series.
- **Reuse an existing value**: if one item already carries P393 (e.g. a 2017 item marked `14`), derive the formula from it and keep it consistent.

Crossing Europe (Y0 = 2004, 2020 cancelled): 2019 = 16, then **2021 = 17** (not 18), 2023 = 19, 2026 = 22. A wrong formula silently shifts every later edition, so always cross-check the post-gap years.

## P155 / P156 follows / followed-by chaining (memorize)

P155 (follows) on an edition points to the **immediately preceding** edition's item; P156 (followed by) points to the **immediately next** edition's item. The chain is **bidirectional and must be consistent**: if `A.P156 = B` then `B.P155 = A`.

- **Appending a new edition** at the end of the series: create item N with `P155 = last item`; update the last item with `P156 = N`.
- **Backfilling a missing edition** between two existing items (prev = P, next = X): create N with `P155 = P` and `P156 = X`; update P with `P156 = N`; update X with `P155 = N`.
- **First edition**: no P155 (nothing precedes it).
- **Cancelled years** get **no item and no chain links** - the chain jumps directly from the last real edition to the next real one (e.g. 2019 → 2021 for Crossing Europe). Do not invent placeholder items.
- **Unmodeled held editions - do NOT bridge the gap.** A P155/P156 link means "the **directly consecutive** editions of this series, with **no held edition in between**". If intermediate editions *were held* but their items do not exist yet (partially modeled series, e.g. editions 1996 and 2006 both exist but 1997-2005 have no items), **leave the chain open**: do not set `1996.P156 = 2006` or `2006.P155 = 1996`. A direct link would falsely imply those years never had an edition. Only connect two items when the event genuinely did not run in between (cancelled) OR the two are truly adjacent years of an annual series. This is distinct from a cancelled year, where bridging is correct.
- **Parallel series** (e.g. an international series plus a national edition): chain within each series only, never across.
- **Verify** the whole chain afterwards with SPARQL over `wdt:P179 wd:<series>` plus `wdt:P155`/`wdt:P156`, checking that every P155 has a matching reverse P156. A **partially modeled series is allowed to have open chain ends** at the boundaries of an unmodeled run of editions - those ends are not errors and must not be "fixed" by linking across the gap.

## Commons year categories (memorize)

The bare `<Event>` category is the topical container: `{{Wikidata Infobox}}`, optionally a short bold description, and **topical** parents (`<thing> in <country>`, `Events in <city>`, `<thing> festivals in <country>`). No year links.

The `<Event> <YYYY>` year category (the standard shape):

```text
{{Wikidata Infobox}}
{{Decade years navbox
|header={{C|<Event>}}
|decade=<YYYY // 10, e.g. 199 for 1996, 200 for 2006>
|cat_prefix=<Event>
|cat_suffix=
|displayredlinks=no
}}

{{en|'''<Event> <YYYY>''', <one-line description>.}}

[[Category:<Event>|YYYY]]
[[Category:<YYYY> events in <city>]]
[[Category:<month> <YYYY> in <city>]]     # only when it exists
[[Category:<YYYY> <thing>]]               # e.g. <YYYY> film festivals
```

- **Sortkey `|YYYY` only on the event parent**; never on the `events in <place>` or `<thing>` links. It makes the year categories sort **numerically** under the event.
- **Probe every parent before linking** - `<month> <YYYY> in <city>` and `<YYYY> events in <city>` usually already exist but occasionally do not. Verify existence via the API first.
- **City-scoped beats country-year**: prefer `2014 events in Stockholm` over `2014 in Sweden`; fall back to the country category only when no city-scoped one exists.
- **`<YYYY> <thing>`** describes what kind of event it is (e.g. `<YYYY> film festivals`, `<YYYY> conferences`) - the "20xx film festivals" style category. Add it when it exists.
- **Multi-day events** use the month category of the majority day; a single-day event also gets `[[Category:YYYY-MM-DD]]` when the daily category exists.
- **Skip the decade navbox** when there is only one year category, or when the year series is spread over multiple cities.
- **The infobox needs the sitelink to propagate**: right after adding the sitelink, the category shows "Uses of Wikidata Infobox with no item" until the Commons pageprops job runs. Touch the category page (null edit) to force it.
- **Renames** leave `{{Category redirect|NewName}}` on the old title (no `Category:` prefix in the parameter); search the category tree first so you update the existing page instead of creating a duplicate.
- **Navbox generation (memorize the traps)** - `{{Decade years navbox}}` builds titles as `cat_prefix + padding + year + padding + cat_suffix`. (1) MediaWiki **trims trailing whitespace** from `cat_prefix`/`cat_suffix`, so never try to smuggle the separator into an affix. (2) An **empty `|padding=` suppresses the default** space - empty is honored as "no separator" and does NOT fall back to the default - so the navbox probes `Event2007` and (with `displayredlinks=no`) renders blank. Omit `padding` (default is a space) or pass `|padding=&#32;` for an explicit one; empty `padding=` is only for tight affixes like `Collision (2014)`. (3) `decade` must be the **first 3 digits of the year** (`year//10`): the template checks `decade*10 + 0..9`, so `decade=190` targets 1900-1909, not the 1990s. (4) Prefer `displayredlinks=no` so an event series shows only existing year categories. `scripts/create_edition.py` now does all of this automatically.

## Reference patterns

- **Dead official page** → cite a **Wayback Machine snapshot** of the official edition page as the `P585`/`P856` reference; confirm the snapshot actually loads before recording it.
- **Wikipedia article data** → imported-from-Wikimedia-project pattern: `P143` = the language Wikipedia (e.g. `Q169514` Swedish Wikipedia), `P813` = retrieved, `P4656` = the article **oldid permalink** (e.g. `https://sv.wikipedia.org/w/index.php?title=Internetdagarna&oldid=46115337`) - as used on series item `Q10536300`.
- **Probe candidate edition URLs** (HTTP status 200) before recording them; festival sites restructure URLs frequently.

## Verify the chain

After editing, re-verify with **SPARQL**: list all editions ordered by `P393` and confirm that **where links exist**, each item's `P155` equals its predecessor's `P156` (bidirectional consistency). A fully modeled series has no gaps; a **partially modeled series legitimately has open chain ends** at unmodeled held editions - those open ends are expected and are not "no sequence claims" errors. Do not "fix" them by linking across a gap (see chaining rules above). Idempotency matters: add only missing claims and run scripts in a dry-run/simulate mode before the real edit.

## Workflow (SOP)

1. **Research**: first-edition year Y0, location, country, event type (P31), edition numbering including cancelled years, and which month/event categories exist.
2. **Inventory**: list the existing year categories and edition items (SPARQL over `P179`/`P393`/`P155`/`P156`); identify missing years and missing claims.
3. **Create the Commons year categories** for the missing years (pattern above; probe candidate names and parents).
4. **Create/update the Wikidata edition items** (claim set above, matching the series conventions; add references and official URLs).
5. **Chain P155/P156** across the series (append/backfill rules above). Only
   link editions that are directly consecutive - never bridge across a run of
   held-but-unmodeled editions.
6. **Verify**: sitelinks resolve both ways, pageprops updated (touch when lagging), P155/P156 chain consistent via SPARQL (open ends allowed at unmodeled gaps), P393 values match the organizer's numbering.

## Automating with the shipped script

`scripts/create_edition.py` (pywikibot) creates one Commons year category and one Wikidata edition item with the full claim set (including P155/P156) and updates the neighboring items so the chain stays consistent. Run it from inside a pywikibot checkout:

```text
python create_edition.py --event "Crossing Europe" --year 2027 \
  --series Q1141279 --edition-type Q27787439 --location Q41329 --country Q40 \
  --edition-no 23 \
  --parents "2027 film festivals" "2027 events in Linz" \
  --desc "annual film festival held in Linz, Austria, since 2004" \
  --prev Q140965123 --next Q140965125 \
  --dry            # preview without editing
```

The navbox `decade` is derived automatically as `--year // 10` (200 for 2027);
the generated navbox uses no `padding` and `displayredlinks=no` - see the
"Navbox generation (memorize the traps)" bullet above. Override with `--decade`
only for an unusual decade bucket.

See the script header for all flags. Already-linked categories and items are detected and skipped, so reruns are safe. The script warns when the year gap to `--prev`/`--next` is > 1 - a warning means those editions are probably **not** directly consecutive, so you should omit the chain flag and leave the chain open unless the gap is a cancelled edition.

## Additional Resources

### Reference Files
- **`references/patterns.md`** - The full worked example (Crossing Europe 2004-2026), naming and renames, media, chain-verification SPARQL, and edge cases.
- **`references/event-editions-workflow.md`** - The detailed step-by-step API strategy (SPARQL → `wbgetentities` → URL probes → Wayback → Pywikibot → SPARQL), the full edition template, reference patterns and lessons learned.

### Scripts
- **`scripts/create_edition.py`** - Create a Commons year category + Wikidata edition item (with P155/P156 chaining).

### Related skills
- **`wikimedia-commons-categories`** - general category naming conventions (person categories, sortkeys, `{{en|...}}`).
- **`wikidata`** - reading/writing entities and claims.
- **`pywikibot`** - running the shipped script.
