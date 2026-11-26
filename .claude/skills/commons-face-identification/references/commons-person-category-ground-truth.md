# Ground truth from Commons person categories

Everything here is public: Commons category pages, their Wikidata items, and Wikidata claims.
No credentials. Send a descriptive `User-Agent` on every call.

## Why categories are usable ground truth

Commons event photos are usually person-categorised by volunteers after upload:
`Category:Jane Doe`, `Category:Jane Doe in 2015`, `Category:Jane Doe smiling`,
`Category:Jane Doe in the Netherlands`, `Category:Jane Doe with people`. Measuring against
that is free, non-circular, and reflects what the community already asserts — unlike a
model-generated label set.

What it is *not*: per-face truth. A file category says "this person is in this photo", not
"this is the 3rd face from the left", and not "this person is prominent". That asymmetry is why
per-person recall has to be reported per person.

## Resolution ladder

```python
# 1. category page -> wikibase item
GET https://commons.wikimedia.org/w/api.php
    ?action=query&prop=pageprops&ppprop=wikibase_item
    &titles=Category:Jane Doe|Category:Jane Doe in 2015&format=json

# 2. item -> P301 (category's main topic) -> the person
GET https://www.wikidata.org/w/api.php
    ?action=wbgetentities&ids=Q...&props=claims|labels
    &languages=en|mul|nl|de&format=json
```

`P31` of a Commons category item is **Q4167836** ("Wikimedia category"), and its **P301** is the
topic. Checking `P31=Q5` on the category item therefore resolves nothing; the check has to be
`P301 → target`, then `P31=Q5` on the target. Some categories are sitelinked from the person
item directly, in which case `P31=Q5` on the item itself is the answer — try both.

Labels: request `en|mul|nl|de`. Wikimedia-community people frequently have **no English label**
at all; one such item accounted for 37 files and printed as a bare QID until the fallback
landed. Fall back to the Commons category name or the commonswiki sitelink.

Qualifier shapes to strip, in this order (longest first):

```
^(.*?) in \d{4}$                    Jane Doe in 2015
^(.*?) in the \d{4}s$               Jane Doe in the 2010s
^(.*?) in the Netherlands$          Jane Doe in the Netherlands
^(.*?) (smiling|gesturing with hands|shaking hands|facing forward)$
^(.*?) (with people|with objects|with microphones)$
^(.*?) wearing .*$                  Jane Doe wearing a red dress
^(.*?) by year$                     Jane Doe by year
```

After stripping, resolve `Category:<base>` through the same ladder. Measured on one
282-photo award category: 44 → 74 people once qualifier categories were handled.

## Five failure modes, each measured

1. **The ancestor walk.** Walking *up* from an event category reaches
   `Royal Palace of Amsterdam` → its architect → and labels 271 of 282 photos with a
   17th-century architect. Ancestors are only safe when reached through a qualifier strip, and
   even then check the label against the child category name. Keep a blacklist for works,
   buildings, collections and trades (`portrait paintings`, `Paintings by …`, `… Trust`,
   `ceremonial guards`, `births`, `deaths`, `alumni`, `staff`).
2. **The unclean tree.** A category tree is not a clean hierarchy: an 88-member Wikimania
   category walked **7,589 files** at depth 2 because a subcategory was a venue museum's
   collection. Always cap depth, keep a visited set, and compare the walked file count with the
   root's member count before trusting a denominator.
3. **HTTP 414 URI Too Long.** Commons file titles are long, so a 50-title `titles=` batch
   overflows the URL and the API answers 414 — not the documented "too many values" error.
   Batch by URL-encoded length (~3.5 KB) *and* keep the 50-title cap.
4. **429 at walking speed.** An unthrottled recursive walk is blocked within a minute
   ("Your bot is making too many requests"). Sleep ~0.2 s between calls, honour
   `Retry-After`, back off exponentially, and pass `maxlag=5`.
5. **Label-less items.** No English label is common for exactly the people you care about. The
   `en|mul|nl|de` fallback plus a category-name fallback keeps the report readable.

## Output contract

`scripts/person_ground_truth.py` writes:

```json
{
  "category": "Category:Erasmus Prize 2015",
  "files": 282,
  "categories_walked": 4,
  "file_persons": {"File:...JPG": {"Q181": "Jimmy Wales"}},
  "person_cat":   {"Category:Jimmy Wales in 2015": {"qid": "Q181", "label": "Jimmy Wales"}},
  "unmapped":     ["Austin Hair", "..."],
  "files": 282
}
```

Print and read, every run: files, labelled files, people, pairs, and the unmapped list. The
automatic pass on the calibration category recovered 441 of the 473 hand-resolved
photo-person pairs across 62 of 74 people — the remaining gap was entirely in the unmapped
list, which is why it is printed rather than logged.

## Couples and multi-person categories

`Category:X and Y, King and Queen of …` resolves to neither person through P301. Handle these
as a small explicit table (two QIDs for that category title) instead of inventing a parser for
English conjunctions; there are only a handful per event.
