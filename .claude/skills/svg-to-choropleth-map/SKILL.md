---
name: svg-to-choropleth-map
description: Convert an SVG choropleth map file into Wikipedia's {{Choropleth map}} template wikitext, with entity extraction, color mapping, {{Legend}} color key generation, caption inference, and multi-language template lookup via Wikidata
license: MIT
compatibility: opencode
---

## SOP: SVG to Wikipedia `{{Choropleth map}}`

## Template Format

Parameter order comes from the template's [TemplateData](https://en.wikipedia.org/wiki/Template:Choropleth_map). Follow it exactly:

```
{{Choropleth map
| countries =
#faa: Mexico; United States; Brazil
#aaf: Italy; Spain; France
| color = #f00
| view = World
| width = 400
| height = 250
| caption = Caption text here
| legends = yes
}}
```

**Critical:** when `entities` spans multiple lines, value lines are **flush-left with no indentation**. `caption` always comes before `legends`.

Use the most semantic alias for the entities parameter: `countries`, `states`, `provinces`, or `entities`.

### Entity value types

| Prefix | Example | Meaning |
|---|---|---|
| Hex color | `#faa: Mexico` | Specific color; shorthand (`#faa`) is valid |
| Percentage | `75%: Brazil` | Proportional shading, 0–100% |
| Numeric | `400: BR` | Shading relative to the maximum value |
| _(none)_ | `Argentina` | Uses the base `color` parameter |

### Entity identifiers accepted

- ISO 3166-1 alpha-2 codes: `US`, `DE`, `FR`
- Exact Wikipedia article title, including disambiguation: `New York (state)`, `Ontario`
- Wikidata IDs: `Q183`

### Key parameters

| Parameter | Default | Notes |
|---|---|---|
| `color` | `#f00` | Base color for entities with no explicit value |
| `view` | _(world map)_ | Continent, country, city, or `auto` |
| `width` | `250` | Pixels or `full` |
| `height` | `200` | Pixels |
| `align` | `right` | `left`, `center`, `right` |
| `frameless` | — | Set to any value to remove border |
| `legends` | — | Set to `yes` for automatic gradient legend (numeric/percentage maps) |
| `caption` | — | End with `:` when labeling a numeric/percentage legend scale |
| `min-opacity` | `0` | 0–1; keeps low-value regions visible |
| `logarithmic-scale` | — | Set to `yes` for wide-range datasets |
| `source` | `ChoroplethMap.map` | Commons `.map` file override |

---

## Step 1 — Check the target Wikipedia

Ask: **"Which Wikipedia are you targeting?"** (default: English)

If not English, fetch the template's Wikidata sitelinks to find the localized template name:

```
https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q136841469&props=sitelinks&format=json
```

Convert the language code to a site ID by appending `wiki` (`fr` → `frwiki`). Check whether that key appears in the `sitelinks` object.

**If found:** use the `title` value stripped of its namespace prefix as the template name (e.g. `frwiki` → `Modèle:Carte choroplèthe` → `{{Carte choroplèthe}}`). Advise the user to verify parameter names at the target wiki, as they may differ.

**If not found:** inform the user and offer: (1) target English Wikipedia instead, (2) search `https://<lang>.wikipedia.org/w/index.php?search=choropleth` to find a template manually, or (3) use raw `<mapframe>` Kartographer markup.

Known sitelinks (always re-fetch — new ones may have been added):

| Language | Template name | Bare name |
|---|---|---|
| English (`enwiki`) | `Template:Choropleth map` | `Choropleth map` |
| French (`frwiki`) | `Modèle:Carte choroplèthe` | `Carte choroplèthe` |
| Spanish (`eswiki`) | `Plantilla:Mapa` | `Mapa` |
| Italian (`itwiki`) | `Template:Mappa coropletica` | `Mappa coropletica` |
| Portuguese (`ptwiki`) | `Predefinição:Mapa coroplético` | `Mapa coroplético` |

---

## Step 2 — Extract region data from the SVG

Read the SVG file. For each `<path>`, `<polygon>`, `<rect>`, or `<g>` element:

1. **ID** — typically the region code (`DE`, `US-CA`, `fr`)
2. **Fill color** — check in order: inline `fill="#..."` attribute → `style="fill:#..."` → `class` resolved against the `<style>` block → fill inherited from a parent `<g>`
3. **`<title>` child** — human-readable region name for disambiguation

