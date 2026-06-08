# Parser Functions Reference

Parser functions are wiki-text functions that process arguments and return values. They are called with `{{#function:}}` syntax and are evaluated by MediaWiki's parser before template expansion.

---

## Conditional Functions

### `#if`

Checks whether a string is non-empty.

```
{{#if: <test string> | <then value> | <else value> }}
```

Returns:
- `then value` if the test string is non-empty (whitespace counts)
- `else value` if the test string is empty or undefined

**Common pattern for optional parameters:**

```wikitext
{{#if: {{{image|}}}
| [[File:{{{image}}}|thumb|{{{caption|}}}]]
}}
```

If `image` is not provided, the entire `#if` produces nothing (no else clause).

**Trap:** A blank parameter value `|param=` is considered **empty** for `#if`. Use `{{{param|}}}` to ensure omitted parameters also produce empty.

### `#ifeq`

Compares two strings for equality (case-sensitive).

```
{{#ifeq: <string A> | <string B> | <equal> | <not equal> }}
```

**Example:**

```wikitext
{{#ifeq: {{{type|}}} | book
| This is a book template
| This is not a book template
}}
```

**Performance:** `#ifeq` does a full string comparison. For branching on many possible values, use `#switch` instead (hash-based lookup).

### `#iferror`

Tests whether a parser expression produces an error.

```
{{#iferror: <test expression> | <error value> | <success value> }}
```

**Example:**

```wikitext
{{#iferror:
  {{#expr: {{{value|}}}/0 }}
  | Division by zero error
  | Value is {{#expr: {{{value|}}} }}
}}
```

### `#ifexpr`

Evaluates a mathematical expression and returns `true`/`false`.

```
{{#ifexpr: <expression> | <true> | <false> }}
```

**Example:**

```wikitext
{{#ifexpr: {{{population|0}}} > 1000000
| Large city
| Small town
}}
```

**Supported operators:** `+`, `-`, `*`, `/`, `^`, `mod`, `round`, `=`, `!=`, `<`, `>`, `<=`, `>=`, `and`, `or`, `not`

### `#ifexist`

Checks whether a page exists on the wiki.

```
{{#ifexist: <page title> | <exists> | <not found> }}
```

**Example:**

```wikitext
{{#ifexist: {{{article|}}}
| [[{{{article}}}]]
| {{red|Article does not exist}}
}}
```

**⚠️ Expensive:** Each `#ifexist` counts against the 500-call limit. Avoid in loops or templates transcluded on thousands of pages. Use `ask`/`SMW` or pre-fetched data when possible.

### `#switch`

Multi-way branch using hash-based lookup.

```
{{#switch: <test value>
| case1 = result1
| case2 = result2
| case3 = {{complex template}}
| #default = fallback result
}}
```

**Key features:**

- Cases are compared case-sensitively
- Multiple cases can share the same value: `| case1 | case2 = same result`
- `#default` is optional — if no match and no default, nothing is output
- `#default` can be anywhere in the list (not necessarily last)
- Case values can use `{{PAGENAME}}`, parameters, or other dynamic values

**Performance notes:**

- `#switch` with static (non-dynamic) cases is compiled into a hash table — O(1) lookup
- `#switch` with dynamic cases (containing template calls) re-evaluates each case sequentially — O(n)
- For 3+ branches, `#switch` is more efficient than nested `#ifeq`

**Example — mutual abbreviation expansion:**

```wikitext
{{#switch: {{{1|}}}
| US | USA | United States = United States
| UK | GBR | Great Britain = United Kingdom
| #default = Unknown country
}}
```

---

## Data Functions

### `#expr`

Evaluates a mathematical expression and returns the computed value.

```
{{#expr: <expression> }}
```

**Examples:**

