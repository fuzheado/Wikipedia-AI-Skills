# Magic Words Reference

Magic words are special strings recognized by MediaWiki's parser that return wiki metadata or control page behavior. They are categorized into three types: **behavior switches**, **variables**, and **template-specific magic words**.

---

## Behavior Switches

These control page display and behavior. They are placed anywhere in the wikitext (usually on their own line).

### Table of Contents

| Word | Effect |
|------|--------|
| `__NOTOC__` | Hides the table of contents |
| `__FORCETOC__` | Forces the TOC to appear before the first heading |
| `__TOC__` | Places the TOC at this exact position in the text |

### Edits and Sections

| Word | Effect |
|------|--------|
| `__NOEDITSECTION__` | Hides the edit links next to each section heading |
| `__NEWSECTIONLINK__` | Adds a "+" tab to add a new section on talk pages |
| `__NONEWSECTIONLINK__` | Removes the "+" tab from talk pages |

### Categories and Indexing

| Word | Effect |
|------|--------|
| `__HIDDENCAT__` | Hides this category from readers (on category pages only) |
| `__EXPECTUNUSEDCATEGORY__` | Suppresses the "unused category" warning |
| `__NOGALLERY__` | On category pages, shows file links instead of thumbnail galleries |

### Search Engine Indexing

| Word | Effect |
|------|--------|
| `__INDEX__` | Allow search engines to index this page |
| `__NOINDEX__` | Prevent search engines from indexing this page |

### Page Behavior

| Word | Effect |
|------|--------|
| `__DISAMBIG__` | Marks the page as a disambiguation page (adds CSS class) |
| `__STATICREDIRECT__` | Prevents "double redirect" fix on redirect pages |

---

## Variables

Variables return page-specific or wiki-specific metadata. They use `{{VARIABLENAME}}` syntax (uppercase, no hash prefix).

### Date and Time

These reflect the **current** date/time in UTC (unless using `#timel`).

| Variable | Returns | Example |
|----------|---------|---------|
| `{{CURRENTYEAR}}` | Current year | `2026` |
| `{{CURRENTMONTH}}` | 2-digit month | `06` |
| `{{CURRENTMONTH1}}` | Month without leading zero | `6` |
| `{{CURRENTMONTHNAME}}` | Full month name | `June` |
| `{{CURRENTMONTHABBREV}}` | Abbreviated month name | `Jun` |
| `{{CURRENTDAY}}` | Day of month | `8` |
| `{{CURRENTDAY2}}` | 2-digit day | `08` |
| `{{CURRENTDOW}}` | Day of week (0=Sun, 6=Sat) | `1` |
| `{{CURRENTDAYNAME}}` | Full day name | `Monday` |
| `{{CURRENTTIME}}` | Time (HH:mm) | `14:30` |
| `{{CURRENTHOUR}}` | Hour (00–23) | `14` |
| `{{CURRENTWEEK}}` | Week number (1–53) | `24` |
| `{{CURRENTTIMESTAMP}}` | ISO timestamp (YYYYMMDDHHMMSS) | `20260608143005` |

### Page Metadata

These return information about the **current** page.

| Variable | Returns | Example |
|----------|---------|---------|
| `{{PAGENAME}}` | Page title (without namespace prefix) | `Einstein` |
| `{{PAGENAMEE}}` | URL-encoded page name | `Einstein` |
| `{{FULLPAGENAME}}` | Full page title with namespace | `Talk:Albert Einstein` |
| `{{FULLPAGENAMEE}}` | URL-encoded full title | `Talk:Albert_Einstein` |
| `{{BASEPAGENAME}}` | Base page (without subpage) | `Albert Einstein` |
| `{{BASEPAGENAMEE}}` | URL-encoded base page | `Albert_Einstein` |
| `{{SUBPAGENAME}}` | Subpage name (after last `/`) | `sandbox` |
| `{{SUBPAGENAMEE}}` | URL-encoded subpage | `sandbox` |
| `{{NAMESPACE}}` | Namespace name | `Talk` |
| `{{NAMESPACEE}}` | URL-encoded namespace | `Talk` |
| `{{NAMESPACENUMBER}}` | Namespace number | `1` |
| `{{TALKPAGENAME}}` | Full talk page title | `Talk:Albert Einstein` |
| `{{TALKPAGENAMEE}}` | URL-encoded talk page | `Talk:Albert_Einstein` |
| `{{SUBJECTPAGENAME}}` | Full article page title (opposite of talk) | `Albert Einstein` |
| `{{SUBJECTPAGENAMEE}}` | URL-encoded article page | `Albert_Einstein` |
| `{{ARTICLEPAGENAME}}` | Full article page title (same as SUBJECTPAGENAME) | `Albert Einstein` |
| `{{ARTICLEPAGENAMEE}}` | URL-encoded article page | `Albert_Einstein` |
| `{{REVISIONID}}` | Current revision ID | `123456789` |
| `{{REVISIONDAY}}` | Day of last revision | `8` |
| `{{REVISIONDAY2}}` | Day of last revision (2-digit) | `08` |
| `{{REVISIONMONTH}}` | Month of last revision | `06` |
| `{{REVISIONMONTH1}}` | Month of last revision (no leading zero) | `6` |
| `{{REVISIONYEAR}}` | Year of last revision | `2026` |
| `{{REVISIONTIMESTAMP}}` | Revision timestamp | `20260608143005` |
| `{{REVISIONUSER}}` | User of last revision | `ExampleUser` |

