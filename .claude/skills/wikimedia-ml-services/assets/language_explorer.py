#!/usr/bin/env python3
"""Interactive language exploration using the langid model.

Type or paste text and see what language Lift Wing thinks it is, with
confidence scores and alternative predictions.

Supports batch mode and interactive mode.

Usage:
    # Interactive mode — type text, get language
    python3 language_explorer.py

    # One-shot mode
    python3 language_explorer.py "Albert Einstein was a physicist"

    # Try built-in test samples
    python3 language_explorer.py --samples

    # Output as JSON
    python3 language_explorer.py "Bonjour le monde" --json
"""

import argparse
import json
import sys
import textwrap

import requests


BASE_URL = "https://api.wikimedia.org/service/lw/inference/v1/models"
USER_AGENT = "LanguageExplorer/1.0 (user@example.com) ContentGapResearch"


def detect_language(text: str) -> dict | None:
    """Call the langid model and return the parsed response."""
    url = f"{BASE_URL}/langid:predict"
    try:
        resp = requests.post(
            url,
            json={"text": text},
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠  Error: {e}", file=sys.stderr)
        return None


def format_result(text: str, result: dict) -> str:
    """Format a language detection result for display."""
    lang_code = result.get("wikicode", "?")
    lang_name = result.get("languagename", result.get("language", "?"))
    score = result.get("score", 0)

    # Truncate text for display
    display_text = text[:80] + ("..." if len(text) > 80 else "")

    # Build a confidence bar
    bar_len = 20
    filled = int(score * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    lines = [
        f"  Text:    \"{display_text}\"",
        f"  Lang:    {lang_name} ({lang_code})",
        f"  Conf:    {score:.1%} {bar}",
    ]
    return "\n".join(lines)


# ── Test samples in various languages ────────────────────────────────────────
SAMPLES = {
    "English": "Albert Einstein was a German-born theoretical physicist, widely acknowledged to be one of the greatest and most influential physicists of all time.",
    "French": "Albert Einstein était un physicien théoricien d'origine allemande, largement reconnu comme l'un des plus grands physiciens de tous les temps.",
    "German": "Albert Einstein war ein deutscher theoretischer Physiker, der allgemein als einer der größten und einflussreichsten Physiker aller Zeiten gilt.",
    "Spanish": "Albert Einstein fue un físico teórico alemán, reconocido como uno de los más grandes e influyentes físicos de todos los tiempos.",
    "Japanese": "アルベルト・アインシュタインは、ドイツ生まれの理論物理学者であり、史上最大かつ最も影響力のある物理学者の一人として広く認められています。",
    "Arabic": "ألبرت أينشتاين كان فيزيائيا نظريا من أصل ألماني، ويعتبر على نطاق واسع أحد أعظم الفيزيائيين وأكثرهم تأثيرا على مر العصور.",
    "Russian": "Альберт Эйнштейн — физик-теоретик немецкого происхождения, широко признанный одним из величайших и наиболее влиятельных физиков всех времён.",
    "Chinese": "阿尔伯特·爱因斯坦是一位出生于德国的理论物理学家，被广泛认为是有史以来最伟大和最有影响力的物理学家之一。",
    "Italian": "Albert Einstein è stato un fisico teorico tedesco, ampiamente riconosciuto come uno dei più grandi e influenti fisici di tutti i tempi.",
    "Hindi": "अल्बर्ट आइंस्टीन एक जर्मन मूल के सैद्धांतिक भौतिक विज्ञानी थे, जिन्हें व्यापक रूप से अब तक के सबसे महान और सबसे प्रभावशाली भौतिकविदों में से एक माना जाता है।",
}


def run_samples():
    """Run detection on all built-in test samples."""
    print(f"\n{'═' * 55}")
    print("🌐 Language Identification — Test Samples")
    print(f"{'═' * 55}\n")

    for lang_name, sample_text in SAMPLES.items():
        print(f"📝 Expected: {lang_name}")
        result = detect_language(sample_text)
        if result:
            print(format_result(sample_text, result))

            detected = result.get("languagename", "")
            expected = lang_name
            if detected.lower().startswith(expected.lower()):
                print(f"  ✅ Correct!\n")
            else:
                print(f"  ❌ Got {detected}, expected {expected}\n")
        else:
            print("  ⚠  Detection failed\n")


def interactive_mode():
    """Interactive REPL for language detection."""
    print(f"\n{'═' * 55}")
    print("🌐 Language Explorer — Interactive Mode")
    print("Type text and see what language it is.")
    print("Type ':samples' to run test samples, ':quit' to exit.")
    print(f"{'═' * 55}\n")

    while True:
        try:
            text = input("→ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text == ":quit":
            break
        if text == ":samples":
            run_samples()
            continue
        if text == ":help":
            print("Commands: :samples (test samples), :quit (exit), :help (this)")
            continue

        result = detect_language(text)
        if result:
            print(format_result(text, result))
            print()
        else:
            print("  ⚠  Detection failed\n")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive language exploration using Lift Wing langid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("text", nargs="?", help="Text to identify language of")
    parser.add_argument("--samples", action="store_true", help="Run test samples")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.samples:
        run_samples()
        return

    if args.text:
        result = detect_language(args.text)
        if not result:
            sys.exit(1)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_result(args.text, result))
        return

    interactive_mode()


if __name__ == "__main__":
    main()
