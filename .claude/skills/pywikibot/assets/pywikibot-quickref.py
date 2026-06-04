#!/usr/bin/env python3
"""
Pywikibot Quick Reference — copy-paste snippets for the most common tasks.

Usage:
    pip install pywikibot
    # Create user-config.py first (see SKILL.md)
    python pywikibot-quickref.py

Or import individual functions into your own scripts.
"""

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot


# ──────────────────────────────────────────────
# 1. CONNECTING TO SITES
# ──────────────────────────────────────────────

def connect_sites():
    """Return common site objects."""
    enwiki = pywikibot.Site('en', 'wikipedia')
    wikidata = pywikibot.Site('wikidata', 'wikidata')
    commons = pywikibot.Site('commons', 'commons')
    return enwiki, wikidata, commons


# ──────────────────────────────────────────────
# 2. READING PAGES
# ──────────────────────────────────────────────

def read_page():
    site = pywikibot.Site('en', 'wikipedia')
    page = pywikibot.Page(site, 'Albert Einstein')

    print('Title:', page.title())
    print('Namespace:', page.namespace())
    print('Exists:', page.exists())
    print('Is redirect:', page.isRedirectPage())
    print('Is talk page:', page.isTalkPage())
    print('Latest rev:', page.latestRevision())
    print('Creator:', page.getCreator())

    # Plain text (first 500 chars)
    print('Text (truncated):', page.text[:500])


# ──────────────────────────────────────────────
# 3. EDITING PAGES
# ──────────────────────────────────────────────

def edit_page():
    site = pywikibot.Site('en', 'wikipedia')
    page = pywikibot.Page(site, 'Wikipedia:Sandbox')
    page.text = page.text + '\n<!-- Bot test edit -->'
    page.save('Bot: test edit')  # edit summary


# ──────────────────────────────────────────────
# 4. PAGE GENERATORS
# ──────────────────────────────────────────────

def page_generators():
    """Demonstrate various page generators."""
    site = pywikibot.Site('en', 'wikipedia')

    # Pages in a category
    gen = site.categorypages('Physics', recurse=False)
    for i, page in enumerate(gen):
        if i >= 5:
            break
        print(f'Category member: {page.title()}')

    # Pages linking to a page
    gen = site.pagebacklinks('Albert Einstein', namespaces=[0])
    for i, page in enumerate(gen):
        if i >= 5:
            break
        print(f'Backlink: {page.title()}')

    # Search results
    gen = site.search('quantum mechanics', total=5)
    for page in gen:
        print(f'Search hit: {page.title()}')

    # Using the GeneratorFactory (for CLI-style composition)
    factory = pagegenerators.GeneratorFactory()
    factory.handle_args(['-cat:Physics', '-namespace:0'])
    gen = factory.getCombinedGenerator()
    if gen:
        for i, page in enumerate(gen):
            if i >= 3:
                break
            print(f'Composite: {page.title()}')


# ──────────────────────────────────────────────
# 5. CATEGORIES
# ──────────────────────────────────────────────

def work_with_categories():
    site = pywikibot.Site('en', 'wikipedia')
    cat = pywikibot.Category(site, 'Category:Physics')

    print(f'Category: {cat.title()}')
    print(f'Category info: {cat.categoryinfo}')

    # List articles
    for article in cat.articles(total=3):
        print(f'  Article: {article.title()}')

    # List subcategories
    for subcat in cat.subcategories(total=3):
        print(f'  Subcat: {subcat.title()}')

    # Move all pages from one category to another
    target = pywikibot.Category(site, 'Category:Physics topics')
    for page in cat.articles():
        page.change_category(cat, target, comment='Bot: recategorizing')
        break  # remove this in real usage!


# ──────────────────────────────────────────────
# 6. USER CONTRIBUTIONS AND ACTIONS
# ──────────────────────────────────────────────

def work_with_users():
    site = pywikibot.Site('en', 'wikipedia')
    user = pywikibot.User(site, 'ExampleUser')

    print(f'Edit count: {user.editCount()}')
    print(f'Registration: {user.registrationTime()}')

    for contrib in user.contributions(total=5):
        print(f'  Edit: {contrib["title"]} @ {contrib["timestamp"]}')


