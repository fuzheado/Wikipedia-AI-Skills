# Wikipedia-AI-Skills — Agent Instructions

Loaded automatically by pi in every session in this repo. See
`CONTRIBUTING.md` for the full contributor guide; this file is the binding
short version.

## PR-first workflow (hard rule)

All changes to `main` go through a pull request. Branch protection enforces
this server-side (5 required CI checks, no reviews); follow it even when you
could bypass it.

1. Start from up-to-date `main`: `git checkout main && git pull --ff-only origin main`
2. Create a branch: `git checkout -b <scope>/<change>` (e.g. `feat/my-skill`, `fix/toolforge`, `docs/agents-md`)
3. Commit with conventional style: `feat|fix|docs|ci|chore(<scope>): <summary>`
4. Push the branch, then `gh pr create` — the template
   (`.github/PULL_REQUEST_TEMPLATE.md`) auto-applies; fill in summary,
   what/why, and how it was tested
5. `gh pr checks --watch` — all 5 checks must pass before merging
6. Merge with `gh pr merge --merge --delete-branch`

Direct pushes to `main` are admin-bypass only, reserved for emergencies
(e.g. CI outage blocking a hotfix). If you bypass, say so explicitly in the
commit/PR.

## Skill contributions

For new or changed skills (`.claude/skills/<name>/`):

- **New skills:** pass the 7-question candidacy filter
  (`docs/design-philosophy.md` §2) and record the verdict in the PR
- **Register:** `README.md` (skill table + "What can I do" table),
  `ROADMAP.md` ("Published skills"), and run
  `python3 scripts/refresh-url-registry.py --new-only` for any new URLs —
  CI's Skill Registration Check enforces the first two
- **Tests:** add mock-based tests under `tests/` for new scripts/assets;
  run `python3 -m pytest tests/ -q`. Some pre-existing failures
  (flickr-wayback, i18n, notability) are unrelated known issues — verify a
  failure is yours before touching it
- **Freshness:** bump `last_verified` in the frontmatter of any changed
  SKILL.md
- **Verify before pushing skill changes** (all offline, all must pass):
  `python3 scripts/verify-links.py && python3 scripts/verify-freshness.py \
  && python3 scripts/verify-snippets.py && python3 scripts/verify-commands.py \
  && python3 scripts/verify-api.py`

## API etiquette (summary)

Every request to Wikimedia/Wikimedia-adjacent hosts needs a descriptive
User-Agent (`$WIKIMEDIA_USER_AGENT`), ≥1s pacing, and 429/403 handling —
see the global AGENTS.md and the `wikimedia-api-access` skill for details.

## Local tooling

- Githooks (pre-push tooling-reference check): `./setup-hooks.sh`
- The 5 required CI checks: `check-skill-registration`,
  `check-conftest-auto-discovery`, `check-roadmap-mentions`, `verify`,
  `validate-tooling` — they run on every PR unconditionally
