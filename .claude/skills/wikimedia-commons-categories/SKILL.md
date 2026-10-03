---
name: wikimedia-commons-categories
description: Create and disambiguate Wikimedia Commons categories from Wikidata data - the occupation-from-country pattern, "by name" people categories, definite-article country phrases, pluralization, existence probing, and homonym disambiguation, distilled from the production Catapult gadget. Recurring-event year categories (<Event> <YYYY>) live in the wikiportraits-event-series skill.
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikidata]
skill_discovery_hints:
  - keywords: ["Commons category", "create category", "category disambiguation", "by name category"]
  - keywords: ["person category", "occupation category", "people by occupation", "surname index"]
  - keywords: ["Catapult", "Wikidata to Commons", "category from Wikidata", "P106 category"]
  - keywords: ["the Netherlands", "definite article", "country category", "category naming"]
last_verified: 2026-09-29
---

> ?? **User-Agent required:** All API calls below hit Wikimedia endpoints. Requests without a descriptive `User-Agent` are blocked with HTTP 403/429. See **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)**.
> ?? **Prerequisites:** For how Commons categories work as a hierarchy, see **[wikipedia-categories](../wikipedia-categories/SKILL.md)** (its tree/DAG rules apply to Commons too). For reading Wikidata entities and claims, see **[wikidata](../wikidata/SKILL.md)**. This skill is specifically the *"build and disambiguate a Commons category from a Wikidata item"* workflow.

---

## What this skill is

Commons stores **people** in categories named `<occupation plural> from <country>`
(e.g. `Vocalists from the Netherlands`) and, when the category indexes people
alphabetically by surname, with a **`by name`** suffix
(`Vocalists from the Netherlands by name`). This skill teaches the exact
algorithm for turning a Wikidata item's claims into the right category name,
checking whether it already exists, and disambiguating homonyms - the same
production logic as the **Catapult** gadget
(`User:1Veertje/Catapult` on Wikidata, `github.com/VDK/Catapult`, by Vera de
Kok). It ships a generator script
(`scripts/suggest_categories.py --item Q123 --check`).

## Categories vs. gallery pages

A category is a **complete, unordered, caption-less** set maintained by whoever adds to it. A Commons **gallery
page** is the opposite: a hand-curated main-namespace page with hand-chosen images, order and captions. They are
complements, usually paired by name (`The Venetian Macao` ↔ `Category:The Venetian Macao`).

Two things worth knowing before you touch either: galleries have **no namespace, no prefix and no page property**
(`Gallery:The Venetian Macao` is a missing page — the prefix is not an alias), and you find them by content
(`hastemplate:"Gallery page"`), never by title. See the **[wikimedia-commons](../wikimedia-commons/SKILL.md)**
skill's *Gallery Pages* section for the measured details and the traps.

## The pattern (memorize this)

For a Wikidata person item, derive category candidates like this:

| Claim | Property | Role in the name |
|---|---|---|
| occupation | P106 | the `<occupation plural>` fragment (e.g. `vocalists`) |
| country of citizenship | P27 | the `<country>` fragment (e.g. `the Netherlands`) |
| sex or gender | P21 | `male`/`female` modifier |
| date of birth / death | P569 / P570 | `Nth-century` modifier and life-years disambiguation |
| Commons category | P373 (on the occupation/country *item*) | explicit override of the fragment |

The full candidate matrix for one occupation x one country:

```
Vocalists from the Netherlands                     (occupation + country)
Vocalists from the Netherlands by name             (occupation + country + by name)
Female vocalists from the Netherlands              (gendered occupation + country)
Female vocalists from the Netherlands by name
female vocalists from the Netherlands              (gender + occupation + country)
female vocalists from the Netherlands by name
20th-century vocalists from the Netherlands        (century + occupation + country)
20th-century vocalists from the Netherlands by name
20th-century female vocalists from the Netherlands (century + gendered occupation + country)
20th-century female vocalists from the Netherlands by name
vocalists                                          (bare occupation - always proposed last)
```

`by name` is the **person** convention (an alphabetical surname index). Never
append it to non-person categories.

