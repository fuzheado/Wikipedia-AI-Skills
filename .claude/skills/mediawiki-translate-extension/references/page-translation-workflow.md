# Page Translation Workflow Guide

Step-by-step guide for the complete translation workflow using the Translate extension.

---

## For Content Authors

### Step 1: Write Your Content

Write the page normally, with one important addition: **wrap translatable content** in `<translate>...</translate>` tags.

```wikitext
<languages />
{{Project/Navigation}}

<translate>
== Introduction == <!--T:1-->
Welcome to our project. This page describes our activities.

== Our Mission == <!--T:2-->
We promote open access to cultural heritage.
</translate>

[[Category:Project]]
```

### Step 2: Add `<languages />`

Place `<languages />` at the **very top** of the page. This shows the language selector bar.

### Step 3: Add Translation Unit Markers

Add `<!--T:N-->` markers after each paragraph, heading, or list item that should be a separate translation unit:

```wikitext
<translate>
== Section 1 == <!--T:1-->
First paragraph content. <!--T:2-->

Second paragraph of content. <!--T:3-->

== Section 2 == <!--T:4-->
More content here. <!--T:5-->
</translate>
```

**Note:** You can skip the manual markers — the system will auto-generate them when the page is marked for translation. But manual markers give you explicit control over unit boundaries.

### Step 4: Use `<tvar>` for Dynamic Content

Wrap numbers, URLs, magic words, and template calls in `<tvar>`:

```wikitext
<translate><!--T:10-->
Our project has <tvar name="members">{{PAGESINCATEGORY:Members}}</tvar> members.
Visit <tvar name="website">https://example.org</tvar> for details.
</translate>
```

### Step 5: Use `Special:MyLanguage/` for Links

All internal links should use `Special:MyLanguage/`:

```wikitext
<translate><!--T:20-->
Learn more about [[Special:MyLanguage/Project/Activities|our activities]].
</translate>
```

### Step 6: Request Translation Marking

Ask a translation administrator to mark the page for translation. On Meta, you can:
- Add the page to a tracking list
- Ask at the appropriate noticeboard
- Contact a translation admin directly

---

## For Translation Administrators

### Step 1: Mark the Page for Translation

Go to `Special:PageTranslation` and enter the page title.

### Step 2: Review the Translation Units

The system will parse the `<translate>` tags and show each translation unit:

```
Page: Project/Our page

Units to be added:
  [1] "Introduction" (heading)
  [2] "Welcome to our project. This page describes our activities."
  [3] "Our Mission" (heading)
  [4] "We promote open access to cultural heritage."
```

Review each unit:
- Are the unit boundaries correct?
- Are `<tvar>` variables properly defined?
- Are there any units that should be merged or split?

### Step 3: Approve the Page

Enable the page for translation. This creates the language subpage structure and makes the page available on `Special:Translate`.

### Step 4: Monitor Translations

Check `Special:Translate` periodically:
- Which translations are complete?
- Which are outdated (fuzzy)?
- Are there any validation issues?

### Step 5: Handle Source Updates

When the source page changes:
1. Edit the source page
2. The affected translation units are automatically marked as **fuzzy** (outdated)
3. Translators see the fuzzy units highlighted in `Special:Translate`
4. They update their translations
5. Review and accept the updated translations

---

## For Translators

### Step 1: Find Pages to Translate

Go to `Special:Translate` on the wiki:
- Select a **message group** (the page you want to translate)
- Select your **target language**
- Click "Translate"

### Step 2: Translate Each Unit

The translation interface shows:
- **Source text** — the original language text
- **Translation field** — where you type the translation
- **Translation suggestions** — from translation memory if available
- **Previous translations** — for consistency

### Step 3: Handle `<tvar>` Variables

`<tvar>` variables appear as `$variablename` in the translation interface. Keep them exactly as-is — do not translate them.

```
Source: "Visit $website for details."
Good translation (Finnish): "Käy $website saadaksesi lisätietoja."
Bad translation: "Käy verkkosivulla."  ← $website removed!
```

### Step 4: Handle Links

Links using `Special:MyLanguage/` should link to the **translated** version of the target page. Translate the link display text normally:

```
Source: "Learn more about [[Special:MyLanguage/Project/Activities|our activities]]"
Finnish: "Lue lisää [[Special:MyLanguage/Project/Activities|toiminnastamme]]"
```

### Step 5: Save and Continue

- Save each unit after translating
- The system tracks your progress
- Units can be revisited later

### Step 6: Review Fuzzy (Outdated) Units

When the source page is updated:
- The affected units are marked **fuzzy** (highlighted in orange)
- Review the changes in the source text
- Update your translation to match
- Save to mark it as up-to-date again

---

## Maintenance: When Source Content Changes

### What Happens

1. Author edits a translation unit on the base page
2. The system detects the change
3. That unit is **automatically marked as fuzzy** for ALL translations
4. Translators see the fuzzy unit in their translation queue

### Best Practices

- **Batch changes** when possible — don't make tiny edits that trigger many fuzzy updates
- **Inform translators** when making significant content changes
- **Review fuzzy units promptly** — stale translations can confuse readers
- Use the **translation diff view** to see exactly what changed

### Preventing Unnecessary Fuzzy Updates

- Fixing a typo in English: This should still trigger a fuzzy update (the translation might need adjustment)
- Changing a `<tvar>` variable name: This always triggers fuzzy — use descriptive variable names to minimize changes
- Restructuring paragraphs: This may create new units — old translations remain but unit boundaries change

---

## Translation Memory

### What It Is

The Translate extension stores **all completed translations** in a searchable database. When translating similar text, the system suggests previous translations as starting points.

### Match Levels

| Match | Meaning | Icon |
|---|---|---|
| 100% (exact) | Identical text already translated | ✅ |
| 75-99% (fuzzy match) | Similar text with minor differences | 🔵 |
| 0-74% | Low confidence | Not shown |

### Benefits

- Consistent translations across pages
- Reduced translation time for repetitive content
- Automatic suggestions for common phrases
- Cross-page consistency for project terminology

---

## Quality Assurance

### Validation Checks

The system automatically validates translations for:

| Check | What It Catches |
|---|---|
| **Missing variables** | Translation omitted a `$tvar` |
| **Unbalanced tags** | HTML tags not properly closed |
| **Too long / too short** | Translation length differs significantly from source |
| **Empty translation** | Unit saved with no content |

### Review Process

Translations can be marked as **reviewed** by a second translator or reviewer. Reviewed translations are shown with a "verified" badge.

### Pre-Translation

For high-match units (>70% in translation memory), administrators can **pre-translate** — automatically fill in suggested translations for review.
