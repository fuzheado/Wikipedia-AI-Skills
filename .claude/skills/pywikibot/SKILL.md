---
name: pywikibot
description: Use Pywikibot — the Python library and CLI tool suite for automating work on MediaWiki sites (Wikipedia, Wikidata, Commons, and any other MediaWiki wiki). Covers installation, configuration, the core object model, page generators, the bot framework, built-in scripts, and Wikidata/Commons integration
license: MIT
compatibility: opencode
---

> ⚠️ **User-Agent required:** Pywikibot sets `User-Agent` automatically based on your `user-config.py` settings, but any direct `curl`/`requests` calls in this skill still need a proper header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for format and rate-limiting patterns. Before writing custom code alongside Pywikibot, load that skill for the required User-Agent boilerplate.

---

## Table of Contents

1. [What Pywikibot Is](#what-pywikibot-is)
2. [Where It Fits in the API Universe](#where-it-fits-in-the-api-universe)
3. [Installation & Setup](#installation--setup)
4. [Core Object Model](#core-object-model)
5. [Page Generators — The Superpower](#page-generators--the-superpower)
6. [Bot Framework](#bot-framework)
7. [Key Built-in Scripts Catalog](#key-built-in-scripts-catalog)
8. [Wikidata & Wikibase Integration](#wikidata--wikibase-integration)
9. [Commons / File Uploads](#commons--file-uploads)
10. [Running on Toolforge & PAWS](#running-on-toolforge--paws)
11. [One-of-a-Kind Capabilities](#one-of-a-kind-capabilities)
12. [When NOT to Use Pywikibot](#when-not-to-use-pywikibot)
13. [Security & Bot Credentials](#security--bot-credentials)
14. [Troubleshooting & FAQ](#troubleshooting--faq)
15. [Reference Links](#reference-links)

---

## What Pywikibot Is

Pywikibot is a **Python library and collection of ready-to-run CLI scripts** that automates work on MediaWiki sites. It started in 2003 and is at version **11.3+** (MIT license). It wraps the MediaWiki Action API (`api.php`) into a high-level Python object model so you work with `Page`, `Site`, `ItemPage`, `Category`, `User` objects instead of raw HTTP/JSON.

It is the **de-facto standard bot framework** for the Wikimedia ecosystem — used on Wikipedia, Wikidata, Commons, Wiktionary, and thousands of third-party MediaWiki wikis.

### Three-Layer Architecture

```
User Code (your script or custom bot)
    ↓  Page / User / Category / ItemPage objects
Pywikibot Library
    ├── site     — Site objects (connection, auth, per-wiki config)
    ├── page     — Page, FilePage, Category, User, ItemPage, PropertyPage, LexemePage
    ├── pagegenerators — 40+ generator types (cat, links, search, transclude, ...)
    ├── bot      — Bot class hierarchy (BaseBot → ExistingPageBot → CurrentPageBot)
    ├── textlib  — Wikitext parsing (section splitting, template extraction, category links)
    ├── cosmetic_changes — Auto-fix wikitext formatting (whitespace, HTML, deprecated syntax)
    ├── data.api — Low-level API request wrapper with auto-retry + continuation
    ├── diff     — Delta computation helpers
    └── i18n     — Internationalization support
        ↓
MediaWiki Action API (api.php) — query | edit | parse | upload | delete | move | protect
```

---

## Where It Fits in the API Universe

Pywikibot is **not** an alternative to the other skills — it is a **meta-layer** that consumes the Action API and provides a framework on top of it. Many tasks that could be done with raw API calls are much easier with Pywikibot.

| Layer | Tools / Skills | Best For |
|---|---|---|
| **REST APIs** (v1) | [`wikimedia-api-access`](../wikimedia-api-access/SKILL.md) | Single-page reads, quick GET requests |
| **Action API** (`api.php`) | [`wikimedia-api-access`](../wikimedia-api-access/SKILL.md), [`wikimedia-diffs`](../wikimedia-diffs/SKILL.md), [`wikipedia-edit-history`](../wikipedia-edit-history/SKILL.md) | Low-level queries, diffs, edit history |
| **SPARQL** (Wikidata Query Service) | [`wikidata`](../wikidata/SKILL.md) | Complex graph queries, aggregations, joins |
| **SQL replicas** (Toolforge DB) | [`wikimedia-database`](../wikimedia-database/SKILL.md) | Deep analytics, JOINs across wiki metadata |
| **Pywikibot** | ⬅️ **This skill** | Full bot lifecycle: edit pages, run mass operations, scrape templates into Wikidata, archive talk pages, move categories, write custom bots |

### API Coverage (Action → Method Mapping)

| API Action | Pywikibot Method |
|---|---|
| `action=edit` | `Page.save()`, `Page.put()`, `Page.touch()` |
| `action=query` | `Site.pagegenerators`, `Site.allpages()`, `Site.search()` |
| `action=delete` | `Page.delete()` |
| `action=move` | `Page.move()` |
| `action=protect` | `Page.protect()` |
| `action=upload` | `Site.upload()`, `FilePage.upload()` |
| `action=parse` | `Page.get_parsed_page()`, `Site.expand_text()` |
| `action=rollback` | `Page.rollback()` |
| `action=watch` | `Page.watch()` |
| `action=block` | `User.block()` |
| `action=emailuser` | `User.send_email()` |
| `action=compare` | `Site.compare()` |
| `action=mergehistory` | `Page.merge_history()` |
| `action=purge` | `Page.purge()` |
| `action=thank` | `Site.thank_revision()` |

> Full cross-reference table: [doc.wikimedia.org/pywikibot/stable/mwapi.html](https://doc.wikimedia.org/pywikibot/stable/mwapi.html)

---

## Installation & Setup

### Method 1: pip (library-only, no built-in scripts)

```bash
pip install pywikibot
```

This gives you the library. You **must** create `user-config.py` manually (see below). The ready-to-run scripts (`archivebot`, `replace`, etc.) are **not** included in this mode.

### Method 2: Repository (full installation with scripts)

```bash
git clone https://gerrit.wikimedia.org/r/pywikibot/core.git
cd core
git submodule update --init
pip install -r requirements.txt
```

This gives you the `pwb.py` wrapper and all built-in scripts.

### user-config.py

Create a file named `user-config.py` in your working directory (or home directory if using pip mode):

```python
# user-config.py — minimal example
mylang = 'en'
family = 'wikipedia'
usernames['wikipedia']['en'] = 'MyBotUsername'
```

For multiple wikis:

```python
mylang = 'en'
family = 'wikipedia'
usernames['wikipedia']['en'] = 'MyBot'
usernames['wikidata']['wikidata'] = 'MyBot'
usernames['commons']['commons'] = 'MyBot'

# Optional: rate limiting
put_throttle = 1      # seconds between saves
max_retries = 5
retry_wait = 30       # seconds

# User-Agent identifier (used for all HTTP requests)
user_agent_description = 'MyBot/1.0 (my@email.com)'
```

Or use the interactive setup script:

```bash
python pwb.py generate_user_files
```

### Quick Test

```python
import pywikibot
site = pywikibot.Site('en', 'wikipedia')
page = pywikibot.Page(site, 'Wikipedia:Sandbox')
print(page.text[:500])
```

---

## Core Object Model

### Site — a wiki connection

```python
# Wikimedia site (auto-detects the wiki family)
site = pywikibot.Site('en', 'wikipedia')

# Wikidata
repo = pywikibot.Site('wikidata', 'wikidata')

# Commons
commons = pywikibot.Site('commons', 'commons')

# Any custom MediaWiki
custom = pywikibot.Site('en', 'mywiki')  # needs a family file
```

### Page — a wiki article

```python
page = pywikibot.Page(site, 'Albert Einstein')

# Read
print(page.text)                  # raw wikitext
print(page.title())               # full title with namespace
print(page.namespace())           # namespace object
print(page.exists())              # bool
print(page.isRedirectPage())      # bool
print(page.toggleTalkPage())      # get the talk page

# Edit
page.text = page.text.replace('foo', 'bar')
page.save('Bot: fixing typo')     # edit summary

# Move / delete / protect
page.move('New Title', 'reason')
page.delete('deletion reason')
page.protect(edit='sysop', move='sysop', reason='protection reason')

# History & meta
for rev in page.revisions(total=5):
    print(rev['user'], rev['timestamp'], rev['comment'])
print(page.getCreator())
print(page.getLatestRevisionId())
```

### Category — category pages

```python
cat = pywikibot.Category(site, 'Category:Physics')
for article in cat.articles():   # pages in this category
    print(article.title())
for subcat in cat.subcategories():  # subcategories
    print(subcat.title())

# All members of a category recursively
for page in cat.articles(recurse=True):
    ...
```

### User — user pages and contributions

```python
user = pywikibot.User(site, 'ExampleUser')
print(user.editCount())
print(user.registrationTime())
for contrib in user.contributions(total=10):
    print(contrib['title'], contrib['timestamp'])

# Admin actions
user.block(reason='vandalism', expiry='24 hours')
user.unblock(reason='appeal granted')

# Email
user.send_email(subject='Greetings', text='Hello!')
```

### FilePage — image/file pages

```python
fp = pywikibot.FilePage(commons, 'File:Example.jpg')
print(fp.fileUrl)                     # direct download URL
print(fp.getImageSize())              # (width, height)
print(fp.getFileVersionHistory())     # list of versions
fp.download('local.jpg')              # save locally

# Upload
fp.upload('source.jpg', comment='Uploading', file_key='...')
```

### Link — internal / interwiki links

```python
from pywikibot import Link
link = Link('Albert Einstein', site)
print(link.title)          # 'Albert Einstein'
print(link.namespace)      # Namespace:Main
print(link.site)           # Site object
```

---

## Page Generators — The Superpower

This is the single most powerful abstraction in Pywikibot. A generator is an iterable that yields `Page` objects, composable with command-line options. You can chain them to build complex page lists.

### 40+ Generator Types (all usable via CLI flags too)

| CLI Flag | Generator | Example |
|---|---|---|
| `-cat:` | Pages in a category | `-cat:Physics` |
| `-catr:` | Pages in category + subcategories | `-catr:Physics` |
| `-links:` | Pages linking to a page | `-links:"Albert Einstein"` |
| `-transcludes:` | Pages that use a template | `-transcludes:"Infobox person"` |
| `-search:` | Full-text search results | `-search:"quantum mechanics"` |
| `-subcats:` | Subcategories of a category | `-subcats:Physics` |
| `-filelinks:` | Pages using a file | `-filelinks:Example.jpg` |
| `-newimages:` | Recently uploaded files | `-newimages:50` |
| `-random:` | Random pages | `-random:10` |
| `-recentchanges:` | Recent changes | `-recentchanges:100` |
| `-page:` | Single page by name | `-page:"Albert Einstein"` |
| `-pageid:` | Single page by ID | `-pageid:12345` |
| `-namespace:` | Filter by namespace | `-namespace:0` (main) |
| `-unusedfiles:` | Unused files | `-unusedfiles` |
| `-uncatfiles:` | Uncategorized files | `-uncatfiles` |
| `-uncatcat:` | Uncategorized categories | `-uncatcat` |
| `-watchlist:` | Current user's watchlist | `-watchlist` |
| `-logevents:` | Log events (move, delete, etc.) | `-logevents:move` |
| `-liverecentchanges:` | Live RC feed | `-liverecentchanges` |
| `-xml:` | From a dump file | `-xml:dump.xml` |
| `-imageused:` | Pages using an image | `-imageused:Example.jpg` |
| `-newpages:` | Newly created pages | `-newpages:50` |
| `-interwiki:` | Same page on other language wikis | `-interwiki` |

### Usage in Code

```python
from pywikibot import pagegenerators

site = pywikibot.Site('en', 'wikipedia')

# Generator: pages in a category (recursive)
gen = site.categorizedpages('Physics', recurse=True)

# Generator: pages linking to a specific page
gen = site.pagebacklinks('Albert Einstein', namespaces=[0])

# Generator: search results
gen = site.search('quantum mechanics', namespaces=[0])

# Generator factory from CLI args
gen_factory = pagegenerators.GeneratorFactory()
gen_factory.handle_args(['-cat:Physics', '-namespace:0'])
gen = gen_factory.getCombinedGenerator()
for page in gen:
    print(page.title())
```

### Chaining + Filters

```python
# All main-namespace pages in Category:Physics and subcats that link to Einstein
gen = site.categorizedpages('Physics', recurse=True)
gen = site.pagebacklinks('Albert Einstein', namespaces=[0])
# Intersect them:
gen = pagegenerators.IntersectPageGenerator(gen1, gen2)

# Or use the CLI composability:
# python pwb.py replace -catr:Physics -links:"Albert Einstein" ...
```

---

## Bot Framework

Pywikibot provides a class hierarchy so you only write the per-page logic:

```
BaseBot
  └── ExistingPageBot   (iterates, calls treat_page for each)
       └── CurrentPageBot (also provides current_page attribute)
  └── ConfigParserBot    (reads options from .ini file)
```

### Minimal Custom Bot

```python
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot

class MyBot(ExistingPageBot):

    update_options = {
        'text': 'Appending this line',
        'summary': 'Bot: appending text'
    }

    def treat_page(self):
        """Called once per page."""
        self.current_page.text += '\n' + self.opt.text
        self.put_current(summary=self.opt.summary)

def main():
    options = {}
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = pywikibot.handle_args()         # global options
    local_args = gen_factory.handle_args(local_args)  # generator options
    for arg in local_args:
        opt, sep, value = arg.partition(':')
        if opt in ('-summary', '-text'):
            options[opt[1:]] = value

    bot = MyBot(generator=gen_factory.getCombinedGenerator(), **options)
    bot.run()

if __name__ == '__main__':
    main()
```

### Running It

```bash
python mybot.py -cat:Physics -summary:"Bot test" -text:"Hello"
```

The bot framework handles:
- Page iteration from any generator
- Save throttling (`put_throttle`)
- Edit conflict detection and retry
- User confirmation prompts (`-always` to skip)
- Logging and error handling
- Dry-run mode (`-simulate`)

---

## Key Built-in Scripts Catalog

Scripts are available only in **repository mode** (git clone). They are run via `python pwb.py <scriptname>`.

### Category Scripts

| Script | What It Does | One-Liner |
|---|---|---|
| `category_redirect` | Move pages out of redirected categories, fix double redirects, log manual cases | `pwb.py category_redirect -cat:"Category:Redirects"` |
| `category_graph` | Visualize category hierarchy as DOT/SVG/HTML | `pwb.py category_graph -from Physics -depth 3` |
| `commonscat` | Add `{{commonscat}}` to categories by following interwiki links | `pwb.py commonscat -start:Category:!` |

### Template Scripts

| Script | What It Does | One-Liner |
|---|---|---|
| `template` | Replace/substitute/remove templates across pages | `pwb.py template "OldTemplate" "NewTemplate" -namespace:0` |
| `templatecount` | Count/list pages transcluding one or more templates | `pwb.py templatecount -count -namespace:0 ref note` |

### General Page Scripts

| Script | What It Does | One-Liner |
|---|---|---|
| `archivebot` | Archive old discussion threads from talk pages | `pwb.py archivebot` |
| `replace` | Find-and-replace text across many pages | `pwb.py replace -cat:Physics "old" "new"` |
| `add_text` | Append/prepend text to pages | `pwb.py add_text -cat:Physics -text:"{{stub}}"` |
| `redirect` | Fix double redirects or delete broken ones | `pwb.py redirect double` |
| `disambredir` | Fix redirects to disambiguation pages | `pwb.py disambredir -cat:Disambiguation` |
| `patrol` | Mark recent changes as patrolled | `pwb.py patrol -page:RecentChanges` |

### Image/File Scripts

| Script | What It Does | One-Liner |
|---|---|---|
| `checkimages` | Audit recently uploaded files for description problems | `pwb.py checkimages -limit:50` |
| `commons_information` | Add language templates to file descriptions on Commons | `pwb.py commons_information -start:File:!` |
| `image_transfer` | Transfer images between wikis (e.g. to Commons) | `pwb.py image_transfer -from:en -to:commons` |

### Admin Scripts

| Script | What It Does | One-Liner |
|---|---|---|
| `delete` | Mass delete or undelete pages | `pwb.py delete -cat:"Category:To delete" -always` |
| `blockpageschecker` | Remove stale protection templates from unprotected pages | `pwb.py blockpageschecker -always` |

### Non-Editing Scripts

| Script | What It Does | One-Liner |
|---|---|---|
| `listpages` | List pages matching a generator, with format options | `pwb.py listpages -cat:Physics -format:"{page.title}"` |
| `pagefromfile` | Create pages from a text file | `pwb.py pagefromfile -file:newpages.txt` |
| `touch` | Touch pages (null-edit to update caches) | `pwb.py touch -cat:Physics` |

### Utility Scripts

| Script | What It Does |
|---|---|
| `generate_user_files` | Interactive `user-config.py` generator |
| `shell` | Interactive Python shell with Pywikibot pre-loaded |
| `version` | Print Pywikibot version and dependency info |
| `login` | Authenticate (store cookies) |

---

## Wikidata & Wikibase Integration

This is where Pywikibot has **no real competitor** — no other tool offers this depth of structured data manipulation.

### Core Classes

| Class | Purpose |
|---|---|
| `pywikibot.ItemPage` | A Wikidata item (Q937 = Einstein) |
| `pywikibot.PropertyPage` | A Wikidata property (P106 = occupation) |
| `pywikibot.Claim` | A statement (item + property + value) |
| `pywikibot.LexemePage` | A Wikibase Lexeme (L-ID) |
| `pywikibot.LexemeForm` | A form within a Lexeme |
| `pywikibot.LexemeSense` | A sense within a Lexeme |
| `pywikibot.SiteLink` | A sitelink object (page on a specific wiki) |

### Reading Items

```python
repo = pywikibot.Site('wikidata', 'wikidata')
item = pywikibot.ItemPage(repo, 'Q937')

# Get all data
data = item.get()  # dict with labels, descriptions, claims, sitelinks

# Labels (multilingual)
print(item.labels)       # {'en': 'Albert Einstein', 'de': 'Albert Einstein', ...}

# Claims
for prop_id, claims in data['claims'].items():
    for claim in claims:
        print(f"{prop_id}: {claim.getTarget()}")

# Sitelinks
for site_id, sitelink in data['sitelinks'].items():
    print(f"{site_id}: {sitelink.title}")
```

### Editing Items

```python
# Add a label
item.editLabels({'en': 'Albert Einstein', 'de': 'Albert Einstein'})

# Add a description
item.editDescriptions({'en': 'German-born theoretical physicist'})

# Add a claim
claim = pywikibot.Claim(repo, 'P106')  # occupation
target = pywikibot.ItemPage(repo, 'Q169470')  # physicist
claim.setTarget(target)
item.addClaim(claim)

# Add a qualifier
qualifier = pywikibot.Claim(repo, 'P580')  # start time
qualifier.setTarget(pywikibot.WbTime(year=1905))
claim.addQualifier(qualifier)

# Add a source
source = pywikibot.Claim(repo, 'P854')  # reference URL
source.setTarget('https://example.com/source')
claim.addSource(source)
```

### Scripts for Wikidata

| Script | What It Does |
|---|---|
| `harvest_template` | Scrape template parameters from wikitext → Wikidata claims. **Uniquely powerful** — maps infobox fields to P-IDs, handles links, multiple values, inverse claims, and cross-wiki harvesting. |
| `claimit` | Add claims in bulk from a list of property→value pairs. Supports geo-coordinates, string values, item values. |
| `illustrate_wikidata` | Add images to Wikidata items from Wikipedia page images (PageImages extension). |
| `merge_items` | Merge duplicate Wikidata items. |
| `interwikidata` | Manage interwiki links through Wikidata. |

### harvest_template — The Killer Feature

This script reads template parameters from Wikipedia articles and writes them as structured Wikidata claims. Example:

```bash
# Scrape "image" param from "Infobox person" on enwiki → Wikidata P18
pwb.py harvest_template \
    -site:wikipedia:en \
    -namespace:0 \
    -template:"Infobox person" \
    image P18

# With multiple fields and inverse claims
pwb.py harvest_template \
    -site:wikipedia:en \
    -template:"Infobox musical artist" \
    current_members P527 \
    -exists:p -multi
```

---

## Commons / File Uploads

```python
from pywikibot import FilePage, Site

commons = Site('commons', 'commons')

# Get file info
fp = FilePage(commons, 'File:Example.jpg')
print(fp.fileUrl)
print(fp.getFileVersionHistory())
fp.download('local.jpg')

# Upload
uploader = commons.upload('local.jpg',
    description='== Summary==\nDescription here\n==Licensing==\n{{self|cc-by-sa-4.0}}',
    comment='Uploading via bot')
```

### Image Transfer Script

```python
# Transfer from enwiki to Commons
pwb.py image_transfer -from:en -to:commons \
    -cat:"Category:Images" \
    -description:"My description" \
    -always
```

---

## Running on Toolforge & PAWS

### Toolforge (Kubernetes)

Pywikibot is pre-installed on Toolforge. See the **[wikimedia-toolforge](../wikimedia-toolforge/SKILL.md)** skill for detailed setup.

```bash
# On a Toolforge tool
ssh <toolname>@login.toolforge.org
become <toolname>

# Create a virtualenv with Pywikibot
python3 -m venv venv
source venv/bin/activate
pip install pywikibot

# Or use the system-wide installation
source /data/project/shared/pywikibot/venv/bin/activate
```

### PAWS (Jupyter Notebooks)

PAWS is the easiest way to try Pywikibot — no installation needed:

1. Go to [paws.wmflabs.org](https://paws.wmflabs.org)
2. Start a new Python 3 notebook
3. `!pip install pywikibot` or use the pre-installed version
4. Authenticate interactively with `pywikibot.Site().login()`

---

## One-of-a-Kind Capabilities

These are tasks that are **extremely difficult or impractical** with any other approach (raw API calls, SPARQL, or SQL):

### ★★★★★ Template-to-Wikidata Harvesting

The `harvest_template` script reads wikitext templates (infoboxes) and writes structured Wikidata claims. It handles:
- Multiple values from multi-valued template parameters
- Link detection (`-islink`: auto-link plain text)
- Inverse claims (`-inverse:P910` — if A has property X pointing to B, also set property Y on B pointing to A)
- Exists-checking (`-exists:ptq` — only add if target/source/qualifier don't match)
- Cross-wiki harvesting (same template on different language Wikipedias → same Wikidata item)

**No other tool can do this.** Raw API calls would require reimplementing template parsing, link resolution, claim deduplication, and cross-wiki coordination.

### ★★★★★ Mass Category Redirect Fixing

The `category_redirect` script finds redirected categories, moves all member pages, fixes double redirects, converts hard→soft redirects, and logs cases that need manual attention. It respects a cooldown period (default 7 days) to avoid edit-warring.

### ★★★★★ Talk Page Archiving

The `archivebot` script parses timestamps in talk page threads, identifies old discussions, moves them to subpages with configurable thresholds, and increments archive counters. Configuration is done entirely via a transcluded template (no CLI flags needed). Variables like `%(counter)d` and `%(page)s` allow dynamic archive page names.

### ★★★★★ Template Substitution / Removal Across Entire Wikis

The `template` script can `-subst` (replace `{{Foo}}` with `{{subst:Foo}}`) or `-remove` templates across millions of pages. The substitution-aware mode (`-assubst`) combines both operations. Process-by-user filters let you restrict to pages edited by a given user within a time window.

### ★★★★★ Cross-Wiki Batch Operations

The `interwiki` generator yields pages across all language versions simultaneously. Combined with any script, this lets you fix interwiki spam or update templates on 300+ Wikipedias from a single command.

### ★★★★★ Geo-Coordinate Claims from Template Data

The `claimit` script accepts decimal coordinates directly:
```bash
pwb.py claimit [generators] P625 -23.3991,-52.0910,0.0001
```
This is otherwise very fiddly with raw API calls (requires coordinate precision handling).

### ★★★★★ Wikitext Cosmetic Cleanup

The `cosmetic_changes` module automatically fixes:
- HTML-style `<br>` → `<br />` and similar
- Deprecated `<center>` → `<div style="text-align: center;">`
- Missing whitespace around headings
- Obsolete self-closing tags
- Double-hyphen → em-dash where appropriate

Running `replace -cosmeticchanges` across a wiki applies these fixes automatically.

### ★★★★★ Batch Image Transfer to Commons

The `image_transfer` script handles the full pipeline: download from source wiki, check license compatibility, build description page with attribution history, upload to Commons. This is a multi-step, multi-API process that Pywikibot coordinates end-to-end.

---

## When NOT to Use Pywikibot

| Scenario | Better Approach |
|---|---|
| **Read a single page** | `curl` + REST API v1 (~2 lines vs Pywikibot's import + site setup) |
| **Simple SPARQL query** | Wikidata Query Service directly (SPARQL is cleaner than Pywikibot's `SPARQLQuery`) |
| **High-concurrency scraping** | Raw `aiohttp` + async (Pywikibot is synchronous/blocking) |
| **Real-time event stream** | EventStreams API (Server-Sent Events, not Pywikibot) |
| **JOIN-heavy analytics** | Toolforge SQL replicas (`wikimedia-database` skill) |
| **One-shot data extraction** | `python3 -c "import requests; print(requests.get(...).json())"` |
| **Non-Python environment** | Direct Action API calls from any language |
| **Minimal serverless function** | REST API v1 (no auth needed for reads, tiny dependency) |
| **Just re-upload one file** | UploadWizard or direct API upload |

**Rule of thumb:** If your task touches fewer than 50 pages and involves no edits, use a lighter tool. If you need to edit 500+ pages, scrape templates into Wikidata, or run a recurring maintenance bot, Pywikibot is the right choice.

---

## Security & Bot Credentials

### Bot Passwords (Recommended for Bots)

1. Go to `Special:BotPasswords` on the wiki
2. Create a bot password with only the permissions you need
3. In `user-config.py`:

```python
usernames['wikipedia']['en'] = 'MyBot'
authenticate['en.wikipedia.org'] = ('MyBot@BotName', 'password_generated_by_special_botpasswords')
```

### OAuth (for tools hosted on Toolforge)

```python
# user-config.py
authenticate['en.wikipedia.org'] = (
    consumer_token,
    consumer_secret,
    access_token,
    access_secret
)
```

### OAuth 2.0 (Pywikibot 9.0+)

```python
# user-config.py
authenticate['*.wikipedia.org'] = (
    'oauth2_client_id',
    'oauth2_client_secret',
    'oauth2_access_token'
)
```

### Never Hardcode Credentials

- Use environment variables or a separate `secrets.py` (gitignored)
- On Toolforge, use `$HOME/.pywikibot/user-config.py` with restrictive permissions (`chmod 600`)
- Bot passwords expire — monitor and rotate them

---

## Troubleshooting & FAQ

### "No module named 'pywikibot'"
Make sure you installed it: `pip install pywikibot`. If using the repository, run `pip install -r requirements.txt`.

### "Script not found" when running `pwb.py scriptname`
Scripts are only available in repository mode. Run from the `core/` directory. Or use `python -m pywikibot.scripts.<scriptname>` from pip mode if the script supports it.

### Login fails / "Not logged in"
- Check `user-config.py` for correct username and family
- Bot passwords must match the format `Username@BotName`
- Some wikis require OAuth — check wiki's bot policy
- Run `python pwb.py login` explicitly to test authentication

### ⚠️ MediaWiki API username quirk: spaces → underscores

The MediaWiki `action=login` API requires the **internal database form** of usernames,
where spaces are stored as underscores (`_`). The `lgname` parameter will fail if you
pass a username with literal spaces (e.g., `"AL Wiki MIT"`), even though that's how
the username displays on wiki pages and in the `Special:BotPasswords` confirmation message.

**Always normalize** usernames by replacing spaces with underscores before passing
them to `lgname` (or let Pywikibot handle it — it does this internally via `Site.login()`).

If you're calling the Action API directly:
```python
lgname = "AL_Wiki_MIT"       # ✓ Works
lgname = "AL Wiki MIT"       # ✗ Fails with "Unknown error"
```

Pywikibot handles this automatically in most cases, but if you're writing raw API
calls or a custom auth flow, remember to normalize the username.

### Rate limiting / 429 errors
Adjust in `user-config.py`:
```python
put_throttle = 2        # wait 2 seconds between saves
max_retries = 10
retry_wait = 60
```

### Edit conflicts / "Page was changed while editing"
Pywikibot detects `badtimestamp` errors and retries automatically by re-fetching the page. You can also call `page.save()` with `force=True` to skip the check (use with caution).

### Cross-wiki: "Unknown family"
Add a family file or use the built-in families. Common families: `wikipedia`, `wikidata`, `commons`, `wiktionary`, `wikisource`, `wikiquote`, `wikivoyage`, `wikinews`, `wikiversity`, `mediawiki`.

### "The module pywikibot is not installed" in pip mode
Scripts are excluded from pip installs. Use library mode: write your own script importing `pywikibot` directly. Alternatively, use `pip install pywikibot[scripts]` where available.

---

## Reference Links

| Resource | URL |
|---|---|
| Official documentation | [doc.wikimedia.org/pywikibot/stable/](https://doc.wikimedia.org/pywikibot/stable/) |
| API reference (all modules) | [doc.wikimedia.org/pywikibot/stable/api_ref/index.html](https://doc.wikimedia.org/pywikibot/stable/api_ref/index.html) |
| MediaWiki API cross-reference | [doc.wikimedia.org/pywikibot/stable/mwapi.html](https://doc.wikimedia.org/pywikibot/stable/mwapi.html) |
| MW Manual: Pywikibot | [mediawiki.org/wiki/Manual:Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot) |
| MW Manual: Cookbook | [mediawiki.org/wiki/Manual:Pywikibot/Cookbook](https://www.mediawiki.org/wiki/Manual:Pywikibot/Cookbook) |
| Source code (Gerrit) | [gerrit.wikimedia.org/r/pywikibot/core](https://gerrit.wikimedia.org/r/pywikibot/core) |
| GitHub mirror | [github.com/wikimedia/pywikibot](https://github.com/wikimedia/pywikibot) |
| PyPI package | [pypi.org/project/pywikibot/](https://pypi.org/project/pywikibot/) |
| Change log | [doc.wikimedia.org/pywikibot/stable/changelog.html](https://doc.wikimedia.org/pywikibot/stable/changelog.html) |
| PAWS (online notebook) | [paws.wmflabs.org](https://paws.wmflabs.org) |
| Toolforge | [toolforge.org](https://toolforge.org) |
| Bot passwords | `Special:BotPasswords` on any Wikimedia wiki |
| User-Agent policy | [foundation.wikimedia.org/wiki/Policy:User-Agent](https://foundation.wikimedia.org/wiki/Policy:User-Agent) |
| Skill: Toolforge | [wikimedia-toolforge](../wikimedia-toolforge/SKILL.md) |
| Skill: API access | [wikimedia-api-access](../wikimedia-api-access/SKILL.md) |
| Skill: Wikidata | [wikidata](../wikidata/SKILL.md) |
| Skill: Wikitext | [wikimedia-wikitext](../wikimedia-wikitext/SKILL.md) |
