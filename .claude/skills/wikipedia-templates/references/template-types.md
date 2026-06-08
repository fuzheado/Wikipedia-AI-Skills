# Template Types Reference

A comprehensive taxonomy of template types on English Wikipedia, with examples, usage patterns, and Lua-backing information.

---

## 1. Infoboxes

Right-aligned summary tables that present key facts. Usually the first template on a page.

### People

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox person}}` | No | `name`, `birth_date`, `birth_place`, `occupation`, `known_for` |
| `{{Infobox scientist}}` | No | Same as person + `fields`, `workplaces`, `doctoral_advisor` |
| `{{Infobox writer}}` | No | Same as person + `genre`, `notable_works` |
| `{{Infobox officeholder}}` | No | Same as person + `office`, `term_start`, `party` |
| `{{Infobox military person}}` | No | `allegiance`, `branch`, `rank`, `battles`, `awards` |
| `{{Infobox artist}}` | No | `known_for`, `movement`, `notable_works` |
| `{{Infobox royalty}}` | Yes | `title`, `succession`, `reign`, `predecessor`, `spouse` |
| `{{Infobox sportsperson}}` | Yes | `sport`, `event`, `medal_records` |
| `{{Infobox criminal}}` | No | `charge`, `conviction`, `penalty`, `victims` |

### Places and Geography

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox settlement}}` | **Yes** | `name`, `population_total`, `area_total_km2`, `subdivision_type` |
| `{{Infobox country}}` | No | `conventional_long_name`, `capital`, `official_languages` |
| `{{Infobox building}}` | No | `location`, `start_date`, `architect`, `floor_count` |
| `{{Infobox mountain}}` | No | `elevation_m`, `prominence_m`, `location`, `range` |
| `{{Infobox river}}` | No | `length_km`, `mouth`, `basin_countries` |
| `{{Infobox body of water}}` | No | `type`, `location`, `area`, `max_depth` |
| `{{Infobox protected area}}` | No | `designation`, `area_km2`, `established` |

### Events and History

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox event}}` | No | `date`, `venue`, `location`, `type`, `outcome` |
| `{{Infobox military conflict}}` | No | `date`, `place`, `result`, `combatant1`, `commander1` |
| `{{Infobox election}}` | No | `country`, `type`, `previous_election`, `next_election`, `turnout` |
| `{{Infobox civil conflict}}` | No | `date`, `place`, `causes`, `goals`, `methods` |
| `{{Infobox historical era}}` | No | `name`, `start_year`, `end_year`, `before`, `after` |

### Media and Culture

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox film}}` | No | `director`, `producer`, `writer`, `starring`, `released` |
| `{{Infobox television}}` | No | `genre`, `creator`, `starring`, `country`, `network`, `released` |
| `{{Infobox television season}}` | No | `series`, `season_number`, `network`, `episodes` |
| `{{Infobox television episode}}` | No | `series`, `season`, `episode`, `director`, `airdate` |
| `{{Infobox album}}` | No | `artist`, `released`, `recorded`, `studio`, `genre`, `length` |
| `{{Infobox song}}` | No | `artist`, `album`, `released`, `genre`, `length` |
| `{{Infobox book}}` | No | `author`, `genre`, `publisher`, `pub_date`, `isbn` |
| `{{Infobox comic strip}}` | No | `author`, `syndicate`, `status`, `first` |
| `{{Infobox magazine}}` | No | `editor`, `category`, `frequency`, `circulation` |
| `{{Infobox radio program}}` | No | `runtime`, `country`, `language`, `home_station`, `starring` |
| `{{Infobox play}}` | No | `writer`, `chorus`, `characters`, `setting`, `premiere` |
| `{{Infobox video game}}` | **Yes** | `developer`, `publisher`, `platform`, `released`, `genre`, `modes` |
| `{{Infobox software}}` | No | `developer`, `latest_release_version`, `operating_system`, `license` |
| `{{Infobox website}}` | No | `creator`, `key_people`, `url`, `commercial`, `registration` |
| `{{Infobox podcast}}` | No | `host`, `genre`, `language`, `began` |

