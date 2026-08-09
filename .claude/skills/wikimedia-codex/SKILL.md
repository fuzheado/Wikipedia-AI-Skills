---
name: wikimedia-codex
description: "Build Wikimedia-consistent UIs with the Codex design system: Vue 3 and CSS-only components, design tokens, icons, composables. For Toolforge tools and MediaWiki frontends."
license: MIT
compatibility: opencode
last_verified: 2026-06-24
skill_discovery_hints:
  - keywords: ["codex", "wikimedia-codex", "design system", "wikimedia", "vue", "components"]
  - keywords: ["toolforge", "mediawiki", "frontend", "ui", "design tokens"]
---

# Codex (Wikimedia design system)

> **⚠️ Known status (2026-06-24): the `codex` package on cdnjs is stale** — it serves 2.3.2 while
> the current npm release is 2.6.2. The `codex.json` fix was merged but not yet deployed (large
> cdnjs backlog, expected to last a long time). **Prefer loading Codex from npm, unpkg, or
> jsDelivr.** If you must use cdnjs, pin the version explicitly and be aware you get an outdated
> build with a different file layout (no `codex.umd.cjs`). See the "CDN / plain script tag"
> section below for working URLs.

Codex is the official design system for Wikimedia projects (MediaWiki, Toolforge tools, and more).
It provides a **style guide**, **design tokens**, **icons**, **Vue 3 components** (each with a
CSS-only variant), and **composables** — all with internationalization, accessibility, and broad
browser/device support built in.

Canonical sources:
- Built docs: <https://doc.wikimedia.org/codex/>
- MediaWiki: <https://www.mediawiki.org/wiki/Codex>
- Codebases: Gerrit `design/codex` (canonical) / GitHub mirror `wikimedia/design-codex`
- Local Markdown sources (the canonical basis): `codex-source/packages/codex-docs/docs/`
  with per-component demos in `codex-source/packages/codex-docs/component-demos/`

## Packages

| Package | Contents |
|---------|----------|
| `@wikimedia/codex` (v2.x) | Vue 3 components (`CdxButton`, `CdxTextInput`, …), CSS-only components, composables (`useComputedDirection`, …), TypeScript prop types. Ships `dist/codex.js` (CJS), `dist/codex.umd.js` (UMD), `dist/codex.mjs` (ESM), `dist/codex.style.css` (+ `codex.style-rtl.css`, experimental `codex.style-bidi.css`), `dist/mixins/*.less`, `dist/modules/`, `dist/types/` |
| `@wikimedia/codex-icons` | Monochrome icons named `cdxIconFoo` (SVG strings/objects) + utilities (`resolveIcon`, `shouldIconFlip`) + the `Icon` type. Files: `codex-icons.mjs` (ESM), `codex-icons.js` (CJS/Node), `codex-icons.json` (used by MediaWiki) |
| `@wikimedia/codex-design-tokens` | Tokens as `theme-wikimedia-ui.css` (CSS variables), `.less` (Less variables), `.scss` (Sass variables), `.json` (detailed data) |

The components package uses tokens internally; installing `@wikimedia/codex` alone is enough to
use CSS-only components. Install `@wikimedia/codex-icons` for icons and
`@wikimedia/codex-design-tokens` to style your own components consistently.

## Loading Codex

### npm
```bash
npm install @wikimedia/codex
```
Load the compiled styles once per page (both usage modes need the CSS):
```js
import '@wikimedia/codex/dist/codex.style.css';
// or in CSS:
@import '@wikimedia/codex/dist/codex.style.css';
```

### CDN / plain script tag (e.g. Toolforge)
The npm package ships a UMD build for use via a plain `<script>` tag. Note the UMD filename is
**`dist/codex.umd.cjs`** (not `codex.umd.js` — that name no longer exists). Serve it together with
`codex.style.css`:

```html
<link rel="stylesheet" href=".../codex.style.css">
<script src=".../codex.umd.cjs"></script>
```

