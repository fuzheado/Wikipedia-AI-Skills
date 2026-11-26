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

Population matters more than the threshold: on the cleaned non-community set (community
members excluded, references restricted to single-face images) a domain expert reviewed every
proposal at ≥0.50 and confirmed **11 of 11** (n=11, one reviewer — small, so treat it as a
direction, not a rate). The 20–40% figure above came from a gallery containing joint photos of
two people, which is what actually destroys precision at that band.

Quote the audit next to the threshold, and say whose judgement it was. A bare "80% recall" at 0.45 is a misleading claim when
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
- **Missed appearances of already-named people: 39 `(photo, person)` attributions at 0.60**
  that collapse into **22 distinct faces**. Of those 22, about a dozen are self-consistent
  (one name per face, best similarity 0.63–0.83). The rest are a contaminated-gallery
  artefact: two people's Commons categories shared 7 of 7 and 9 files, their centroid cosine
  was 0.94, and one face collected three different names (Max Sparreboom / Erik Borra /
  Jimmy Wales). A pre-collapse count of the same set (counting every `(person, photo)` pair
  without requiring the face's top-1 name) gives 69 — that figure double-counts the
  contaminated face and should not be quoted as a backlog. Report the collapsed face count,
  and print the most-similar gallery pairs first.
- The measurement worth acting on is therefore per-face, not per-pair: **22 faces in photos
  that do not credit the person the pipeline names.** Fix the contaminated categories
  upstream before turning any of them into `depicts`. 

## Population filters change the numbers (community members excluded)

47 of 71 classified people were Wikipedians/Wikimedians by category ancestry. Dropping every
photo that names one removed 100 photos; a stricter pass that also drops photos where the
matcher places a community member in frame (unlabelled) removed 7 more. 173 photos and 671 of
the 1,537 faces remained, with 24 non-community people holding gallery references.

| threshold | recall on the 116 non-community pairs | people matched at least once |
|---|---|---|
| 0.50 | 69% | 21/24 |
| 0.55 | 55% | 21/24 |
| 0.60 | 42% | 18/24 |
| 0.65 | 31% | 14/24 |

Lower than the pooled figures because the surviving photos are the ceremonial wide shots
(small faces) and the stale-reference case is a larger share. New attributions on that
population: 2 at 0.60, 11 at 0.50. Identity clustering over the 671 faces gave 40 clusters of
≥3 faces, 31 of them nameless at 0.50 — the anonymous recurring people, counted but not shown.

## Usability gate (what a reviewer can actually act on)

Gate: bbox width ≥ 90 px, detector score ≥ 0.70, |yaw| ≤ 0.20 (nose x-offset / inter-ocular
distance from the 5-point landmarks), Laplacian variance of the crop ≥ 40.

- 108 of 671 faces (16%) pass on the non-community set.
- Proposals by band: 0.60+ → 2 proposals, 1 usable; 0.50–0.60 → 9 proposals, 0 usable;
  0.40–0.50 → 6 proposals, 1 usable. **2 usable proposals in total**, both in one photo.
- Consequence: on crowd/ceremony photography the binding constraint is photo quality. Measure
  usable faces per photo on a sample before scoping any labelling work.

## Corpus-matched gallery: the writer pilot (public data, 2026-11-25)

Cohort: 663 Dutch people with a writing occupation, born 1890-1935, holding both a Wikidata
portrait (P18) and a Commons category. Gallery refs preferred from files dated 1945-1990.

- Build: 623 people with refs, **488 with at least one era-matched ref**, 46.9 min on 4 CPU cores.
- Target corpus: `Category:Boekenbal` tree, 113 files, 1947-1985 press photography. 944 faces,
  **83 usable (9%)** in 51 photos.
- Matches with an era-matched gallery: 14 faces / 11 distinct people at 0.55-0.60, 17 at 0.45,
  best 0.97 (Ed Hoornik, whose name is in the file title), 0.97 and 0.81 for two other
  writers. The same gallery built from P18 alone produced **zero** matches (max 0.29).
- Precision by eye: the ≥0.73 hits look right; the 0.60-0.67 band contained clear false
  positives (three Kosiński photographs named as Adriaan Morriën). Treat 0.70 as the
  auto-suggest floor for historical corpora and review down to 0.55.
- A title-derived ground truth is not usable as a recall denominator here: 82 `(file, person)`
  pairs fall out of name-matching in titles, but most of those people are not visible in a
  usable face, so "2% recall" measures the titles, not the matcher.

### Cohort sampling trap (cost two builds)

`ORDER BY ?p LIMIT 500` on Wikidata sorts the QID **IRI as a string**, so `Q1000123` sorts
before `Q927`. A 500-person "sample" selected that way was 500 arbitrary high-numbered items,
mostly 17th-18th-century figures, and the corpus names (Mulisch, Q927) were absent — which
produced a false "the method does not work" result. Select on a real attribute (birth year
window matching the corpus era), dedupe in code, and assert that a known in-corpus person is
in the cohort before spending an hour on the build.

## Cost, measured on CPU

| step | images | time |
|---|---|---|
| gallery embedding (700 px thumbs, det 640) | 677 | ≈7 min |
| event inference (1,800 px photos, det 1024) | 278 | ≈4–5 min |
| ground-truth script, 282-file tree | — | ≈25 s |
| ground-truth script, 7,589-file polluted tree (depth 2) | — | ≈3 min |