Skip decorative elements (`id` contains `background`, `ocean`, `sea`, `lakes`, `graticule`, `frame`, `border`, `legend`, `shadow`), elements with `fill:none`, and elements with no `id`.

### Map type from ID patterns

| Pattern | Type |
|---|---|
| `DE`, `US`, `CN` | World countries (ISO 3166-1 alpha-2) |
| `US-CA`, `US-TX` | US states |
| `CA-ON`, `CA-QC` | Canadian provinces |
| `DE-BY`, `AU-NSW` | Other ISO 3166-2 subdivisions |
| Numeric | FIPS or custom — resolve via `<title>` or WebSearch |

### ID → Wikipedia entity

- ISO alpha-2 country codes: use directly
- ISO 3166-2 codes like `US-CA`: strip the country prefix → `CA`, or use the full English article title (`California`)
- Unknown IDs: use `<title>` text, or search for the Wikipedia article title

### Color → value type

- **2–6 distinct colors** (election maps, categories): use hex values directly
- **Gradient of one hue** (true choropleth): set the darkest shade to 100% and scale others by relative lightness
- **Single color**: use `color` parameter; list all regions with no value prefix

---

## Step 3 — Extract caption from SVG metadata

Check these sources in order, most specific first:

1. `<text>` / `<tspan>` elements — rendered title, year, source attribution, legend labels
2. Top-level `<title>` element (direct child of `<svg>`)
3. `dc:title` inside `<metadata>`
4. `<desc>` or `dc:description`
5. Commons file page (`https://commons.wikimedia.org/wiki/File:<filename>`) — description, author, source field, and legend tier names

Synthesize a caption: lead with the title, append year and source if present, keep under 120 characters. For numeric/percentage maps with `legends = yes`, end with a colon (e.g. `GDP per capita (in thousands of USD):`). If nothing useful is found, omit `caption` and note this to the user.

---

## Step 4 — Generate the wikitext

1. Group regions sharing a value on one line, separated by `;`
2. Sort lines highest → lowest (numeric/percentage maps)
3. Match `width`/`height` to the SVG aspect ratio (default: 400×225 world, 400×260 US, 400×300 single-country)
4. Omit parameters not needed: omit `color` when every entity has an explicit hex value; omit `legends` for categorical hex-color maps; omit `caption` if none found

Output inside a single fenced code block, with `{{Legend}}` entries embedded inside the `caption` parameter value.

### `{{Legend}}` color key

After the closing `}}` of the choropleth template, add one `{{Legend}}` line per distinct color to label what each color means:

```
{{legend|#color|Label text}}
```

- **Order:** highest/best tier first, lowest/worst last
- **`outline` parameter:** required for light colors (pale yellows, pastels, near-white) so the swatch is visible — use `outline=silver` or `outline=#A2A9B1`
- **Label text:** use tier names found in Step 3 (SVG text elements or Commons file page); if none found, ask the user
- **Single-color maps:** omit `{{Legend}}` entries entirely
- **Numeric/percentage maps:** use `legends = yes` in the template instead of `{{Legend}}` entries

Embed `{{Legend}}` entries inside the `caption` parameter — on new lines after the caption text, before the template's closing `}}`. This is the same pattern used in Wikipedia image captions:

**Example output (categorical):**
```
{{Choropleth map
| countries =
#31a354: CL; MA; IN; EE; NO; GB; PH; NL; PT; FI; DE; LU; MT
#fee391: EG; LT; CH; ES; GR; LV; ID; CO; FR; IT; HR; MX; AT; NZ; SK
#fe9929: CY; BG; IE; BR; BE; VN; SI; TH; RO; ZA; CZ; BY; TR; DZ; AR
#d7301f: JP; CN; US; HU; PL; AU; MY; TW; CA; RU; KR; KZ; SA; IR
| view = World
| width = 500
| height = 280
| caption = Countries by Climate Change Performance Index ranking (2023)
{{legend|#31a354|High}}
{{legend|#fee391|Medium|outline=silver}}
{{legend|#fe9929|Low}}
{{legend|#d7301f|Very Low}}
}}
```

After the block, note: map type detected, region count, value format used, legend labels source, and any IDs that could not be resolved.

---

## Edge cases

- **`rgb()` fill values:** convert to hex
- **External stylesheet:** cannot resolve; output fills as `none` and ask user for color data
- **`<use>` references:** resolve `href`/`xlink:href` to the original element
- **Ambiguous article titles:** always include Wikipedia disambiguation suffix (e.g. `New York (state)` not `New York`)