**CDN status (verified 2026-06-24):**
- **cdnjs** (`codex` package) is **stale**: the latest available version is **2.3.2**, while the
  current npm release is **2.6.2**. The fix for `packages/c/codex.json` was merged, but there is a
  large deployment backlog, so newer versions are not yet published. cdnjs also serves a different
  file layout (`codex.js`/`codex.min.js` + `codex.style*.css`, no UMD build, no
  `messageKeys.json`/`mixins`/`modules`).
- **For current versions**, use a CDN that mirrors npm directly, e.g. jsDelivr or unpkg:
  - `https://cdn.jsdelivr.net/npm/@wikimedia/codex@2.6.2/dist/codex.umd.cjs`
  - `https://cdn.jsdelivr.net/npm/@wikimedia/codex@2.6.2/dist/codex.style.css`
  - (also available: `codex.style-rtl.css`, `codex.style-bidi.css`, `messageKeys.json`)
- The cdnjs packages for Codex are `codex`, `codex-icons`, `codex-design-tokens`.

### MediaWiki
Use ResourceLoader (`CodexModule`, `vue.createMwApp`) — see
<https://www.mediawiki.org/wiki/Codex> for the JavaScript and CSS-only instructions.

## Two ways to use components

### 1. Vue 3 components (interactive — needs Vue 3 + JavaScript)
Import only the components you need and register them:
```vue
<template>
	<div>
		<cdx-button action="progressive" weight="primary">Save</cdx-button>
	</div>
</template>
<script>
import { defineComponent } from 'vue';
import { CdxButton } from '@wikimedia/codex';
export default defineComponent( {
	components: { CdxButton }
} );
</script>
```
Vue components do **not** work with Vue 2.

### 2. CSS-only components (no JavaScript required)
Output the documented HTML with the documented CSS classes. Every component page has a
"CSS-only version" section (e.g. the CSS-only Button):
```html
<button class="cdx-button cdx-button--action-progressive cdx-button--weight-primary">
	Save
</button>
```
Some CSS-only components are provided as Less mixins instead of markup (e.g. `mixins/link.less`).

## Icons
- **Vue:** import the icon from `@wikimedia/codex-icons` and render it with `CdxIcon`
  (from `@wikimedia/codex`). Expose icons to the template via `setup()` (Composition API)
  or `data` (Options API):
  ```vue
  <cdx-button action="destructive">
	  <cdx-icon :icon="cdxIconTrash" /> Delete this item
  </cdx-button>
  <script>
  import { CdxButton, CdxIcon } from '@wikimedia/codex';
  import { cdxIconTrash } from '@wikimedia/codex-icons';
  </script>
  ```
- **CSS-only:** apply the `css-icon` Less mixin to a `<span>`:
  ```less
  @import ( reference ) '@wikimedia/codex-design-tokens/theme-wikimedia-ui.less';
  @import ( reference ) '@wikimedia/codex/mixins/css-icon.less';
  .my-icon {
	  &--trash { .cdx-mixin-css-icon( @cdx-icon-trash, @param-is-button-icon: true ); }
  }
  ```
  ```html
  <span class="my-icon--trash"></span>
  ```
- **Performance:** never ship the whole icon package to the browser — use a bundler that
  tree-shakes (only extracted icons are included) or another minimization technique.
- Icons adapt to the surrounding text direction (they flip in RTL).

## Design tokens
Design tokens are the smallest style pieces of the system — use them instead of hard-coded
values:
```css
@import '@wikimedia/codex-design-tokens/theme-wikimedia-ui.css';
.my-custom-element {
	background-color: var( --background-color-interactive );
	width: calc( var( --size-icon-medium ) + 2 * var( --spacing-100 ) );
	margin-left: calc( var( --size-icon-medium ) * -1 );
	padding: var( --spacing-25 ) var( --spacing-50 );
}
```
Less and Sass equivalents exist (`@background-color-interactive`, `$background-color-interactive`).

