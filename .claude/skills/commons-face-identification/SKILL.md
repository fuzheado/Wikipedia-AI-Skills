---
name: commons-face-identification
description: "Read before identifying people in Commons photos by face — WikiVisage vs a local InsightFace pipeline, ground truth from person categories, thresholds, per-person recall."
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikimedia-commons-sdc]
last_verified: 2026-11-25
skill_discovery_hints:
  - keywords: ["face recognition", "facial recognition", "identify people in photos", "who is in this photo", "depicts person", "P180 people"]
  - keywords: ["insightface", "arcface", "scrfd", "face embeddings", "face matching", "wikivisage"]
  - keywords: ["event photos unlabelled", "unnamed people", "person categories", "categorise people in photos"]
  - keywords: ["recall precision threshold", "how many people can be identified", "face recognition accuracy"]
---

# Identify people in Commons photos by face

> ⚠️ **User-Agent required.** Every request below hits a Wikimedia API and needs a descriptive
> `User-Agent` (see [wikimedia-api-access](../wikimedia-api-access/SKILL.md)); anonymous default
> agents are blocked with 403/429. All data is public: Commons categories, Wikidata claims, and
> freely licensed images. No credentials are needed for anything in this skill.

Two questions get confused, and the answer to each is different:

1. **"Can a machine name the people in these photos?"** — a matching problem, solved well by
   existing tooling, bounded by the *gallery* (who has a usable reference portrait).
2. **"How many people here are unidentified?"** — a metadata problem. Face recognition cannot
   name someone who exists nowhere in your reference set, so it can cluster that person
   ("appears in 15 photos") but not name them.

State which one you are measuring before you write code, and never report a single pooled
accuracy for both.

## When to use

- Someone asks how good face recognition is on Commons, or how many people in a category
  could be identified.
- An event category needs person labels (`depicts`/P180 or person categories) and you want the
  expected yield before proposing work.
- You need an honest recall/precision number for a people-recognition pipeline, with the
  per-person failures visible — not a demo.

Not for: reading who is already named in a file description (use
[wikimedia-commons](../wikimedia-commons/SKILL.md)), or measuring how many views those files get.

Pick the mode first:

| Goal | Path |
|---|---|
| A human is going to label Commons metadata | **WikiVisage** — https://wikivisage.toolforge.org (Toolforge, MIT, OAuth, active learning, writes P180) |
| Measure quality / count who is missed / one-off audit | Local InsightFace pipeline, SOP 1–4 below |

## Quick smoke test

```bash
# does the category carry person categories at all? (the ground-truth precondition)
curl -s -A "MyTool/1.0 (contact: me@example.org)" \
  "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Erasmus_Prize_2015&cmlimit=50&format=json" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['query']['categorymembers']), 'members')"
```

If every member is a `Category:` row and no file carries a person category, there is no free
ground truth — you are in a labelling project, not an evaluation. Say so and use WikiVisage.

## SOP 1 — Ground truth from person categories

Event categories are usually already person-categorised (`Category:Jane Doe`,
`Category:Jane Doe in 2015`, `Category:Jane Doe smiling`). That is free ground truth; never
hand-label what the tree already states.

```bash
python3 scripts/person_ground_truth.py "Category:Erasmus Prize 2015" --out gt.json
# files 282 | labelled 189 | people 62 | pairs 441
# unmapped categories (89) — eyeball these:
```

The resolution ladder, in order — the first step is the one everyone gets wrong:

1. `prop=pageprops&ppprop=wikibase_item` on the category page.
2. That item's **P301** → the person. Commons category items are `P31=Q4167836`
   ("Wikimedia category"), so a check for `P31=Q5` alone resolves **nothing**.
3. Otherwise the item itself is `P31=Q5`.
4. Qualifier shapes (`X in 2015`, `X in the Netherlands`, `X smiling`, `X wearing …`,
   `X with people`): strip the qualifier, resolve `Category:<base>` the same way. This is where
   most missing people are hiding — in the calibration category it moved coverage from
   44 to 74 people.
5. Last resort: `action=parse&prop=wikitext` on the category page, regex a `Q\d+` out of the
   infobox.

Then read the unmapped list **before trusting the output**. A name that reads like a person
means a qualifier shape is missing; one that reads like a work, building or collection means
the blacklist needs widening. Both are cheap to fix and both silently change your denominators.

Full API calls, the ancestor-walk trap and five failure modes:
[references/commons-person-category-ground-truth.md](references/commons-person-category-ground-truth.md).

## SOP 2 — Build the gallery (and keep it out of the test set)

- Models: `insightface` `buffalo_l` — SCRFD-10G detector + ArcFace-R50 512-D, ONNX Runtime.
  CPU is enough: ≈0.5 s per 700 px thumbnail, ≈1 s per 1800 px event photo on 4 cores.
- Install in an isolated venv: `pip install insightface onnxruntime opencv-python-headless`.
  `insightface` declares `opencv-python`, which shadows the headless build and dies with
  `libGL.so.1: cannot open shared object file` on a server — `pip uninstall -y opencv-python`
  and keep headless.
