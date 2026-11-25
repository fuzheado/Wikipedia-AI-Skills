# Measured operating points (one calibrated corpus, not a law)

Corpus: public Commons category tree `Category:Erasmus Prize 2015` — 282 photos of a single
2015 award ceremony (271 in the main category, 3 subcategories), fetched as 1,800 px
thumbnails. 1,537 faces detected across 257 photos (median 4 per photo, max 82 in the group
shots); 21 photos had no detectable face (paintings, palace interiors, the award object).
Gallery: 68 people with usable references, built from Wikidata P18 plus Commons person
categories (677 candidate images, all event files excluded). Model: InsightFace `buffalo_l`
(SCRFD-10G detector + ArcFace-R50, 512-D), ONNX Runtime, CPU, 4 cores.

Ground truth: 74 people across 195 files → 473 `(file, person)` pairs, 440 of which have a
detectable face in that photo. (`scripts/person_ground_truth.py` reproduces 62 people / 441
pairs automatically; the difference is the unmapped-category list, closed by hand for the
calibration.)

Re-measure for a different corpus, era or embedding model. These numbers tell you what a
plausible result looks like and where the thresholds sit — not what your run will produce.

## Recall on labelled pairs (440 pairs with a face present)

| cosine | pair recall | distinct persons matched | faces given a name |
|---|---|---|---|
| 0.40 | 83% | 66/68 | 31% |
| 0.45 | 80% | 66/68 | 28% |
| 0.50 | 74% | 64/68 | 25% |
| 0.55 | 64% | 62/68 | 22% |
| 0.60 | 51% | 56/68 | 17% |
| 0.65 | 40% | 47/68 | 13% |

Only 17% of all faces get a name even at the loosest useful threshold: most faces in an event
corpus are background guests, and group shots dominate the face count.

## Precision (visual audit, gallery-ref vs event-crop tiles, judged by eye)

- ≥0.60 band, 36 top matches: ~27 same person, ~6 unclear (low-quality reference angle),
  ~3 wrong → **~75%**.
- 0.42–0.50 band, 36 sampled: ~7 clear matches, ~20 clearly different, the rest unclear →
  **20–40%**. Below 0.50 the output is not usable without a human decision on every tile.

Quote the audit next to the threshold. A bare "80% recall" at 0.45 is a misleading claim when
most of those fires are the wrong face in the right photo.

## Per-person variance at a fixed 0.60 threshold

| person | labelled files | found | note |
|---|---|---|---|
| Wim Pijbes | 4 | 4 (100%) | several era-appropriate portraits |
| Piet Hein Donner | 5 | 5 (100%) | same |
| Lodewijk Gelauff | 37 | 31 (84%) | community photos, same era |
| Beatrix of the Netherlands | 19 | 15 (79%) | one large reference, same era |
| Max Sparreboom | 36 | 28 (78%) | same era |
| Adele Godoy Vrana | 39 | 20 (51%) | many wide shots, small faces |
| Phoebe Ayers | 32 | 15 (47%) | group-shot references |
| Martijn Sanders | 32 | 5 (16%) | same |
| Willem-Alexander | 48 | 4 (8%) | **only reference taken 11 years later** |

Report per person. The pooled 51% hides both the 100% cases and the 8% case, and the 8% case
is the one a practitioner will hit.

## Fixed gallery vs in-event centroid (the WikiVisage method)

Held-out protocol: people with ≥8 labelled photos; centroid seeded from faces in the first 5
labelled photos only; scored on the remaining **269 photos**; identical 0.60 threshold.

| method | recall @0.60 | recall @0.50 |
|---|---|---|
| fixed portrait gallery | 49% | 74% |
| in-event centroid (~8 seed faces) | **78%** | **86%** |

Per-person deltas from the gallery baseline to the centroid: Willem-Alexander 5% → 91%,
Martijn Sanders 19% → 67%, Phoebe Ayers 46% → 69%, Jimmy Wales 56% → 89%, Max Sparreboom
77% → 97%.

False-fire proxy: for those 13 people, the centroid fired on 278 `(person, photo)` pairs whose
photo does not carry that person's category — 17 of them at 0.60. Some of those are genuinely
missing labels, so ~94% precision is a lower bound.

## Population shape — why "who was missed" is mostly a gallery question

- 74 people named by categories. **87 photos carry no person label at all**; 67 of those
  contain faces (290 faces).
- Of those 290 faces, 3 matched a named person at 0.60 and 10 at 0.45. A gallery built from the
  labelled set can only name people labelled *somewhere*, so this measures missing labels on
  known people, not unknown identities. Report it that way.
- Identity clustering at cosine 0.60: 140 clusters with ≥2 faces, 79 with ≥3 → roughly
  **100–140 recurring people**, i.e. about half the recurring people in the category are
  anonymous in Commons metadata. Clustering over-splits; treat the count as an upper bound.
- **Missed appearances of already-named people: 69 `(person, photo)` pairs** (top individuals
  +10, +10, +10, +9). This is the concrete backlog a suggestion tool would clear, and it is
  much easier to justify than "label the unknown guests".

## Cost, measured on CPU

| step | images | time |
|---|---|---|
| gallery embedding (700 px thumbs, det 640) | 677 | ≈7 min |
| event inference (1,800 px photos, det 1024) | 278 | ≈4–5 min |
| ground-truth script, 282-file tree | — | ≈25 s |
| ground-truth script, 7,589-file polluted tree (depth 2) | — | ≈3 min |