**Token categories** (each has a demo page in the docs): `color`, `spacing`, `size`, `font`,
`border`, `box-shadow`, `box-sizing`, `breakpoint`, `cursor`, `opacity`, `outline`, `position`,
`z-index`, `animation`, `transition`.

**Caveat:** several token categories are exposed as CSS custom properties (CSS variables)
rather than raw values, so arithmetic on them must use CSS `calc()` — preprocessor math like
Less `unit()` will not work on those tokens.

### Dark mode
Codex 1.5+ supports automatic light/dark switching based on the user's environment:
```css
@import url( ./node_modules/@wikimedia/codex-design-tokens/theme-wikimedia-ui-root.css );
@import url( ./node_modules/@wikimedia/codex-design-tokens/theme-wikimedia-ui-mode-dark.css )
	only screen and ( prefers-color-scheme: dark );
```
(or as `<link media="( prefers-color-scheme: dark )">` elements). Always reference color tokens
(e.g. `var( --background-color-base )`) in custom CSS instead of hardcoding hex values so dark
mode keeps working.

## Composables (from `@wikimedia/codex`)
`useBreakpoint`, `useButtonGroupKeyboardNav`, `useComputedDirection`, `useComputedDisabled`,
`useComputedLanguage`, `useFieldData`, `useFloatingMenu`, `useFocusTrap`, `useGeneratedId`,
`useI18n`, `useI18nWithOverride`, `useIconOnlyButton`, `useIntersectionObserver`,
`useLabelChecker`, `useModelWrapper`, `useOptionalModelWrapper`, `useResizeObserver`,
`useScrollLock`, `useSlotContents`, `useSplitAttributes`, `useWarnOnce`.
Frequently used: `useComputedDirection`, `useModelWrapper`, `useFloatingMenu`,
`useResizeObserver`, `useIntersectionObserver`.

## Bidirectionality & accessibility
- Fully-LTR pages: `codex.style.css`; fully-RTL pages: `codex.style-rtl.css`.
  (Experimental `codex.style-bidi.css` supports client-side direction flipping via `[dir]`
  selectors as of v1.12+.)
- Codex supports pages entirely LTR or entirely RTL; mixed or runtime-changing directionality is
  not supported except special cases.
- Accessibility is baked into every component (see the style-guide `accessibility` page).

## Component selection guide
Pick the component by need (full details in `references/components.md`):
- **Text entry:** `text-input`, `text-area`, `search-input`, `select`, `combobox`, `lookup`,
  `multiselect-lookup`, `typeahead-search`, `chip-input`, `field` (label + input wrapper)
- **Selection:** `checkbox`, `radio`, `toggle-switch`, `toggle-button`, `toggle-button-group`
- **Actions:** `button`, `button-group`, `menu-button`
- **Overlays / feedback:** `dialog`, `menu`, `menu-button`, `menu-item`, `popover`, `tooltip`,
  `toast`, `message`
- **Navigation / structure:** `tabs`, `tab`, `accordion`, `breadcrumb`, `container`, `table`,
  `card`
- **Media / indicators:** `icon`, `image`, `thumbnail`, `search-result-title`,
  `progress-bar`, `progress-indicator`, `info-chip`, `input-chip`, `label`

## Working from the local checkout
The canonical docs are checked out at `codex-source/packages/codex-docs/docs/` (Markdown) with
per-component demos under `codex-source/packages/codex-docs/component-demos/<component>/` and
component source under `codex-source/packages/codex/src/components/<component>/`.
Run `scripts/list-codex-checkout.ps1` to list all components and demo folders found locally.

## References
- `references/accessing-codex.md` — what Codex is, resources, Figma/MediaWiki/Gerrit/GitHub
- `references/developing.md` — installation, usage modes, packages, dark mode, bidirectionality
- `references/components.md` — component types overview
- `references/design-tokens.md` — token system overview and categories
- `references/icons.md` — icon system overview
- `references/composables.md` — composables overview and demo pages
