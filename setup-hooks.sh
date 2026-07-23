#!/usr/bin/env bash
# setup-hooks.sh — Configure git hooks for this repository
# Run once after cloning:  bash setup-hooks.sh
set -euo pipefail

cd "$(dirname "$0")"
git config core.hooksPath .githooks
echo "✅ Git hooks configured: core.hooksPath = .githooks"
echo "   pre-push: Validates all tooling references in SKILL.md files"
echo ""
echo "   This is optional — GitHub Actions CI also runs this check on every push."
