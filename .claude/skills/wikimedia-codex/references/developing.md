# Developing with Codex

Condensed from `codex-docs/docs/using-codex/developing.md` (canonical). Using Codex in MediaWiki?
See https://www.mediawiki.org/wiki/Codex.

## Installation

```bash
npm install @wikimedia/codex
```
This is the only required package to use **CSS-only components**. Additional packages:
- Vue 3 components → also install Vue.js (https://vuejs.org/guide/quick-start.html)
- Icons → `@wikimedia/codex-icons`
- CSS/Less/Sass variables → `@wikimedia/codex-design-tokens`

## Using components

Two kinds: **Vue 3 components** and **CSS-only components**. Both require the compiled CSS,
loaded once per page load:
```js
import '@wikimedia/codex/dist/codex.style.css';
// or
@import '@wikimedia/codex/dist/codex.style.css';
```
A right-to-left variant `codex.style-rtl.css` is also available.

### Vue 3 components
Import from `@wikimedia/codex`, register in `components`, use in the template:
```vue
<template>
	<cdx-button action="progressive" weight="primary">Save</cdx-button>
</template>
<script>
import { defineComponent } from 'vue';
import { CdxButton } from '@wikimedia/codex';
export default defineComponent( { components: { CdxButton } } );
</script>
```
Label buttons with the action they trigger (e.g. `Save`, `Search`, `Add to list`) — never
"Click me"/"Click here": the button text is the accessible name, and generic labels fail
assistive tech and usability.

Per-component docs live in the "Components" section, e.g. the Button page.

### CSS-only components
Output the documented HTML with the documented classes (see each component page's
"CSS-only version"):
```html
<button class="cdx-button cdx-button--action-progressive cdx-button--weight-primary">
	Save
</button>
```

## Using icons

See the Icon docs. **Vue:** import icons from `@wikimedia/codex-icons`, render via `CdxIcon`.
Expose the icon in `setup()` (Composition API) or `data` (Options API):
```vue
<template>
	<cdx-button action="destructive">
		<cdx-icon :icon="cdxIconTrash" /> Delete this item
	</cdx-button>
</template>
<script>
import { defineComponent } from 'vue';
import { CdxButton, CdxIcon } from '@wikimedia/codex';
import { cdxIconTrash } from '@wikimedia/codex-icons';
export default defineComponent( {
	components: { CdxButton, CdxIcon },
	setup() { return { cdxIconTrash }; }
} );
</script>
```

**CSS-only:** import the tokens theme + the `css-icon` mixin, apply to a `<span>`:
```less
@import ( reference ) '@wikimedia/codex-design-tokens/theme-wikimedia-ui.less';
@import ( reference ) '@wikimedia/codex/mixins/css-icon.less';
.my-icon-class {
	&--map-pin { .cdx-mixin-css-icon( @cdx-icon-map-pin ); }
	&--trash   { .cdx-mixin-css-icon( @cdx-icon-trash, @param-is-button-icon: true ); }
}
```
```html
<span class="my-icon-class--trash"></span>
```

## Using design tokens

Import the appropriate theme file (CSS / Less / Sass). **Caveat:** several token categories are
CSS custom properties rather than raw values — use CSS `calc()` for arithmetic, not preprocessor
math like Less `unit()`.

```css
@import '@wikimedia/codex-design-tokens/theme-wikimedia-ui.css';
.my-custom-element {
	background-color: var( --background-color-interactive );
	width: calc( var( --size-icon-medium ) + 2 * var( --spacing-100 ) );
	margin-left: calc( var( --size-icon-medium ) * -1 );
	padding: var( --spacing-25 ) var( --spacing-50 );
}
```

Less: `@import ( reference ) '@wikimedia/codex-design-tokens/theme-wikimedia-ui.less';`
and use `@background-color-interactive`, `@spacing-25`, etc.
Sass: `@import '@wikimedia/codex-design-tokens/theme-wikimedia-ui.scss';`
and use `$background-color-interactive`, etc.

## Using Less mixins

Import the tokens theme first, then the mixin:
```less
@import ( reference ) '@wikimedia/codex-design-tokens/theme-wikimedia-ui.less';
@import ( reference ) '@wikimedia/codex/mixins/link.less';
.my-custom-link { .cdx-mixin-link(); }
```

## Packages

### `@wikimedia/codex`
Vue 3 components (Vue 2 NOT supported). Exports:
- Vue components named `CdxFooBar` (e.g. `CdxButton`, `CdxTextInput`)
- Composables named `useFooBar` (Composition API)
- TypeScript prop types (capitalized, e.g. `ButtonType`, `HTMLDirection`); the `Icon` type lives
  in the icons package

Files in a release (actual dist layout, verified for v2.6.x):
- `codex.cjs` (CommonJS)
- `codex.js` (ES module build)
- `codex.umd.cjs` (UMD — plain script tag or CDN; note: NOT `codex.umd.js`, that name no longer exists)
- `codex.style.css` (LTR), `codex.style-rtl.css` (RTL), plus experimental `codex.style-bidi.css`
- `messageKeys.json`
- `mixins/*.less`, `modules/` (per-component CJS/ESM chunks + CSS), `types/`

### `@wikimedia/codex-icons`
Icons + utils + types. Exports: icons `cdxIconFoo` (SVG strings/objects), utilities
`resolveIcon`, `shouldIconFlip`, and the `Icon` type. Files: `codex-icons.mjs` (ESM),
`codex-icons.js` (CJS/Node), `codex-icons.json` (all icons for non-JS, used by MediaWiki).
The package is large — always tree-shake (or otherwise minimize) what is sent to the browser.

### `@wikimedia/codex-design-tokens`
`theme-wikimedia-ui.css` (CSS variables, e.g. `--color-placeholder: #72777d`),
`.less` (e.g. `@color-placeholder`), `.scss` (e.g. `$color-placeholder`),
`.json` (detailed token data). Components use tokens internally; installing this package is only
needed for your own custom styling.

### Versioning
SemVer. Breaking changes bump the major version and are documented in `CHANGELOG.md`, always
preceded (at least one minor version before) by a deprecating change.

## Dark mode

Codex 1.5.0+ supports a dark color scheme, automatic and/or user-toggled.

**Automatic switching** — import both light and dark tokens:
```css
@import url( ./node_modules/@wikimedia/codex-design-tokens/theme-wikimedia-ui-root.css );
@import url( ./node_modules/@wikimedia/codex-design-tokens/theme-wikimedia-ui-mode-dark.css )
	only screen and ( prefers-color-scheme: dark );
```
…or as `<link>` elements with `media="( prefers-color-scheme: dark )"`.
All Codex components then switch automatically. In custom CSS, reference color tokens
(e.g. `var( --background-color-base )`) instead of hardcoding values.

## Bidirectionality

- Supported: pages entirely LTR or entirely RTL. Not supported: mixed directionality or
  runtime direction changes (except special cases).
- LTR pages: `codex.style.css`; RTL pages: `codex.style-rtl.css`.
- Experimental (v1.12+): `codex.style-bidi.css` — client-side flipping via `[dir]` selectors.
- Some components detect surrounding direction (e.g. arrow-key behavior); icons adjust too.
