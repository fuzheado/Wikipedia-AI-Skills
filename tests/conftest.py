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

# Auto-discover all skill directories (alphabetical, no manual list to maintain)
SKILL_NAMES = sorted(
    d.name for d in SKILLS_DIR.iterdir()
    if d.is_dir() and (d / 'SKILL.md').exists()
)


def skill_path(name):
    """Return the path to a skill's SKILL.md file."""
    return SKILLS_DIR / name / 'SKILL.md'


def read_skill(name):
    """Read the full text of a skill's SKILL.md."""
    path = skill_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {path}")
    return path.read_text('utf-8')
