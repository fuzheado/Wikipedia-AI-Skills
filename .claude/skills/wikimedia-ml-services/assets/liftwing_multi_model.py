#!/usr/bin/env python3
"""Score a revision across multiple Lift Wing models with caching and rate-limit awareness.

This script demonstrates the production pattern: score an edit against
revert risk, goodfaith, and damaging models in parallel, with a local
cache to avoid redundant calls.

Usage:
    # Score enwiki revision 123456789 against revert risk + goodfaith
    python3 liftwing_multi_model.py enwiki 123456789

    # Score with all available models for that wiki
    python3 liftwing_multi_model.py enwiki 123456789 --all

    # Score without caching (bypass cache for fresh results)
    python3 liftwing_multi_model.py enwiki 123456789 --no-cache

    # Authenticated (higher rate limits)
    export ACCESS_TOKEN="your_oauth_token"
    python3 liftwing_multi_model.py enwiki 123456789
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests


# ── Rate-limit constants ─────────────────────────────────────────────────────
MIN_INTERVAL_SECONDS = 0.1       # 10 req/s max (safe for anonymous 15 req/s)
CACHE_TTL_SECONDS = 3600         # Cache scores for 1 hour

# ── API configuration ────────────────────────────────────────────────────────
BASE_URL = "https://api.wikimedia.org/service/lw/inference/v1/models"
USER_AGENT = "LiftWingMultiModel/1.0 (user@example.com) ContentGapResearch"


# ── Score Cache ──────────────────────────────────────────────────────────────
class ScoreCache:
    """Simple in-memory cache for ML scores.

    Lift Wing has no server-side caching (unlike ORES), so every identical
    request costs an inference call. This cache avoids redundant scoring
    when the same revision is queried multiple times within TTL.
    """

    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self._data: dict[tuple[str, int], dict] = {}
        self._ttl = ttl

    def get(self, model: str, rev_id: int) -> dict | None:
        key = (model, rev_id)
        entry = self._data.get(key)
        if entry is None:
            return None
        if time.time() - entry["ts"] > self._ttl:
            del self._data[key]
            return None
        return entry["result"]

    def set(self, model: str, rev_id: int, result: dict):
        self._data[(model, rev_id)] = {"result": result, "ts": time.time()}

    def clear(self):
        self._data.clear()

    def __len__(self):
        return len(self._data)


# ── Model definitions ────────────────────────────────────────────────────────
MODERN_MODELS = {
    "revertrisk-language-agnostic": {
        "params": {"rev_id": int, "lang": str},
        "description": "Revert risk (language-agnostic, replaces goodfaith+damaging)",
    },
    "revertrisk-multilingual": {
        "params": {"rev_id": int, "lang": str},
        "description": "Revert risk (multilingual, 300+ languages)",
    },
    "revertrisk-wikidata": {
        "params": {"rev_id": int},
        "description": "Revert risk (Wikidata-specific)",
    },
    "readability": {
        "params": {"rev_id": int, "lang": str},
        "description": "Readability score and grade level",
    },
    "reference-need": {
        "params": {"rev_id": int, "lang": str},
        "description": "Reference need score (how many claims need citations)",
    },
    "reference-risk": {
        "params": {"rev_id": int, "lang": str},
        "description": "Reference quality risk",
    },
}

REVSCORING_MODELS = {
    "goodfaith": {"params": {"rev_id": int}, "description": "Good/bad faith prediction (frozen)"},
    "damaging": {"params": {"rev_id": int}, "description": "Is edit damaging? (frozen)"},
    "articlequality": {"params": {"rev_id": int}, "description": "Article quality grade (frozen)"},
}


def get_session() -> requests.Session:
    """Create a requests.Session with proper headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    })
    token = os.environ.get("ACCESS_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def score_revision(
    session: requests.Session,
    cache: ScoreCache,
    wiki: str,
    rev_id: int,
    model_name: str,
    no_cache: bool = False,
    lang: str = "en",
) -> dict | None:
    """Score a single revision against one model.

    Returns the parsed JSON response, or None on failure.
    Respects cache unless no_cache=True.
    """
    # Check cache first
    if not no_cache:
        cached = cache.get(model_name, rev_id)
        if cached is not None:
            return cached

    # Determine if this is a modern or Revscoring model
    if model_name in MODERN_MODELS:
        full_name = model_name
        payload = {"rev_id": rev_id, "lang": lang}
    elif model_name in REVSCORING_MODELS:
        full_name = f"{wiki}-{model_name}"
        payload = {"rev_id": rev_id}
    else:
        # Assume it's a fully qualified model name
        full_name = model_name
        payload = {"rev_id": rev_id}

    url = f"{BASE_URL}/{full_name}:predict"

    try:
        resp = session.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  Error scoring {model_name}: {e}", file=sys.stderr)
        return None

    # Cache the result
    cache.set(model_name, rev_id, result)
    return result