- Gallery per person: Wikidata **P18** first, then up to ~25 files from the person's Commons
  category, **excluding every file in the event set**. A gallery drawn from the photos you are
  about to score is training on test, and it inflates recall by tens of points.
- Cap at ~8 references per person, largest faces first. Expect ~5 refs per person; some people
  end up with none — report those as *excluded*, never as misses.
- `det_size` per input: 640 for 600–700 px thumbnails, **1024 for 1800 px event photos**. Group
  shots lose the small faces at 640. Drop gallery faces under 45 px wide; keep every event face
  but record its bbox width, because width is what explains almost every later failure.

## SOP 3 — Detect, embed, match

```python
import numpy as np
from insightface.app import FaceAnalysis          # buffalo_l: det_10g + w600k_r50
app = FaceAnalysis(name='buffalo_l', root='models_ia',
                   allowed_modules=['detection', 'recognition'])
app.prepare(ctx_id=-1, det_size=(1024, 1024))     # 1024 for 1800-px event photos

faces = app.get(cv2.imread(path))                 # list of Face(bbox, det_score, normed_embedding)
E = np.stack([f.normed_embedding for f in faces]) # already L2-normalised
sims = E @ G.T                                    # G: (persons*refs, 512) gallery matrix
```

Cosine similarity is the score; take the **max over a person's references**, then the argmax
over persons. Two habits that keep the run honest:

- **Checkpoint embeddings to JSON per image** and run long inference as a background process
  (`nohup`, poll the log). A tool call that times out is killed and unsaved embeddings are
  lost — a 677-image gallery run died at image 500 before checkpointing was added.
- **Record bbox width and det_score** for every face. "Not found" is usually "40 px face in a
  wide shot", and you cannot say that after the fact without the width.

## SOP 4 — Measure three populations, then the threshold sweep

1. **Labelled pairs** `(file, person)` → recall across a sweep. This is the validation number.
2. **Photos with no person label at all** → face count and how many got a name. This is the
   population that answers "how many people are being missed", and its ceiling is structural:
   a gallery built from the labelled set can only name people who are labelled *somewhere*.
   Say that out loud instead of reporting a low hit rate and stopping.
3. **Identity clusters** over all faces (cosine ≥ 0.60, transitive union-find) → how many
   distinct people are visibly present versus how many Commons names exist. Clustering
   over-splits (same person in two clusters) and rarely over-merges at 0.6, so treat the count
   as an upper bound on identities.

Plus the number a curation tool would actually act on: **missed appearances** —
`(person, photo)` pairs where a face matches a named person but the photo does not carry their
category.

**Never report a threshold without a visual audit.** Build side-by-side tiles (gallery
reference | event crop, similarity in the label), judge same/different/unclear yourself in the
high band and the near-threshold band separately, and quote the audit next to the number.
Calibration on 282 photos, 1,537 faces: with ArcFace-R50 cosine, ≈75% of ≥0.60 matches were
correct and only 20–40% in 0.42–0.50 — but that audit ran on the *mixed* population with
contaminated references. On the cleaned non-community set (47 community members excluded,
references from single-face images) a domain expert confirmed **11 of 11** proposals at ≥0.50.
The band is not a constant: gallery quality moves it. Re-audit per population, and quote whose
judgement the audit used. Recall falls off
fast above 0.65 and precision collapses below 0.50.

Measured operating points, per-person variance and the population shape:
[references/calibration-measurements.md](references/calibration-measurements.md).

## SOP 5 — Prefer in-event seeds over a portrait gallery

Gallery quality, not the model, is the bottleneck. The worst case is a single reference
portrait from another era: one person whose only gallery image was taken **11 years after** the
event scored 5–8% recall, while peers with era-appropriate photos scored 70–100%.

Fix it the way WikiVisage does — active learning instead of a fixed gallery:

1. Take ~5 **confirmed in-event** faces for the person (human clicks Y/N, or labels you trust).
2. Average their embeddings into a centroid, L2-normalise.
3. Classify every remaining face by similarity to the centroid.

Held-out protocol (people with ≥8 labelled photos; centroid seeded from the first 5 photos
only; scored on the remaining 269 photos, same 0.60 threshold):

| method | recall @0.60 | recall @0.50 |
|---|---|---|
| fixed portrait gallery | 49% | 74% |
| in-event centroid (~8 seed faces) | **78%** | **86%** |

False-fire proxy for the centroid: 17 of 278 fires were on photos the category does not list
the person in — and some of those are genuinely missing labels, so ~94% is a *lower* bound.
Replicate this before tuning thresholds.

Rules that keep the comparison fair: hold out whole **photos**, never individual faces; never
seed a centroid from the photos you score; keep the same threshold across both methods.

## SOP 6 — Write back, with a human in the loop

Do not auto-apply. The write path and its constraints belong to
[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md): one `P180` claim per person, and
for group photos add the `P2677` (relative position within image) qualifier from the face
bbox — that is what makes a face-level annotation checkable later.

