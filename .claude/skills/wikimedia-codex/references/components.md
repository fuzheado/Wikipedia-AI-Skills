# Components

Condensed from `codex-docs/docs/components/overview.md` (canonical).

Components are the interactive building blocks of the design system. Two types:

1. **Vue 3 components** — fully interactive, require Vue 3 and JavaScript.
2. **CSS-only components** — styles with suggested markup (e.g. the CSS-only Button) or a Less
   mixin (e.g. Link). Most Vue components have a corresponding CSS-only version and can be used
   without JavaScript.

Each component has a demo page with working examples, copyable code samples, and detailed usage
info for both the Vue and CSS-only implementations.

## Using components

- **Figma**: use the Codex Figma library to reuse components in design files.
- **npm**: see `references/developing.md` (installation + using components).
- **MediaWiki**:
  - Vue components: https://www.mediawiki.org/wiki/Codex#Usage_with_JavaScript
  - CSS-only: https://www.mediawiki.org/wiki/Codex#Usage_without_JavaScript_(CSS-only_Codex_components)

## Component roadmap

Planned components: https://www.mediawiki.org/wiki/Codex/Planned_Components

## Local component/demo inventory

Component demo sources live in `codex-source/packages/codex-docs/component-demos/<component>/`
(an `examples/` subfolder per component). Component Vue sources live in
`codex-source/packages/codex/src/components/<component>/`.

Vue components (as of the local checkout):
accordion, button, button-group, card, checkbox, chip-input, combobox, dialog, field, icon,
image, info-chip, input-chip, label, lookup, menu, menu-button, menu-item, message,
multiselect-lookup, popover, progress-bar, progress-indicator, radio, search-input,
search-result-title, select, tab, table, tabs, text-area, text-input, thumbnail, toast,
toggle-button, toggle-button-group, toggle-switch, tooltip, typeahead-search.

Components with docs demos (as of the local checkout):
accordion, breadcrumb, button, button-group, card, checkbox, chip-input, combobox, container,
dialog, field, icon, image, info-chip, label, lookup, menu, menu-button, menu-item, message,
multiselect-lookup, popover, progress-bar, progress-indicator, radio, search-input, select, tab,
table, tabs, text-area, text-input, thumbnail, toast, toggle-button, toggle-button-group,
toggle-switch, tooltip, typeahead-search.

Directives: `v-tooltip`. Mixins: `link`. See `docs/components/directives/tooltip.md` and
`docs/components/mixins/link.md`.