### Organizations

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox company}}` | No | `type`, `industry`, `founded`, `founder`, `hq_location` |
| `{{Infobox university}}` | No | `type`, `established`, `president`, `students`, `city` |
| `{{Infobox school}}` | No | `type`, `established`, `principal`, `enrollment`, `campus_type` |
| `{{Infobox museum}}` | No | `type`, `collection_size`, `director`, `curator` |
| `{{Infobox library}}` | No | `type`, `established`, `items_collected`, `director` |
| `{{Infobox hospital}}` | No | `location`, `type`, `beds`, `emergency`, `helipad` |
| `{{Infobox political party}}` | No | `leader`, `foundation`, `headquarters`, `ideology` |
| `{{Infobox trade union}}` | No | `founded`, `members`, `affiliation`, `headquarters` |

### Science and Nature

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox species}}` | No | `genus`, `species`, `authority`, `status`, `range_map` |
| `{{Infobox planet}}` | No | `discoverer`, `discovery_site`, `discovered`, `mpc_name` |
| `{{Infobox galaxy}}` | No | `epoch`, `constellation`, `distance_ly`, `appmag_v` |
| `{{Infobox star}}` | No | `constellation`, `distance_ly`, `magnitude`, `mass` |
| `{{Infobox drug}}` | No | `type`, `drug_name`, `target`, `cas_number`, `atc_prefix` |
| `{{Infobox medical condition}}` | No | `symptoms`, `complications`, `onset`, `duration`, `causes` |
| `{{Infobox disease}}` | No | `icd10`, `icd9`, `omim`, `mesh` |

### Transport

| Template | Lua? | Key Parameters |
|----------|------|---------------|
| `{{Infobox aircraft type}}` | No | `type`, `national_origin`, `manufacturer`, `first_flight` |
| `{{Infobox automobile}}` | No | `manufacturer`, `production`, `assembly`, `class`, `layout` |
| `{{Infobox locomotive}}` | No | `powertype`, `builder`, `builddate`, `total_production` |
| `{{Infobox ship}}` | **Yes** | `ship_type`, `ship_class`, `ship_tonnage`, `ship_length` |
| `{{Infobox rail line}}` | No | `type`, `system`, `status`, `locale`, `stations` |
| `{{Infobox public transit}}` | No | `locale`, `transit_type`, `began_operation`, `lines`, `stations` |
| `{{Infobox road}}` | No | `route`, `length_mi`, `direction`, `termini`, `junction` |

---

## 2. Citation Templates

See the `wikipedia-citations` skill for complete coverage. Quick reference:

| Template | Lua? | For |
|----------|------|-----|
| `{{cite web}}` | **Yes** | General web pages |
| `{{cite news}}` | **Yes** | News articles |
| `{{cite book}}` | **Yes** | Books |
| `{{cite journal}}` | **Yes** | Academic papers |
| `{{cite magazine}}` | **Yes** | Magazines |
| `{{cite encyclopedia}}` | **Yes** | Encyclopedia entries |
| `{{sfn}}` | **Yes** | Shortened footnotes |
| `{{harvnb}}` | **Yes** | Harvard-style author-date |
| `{{sfnp}}` | **Yes** | Parenthetical sfn |
| `{{r}}` | No | Named reference shortcut |
| `{{cn}}` | No | Citation needed |
| `{{full citation needed}}` | No | Full details missing |

---

## 3. Navigation Templates

### Navboxes

Collapsible navigation at the bottom of articles, above categories.

| Template | Lua? | Description |
|----------|------|-------------|
| `{{Navbox}}` | **Yes** | Standard collapsible navigation |
| `{{Navbox with collapsible groups}}` | **Yes** | Multi-section navbox |
| `{{Navbox musical artist}}` | **Yes** | Artist discography navbox |
| `{{Navbox years}}` | No | Year-by-year chronology |
| `{{Navbox subgroup}}` | No | Nested navigation groups |

### Sidebars

Right-aligned navigation columns (replaced navboxes in some contexts).

| Template | Lua? | Description |
|----------|------|-------------|
| `{{Sidebar}}` | No | Generic sidebar |
| `{{Sidebar with collapsible lists}}` | No | Sidebar with expandable sections |

### Series and Subject Navigation

