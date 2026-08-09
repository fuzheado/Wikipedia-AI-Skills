# Design tokens

Condensed from `codex-docs/docs/design-tokens/` (canonical).

Design tokens are the smallest stylistic pieces of the design system. Use them:
- as a single source of truth instead of hard-coded style values / single-use variables;
- to ensure only systematic decisions style components and features.

Available formats: CSS custom properties, Less variables, SCSS variables, ES6 variables, JSON.

Each token category has a demo page with names, values, and origin info.

## Using tokens

- **Figma**: use the Codex Figma library.
- **npm**: see `references/developing.md`.
- **MediaWiki**: https://www.mediawiki.org/wiki/Codex#Using_design_tokens_directly

## Categories (demo pages in the docs)

- `animation` — easing/timing tokens
- `border` — widths, radii, styles
- `box-shadow`
- `box-sizing`
- `breakpoint`
- `color` — the WikimediaUI color palette (background, text, link, border, accent/destructive/
  progressive, etc.)
- `cursor`
- `font` — families, sizes, weights, line-height
- `opacity`
- `outline`
- `position` — z-index related layout tokens
- `size` — icon, thumbnail, min-size tokens
- `spacing` — the spacing scale (`--spacing-25`, `--spacing-50`, `--spacing-100`, …)
- `transition`
- `z-index`

## Structure

See `docs/design-tokens/definition-and-structure.md` for how the token system is defined and
organized, and `docs/contributing/contributing-tokens.md` to add or request a token.
