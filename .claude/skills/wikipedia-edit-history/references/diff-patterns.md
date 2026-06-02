# Diff Patterns Reference

Common patterns to look for when examining Wikipedia diffs. Understanding
the type of change helps determine whether it's constructive, problematic,
or neutral.

## Patterns by Byte Change

### Small Change (1–200 bytes)
Most common. Usually constructive.

| Pattern | Typical Summary | What to Look For |
|---------|-----------------|------------------|
| **Copyedit** | `copyedit`, `fix typo`, `ce` | Small word changes, punctuation fixes, grammatical corrections |
| **Wikilink fix** | `fix link`, `bypass redirect` | `[[Page]]` → `[[New page]]`, or adding/removing a link |
| **Formatting** | `fmt`, `format` | Whitespace changes, heading levels, list formatting |
| **Clarification** | `clarify`, `rewrite` | A sentence reworded for clarity without changing meaning |

### Medium Change (200–2,000 bytes)
Still common. Often constructive, but warrants a quick scan.

| Pattern | Typical Summary | What to Look For |
|---------|-----------------|------------------|
| **Add citation** | `+ref`, `add ref`, `cite` | A `<ref>` tag and citation template added to support a claim |
| **Add paragraph** | `add section`, `expand` | A new paragraph adding relevant content |
| **Update stats** | `update`, `as of 2026` | Numerical data updated (population, election results, etc.) |
| **Minor addition** | `add detail`, `more context` | A few sentences of additional information |

### Large Change (2,000–20,000 bytes)
Less common. Needs careful review.

| Pattern | Typical Summary | What to Look For |
|---------|-----------------|------------------|
| **New section** | `add section on X` | A substantial new section added |
| **Rewrite subsection** | `rewrite`, `restructure` | An existing section replaced with new content |
| **Add infobox** | `add infobox` | An infobox template and parameters added |
| **Add references** | `add refs`, `+sources` | Multiple citations added at once |
| **Cleanup** | `cleanup`, `rm unsourced` | Content removed because it's unsourced |

### Very Large Change (20,000+ bytes)
Rare. Usually significant.

| Pattern | Typical Summary | Red Flags |
|---------|-----------------|-----------|
| **New article** | `create page` | Check for copyright violations if from a new user |
| **Major overhaul** | `major rewrite` | Large-scale restructuring — check talk page for consensus |
| **Content dump** | (often no summary) | Large paste from external source — possible copyright issue |
| **Page blanking** | `blank`, `rm content` | If size drops to near zero, likely vandalism |

## Patterns by Visual Signature

### Content Addition (constructive)
```
Line removed from old
Line removed from old
Line removed from old
                         ← new content inserted here
Line unchanged
Line unchanged
```

**Signs of health:** relevant citations included, proper formatting, consistent with article tone.

### Content Removal (constructive)
```
Line unchanged
Line unchanged
                         ← content removed here
Line removed from old
Line removed from old
```

**Signs of health:** edit summary explains removal (e.g., "rm unsourced BLP violation"), content is genuinely problematic (unsourced, promotional, off-topic).

### Content Removal (problematic — possible vandalism)
```
Line unchanged
                         ← large block removed
                         ← without explanation
Line unchanged
```

**Red flags:** No edit summary, large removal from a new/anonymous user, removal of well-sourced content, removal of BLP content.

### Revert
```
Line A
Line B           ← User 1 adds content
Line C

Line A           ← User 2 reverts: same lines as before
Line B
Line C
```

**How to detect:** The diff shows the old version being restored nearly identically. The edit summary contains "rv", "Reverted", "Undid". The reverting user is different from the reverted user.

### Edit War
```
Rev 1: Alice adds "X"
Rev 2: Bob removes "X"    (rv)
Rev 3: Alice adds "X"     (undo)
Rev 4: Bob removes "X"    (rv)
Rev 5: Alice adds "X"     (undo)
```

**Pattern:** The same content alternates between present and absent, with the same two users trading reversions. Each reversion has a short summary ("rv", "undo").

**Watch for:** 3RR violation if more than 3 reverts by one user in 24 hours.

### Page Blanking (vandalism)
```
Before: 25,000 bytes of content
After:  50 bytes

"asdf" or "deleted"
```

**Red flags:** Size drops dramatically (often to <100 bytes). Edit summary is empty or nonsense. User is anonymous or new.

### New User Creating Article (copyright risk)
```
Before: 0 bytes (page doesn't exist)
After:  30,000 bytes of dense text

No edit summary or "create page"
```

**Red flags:** User has few or no other edits. Text is unusually polished. No citation templates (bare URLs or no refs).

## Patterns by Edit Summary Keywords

| Summary Contains | Likely Change |
|-----------------|---------------|
| `rv`, `revert`, `Reverted`, `undid` | Revert — look at what was removed |
| `/* */` (section link) | Section-specific edit — the section name tells you the scope |
| `copyedit`, `ce`, `fix typo`, `fmt` | Minor formatting/grammar — low risk |
| `add ref`, `+ref`, `cite` | Citation added — usually positive |
| `rm`, `remove`, `delete` | Content removed — check for vandalism vs. legitimate cleanup |
| `update`, `as of`, `2026` | Data update — check if numbers match the cited source |
| `/* top */` | Lead section edit — significant changes here affect the article summary |
| `BOT`, `bot` | Bot edit — usually safe but worth spot-checking |
| `[[:en:`, `translate` | Translation from another language — check quality |
| (empty) | No context given — inspect the diff to understand |

## Detecting Automated/Low-Quality Edits

| Signal | What to Check |
|--------|---------------|
| `possible vandalism` tag | Abuse filter flagged it — review carefully |
| `mobile edit`, `mobile web edit` | Made from a phone — not inherently bad, but often lower quality |
| `visual editor` | Used the visual editor — check for formatting issues (extra blank lines, broken templates) |
| `mw-reverted` tag | This edit was later undone by someone else — find out why |
| Bot flag | Bot account — generally reliable, but watch for malfunctioning bots |
| Consecutive edits by same user | User may be building an article incrementally (good) or edit-counting (bad) |