| Template | Lua? | Description |
|----------|------|-------------|
| `{{Series sidebar}}` | No | Sequential topic navigation |
| `{{Subject bar}}` | No | Portal and sister project links |
| `{{Portal bar}}` | No | Related portal links |
| `{{Authority control}}` | **Yes** | Library catalog identifiers |
| `{{Sister project links}}` | No | Links to other Wikimedia projects |

---

## 4. Maintenance and Cleanup Templates

These signal issues and are placed at the top of articles or inline.

### Top-of-Article

| Template | Signal |
|----------|--------|
| `{{POV}}` | Article neutrality disputed |
| `{{disputed}}` | Article content disputed |
| `{{original research}}` | Unverified synthesis |
| `{{refimprove}}` | Not enough sources |
| `{{more citations needed}}` | Not enough references |
| `{{one source}}` | Only one source |
| `{{lead missing}}` | No lead section |
| `{{lead too short}}` | Lead section too brief |
| `{{cleanup}}` | General cleanup needed |
| `{{tone}}` | Inappropriate tone |
| `{{update}}` | Out of date |
| `{{in use}}` | Being actively edited |
| `{{under construction}}` | Major edit in progress |

### Inline Templates

| Template | Signal |
|----------|--------|
| `{{cn}}` | Citation needed |
| `{{clarify}}` | Text is confusing |
| `{{when}}` | Time-sensitive statement |
| `{{where}}` | Location unclear |
| `{{who}}` | Vague attribution |
| `{{according to whom}}` | Attribution needed |
| `{{dubious}}` | Discuss on talk page |
| `{{failed verification}}` | Source doesn't support claim |
| `{{better source}}` | Weak citation |
| `{{primary source inline}}` | Needs secondary source |
| `{{dead link}}` | URL no longer resolves |
| `{{full citation needed}}` | Missing details |
| `{{page needed}}` | Missing page number |
| `{{quote without source}}` | Unattributed quote |
| `{{self-published source}}` | Non-independent source |
| `{{third-party inline}}` | Needs independent source |

### Section Templates

| Template | Signal |
|----------|--------|
| `{{expand section}}` | Section too brief |
| `{{empty section}}` | Section has no content |
| `{{POV section}}` | Section neutrality disputed |
| `{{sources section}}` | Section under-sourced |
| `{{unreferenced section}}` | No sources in section |

---

## 5. Stub Templates

Mark very short articles needing expansion. Usually auto-placed by WikiProject tools.

**Convention:** `{{<topic>-stub}}` format.

```
{{stub}}              {{physics-stub}}
{{bio-stub}}          {{film-stub}}
{{geo-stub}}          {{sci-stub}}
{{history-stub}}      {{lit-stub}}
{{sport-stub}}        {{music-stub}}
{{politics-stub}}     {{chem-stub}}
{{math-stub}}         {{comp-sci-stub}}
```

Stub templates should be the **last** wikitext on the page, after categories.

---

## 6. Hatnote and Disambiguation Templates

These appear at the very top of articles, before the infobox, to resolve naming ambiguity.

### Hatnotes

| Template | Usage |
|----------|-------|
| `{{About|topic}}` | Main disambiguation hatnote |
| `{{For|other uses}}` | For other uses of the same name |
| `{{For2|other uses|custom text}}` | Custom text variant |
| `{{Distinguish|similar}}` | Similar name caution |
| `{{Redirect|redirect}}` | Redirect hatnote |
| `{{Other uses}}` | General other-uses link |
| `{{Redirect-distinguish|redirect|other}}` | Combined redirect + distinguish |
| `{{See also|related}}` | Cross-reference hatnote |

### Disambiguation

| Template | Variant |
|----------|---------|
| `{{disambiguation}}` | Generic disambiguation |
| `{{geodis}}` | Geographic disambiguation |
| `{{hndis}}` | Human name disambiguation |
| `{{schooldis}}` | School name disambiguation |
| `{{numberdis}}` | Number disambiguation |

---

## 7. Structural Templates

Organize page layout and content flow.

| Template | Purpose |
|----------|---------|
| `{{TOC left}}` / `{{TOC right}}` | Floating table of contents |
| `{{TOC limit|3}}` | Limit TOC depth |
| `{{Clear}}` | Clear floating elements |
| `{{-}}` | Shortcut for {{clear}} |
| `{{Stack|...}}` | Stack floated elements |
| `{{Column-start}}` / `{{Column-end}}` | Multi-column layout |
| `{{Columns-list}}` | Multiple columns |
| `{{Div col}}` | CSS column layout |
| `{{Ordered list}}` vs. `{{Unordered list}}` | HTML list rendering |