## Occupation fragment resolution (P106 -> "vocalists")

For each P106 value QID, in order:

1. Explicit mapping table wins (`Q177220 -> "vocalists"`).
2. Else the occupation item's **P373** (Commons category) name.
3. Else the item's English label.
4. Else the QID.

Then: strip `Category:`, trim, **pluralize** (`vocalist -> vocalists`,
`secretary -> secretaries`, `person -> people`, already-`s` stays), apply
`occupationCategoryReplacements` (`Singers -> vocalists`,
`Businesspersons -> businesspeople`), and lowercase the first letter.

Also walk **P279 (subclass of)** and **P31 (instance of)** parents of the
occupation item and add those as lower-ranked fallbacks. Drop generic
fallbacks: `workers`, `professions`, `professionals`, `people by occupation`.

## Country fragment resolution (P27 -> "the Netherlands")

For each P27 value QID, in order:

1. Explicit mapping (`Q55 -> "the Netherlands"`).
2. Else the item's **P1813** en short name.
3. Else its **P373**.
4. Else the English label / QID.

Then apply the definite-article rules (this is where most naming errors come
from - do **not** guess):

- `United States` / `United Kingdom` (anything starting `United `) -> `the ...`
- `Bahamas`, `Comoros`, `Gambia`, `Maldives`, `Philippines`, `Seychelles` -> `the ...`
- `Central African Republic`, `Dominican Republic`, `Czech Republic` -> `the ...`
- `Marshall Islands`, `Solomon Islands` -> `the ...`
- canonicalize via replacements (`Czechia -> the Czech Republic`,
  `Kingdom of the Netherlands -> the Netherlands`)

Germany, France, India, Belgium etc. stay article-free.

## Gender and century modifiers

- **Gender** (P21): only `male` (Q6581097) and `female` (Q6581072) count.
  Exactly one occupation gets a gendered form: `businesspeople ->
  businessmen` / `businesswomen`. Otherwise the `male/female + occupation`
  form is used.
- **Century** (P569/P570): `ordinal(ceil(year/100))-century`. Basis year =
  death year, else birth year+60 if born more than 120 years ago (historical
  figures), else current year.

## Resolve the current name first (entities get renamed)

A Commons category must use the entity's **current** name, and the Wikipedia article title is the
most reliable source for it -- page moves track renames long before Wikidata labels, aliases and
Commons categories catch up. Before generating or probing a category name:

```bash
# Current article title -> QID (redirects=1 follows the move left at the old title)
curl -s -A "$WIKIMEDIA_USER_AGENT" -G "https://en.wikipedia.org/w/api.php" \
  --data-urlencode "action=query" --data-urlencode "titles=Andrew Carnegie Foundation" \
  --data-urlencode "redirects=1" --data-urlencode "prop=pageprops" --data-urlencode "ppprop=wikibase_item" \
  --data-urlencode "format=json" --data-urlencode "formatversion=2"
```

Cross-check `wbgetentities&props=labels|aliases|sitelinks`: if `sitelinks.enwiki.title` differs from
`labels.en`, the label is stale -- **the sitelink is the current name**. (Verified 2026-09: Q3660410 is
still labelled "Carnegie Corporation of New York" while enwiki and the real-world organisation have
used "Andrew Carnegie Foundation" since June 2026; the alias was never added.)

Naming and migration rules:

- **Create under the current name**; leave the old name as a `{{Category redirect|New name}}` so
  existing links and old uploads keep resolving.
- Probe **both** names for pre-existing content -- files are often filed under the superseded name
  because they predate the rename.
- Add the current name as a Wikidata **alias** and set/refresh **P373** to the category you create,
  otherwise the next person repeats the same failed label search.

## Check existence before doing anything

Probe candidates in batches of 50 against Commons - always with the full
`Category:` prefix, otherwise the API resolves them in the main namespace
(ns=0) and reports every category as missing:

```text
GET commons.wikimedia.org/w/api.php?action=query&prop=info|pageprops&titles=Category:Vocalists%20from%20the%20Netherlands|...&formatversion=2&format=json
```

