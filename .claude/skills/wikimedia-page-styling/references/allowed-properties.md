# TemplateStyles Allowed CSS Properties

Complete reference of CSS properties, at-rules, and values allowed by the TemplateStyles sanitizer. Properties not listed here are silently dropped when the CSS is compiled.

## Box Model

| Property | Allowed Values | Notes |
|---|---|---|
| `width` | Any | |
| `height` | Any | |
| `min-width` | Any | |
| `max-width` | Any | |
| `min-height` | Any | |
| `max-height` | Any | |
| `padding` | Any | Shorthand |
| `padding-top` | Any | |
| `padding-right` | Any | |
| `padding-bottom` | Any | |
| `padding-left` | Any | |
| `margin` | Any | Shorthand |
| `margin-top` | Any | |
| `margin-right` | Any | |
| `margin-bottom` | Any | |
| `margin-left` | Any | |
| `box-sizing` | `border-box`, `content-box` | |

## Display & Layout (Full CSS Grid Support)

| Property | Allowed Values | Notes |
|---|---|---|
| `display` | `block`, `inline`, `inline-block`, `flex`, `inline-flex`, `grid`, `inline-grid`, `table`, `inline-table`, `table-cell`, `table-row`, `list-item`, `none`, `contents` | Full grid and flex support |
| `flex` | Any | Shorthand |
| `flex-direction` | `row`, `row-reverse`, `column`, `column-reverse` | |
| `flex-wrap` | `nowrap`, `wrap`, `wrap-reverse` | |
| `flex-flow` | Any | Shorthand |
| `flex-grow` | Numeric | |
| `flex-shrink` | Numeric | |
| `flex-basis` | Any | |
| `order` | Integer | |
| `grid` | Any | Shorthand |
| `grid-template` | Any | Shorthand |
| `grid-template-columns` | Any | `repeat()`, `minmax()`, `auto-fit`, `auto-fill`, `fr` all supported |
| `grid-template-rows` | Any | |
| `grid-template-areas` | Any | |
| `grid-column` | Any | Shorthand |
| `grid-column-start` | Any | |
| `grid-column-end` | Any | |
| `grid-row` | Any | Shorthand |
| `grid-row-start` | Any | |
| `grid-row-end` | Any | |
| `grid-area` | Any | |
| `gap` / `grid-gap` | Any | |
| `column-gap` / `grid-column-gap` | Any | |
| `row-gap` / `grid-row-gap` | Any | |
| `align-items` | `start`, `end`, `center`, `stretch`, `baseline` | |
| `align-content` | `start`, `end`, `center`, `stretch`, `space-between`, `space-around`, `space-evenly` | |
| `align-self` | `start`, `end`, `center`, `stretch`, `baseline` | |
| `justify-items` | `start`, `end`, `center`, `stretch` | |
| `justify-content` | `start`, `end`, `center`, `stretch`, `space-between`, `space-around`, `space-evenly` | |
| `justify-self` | `start`, `end`, `center`, `stretch` | |
| `place-items` | Any | Shorthand |
| `place-content` | Any | Shorthand |
| `place-self` | Any | Shorthand |

## Positioning

| Property | Allowed Values | Notes |
|---|---|---|
| `position` | `static`, `relative`, `absolute`, `fixed`, `sticky` | `fixed` and `sticky` may be flagged for review |
| `top` | Any | |
| `right` | Any | |
| `bottom` | Any | |
| `left` | Any | |
| `overflow` | `visible`, `hidden`, `scroll`, `auto`, `clip` | |
| `overflow-x` | `visible`, `hidden`, `scroll`, `auto`, `clip` | |
| `overflow-y` | `visible`, `hidden`, `scroll`, `auto`, `clip` | |
| `z-index` | Integer | |
| `float` | `left`, `right`, `none`, `inline-start`, `inline-end` | |
| `clear` | `none`, `left`, `right`, `both`, `inline-start`, `inline-end` | |

## Typography