| Code | Result |
|------|--------|
| `{{#expr: 1+1}}` | `2` |
| `{{#expr: 2^10}}` | `1024` |
| `{{#expr: 10 mod 3}}` | `1` |
| `{{#expr: 100 / 3 round 2}}` | `33.33` |
| `{{#expr: 1e6 + 1}}` | `1000001` |
| `{{#expr: floor(3.14)}}` | `3` |
| `{{#expr: ceil(3.14)}} | `4` |

**Supported operations:**

| Operator | Operation | Example |
|----------|-----------|---------|
| `+` | Addition | `1 + 2` |
| `-` | Subtraction / negation | `5 - 3` / `-1` |
| `*` | Multiplication | `2 * 3` |
| `/` | Division | `10 / 3` (returns `3.333...`) |
| `^` | Exponentiation | `2 ^ 10` |
| `mod` | Modulo | `10 mod 3` → `1` |
| `round` | Round to decimal places | `3.14159 round 2` → `3.14` |
| `abs` | Absolute value | `abs(-5)` → `5` |
| `trunc` | Truncate to integer | `trunc(3.9)` → `3` |
| `floor` | Floor | `floor(3.9)` → `3` |
| `ceil` | Ceiling | `ceil(3.9)` → `4` |
| `sin` | Sine (radians) | `sin(0)` → `0` |
| `cos` | Cosine (radians) | `cos(0)` → `1` |
| `tan` | Tangent (radians) | `tan(0)` → `0` |
| `asin` | Arc sine | `asin(1)` → `1.5708` |
| `acos` | Arc cosine | `acos(0)` → `1.5708` |
| `atan` | Arc tangent | `atan(1)` → `0.7854` |
| `ln` | Natural log | `ln(100)` → `4.605...` |
| `exp` | Exponential (e^x) | `exp(1)` → `2.718...` |

**Errors:**

- Division by zero: `{{#expr: 1/0}}` → **Error: Division by zero**
- Invalid expression: `{{#expr: hello}}` → **Error: Expression error**

### `#time`

Formats a date/time, defaulting to the current UTC time.

```
{{#time: <format> | <timestamp> | <language> }}
```

**Format codes:**

| Code | Output | Example (2026-06-08 14:30:05 UTC) |
|------|--------|-----------------------------------|
| `Y` | 4-digit year | `2026` |
| `y` | 2-digit year | `26` |
| `L` | Leap year (1 or 0) | `0` |
| `F` | Full month name | `June` |
| `M` | Abbreviated month | `Jun` |
| `m` | 2-digit month | `06` |
| `n` | Month (no leading zero) | `6` |
| `d` | 2-digit day | `08` |
| `j` | Day (no leading zero) | `8` |
| `D` | Abbreviated weekday | `Mon` |
| `l` | Full weekday | `Monday` |
| `N` | ISO weekday (1=Mon, 7=Sun) | `1` |
| `w` | Numeric weekday (0=Sun) | `1` |
| `W` | ISO week number | `24` |
| `H` | 2-digit hour (00–23) | `14` |
| `h` | 2-digit hour (01–12) | `02` |
| `i` | 2-digit minute | `30` |
| `s` | 2-digit second | `05` |
| `A` | AM/PM (uppercase) | `PM` |
| `a` | am/pm (lowercase) | `pm` |
| `g` | Hour in 12h (no leading zero) | `2` |
| `G` | Hour in 24h (no leading zero) | `14` |
| `O` | Timezone offset | `+0000` |
| `T` | Timezone abbreviation | `UTC` |
| `r` | RFC 2822 date | `Mon, 08 Jun 2026 14:30:05 +0000` |
| `c` | ISO 8601 date | `2026-06-08T14:30:05+00:00` |
| `xn` | Toggle numeric raw (format codes as-is) | — |
| `xr` | Toggle roman numerals | — |

**Timestamp formats understood by `#time`:**

| Format | Example |
|--------|---------|
| ISO 8601 | `2026-06-08T14:30:05Z` |
| SQL | `2026-06-08 14:30:05` |
| RFC 2822 | `Mon, 08 Jun 2026 14:30:05 +0000` |
| YYYYMMDD | `20260608` |
| YYYYMM | `202606` |
| YYYY | `2026` |
| UNIX timestamp | `1750000000` |

**Examples:**

```wikitext
{{#time: Y-m-d}}              → 2026-06-08
{{#time: j F Y}}              → 8 June 2026
{{#time: l, j F Y H:i}}      → Monday, 8 June 2026 14:30
{{#time: Y-m-d|{{REVISIONTIMESTAMP}}}}  → Revision date in ISO format
{{#time: M Y|-1 month}}      → May 2026 (relative)
{{#time: r|now}}              → Mon, 08 Jun 2026 14:30:05 +0000
```

**⚠️ Performance:** `#time: Y` (year only) is cached. Complex format strings are not cached.

---

## Technical Functions

### `#tag`

Generates an XML-like tag, which is useful for tags that the parser would otherwise interpret.

```
{{#tag: <tagname> | <content> | <attribute1>=<value1> | <attribute2>=<value2> }}
```

**Example — creating `<ref>` tags dynamically:**

```wikitext
{{#tag:ref
| Citation text goes here
| name=foo
| group=notes
}}
```

This produces:
```html
<ref name="foo" group="notes">Citation text goes here</ref>
```

**Why not just write `<ref>...</ref>`?** When you need the tag content to contain template calls or other parser functions, `#tag` ensures they're expanded correctly.

### `#invoke`

Calls a Lua module function.

```
{{#invoke: <Module name> | <function name> | <arg1> | <arg2> | ... }}
```

See SOP: Lua Modules in the main SKILL.md for full details.

### `#property`

Fetches a Wikidata property for the current page's item.

```
{{#property: <property ID> }}
```

**Example:**

```wikitext
{{#property: P18}}    → Image filename from Wikidata
{{#property: P569}}   → Date of birth from Wikidata
```

### `#statements`

Fetches a Wikidata property for a specific Q-item.

```
{{#statements: <property ID> | from=<Q ID> }}
```

**Example:**

```wikitext
{{#statements: P856 | from=Q937}}    → Official website for Albert Einstein
```

---

## String Functions (via `Module:String`)

These are Lua-based string operations invoked through `#invoke:String`.

```wikitext
{{#invoke:String|len|<target string>}}
{{#invoke:String|sub|<target>|<start index>|<end index>}}
{{#invoke:String|match|<target>|<pattern>|<start>|<match number>|<plain flag>|<nomatch>}}
{{#invoke:String|find|<target>|<search string>|<start>|<plain flag>}}
{{#invoke:String|replace|<target>|<old>|<new>|<number of replacements>|<plain flag>}}
{{#invoke:String|trim|<target string>}}
{{#invoke:String|split|<target>|<delimiter>}}
```

**Examples:**

```wikitext
{{#invoke:String|len|Hello}}              → 5
{{#invoke:String|sub|Hello|2|4}}           → ell
{{#invoke:String|match|abc123def|%d+}}     → 123
{{#invoke:String|replace|Hello, world!|Hello|Goodbye}} → Goodbye, world!
{{#invoke:String|trim|  hello  }}          → hello
```

---

## Performance Summary

| Function | Cost | Best Practice |
|----------|------|---------------|
| `#if` | Low | Use for simple empty/non-empty checks |
| `#ifeq` | Medium | Use `#switch` for 3+ branches |
| `#switch` (static) | Low (hash) | Preferred for multi-way branching |
| `#switch` (dynamic) | Medium-High | Avoid dynamic case values |
| `#ifexpr` | Medium | Precompute when possible |
| `#ifexist` | **High** | Limit to ≤10 per page |
| `#expr` | Medium | Precompute or use static values |
| `#time` | Low-Medium | Simple formats are cached |
| `#invoke` (Lua) | Low-Medium | Well-written Lua is faster than wikitext |
| `#tag` | Low | Same as writing raw tags |
| `#property` | **High** | Cached but involves a DB query |
| `#statements` | **High** | Same as #property, for a specific Q-item |

---

## Common Pitfalls

1. **Whitespace in `#if`** — a space is considered non-empty: `{{#if: | yes | no}}` returns `no`, but `{{#if:  | yes | no}}` (with a space) returns `yes`.
2. **`#ifeq` is case-sensitive** — `{{#ifeq: A | a | same | different}}` returns `different`.
3. **`#switch` default position** — `#default` can appear anywhere, but only one is used per switch block.
4. **`#expr` integer precision** — `#expr` uses 64-bit floating-point. Very large integers may lose precision.
5. **`#time` with negative timestamps** — Dates before 1970-01-01 may not work correctly on all wikis.
6. **`#ifexist` caching** — Results are cached for 30 seconds on most wikis; repeated checks within that window are free.
7. **Nested parser functions** — Deep nesting (40+ levels) will fail with a parser depth error.
