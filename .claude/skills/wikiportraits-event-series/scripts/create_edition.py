#!/usr/bin/env python3
"""Create a Commons year category and a Wikidata edition item for a recurring event.

Example:
  python create_edition.py --event "Crossing Europe" --year 2027 \\
      --series Q1141279 --edition-type Q27787439 --location Q41329 --country Q40 \\
      --edition-no 23 \\
      --parents "2027 film festivals" "2027 events in Linz" \\
      --desc "annual film festival held in Linz, Austria, since 2004" \\
      --prev Q140965123 --next Q140965125 --dry

The navbox `decade` defaults to `--year // 10` (200 for 2027); override with
`--decade` only when the event series uses an unusual decade bucket.

Dates: pass `--date YYYY-MM-DD` for a one-day event (sets P585 to the exact
date, day precision) or `--start YYYY-MM-DD --end YYYY-MM-DD` for a multi-day
event (sets P580/P582 at day precision and keeps P585 at year precision, like
Q61654036). With neither, P585 falls back to the year.

Existing categories and items are detected and skipped (reruns are safe).
When --prev and/or --next are given, the neighboring items are updated
(P156 on the previous edition, P155 on the next edition) so the P155/P156
chain stays consistent both ways.

Chain-safety rule: --prev/--next must be the *directly consecutive* editions
(nothing held in between). If a run of held editions is not yet modeled, do
NOT pass --prev/--next across the gap - leave the chain open instead. The
script prints a warning when the year gap to --prev/--next is > 1, but it is
your responsibility to confirm the editions really are adjacent.

Run from inside a pywikibot checkout with user-config.py configured for the
'commons' and 'wikidata' sites.
"""

import argparse
import re
import sys
import time
from datetime import date as _date

import pywikibot


def robust(fn, *args, retries=5, base_delay=20, **kwargs):
    """Retry an edit, typically because of Wikidata replication lag (maxlag)."""
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except pywikibot.exceptions.OtherPageSaveError as exc:
            if attempt == retries - 1:
                raise
            print(f'   retry {attempt + 1} after: {str(exc)[:120]}')
            time.sleep(base_delay * (attempt + 1))


def make_claim(repo, pid, target):
    c = pywikibot.Claim(repo, pid)
    c.setTarget(target)
    return c


def parse_date(s):
    """Parse 'YYYY-MM-DD' (zero-padded) into (year, month, day)."""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s or ''):
        raise SystemExit(f'date must be YYYY-MM-DD (zero-padded), got: {s!r}')
    year, month, day = (int(x) for x in s.split('-'))
    try:
        _date(year, month, day)
    except ValueError:
        raise SystemExit(f'date out of range: {s!r}')
    return year, month, day


def claims_of(item):
    try:
        return item.claims
    except Exception:
        return {}


def desc_of(item):
    try:
        return item.descriptions
    except Exception:
        return {}


def sitelinks_of(item):
    try:
        return item.sitelinks
    except Exception:
        return {}


def add_claim_if_missing(item, repo, pid, target, summary, dry):
    """Add a claim unless an identical one exists. target is an ItemPage,
    a str, or a WbTime."""
    for c in claims_of(item).get(pid, []):
        t = c.getTarget()
        if t is None:
            continue
        if isinstance(target, str):
            if str(t) == target:
                return
        elif hasattr(target, 'year'):  # WbTime
            if getattr(t, 'year', None) == target.year:
                return
        elif getattr(t, 'getID', lambda: None)() == target.getID():
            return
    if dry:
        if isinstance(target, str):
            show = target
        elif hasattr(target, 'year'):
            show = target.year
        else:
            show = target.getID()
        print(f'   would add {pid} -> {show}')
        return
    robust(item.addClaim, make_claim(repo, pid, target), summary=summary)
    print(f'   added {pid} -> {getattr(target, "year", target)}')


def find_item_for_category(commons, repo, cat_title):
    """Return the ItemPage linked to a Commons category, or None."""
    page = pywikibot.Page(commons, cat_title)
    try:
        item = pywikibot.ItemPage.fromPage(page)
        item.get()
        return item
    except Exception:
        pass
    try:
        data = repo.simple_request(action='wbgetentities', sites='commonswiki',
                                   titles=cat_title, props='info').submit()
        for qid, ent in data.get('entities', {}).items():
            if not ent.get('missing'):
                item = pywikibot.ItemPage(repo, qid)
                item.get()
                return item
    except Exception:
        pass
    return None