| Property | Allowed Values | Notes |
|---|---|---|
| `font` | Any | Shorthand |
| `font-family` | Generic families + `@font-face` hosted on WMF | `sans-serif`, `serif`, `monospace`, `cursive`, `fantasy`, `system-ui` |
| `font-size` | Any | |
| `font-weight` | `normal`, `bold`, `lighter`, `bolder`, `100`…`900` | |
| `font-style` | `normal`, `italic`, `oblique` | |
| `font-variant` | Any | |
| `line-height` | Any | |
| `text-align` | `start`, `end`, `left`, `right`, `center`, `justify` | |
| `text-decoration` | Any | |
| `text-transform` | `none`, `capitalize`, `uppercase`, `lowercase` | |
| `text-overflow` | `clip`, `ellipsis` | |
| `text-shadow` | Any | |
| `letter-spacing` | Any | |
| `word-spacing` | Any | |
| `white-space` | `normal`, `nowrap`, `pre`, `pre-wrap`, `pre-line`, `break-spaces` | |
| `word-break` | `normal`, `break-all`, `keep-all`, `break-word` | |
| `overflow-wrap` | `normal`, `break-word`, `anywhere` | |
| `hyphens` | `none`, `manual`, `auto` | |
| `direction` | `ltr`, `rtl` | |
| `unicode-bidi` | `normal`, `embed`, `override`, `isolate`, `isolate-override`, `plaintext` | |
| `column-count` | Integer | |
| `column-gap` | Any | |
| `column-width` | Any | |
| `columns` | Any | Shorthand |

## Color & Background

| Property | Allowed Values | Notes |
|---|---|---|
| `color` | Any color value | |
| `background` | Any (except `url()` in images) | |
| `background-color` | Any color value | |
| `background-image` | **Gradients only** — `linear-gradient()`, `radial-gradient()`, `conic-gradient()`, `repeating-linear-gradient()`, `repeating-radial-gradient()`, `repeating-conic-gradient()` | ⚠️ `url()` is NOT allowed |
| `background-repeat` | `repeat`, `repeat-x`, `repeat-y`, `no-repeat`, `space`, `round` | |
| `background-size` | Any | |
| `background-position` | Any | |
| `background-attachment` | `scroll`, `fixed`, `local` | |
| `background-clip` | `border-box`, `padding-box`, `content-box`, `text` | |
| `background-origin` | `border-box`, `padding-box`, `content-box` | |
| `opacity` | 0.0–1.0 | |

## Border & Outline

| Property | Allowed Values | Notes |
|---|---|---|
| `border` | Any | Shorthand |
| `border-collapse` | `collapse`, `separate` | |
| `border-color` | Any color value | |
| `border-style` | `none`, `hidden`, `dotted`, `dashed`, `solid`, `double`, `groove`, `ridge`, `inset`, `outset` | |
| `border-width` | Any | |
| `border-top` / `-right` / `-bottom` / `-left` | Any | |
| Complete directional variants | All allowed | |
| `border-radius` | Any | Shorthand |
| `border-top-left-radius` | Any | |
| `border-top-right-radius` | Any | |
| `border-bottom-left-radius` | Any | |
| `border-bottom-right-radius` | Any | |
| `outline` | Any | |
| `outline-color` | Any color value | |
| `outline-style` | Same as `border-style` | |
| `outline-width` | Any | |

## Visual Effects

| Property | Allowed Values | Notes |
|---|---|---|
| `box-shadow` | Any | |
| `filter` | All filter functions | ⚠️ `url()` not allowed |
| `backdrop-filter` | All filter functions | ⚠️ `url()` not allowed |
| `transform` | All transform functions | |
| `transition` | Any | Shorthand |
| `transition-property` | Any | |
| `transition-duration` | Time values | |
| `transition-timing-function` | All timing functions | |
| `transition-delay` | Time values | |
| `animation` | Any | Shorthand |
| `animation-name` | `@keyframes` name | |
| `animation-duration` | Time values | |
| `animation-timing-function` | All timing functions | |
| `animation-delay` | Time values | |
| `animation-iteration-count` | `infinite`, numeric | |
| `animation-direction` | `normal`, `reverse`, `alternate`, `alternate-reverse` | |
| `animation-fill-mode` | `none`, `forwards`, `backwards`, `both` | |
| `animation-play-state` | `running`, `paused` | |