def extract_prediction(rev_id: int, model_name: str, result: dict) -> dict:
    """Extract the human-readable prediction from a model response.

    Handles:
    - Revscoring format (ORES-style nested under wiki.scores.rev_id.model.score)
    - Modern revert-risk format (model_name, model_version, output.prediction)
    - Readability format (output.score + output.fk_score_proxy)
    - Reference formats (reference_need_score, reference_risk_score)
    """
    wiki = result.get("model_name", "").split("-")[0] if "model_name" in result else "enwiki"

    # Try Revscoring ORES format first
    for key in list(result.keys()):
        if isinstance(result[key], dict) and "scores" in result[key]:
            try:
                score = result[key]["scores"][str(rev_id)][model_name]["score"]
                return {
                    "prediction": score.get("prediction", "N/A"),
                    "probability": score.get("probability", {}),
                }
            except (KeyError, TypeError):
                pass

    # Try Lift Wing unified envelope (model_name, output keys)
    output = result.get("output", {})
    if output:
        # revert-risk: output.prediction (bool) + output.probabilities
        if "prediction" in output and isinstance(output["prediction"], bool):
            return {
                "prediction": output["prediction"],
                "probability": output.get("probabilities", {}),
            }
        # readability: output.score (float) + output.fk_score_proxy
        if "score" in output and "fk_score_proxy" in output:
            return {
                "score": output["score"],
                "fk_score_proxy": output["fk_score_proxy"],
            }

    # Try top-level fields for reference models
    if "reference_need_score" in result:
        return {"reference_need_score": result["reference_need_score"]}

    if "reference_risk_score" in result:
        return {
            "reference_risk_score": result["reference_risk_score"],
            "reference_count": result.get("reference_count"),
            "survival_ratio": result.get("survival_ratio"),
        }

    if "prediction" in result:
        # outlink-topic-model, article-country
        return result

    return {"raw": str(result)[:200]}


def format_score_line(model_name: str, label: str, extracted: dict) -> str:
    """Format a single score line for terminal output."""
    if "score" in extracted and "fk_score_proxy" in extracted:
        # Readability
        s = extracted["score"]
        grade = extracted["fk_score_proxy"]
        level = (
            "Very Easy" if s > 0.8
            else "Easy" if s > 0.6
            else "Fairly Difficult" if s > 0.4
            else "Difficult" if s > 0.2
            else "Very Confusing"
        )
        return f"  • {label}: score={s:.3f}, grade={grade:.1f} ({level})"

    if "reference_need_score" in extracted:
        return f"  • {label}: need={extracted['reference_need_score']:.1%}"

    if "reference_risk_score" in extracted:
        return (
            f"  • {label}: risk={extracted['reference_risk_score']:.1%}, "
            f"refs={extracted.get('reference_count', '?')}"
        )

    prediction = extracted.get("prediction", "")
    probability = extracted.get("probability", {})

    # Bool predictions (revert-risk) get SAFE/RISKY format
    if isinstance(prediction, bool):
        return f"  • {label}: {'RISKY' if prediction else 'SAFE'}"

    if isinstance(probability, dict) and probability:
        sorted_probs = sorted(
            probability.items(), key=lambda x: x[1], reverse=True
        )[:3]
        prob_str = ", ".join(
            f"{k}: {v:.1%}" for k, v in sorted_probs if isinstance(v, (int, float))
        )
        return f"  • {label}: {prediction} (prob: {prob_str})"

    if "results" in extracted:
        # outlink-topic or article-country
        results = extracted.get("results", extracted.get("prediction", {}).get("results", []))
        top_items = [r.get("topic", r.get("country", "?")) for r in results[:3]]
        return f"  • {label}: {', '.join(top_items)}"

    return f"  • {label}: {prediction}"


def main():
    parser = argparse.ArgumentParser(
        description="Score a revision across multiple Lift Wing ML models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("wiki", help="Wiki code (e.g., enwiki, frwiki, arwiki)")
    parser.add_argument("rev_id", type=int, help="Revision ID to score")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Score against all available models",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Specific models to score (e.g., goodfaith damaging revertrisk-language-agnostic)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache and force fresh scores",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Language code for language-specific models (default: en)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=MIN_INTERVAL_SECONDS,
        help=f"Minimum seconds between requests (default: {MIN_INTERVAL_SECONDS})",
    )

    args = parser.parse_args()

    session = get_session()
    cache = ScoreCache()

    if args.models:
        models_to_score = {}
        for m in args.models:
            if m in MODERN_MODELS:
                models_to_score[m] = MODERN_MODELS[m]
            elif m in REVSCORING_MODELS:
                models_to_score[m] = REVSCORING_MODELS[m]
            else:
                models_to_score[m] = {"params": {}, "description": m}
    elif args.all:
        models_to_score = {**MODERN_MODELS, **REVSCORING_MODELS}
    else:
        models_to_score = {
            "revertrisk-language-agnostic": MODERN_MODELS["revertrisk-language-agnostic"],
            **REVSCORING_MODELS,
        }

    results = {}

    print(f"\n🧠 Scoring revision {args.rev_id} on {args.wiki}", file=sys.stderr)
    print(f"   Language: {args.lang}", file=sys.stderr)
    print(f"   Models: {', '.join(models_to_score.keys())}", file=sys.stderr)
    print(f"   Cache: {'disabled' if args.no_cache else 'enabled (TTL: {}s)'}".format(
        CACHE_TTL_SECONDS
    ), file=sys.stderr)
    print(file=sys.stderr)

    for i, (model_name, model_info) in enumerate(models_to_score.items()):
        print(
            f"  [{i+1}/{len(models_to_score)}] {model_name} — {model_info['description']}",
            file=sys.stderr,
        )

        result = score_revision(
            session,
            cache,
            args.wiki,
            args.rev_id,
            model_name,
            no_cache=args.no_cache,
            lang=args.lang,
        )

        if result is not None:
            results[model_name] = result

        if i < len(models_to_score) - 1:
            time.sleep(args.interval)

    if args.output == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"\n📊 Results for revision {args.rev_id} on {args.wiki}:")
        print(f"   Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print()
        for model_name, result in results.items():
            label = f"{model_name} ({models_to_score[model_name]['description']})"
            extracted = extract_prediction(args.rev_id, model_name, result)
            print(format_score_line(model_name, label, extracted))
        print()

    print(f"   Cache entries: {len(cache)}", file=sys.stderr)


if __name__ == "__main__":
    main()