# ──────────────────────────────────────────────
# 7. WIKIDATA — READ ITEMS
# ──────────────────────────────────────────────

def read_wikidata():
    repo = pywikibot.Site('wikidata', 'wikidata')
    item = pywikibot.ItemPage(repo, 'Q937')  # Albert Einstein
    data = item.get()

    print('Labels:', data['labels'])
    print('Descriptions:', data['descriptions'])
    print('Sitelinks:')
    for site_id, link in data['sitelinks'].items():
        print(f'  {site_id}: {link.title}')

    print('Claims:')
    for prop_id, claims in data['claims'].items():
        for claim in claims:
            target = claim.getTarget()
            print(f'  {prop_id}: {target}')


# ──────────────────────────────────────────────
# 8. WIKIDATA — EDIT ITEMS
# ──────────────────────────────────────────────

def edit_wikidata():
    """Add a claim (occupation → physicist) to an item."""
    repo = pywikibot.Site('wikidata', 'wikidata')
    item = pywikibot.ItemPage(repo, 'Q937')

    # Create claim: occupation (P106) = physicist (Q169470)
    claim = pywikibot.Claim(repo, 'P106')
    target = pywikibot.ItemPage(repo, 'Q169470')
    claim.setTarget(target)

    # Add to item
    item.addClaim(claim)

    # Add a qualifier: start time (P580)
    qualifier = pywikibot.Claim(repo, 'P580')
    qualifier.setTarget(pywikibot.WbTime(year=1905))
    claim.addQualifier(qualifier)

    print(f'Added claim {claim} to {item}')


# ──────────────────────────────────────────────
# 9. COMMONS — FILE OPERATIONS
# ──────────────────────────────────────────────

def commons_file_ops():
    commons = pywikibot.Site('commons', 'commons')
    fp = pywikibot.FilePage(commons, 'File:Example.jpg')

    print('Url:', fp.fileUrl)
    print('Size:', fp.getImageSize())

    # Download
    fp.download('local_copy.jpg')

    # Upload
    uploader = commons.upload(
        'local.jpg',
        description='== Summary ==\nTest upload\n== Licensing ==\n{{self|cc-by-sa-4.0}}',
        comment='Bot: upload test'
    )
    print(f'Upload result: {uploader}')


# ──────────────────────────────────────────────
# 10. BOT FRAMEWORK — CUSTOM BOT
# ──────────────────────────────────────────────

class AppendTextBot(ExistingPageBot):
    """Append a line to every page from the generator."""

    update_options = {
        'text': '',       # text to append
        'summary': 'Bot: appending text',
    }

    def treat_page(self):
        self.current_page.text += '\n' + self.opt.text
        self.put_current(summary=self.opt.summary)


def run_bot():
    """Run the custom bot on pages from Category:Physics."""
    site = pywikibot.Site('en', 'wikipedia')
    gen = site.categorypages('Physics')
    bot = AppendTextBot(
        generator=gen,
        text='[[Category:Physics stubs]]',
        summary='Bot: adding stub category')
    bot.run()


# ──────────────────────────────────────────────
# 11. REVISION HISTORY
# ──────────────────────────────────────────────

def read_history():
    site = pywikibot.Site('en', 'wikipedia')
    page = pywikibot.Page(site, 'Albert Einstein')

    for rev in page.revisions(total=5):
        print(f'  r{rev["revid"]} by {rev["user"]} @ {rev["timestamp"]}')
        print(f'    Comment: {rev["comment"]}')


# ──────────────────────────────────────────────
# 12. DIFFS
# ──────────────────────────────────────────────

def compare_revisions():
    site = pywikibot.Site('en', 'wikipedia')

    # Compare two specific revisions
    diff = site.compare(oldid=123456789, diffid=123456790)
    print('Diff body:', diff[:500])  # raw HTML diff


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == '__main__':
    print("Pywikibot Quick Reference\n")
    print("-" * 50)
    print("Reading a page...")
    read_page()
    print("\nPage generators...")
    page_generators()
    print("\nCategories...")
    work_with_categories()
    print("\nWikidata...")
    read_wikidata()
    print("\nHistory...")
    read_history()
    print("\nDone.")
