# Category Naming Conventions

Condensed from **[Wikipedia:Category names](https://en.wikipedia.org/wiki/Wikipedia:Category_names)**.
Use this reference when creating, evaluating, or renaming categories.

---

## General Rules

1. **Article naming conventions apply** — use the name from verifiable reliable
   sources, not a made-up name
2. **Neutral** — avoid subjective adjectives (famous, large, beautiful)
3. **No abbreviations** — "Military equipment of World War II", not "WW2"
   (except for acronyms that *are* the name: NATO, UNESCO)
4. **Singular for topic categories** — `Category:France`, `Category:Opera`
5. **Plural for set categories** — `Category:Cities in France`, `Category:Operas`
6. **Disambiguation** — if the main article uses a disambiguated title, the
   eponymous category uses the same disambiguation:
   - Article: `Washington (state)` → Category: `Category:Washington (state)`
   - Subcategory: `Category:Washington (state) legislative districts`

---

## Topic vs. Set Categories

| | Topic Category | Set Category |
|---|---|---|
| Form | Singular | Plural |
| Contains | Everything *about* the topic | Things that *are* the class |
| Example | `Category:Opera` | `Category:Operas` |
| Members | Opera (article), History of opera, Opera houses | The Magic Flute, Carmen |
| Template | (none) | `{{Set category}}` |

**When both exist:** Be careful which one to use. An article about a specific
opera goes in the *set category* (`Category:Operas`), not the *topic category*
(`Category:Opera`). The topic category is for articles *about* opera as a
subject.

---

## Eponymous Categories

An eponymous category is named after an article's title:

| Article | Eponymous category |
|---|---|
| Albert Einstein | Category:Albert Einstein |
| New York City | Category:New York City |
| Mekong | Category:Mekong River |

Rules:
- The category name should match the article title (or a close variant)
- Only create if enough directly related pages/subcategories exist
- The category should have only the article's categories that are relevant
  to the category's *content*, not all of the article's categories
- The article itself goes in the eponymous category

---

## Disambiguation in Category Names

When a category name needs disambiguation, use the same parenthetical as the
main article:

| Article | Category |
|---|---|
| Mercury (element) | Category:Mercury (element) |
| Mercury (planet) | Category:Mercury (planet) |
| Mercury (mythology) | Category:Mercury (mythology) |

Subcategories should generally use the same disambiguation as their parent:

```
Category:Washington (state)
  └─ Category:Washington (state) legislative districts
```

Even if the subcategory name would not be ambiguous on its own.

---

## What NOT to Do

| ❌ Avoid | Why | ✅ Instead |
|---|---|---|
| `Category:Famous physicists` | Subjective adjective | `Category:Physicists` |
| `Category:WW2 equipment` | Abbreviation | `Category:World War II military equipment` |
| `Category:Physics stuff` | Vague, informal | `Category:Physics` |
| `Category:People named Smith` | Shared name, not defining | Disambiguation page |
| `Category:Tall buildings in Chicago` | Subjective ("tall") | `Category:Skyscrapers in Chicago` |
| `Category:Beautiful paintings` | Subjective ("beautiful") | `Category:Paintings` (or a specific genre/period) |

---

## Stub Categories

Stub categories follow their own naming conventions under
Wikipedia:WikiProject Stub sorting. Generally:

- Named as `Category:Topic stubs` or `Category:Topic-class stubs`
- Must be a subcategory of `Category:Stub categories`
- Created via the stub template, not manually

---

## Namespace Precedence

Categories should generally NOT duplicate what's already captured by
namespace:

- Template categories go in `Category:Template namespace` subcategories
- File categories go in `Category:File namespace` subcategories
- A page's namespace is already reflected in the URL and search filters

The exception is when the namespace alone is not specific enough — e.g.,
`Category:Wikipedia essays` is more specific than "Wikipedia namespace".
