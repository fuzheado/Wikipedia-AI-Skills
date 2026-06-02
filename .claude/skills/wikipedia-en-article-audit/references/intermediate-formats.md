# Intermediate Format Reference — wikipedia-en-article-audit

## diagnosis.json

Top-level fields:

```json
{
  "article_title": "Pyrrhus Concer",
  "page_id": 9773804,
  "article_type": "biography_general",
  "blp": false,
  "structural": {
    "short_description": "American sailor (1814–1897)",
    "short_description_issues": [],
    "has_infobox": false,
    "infobox_type": null,
    "sections": ["Legacy", "References", "External links"],
    "section_count": 3,
    "categories": ["1814 births", "1897 deaths", "..."],
    "category_count": 11,
    "missing_expected_sections": ["Early life", "Career", "Later life"],
    "blp": false,
    "current_assessment": "Stub",
    "protection": "none",
    "reference_count": 4,
    "length_bytes": 5760,
    "maintenance_templates": [],
    "image_notes": "Check Commons: https://commons.wikimedia.org/wiki/Category:Pyrrhus_Concer"
  },
  "npov_flags": [
    {
      "sentence_index": 12,
      "text": "It is noteworthy that he could lend...",
      "trigger": "noteworthy",
      "category": "editorial_praise"
    }
  ],
  "citations": [
    {
      "ref_index": 0,
      "short_ref": "Pioneer American Merchants in Japan",
      "url": null,
      "accessible": null,
      "sentences_supported": []
    }
  ],
  "sources_summary": []
}
```

## sentences.jsonl

One JSON line per extracted sentence:

```json
{"index": 1, "text": "Pyrrhus Concer (March 17, 1814 – August 23, 1897) was...", "section": "lead", "verdict": null}
{"index": 2, "text": "Pyrrhus Concer was born March 17, 1814 in Southampton NY...", "section": "lead", "verdict": null}
```

The `verdict` field is filled by the human reviewer during Phase 2.

## verification.json / verification_stub.json

Array of sentences with verdicts filled in by the human reviewer:

```json
{
  "article_title": "Pyrrhus Concer",
  "sentences": [
    {
      "index": 1,
      "text": "...",
      "section": "lead",
      "verdict": "confirmed"
    },
    {
      "index": 2,
      "text": "Concer was enslaved by the Pyrrhus family...",
      "section": "lead",
      "verdict": "contradicted",
      "contradiction": {
        "source": "Newsday 2005",
        "source_url": "https://web.archive.org/...",
        "source_quote": "He was owned by the Pelletreau family",
        "explanation": "..."
      },
      "correction": "Concer...was enslaved by the Pelletreau family",
      "correction_citation": {
        "template": "cite news",
        "params": {"last": "Bleyer", ...}
      }
    }
  ]
}
```

### Verdict types

| Verdict | Required fields | Description |
|---|---|---|
| `confirmed` | — | Claim is supported by a reliable source and neutrally framed |
| `contradicted` | `contradiction` object + `correction` + `correction_citation` | Source contradicts the claim; correction is provided |
| `npov_or` | `npov_explanation` + `suggested_action` | Claim is editorial or speculative; needs neutral rewrite |
| `unverifiable` | `reason` + `suggested_action` | No accessible source could be found |
| `mixed` | `sub_claims` array | Sentence contains multiple sub-claims with different verdicts |

## Citation accessibility tracking

```json
{
  "ref_index": 2,
  "accessible": false,
  "access_attempted": ["direct_http", "wayback_machine", "google_scholar"],
  "access_note": "Cloudflare protection on repository.library.brown.edu; PDF not publicly accessible"
}
```