Existing suggestion surfaces worth wiring into a review queue rather than reinventing:
WikiVisage (active learning), `commons-metadata-suggester` (suggests categories/depicts from
existing metadata), DepictAssist, and `wd-image-positions` for inspecting `P2677` coverage.

## Constraints & guardrails

1. **Face embeddings are biometric data.** Keep them local, never upload embeddings or crops of
   non-public figures, and treat "who is this anonymous guest" as out of scope —
   `Commons:Photographs of identifiable people` applies.
2. **InsightFace `buffalo_l` weights are non-commercial.** Fine for analysis; a blocker for
   anything Commons-facing. WikiVisage ships the same restriction — flag it, do not ship it
   silently.
3. **File-level categories are file-level truth.** A label does not mean the person is
   prominent in that frame, so per-person recall swings 0–100% and must be shown per person,
   not only pooled. A pooled number hides the failure that matters.
4. **A category tree is not a clean hierarchy.** Event categories contain members that point
   sideways or upward (a venue museum's collection, a parent category). Cap depth, keep a
   visited set, and sanity-check the file count against the root's member count before
   believing any denominator. One 88-member Wikimania category walked 7,589 files at depth 2.
5. **"50 titles per call" overflows the URL.** Commons file titles are long, so a 50-title
   `titles=` batch answered HTTP 414 URI Too Long. Batch by URL-encoded length *and* count.
6. **429 is normal at walking speed.** Sleep ~0.2 s between calls, honour `Retry-After`, and
   back off; an unthrottled recursive walk gets blocked within a minute.
7. **No faces detected ≠ no people.** 21 of 282 photos had no detectable face — paintings,
   interiors, the award object. Exclude them from the face denominator and say why.
8. **Never tune a threshold on the set you report.** Sweep on one category, report on another,
   or hold out photos.
9. **Decide the population before you measure — community members are a privacy boundary.**
   If the deliverable is about the outsiders in the frame (an award, a GLAM event, a
   conference), exclude Wikipedians/Wikimedians: their categories sit under
   `Wikipedians …`/`Wikimedians …`/`Wikimedia movement …` trees, so walk category ancestry
   and drop every photo that names one. If the ask is privacy-driven, also drop photos where
   the matcher puts a community member in frame even though nothing is labelled. Measured on
   the calibration corpus: 47 of 71 people were community members, 100 photos were dropped on
   the label rule and 7 more on the match rule, leaving 173 photos and 671 of 1,537 faces.
   The numbers change with the population — recall on the remaining 116 pairs was 42% at 0.60,
   not the pooled 51%, because ceremonial wide shots dominate what is left. Never mix the two
   populations in one accuracy claim.
10. **A person's Commons category contains other people.** Joint photos (a partner, a colleague,
   a co-author) are filed under both names — two people's categories shared 7 of 7 and 9 files
   in the calibration corpus, and a gallery built "largest face first" then locks onto whichever
   face is biggest. Their centroid cosine was **0.94**: the two "identities" were one face.
   Build gallery references from single-face images only, prefer P18, and print the
   most-similar gallery pairs before reporting counts. Contamination inflates "missed
   appearances" by double-naming the same face.

## Example use cases

- *"How many people in this award-ceremony category are unidentified?"* — SOP 1 for ground
  truth, SOP 4 population 2 and 3 for the answer: ~140 recurring people clustered, 74 named,
  so roughly half are anonymous, and only people already labelled somewhere can be matched.
- *"Is face recognition good enough to suggest depicts statements?"* — SOP 4 sweep + visual
  audit: yes at 0.55–0.60 with review, no below 0.50.
- *"A photographer uploaded 4,000 conference photos with no person categories."* — SOP 5 with
  WikiVisage: confirm five faces per speaker, let the centroid classify, review, then write
  `P180`.

## Tooling

| Tool | Use |
|---|---|
| `scripts/person_ground_truth.py` | Walks a category tree, resolves person categories to QIDs, writes `file_persons.json`, prints denominators and the unmapped list. Stdlib only; refuses to run without a category. |
| https://wikivisage.toolforge.org | Active-learning labelling, MIT, OAuth, writes P180. Use it when a human will do the labelling. |
| https://reframe.toolforge.org | Face-aware cropping — useful for building a reference set, not for identification. |
| https://commons-metadata-suggester.toolforge.org | API that suggests metadata (categories, depicts) from existing file metadata. |

## Cross-references

| Skill | Why |
|---|---|
| [wikimedia-api-access](../wikimedia-api-access/SKILL.md) | User-Agent, 429/403 handling, `maxlag`; every call here needs it. |
| [wikimedia-commons](../wikimedia-commons/SKILL.md) | Category traversal, file metadata, thumbnail URLs. |
| [wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md) | The only sanctioned write path for `P180` claims. |
| [wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md) | Thumbnail widths — detection quality depends on the pixel width you fetch. |
| [wikiportraits-event-series](../wikiportraits-event-series/SKILL.md) | Event categories and edition items the person labels attach to. |
| [wikimedia-ml-services](../wikimedia-ml-services/SKILL.md) | A VLM second opinion (LiftWing) when you want an independent check on a crop. |
