"""Shared fixtures for skill tests."""

import os
import sys
from pathlib import Path

# Path to the repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / '.claude' / 'skills'

# Path to pi extensions
EXTENSIONS_DIR = REPO_ROOT / '.pi' / 'extensions'

# Add assets directory to path so we can import the pipeline script
sys.path.insert(0, str(SKILLS_DIR / 'wikimedia-api-access' / 'assets'))

# All skill directories (alphabetical order, no duplicates)
SKILL_NAMES = [
    'mediawiki-page-navigation',
    'mediawiki-translate-extension',
    'pagetriage-api',
    'pywikibot',
    'wikidata',
    'wikidata-vector-search',
    'wikipedia-categories',
    'wikipedia-citations',
    'wikimedia-api-access',
    'wikimedia-api-strategy',
    'wikimedia-auth-oauth',
    'wikimedia-cdn-assets',
    'wikimedia-commons',
    'wikimedia-database',
    'wikimedia-diffs',
    'wikimedia-eventstreams',
    'wikimedia-ml-services',
    'wikimedia-page-assessment',
    'wikimedia-page-styling',
    'wikimedia-pageviews',
    'wikimedia-toolforge',
    'wikimedia-wikitext',
    'wikipedia-edit-history',
    'wikipedia-en-article-audit',
    'wikipedia-en-biography-writing',
    'wikipedia-error-handling',
    'wikipedia-page-anatomy',
    'wikipedia-reference-verifiability',
    'wikipedia-talk-page',
    'wikipedia-templates',
    'wikipedia-wikitables',
]


def skill_path(name):
    """Return the path to a skill's SKILL.md file."""
    return SKILLS_DIR / name / 'SKILL.md'


def read_skill(name):
    """Read the full text of a skill's SKILL.md."""
    path = skill_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {path}")
    return path.read_text('utf-8')