---

## 8. Media and File Templates

| Template | Purpose |
|----------|---------|
| `{{Listen}}` | Audio file player |
| `{{Multiple image}}` | Side-by-side images |
| `{{Superimpose}}` | Overlay images |
| `{{Image label}}` | Labels on image coordinates |
| `{{Photomontage}}` | Composite image |
| `{{Video}}` | Video file player |
| `{{External media}}` | Off-site media links |
| `{{CSS image crop}}` | Image cropping |

---

## 9. Linking and Reference Templates

| Template | Purpose |
|----------|---------|
| `{{Commons category}}` | Commons link |
| `{{Wikiquote}}` | Wikiquote link |
| `{{Wiktionary}}` | Wiktionary link |
| `{{Wikisource}}` | Wikisource link |
| `{{Main article}}` | Main article cross-reference |
| `{{Further}}` | Further information link |
| `{{See also}}` | See-also cross-reference |
| `{{Crossreference}}` | In-text cross-reference |
| `{{Anchor}}` | Named anchor for linking |

---

## 10. Date and Formatting Templates

| Template | Purpose |
|----------|---------|
| `{{Date}}` | Format a date |
| `{{Start date}}` | Start date (ISO for metadata) |
| `{{End date}}` | End date |
| `{{Birth date}}` / `{{Death date}}` | Life dates |
| `{{Birth date and age}}` | Birth date with computed age |
| `{{Age}}` | Compute age between two dates |
| `{{Years or months ago}}` | Relative time |
| `{{USD}}` / `{{GBP}}` / `{{€}}` | Currency formatting |
| `{{Convert|100|km|mi}}` | Unit conversion |
| `{{Format price}}` | Number formatting |
| `{{Ordinal}}` | Ordinal suffix |
| `{{Abbr}}` | Abbreviation tooltip |
| `{{Not a typo}}` | Prevent bot correction |
| `{{Sic}}` | "[sic]" marker |
| `{{Proper name}}` | Proper noun formatting |
| `{{Lang}}` / `{{Lang-xx}}` | Language markup |

---

## 11. User Talk and Warning Templates

| Template | Purpose |
|----------|---------|
| `{{Welcome}}` | Welcome message |
| `{{Uw-vandalism1}}` through `{{Uw-vandalism4im}}` | Vandalism warning levels |
| `{{Uw-test1}}` | Test edit warning |
| `{{Uw-AIV}}` | User reported at AIV |
| `{{Block indent}}` | Block quote formatting |
| `{{Reply to}}` / `{{Ping}}` | Notify user in discussion |
| `{{Talkquote}}` | Quote formatting on talk |
| `{{outdent}}` | Outdent reply |
| `{{unsigned}}` / `{{unsigned2}}` | Timestamp unsigned comments |

---

## 12. Template Documentation Templates

| Template | Purpose |
|----------|---------|
| `{{Documentation}}` | Pulls `/doc` subpage content |
| `{{Documentation subpage}}` | Header for doc pages |
| `{{TemplateData header}}` | TemplateData section header |
| `{{Sandbox other}}` | Detects if on /sandbox subpage |
| `{{Bool}}, {{Yes}}, {{No}}` | Boolean display |
| `{{Para}}` | Parameter formatting in docs |
| `{{Parameter names example}}` | Example parameter table |
| `{{Template shortcut}}` | Shortcut alias display |
| `{{Template display}}` | Source code display |

---

## 13. WikiProject Banners (Talk Page)

| Template | Purpose |
|----------|---------|
| `{{WikiProject Biography}}` | Biography articles |
| `{{WikiProject Physics}}` | Physics articles |
| `{{WikiProject Cities}}` | Settlement articles |
| `{{WikiProject Film}}` | Film articles |
| `{{WikiProject Companies}}` | Company articles |
| `{{ArticleHistory}}` | Featured article history |
| `{{Annual report}}` | WikiProject annual assessment |
| `{{Peer review}}` | Article peer review status |
| `{{GA nominee}}` | Good article nomination |
| `{{DYK nom}}` | Did You Know nomination |