def ensure_sitelink(item, commons, cat_title, dry):
    if cat_title in sitelinks_of(item):
        return
    if dry:
        print(f'   would set sitelink commonswiki -> {cat_title}')
        return
    robust(item.setSitelink, pywikibot.SiteLink(cat_title, site=commons),
           summary='Link Commons category')
    print('   set sitelink')


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--event', required=True, help='event name, e.g. "Crossing Europe"')
    ap.add_argument('--year', required=True, type=int)
    ap.add_argument('--series', required=True, help='QID of the event/series item')
    ap.add_argument('--edition-type', required=True,
                    help='QID of the edition class, e.g. Q27787439')
    ap.add_argument('--location', required=True, help='QID of the city, e.g. Q41329')
    ap.add_argument('--country', required=True, help='QID of the country, e.g. Q40')
    ap.add_argument('--edition-no', required=True, type=int,
                    help='ordinal edition number (P393)')
    ap.add_argument('--decade', type=int, default=None,
                    help='decade for the navbox (first 3 digits of the year); '
                         'default = year//10, e.g. 200 for the 2020s')
    ap.add_argument('--date', default=None, metavar='YYYY-MM-DD',
                    help='exact date of a one-day event (P585 day precision); '
                         'mutually exclusive with --start/--end')
    ap.add_argument('--start', default=None, metavar='YYYY-MM-DD',
                    help='start date of a multi-day event (P580 day precision)')
    ap.add_argument('--end', default=None, metavar='YYYY-MM-DD',
                    help='end date of a multi-day event (P582 day precision)')
    ap.add_argument('--parents', nargs='*', default=[],
                    help='extra parent categories, e.g. "2027 film festivals"')
    ap.add_argument('--desc', default=None,
                    help='English description; default "film festival edition"')
    ap.add_argument('--prev', default=None, help='QID of the previous edition item')
    ap.add_argument('--next', default=None, help='QID of the next edition item')
    ap.add_argument('--put-throttle', type=float, default=2.0)
    ap.add_argument('--dry', action='store_true', help='preview without editing')
    args = ap.parse_args()

    if args.decade is None:
        args.decade = args.year // 10  # 199 for 1996, 200 for 2006, 202 for 2027

    if args.date and (args.start or args.end):
        raise SystemExit('--date is mutually exclusive with --start/--end')
    if bool(args.start) != bool(args.end):
        raise SystemExit('--start and --end must be given together')

    date_parts = None    # one-day event: (y, m, d) for P585 day precision
    start_parts = None   # multi-day event: (y, m, d) for P580
    end_parts = None     # multi-day event: (y, m, d) for P582
    if args.date:
        date_parts = parse_date(args.date)
    elif args.start:
        start_parts = parse_date(args.start)
        end_parts = parse_date(args.end)
        if start_parts > end_parts:
            raise SystemExit(f'--start {args.start} is after --end {args.end}')

    pywikibot.config.put_throttle = args.put_throttle

    commons = pywikibot.Site('commons', 'commons')
    repo = pywikibot.Site('wikidata', 'wikidata')
    if not args.dry:
        commons.login()
        repo.login()

    label = f'{args.event} {args.year}'
    cat_title = f'Category:{label}'
    desc = args.desc or 'film festival edition'

    # --- 1. Commons year category -----------------------------------------
    page = pywikibot.Page(commons, cat_title)
    if page.exists():
        print(f'skip category (exists): {cat_title}')
    else:
        text = '{{Wikidata Infobox}}\n'
        # Navbox: omit |padding= (an empty padding suppresses the template's
        # default space separator, and a trailing space in cat_prefix would be
        # trimmed by MediaWiki - either leaves titles like "<Event>2007" and
        # #ifexist hides every year link). displayredlinks=no hides years that
        # have no category yet.
        text += (f'{{{{Decade years navbox\n|header={{{{C|{args.event}}}}}\n'
                 f'|decade={args.decade}\n|cat_prefix={args.event}\n'
                 f'|cat_suffix=\n|displayredlinks=no\n}}}}\n\n')
        parent_lines = [f'[[Category:{p}]]' for p in args.parents]
        parent_lines.append(f'[[Category:{args.event}|{args.year}]]')
        text += '\n'.join(parent_lines) + '\n'
        print(f'create category {cat_title}')
        if not args.dry:
            page.text = text
            robust(page.save, summary=f'Create year category for {label}')
            print('   saved category')

    # --- 2. Wikidata edition item -----------------------------------------
    item = find_item_for_category(commons, repo, cat_title)
    if item is None:
        print(f'no existing item; create new: {label}')
        item = pywikibot.ItemPage(repo)
        if not args.dry:
            robust(item.editLabels, {'en': label}, summary=f'Create item for {label}')
            robust(item.editDescriptions, {'en': desc}, summary=f'Create item for {label}')
            print('   created item', item.title())
    else:
        print(f'found existing item: {item.title()}')
        if desc_of(item).get('en') != desc:
            if args.dry:
                print(f'   would set description en = {desc!r}')
            else:
                robust(item.editDescriptions, {'en': desc},
                       summary='Align description with series pattern')

    # --- 3. Claims ---------------------------------------------------------
    add_claim_if_missing(item, repo, 'P31',
                         pywikibot.ItemPage(repo, args.edition_type), 'Add edition type', args.dry)
    add_claim_if_missing(item, repo, 'P179',
                         pywikibot.ItemPage(repo, args.series), 'Add event series', args.dry)
    add_claim_if_missing(item, repo, 'P276',
                         pywikibot.ItemPage(repo, args.location), 'Add location', args.dry)
    add_claim_if_missing(item, repo, 'P17',
                         pywikibot.ItemPage(repo, args.country), 'Add country', args.dry)
    add_claim_if_missing(item, repo, 'P393', str(args.edition_no), 'Add edition number', args.dry)
    add_claim_if_missing(item, repo, 'P373', label, 'Add Commons category', args.dry)
    if start_parts:
        sy, sm, sd = start_parts
        add_claim_if_missing(item, repo, 'P580',
                             pywikibot.WbTime(year=sy, month=sm, day=sd, precision='day'),
                             'Add start date', args.dry)
        ey, em, ed = end_parts
        add_claim_if_missing(item, repo, 'P582',
                             pywikibot.WbTime(year=ey, month=em, day=ed, precision='day'),
                             'Add end date', args.dry)
        add_claim_if_missing(item, repo, 'P585',
                             pywikibot.WbTime(year=args.year, precision='year'),
                             'Add year of edition', args.dry)
    elif date_parts:
        y, m, d = date_parts
        add_claim_if_missing(item, repo, 'P585',
                             pywikibot.WbTime(year=y, month=m, day=d, precision='day'),
                             'Add date of edition', args.dry)
    else:
        add_claim_if_missing(item, repo, 'P585',
                             pywikibot.WbTime(year=args.year, precision='year'),
                             'Add year of edition', args.dry)
    ensure_sitelink(item, commons, cat_title, args.dry)

    # --- 4. P155/P156 chaining --------------------------------------------
    def warn_gap(pid, other_year):
        gap = abs(args.year - other_year)
        if gap > 1:
            print(f'   WARNING: year gap to {pid} is {gap} (>1); only chain '
                  f'when {pid} is the directly consecutive edition '
                  f'(intermediate years held but unmodeled must NOT be bridged).')

    if args.prev:
        prev = pywikibot.ItemPage(repo, args.prev)
        prev.get()
        prev_year = None
        for c in claims_of(prev).get('P585', []):
            t = c.getTarget()
            if getattr(t, 'year', None):
                prev_year = t.year
                break
        if prev_year:
            warn_gap('--prev', prev_year)
        add_claim_if_missing(item, repo, 'P155', prev, 'Add previous edition', args.dry)
        add_claim_if_missing(prev, repo, 'P156', item, 'Add next edition', args.dry)
    if args.next:
        nxt = pywikibot.ItemPage(repo, args.next)
        nxt.get()
        nxt_year = None
        for c in claims_of(nxt).get('P585', []):
            t = c.getTarget()
            if getattr(t, 'year', None):
                nxt_year = t.year
                break
        if nxt_year:
            warn_gap('--next', nxt_year)
        add_claim_if_missing(item, repo, 'P156', nxt, 'Add next edition', args.dry)
        add_claim_if_missing(nxt, repo, 'P155', item, 'Add previous edition', args.dry)

    print('DONE')
    sys.exit(0)


if __name__ == '__main__':
    main()