## Lists

| Property | Allowed Values | Notes |
|---|---|---|
| `list-style` | Any | Shorthand |
| `list-style-type` | Any | |
| `list-style-image` | Any | |
| `list-style-position` | `inside`, `outside` | |

## Tables

| Property | Allowed Values | Notes |
|---|---|---|
| `table-layout` | `auto`, `fixed` | |
| `empty-cells` | `show`, `hide` | |
| `caption-side` | `top`, `bottom` | |
| `vertical-align` | `baseline`, `sub`, `super`, `text-top`, `text-bottom`, `middle`, `top`, `bottom`, percentages | |

## Content & Counters

| Property | Allowed Values | Notes |
|---|---|---|
| `content` | Any | For `::before` / `::after` |
| `counter-increment` | Any | |
| `counter-reset` | Any | |
| `quotes` | Any | |

## UI & Interaction

| Property | Allowed Values | Notes |
|---|---|---|
| `cursor` | Standard CSS keywords only | ⚠️ `url()` not allowed |
| `visibility` | `visible`, `hidden`, `collapse` | |
| `clip` | `rect()` shape | Deprecated in favor of `clip-path` |
| `clip-path` | Any | ⚠️ `url()` not allowed |
| `pointer-events` | `auto`, `none` | |
| `resize` | `none`, `both`, `horizontal`, `vertical` | |
| `user-select` | `none`, `auto`, `text`, `contain`, `all` | |
| `caret-color` | Any color value | |

## At-Rules

| At-rule | Allowed? | Notes |
|---|---|---|
| `@media` | ✅ | All media features (width, height, resolution, prefers-color-scheme, etc.) |
| `@supports` | ✅ | Feature queries |
| `@font-face` | ✅ | `src` must be WMF-hosted URL |
| `@keyframes` | ✅ | Named animations |
| `@counter-style` | ✅ | Custom list counter styles |
| `@page` | ❌ | Not supported |
| `@import` | ❌ | Use separate `<templatestyles>` tags |
| `@namespace` | ❌ | Not supported |

## Pseudo-Classes and Pseudo-Elements

All standard CSS pseudo-classes and pseudo-elements are allowed:

```
:hover, :focus, :active, :visited, :link, :first-child,
:last-child, :nth-child(), :nth-of-type(), :not(),
:empty, :target, :disabled, :checked, :required, :valid,
:invalid, :in-range, :out-of-range, :placeholder-shown,
:read-only, :read-write, :lang(), :dir(),
::before, ::after, ::first-letter, ::first-line,
::selection, ::placeholder, ::marker
```

## Media Features for `@media`

```
width, min-width, max-width, height, min-height, max-height,
resolution, min-resolution, max-resolution,
color, monochrome, grid, scan, orientation,
prefers-color-scheme, prefers-reduced-motion,
prefers-contrast, prefers-color-scheme,
any-hover, any-pointer, hover, pointer
```

## ⚠️ Common Mistakes

| ❌ Wrong | ✅ Right | Why |
|---|---|---|
| `background-image: url('image.png')` | `background-image: linear-gradient(...)` | External image URLs blocked |
| `@import url('other.css')` | `<templatestyles src="Other/style.css" />` | `@import` not supported |
| `font-family: 'MyCustomFont'` | `font-family: 'MyCustomFont', sans-serif` + `@font-face` | Custom fonts need `@font-face` declaration |
| `cursor: url('custom.cur'), auto` | `cursor: pointer` | URL cursors blocked |
| `position: fixed` on a card | `position: relative` | `fixed` allowed but may be flagged |

> **Full source:** [mediawiki-extensions-TemplateStyles](https://github.com/wikimedia/mediawiki-extensions-TemplateStyles)