Read per page: `exists` (not missing), `redirect`, `pageprops.wikibase_item`.
Track `normalized` titles back to input casing. Then:

| Probe result | What to do |
|---|---|
| exists, `wikibase_item` = the subject's item | done - the category already exists for this person |
| exists, `wikibase_item` = a **different** item | **name collision** - never reuse; disambiguate |
| exists, no `wikibase_item` | safe to link/reuse (an unlinked category) |
| redirect | resolve the target first (a redirect carries no item) |
| missing | free to create |

Categories existing without a `wikibase_item` can still be linked to Wikidata;
resolve them via `wbgetentities` on the Commons sitelink
(`sites=commonswiki&titles=...&redirects=yes`).

## Disambiguating homonyms

If the desired name is taken by a different subject, create a parenthesized
category instead:

- `Category:<name> (<occupation>)` - one option per P106 value, most specific
  label first; skip `university teacher` (too generic).
- `Category:<name> (<birth>-<death>)` - when there is no usable occupation.
- `Category:<name> (born <year>)` - when only a birth year is known.

If the base name is *already* a disambiguation category (suffixed
subcategories exist, found with `list=search&srnamespace=14&srsearch=intitle:"<base> ("`),
reuse the matching suffixed category instead of creating another bare one.

## SOP: creating a person category (agent workflow)

1. **Fetch** the Wikidata item (`wbgetentities`, props `labels|claims`).
2. **Resolve** P106 -> occupation fragments, P27 -> country fragments
   (mappings first, then P373, then labels).
3. **Generate** the candidate matrix above (occupations x countries x
   modifiers, each with and without ` by name`).
4. **Probe** Commons for all candidates (batched, 50/call).
5. **Pick**: best existing candidate via the ranking rules
   (country-scoped > gendered > bare occupation; `by name` last); if none
   exists, create the top ranked candidate. On a `wikibase_item` collision,
   offer disambiguation options instead.
6. **Create** the category page with `[[Category:<parent>]]` on it - the
   parent is the country-scoped category (or the next-ranking candidate that
   exists). Never create a category without a parent in the tree.

The bundled script automates steps 1-5:

```text
python3 .claude/skills/wikimedia-commons-categories/scripts/suggest_categories.py --item Q123 --check
```

## Production lessons (field-tested in Catapult)

- **`wikibase_item` is the collision detector.** An existing category tied to a
  different item must never be silently reused for a second subject.
- **Country-scoped beats bare occupation.** Bare `occupation` candidates are
  proposed last and rank lowest; generic containers (`Occupations`,
  `Positions`) are blacklisted outright.
- **Definite articles are the #1 near-duplicate source.** `the Netherlands`
  vs `Netherlands` creates two categories for the same thing. Maintain the
  phrase tables, don't guess.
- **Pluralization errors orphan categories.** `secretary -> secretaries`,
  `person -> people`; a wrong plural needs a later merge cleanup.
- **Filter claims first:** drop `deprecated` ranks and emoji-flag claims
  (P3831 = Q28840786); prefer `preferred` rank over normal.
- **Category redirects carry no item.** If a candidate resolves to a redirect,
  follow it (action=query `redirects=1`) before deciding reuse vs creation.

## Recurring events

For recurring events (festivals, conferences, WikiPortraits event series) the
year-category pattern (`<Event> <YYYY>` with `{{Wikidata Infobox}}`,
`{{Decade years navbox}}`, `{{en|...}}`, numeric sortkeys) and the full
Wikidata edition-item workflow (claims, P155/P156 chaining, edition numbering)
live in the dedicated **[`wikiportraits-event-series`](../wikiportraits-event-series/SKILL.md)**
skill.

## References

- **`references/catapult-category-patterns.md`** - the full field-by-field
  specification: candidate matrix, pluralize/country/century rules, ranking
  algorithm, disambiguation, mapping-table reference, and production gotchas.
- **`assets/mappings-sample.json`** - a Catapult-style mappings table
  (occupation/country/blacklist/replacements) you can extend and pass with
  `--mappings`.
- **`scripts/suggest_categories.py`** - the generator/validator CLI.