### Site Metadata

| Variable | Returns | Example |
|----------|---------|---------|
| `{{SITENAME}}` | Wiki site name | `Wikipedia` |
| `{{SERVER}}` | Full server URL | `https://en.wikipedia.org` |
| `{{SERVERNAME}}` | Server hostname | `en.wikipedia.org` |
| `{{SCRIPTPATH}}` | Relative script path | `/w` |
| `{{CONTENTLANGUAGE}}` | Wiki default content language | `en` |
| `{{CONTENTLANG}}` | Same as CONTENTLANGUAGE | `en` |

### Page Statistics

| Variable | Returns |
|----------|---------|
| `{{PAGESINCATEGORY:CategoryName}}` | Number of pages in a category |
| `{{PAGESINCATEGORY:CategoryName|R}}` | Raw number (no formatting) |
| `{{PAGESIZE:PageTitle}}` | Size of a page in bytes |
| `{{PAGESIZE:PageTitle|R}}` | Raw size (no formatting) |
| `{{NUMBEROFPAGES}}` | Total number of pages on the wiki |
| `{{NUMBEROFARTICLES}}` | Number of content articles |
| `{{NUMBEROFFILES}}` | Number of uploaded files |
| `{{NUMBEROFUSERS}}` | Number of registered users |
| `{{NUMBEROFACTIVEUSERS}}` | Number of active users |
| `{{NUMBEROFADMINS}}` | Number of administrators |
| `{{PAGEID}}` | Page database ID |

### Protection Information

| Variable | Returns |
|----------|---------|
| `{{PROTECTIONLEVEL:action}}` | Protection level (`autoconfirmed`, `sysop`, or empty) |
| `{{PROTECTIONEXPIRY:action}}` | Protection expiry (`infinity` or a timestamp) |
| `{{PROTECTIONLEVEL:edit}}` | Edit protection |
| `{{PROTECTIONLEVEL:move}}` | Move protection |

**Example — conditional output based on protection:**

```wikitext
{{#if: {{PROTECTIONLEVEL:edit}}
| ⚠️ This page is protected ({{PROTECTIONLEVEL:edit}} level)
| This page is unprotected
}}
```

### Language-Dependent Variables

These vary based on the wiki's content language.

| Variable | Returns (English Wikipedia) |
|----------|----------------------------|
| `{{LOCALYEAR}}` | `2026` (in wiki's local time) |
| `{{LOCALMONTH}}` | `06` |
| `{{LOCALMONTHNAME}}` | `June` |
| `{{LOCALMONTHABBREV}}` | `Jun` |
| `{{LOCALDAY}}` | `8` |
| `{{LOCALDAY2}}` | `08` |
| `{{LOCALDOW}}` | `1` |
| `{{LOCALDAYNAME}}` | `Monday` |
| `{{LOCALTIME}}` | `14:30` |
| `{{LOCALHOUR}}` | `14` |
| `{{LOCALWEEK}}` | `24` |
| `{{LOCALTIMESTAMP}}` | `20260608143005` |

---

## Template-Specific Magic Words

### In Templates

These are useful inside template code to detect context.

| Word | Effect |
|------|--------|
| `{{TALKPAGENAME}}` | Full talk page title (useful for {{Talk header}}) |
| `{{SUBJECTPAGENAME}}` | Full article page (useful for WikiProject banners on talk) |
| `{{NAMESPACE}}` | Current namespace (useful for conditionals) |
| `{{REVISIONID}}` | Revision ID — use as a cache buster in template URLs |

### In Doc Pages

| Word | Effect |
|------|--------|
| `{{BASEPAGENAME}}` | Name of the template (when on /doc subpage) |
| `{{FULLPAGENAME}}` | Full page of current doc page |
| `{{SUBPAGENAME}}` | `doc` when on the /doc subpage |

---

## Detection via API

Magic words used on a page can be detected through the Action API:

```
action=parse&page=PageTitle&prop=properties&format=json
```

The response includes `displaytitle`, `defaultsort`, `wikibase_item`, etc. However, magic words are typically understood contextually — they are processed by the parser and do not appear in the rendered output or the API's template list.

To find which magic words a page uses, examine the raw wikitext:

```
action=raw&title=PageTitle
```

Then search for `__...__` patterns (behavior switches) or `{{[A-Z_]+}}` patterns (variables) using `mwparserfromhell` or the scripts shipped with this skill.
