# Template Reference for Wikipedia Page Anatomy

## Common Infobox Templates

### People
| Template | Key Parameters |
|----------|---------------|
| `{{Infobox person}}` | `name`, `image`, `caption`, `birth_date`, `birth_place`, `death_date`, `death_place`, `occupation`, `known_for`, `awards`, `alma_mater`, `spouse`, `children` |
| `{{Infobox scientist}}` | Same as person plus: `fields`, `institutions`, `thesis_title`, `doctoral_advisor`, `academic_advisors`, `notable_students`, `known_for`, `prizes` |
| `{{Infobox writer}}` | Same as person plus: `period`, `genre`, `movement`, `notable_works`, `spouse`, `awards` |
| `{{Infobox officeholder}}` | Same as person plus: `office`, `term_start`, `term_end`, `predecessor`, `successor`, `president`, `party` |
| `{{Infobox military person}}` | `name`, `image`, `birth_date`, `death_date`, `placeofburial`, `allegiance`, `branch`, `serviceyears`, `rank`, `unit`, `commands`, `battles`, `awards` |
| `{{Infobox artist}}` | `name`, `image`, `birth_date`, `death_date`, `nationality`, `known_for`, `notable_works`, `movement`, `patrons`, `awards` |

### Places
| Template | Key Parameters |
|----------|---------------|
| `{{Infobox settlement}}` | `name`, `official_name`, `nickname`, `motto`, `image_skyline`, `image_flag`, `image_map`, `map_caption`, `subdivision_type`, `subdivision_name`, `leader_title`, `leader_name`, `area_total_km2`, `population_total`, `population_density_km2`, `timezone1`, `utc_offset1`, `website` |
| `{{Infobox country}}` | `conventional_long_name`, `common_name`, `image_flag`, `image_coat`, `national_motto`, `national_anthem`, `capital`, `largest_city`, `official_languages`, `ethnic_groups`, `demonym`, `government_type`, `leader_title1`, `leader_name1`, `legislature`, `area_rank`, `area_km2`, `population_estimate`, `population_density_km2`, `GDP_nominal`, `GDP_nominal_year`, `currency`, `time_zone`, `calling_code`, `cctld` |
| `{{Infobox building}}` | `name`, `image`, `caption`, `location`, `address`, `coordinates`, `status`, `start_date`, `completion_date`, `opening`, `building_type`, `architectural`, `roof`, `top_floor`, `floor_count`, `elevator_count`, `cost`, `architect`, `developer`, `owner`, `website` |
| `{{Infobox mountain}}` | `name`, `photo`, `photo_caption`, `elevation_m`, `elevation_ref`, `prominence_m`, `location`, `range`, `coordinates`, `topo`, `type`, `age`, `volcanic_arc`, `last_eruption`, `first_ascent`, `easiest_route` |

### Events
| Template | Key Parameters |
|----------|---------------|
| `{{Infobox event}}` | `title`, `image`, `caption`, `date`, `time`, `duration`, `venue`, `location`, `coordinates`, `type`, `cause`, `motive`, `organisers`, `participants`, `outcome`, `deaths`, `injuries`, `reported missing`, `arrests`, `convictions`, `inquiries`, `website` |
| `{{Infobox military conflict}}` | `conflict`, `partof`, `image`, `caption`, `date`, `place`, `coordinates`, `result`, `status`, `territorial_changes`, `combatant1`, `combatant2`, `commander1`, `commander2`, `strength1`, `strength2`, `casualties1`, `casualties2`, `notes` |
| `{{Infobox election}}` | `election_name`, `country`, `type`, `ongoing`, `previous_election`, `previous_year`, `next_election`, `next_year`, `seats_for_election`, `majority_seats`, `turnout`, `image1`, `candidate1`, `party1`, `alliance1`, `popular_vote1`, `percentage1`, `swing1`, `electoral_vote1` (repeat for candidates 2, 3) |

### Media
| Template | Key Parameters |
|----------|---------------|
| `{{Infobox film}}` | `name`, `image`, `caption`, `director`, `producer`, `writer`, `screenplay`, `story`, `starring`, `music`, `cinematography`, `editing`, `studio`, `distributor`, `released`, `runtime`, `country`, `language`, `budget`, `gross` |
| `{{Infobox television episode}}` | `title`, `series`, `image`, `caption`, `season`, `episode`, `director`, `writer`, `teleplay`, `story`, `presenter`, `narrator`, `music`, `production`, `feature`, `photography`, `editor`, `airdate`, `running_time`, `guests`, `prev`, `next`, `episode_list` |
| `{{Infobox album}}` | `name`, `type`, `artist`, `cover`, `alt`, `released`, `recorded`, `venue`, `studio`, `genre`, `length`, `label`, `producer`, `prev_title`, `prev_year`, `next_title`, `next_year` |
| `{{Infobox book}}` | `name`, `image`, `image_caption`, `author`, `audio_read_by`, `title_orig`, `orig_lang_code`, `translator`, `illustrator`, `cover_artist`, `country`, `language`, `series`, `release_number`, `subject`, `genre`, `set_in`, `publisher`, `pub_date`, `english_pub_date`, `media_type`, `pages`, `awards`, `isbn`, `oclc`, `dewey`, `congress`, `preceded_by`, `followed_by` |

### Organizations
| Template | Key Parameters |
|----------|---------------|
| `{{Infobox company}}` | `name`, `logo`, `image`, `type`, `traded_as`, `industry`, `founded`, `founder`, `defunct`, `fate`, `successor`, `hq_location`, `hq_location_city`, `hq_location_country`, `area_served`, `key_people`, `products`, `production`, `brands`, `services`, `revenue`, `operating_income`, `net_income`, `assets`, `equity`, `owner`, `num_employees`, `parent`, `divisions`, `subsid`, `website` |
| `{{Infobox university}}` | `name`, `image`, `caption`, `latin_name`, `motto`, `mottoeng`, `established`, `type`, `academic_affiliation`, `endowment`, `budget`, `president`, `provost`, `faculty`, `administrative_staff`, `students`, `undergrad`, `postgrad`, `doctoral`, `other`, `city`, `state`, `country`, `campus`, `language`, `free_label`, `free`, `colors`, `sports_nickname`, `mascot`, `sporting_affiliations`, `website` |

### Biology
| Template | Key Parameters |
|----------|---------------|
| `{{Infobox species}}` | `name`, `image`, `image_caption`, `status`, `status_system`, `status_ref`, `genus`, `species`, `authority`, `range_map`, `range_map_caption` |
| `{{Infobox plant}}` | `name`, `image`, `image_caption`, `status`, `status_system`, `regnum`, `unranked_divisio`, `unranked_classis`, `unranked_ordo`, `familia`, `genus`, `species`, `binomial`, `binomial_authority`, `synonyms` |

## Common Citation Templates

| Template | When to Use | Minimum Parameters |
|----------|------------|-------------------|
| `{{cite web}}` | General websites, news articles | `url`, `title` |
| `{{cite news}}` | Newspaper/magazine articles | `url`, `title`, `newspaper`, `date` |
| `{{cite book}}` | Books | `title`, `author`, `year`, `publisher` |
| `{{cite journal}}` | Academic journal articles | `title`, `author`, `journal`, `year`, `volume`, `pages` |
| `{{cite report}}` | Reports, white papers | `title`, `author`, `year`, `publisher` |
| `{{cite thesis}}` | Theses and dissertations | `title`, `author`, `year`, `type`, `publisher` |
| `{{cite conference}}` | Conference proceedings | `title`, `author`, `booktitle`, `year`, `publisher` |
| `{{cite encyclopedia}}` | Encyclopedia entries | `title`, `encyclopedia`, `year`, `publisher` |
| `{{cite web}}` | YouTube, online videos | `url`, `title`, `website=YouTube` |
| `{{cite web}}` with `type=Audiobook` | Podcasts, audiobooks | `url`, `title`, `website` |

### Template Parameter Reference

```wikitext
{{cite web
| url         = https://example.com/article
| title       = Article Title
| last        = Smith        ← Author surname
| first       = John         ← Author given name
| date        = 2026-01-15   ← Publication date (ISO 8601 preferred)
| website     = Example News ← Source name
| publisher   = Example Corp ← Publishing organization
| access-date = 2026-05-23   ← When you accessed the URL
| archive-url = https://archive.org/...  ← Link to archived copy
| archive-date = 2026-02-01  ← Date of archive
| url-status  = live | dead  ← Whether the original URL is still live
| language    = fr           ← Non-English source language
}}
```

## Maintenance Templates Quick Reference

| Code | Full Name | Typical Usage |
|------|-----------|---------------|
| `{{cn}}` | citation needed | After unsupported claim |
| `{{better source}}` | better source needed | After a weak citation |
| `{{failed verification}}` | failed verification | Citation doesn't support the claim |
| `{{dead link}}` | dead link | URL no longer resolves |
| `{{POV}}` | neutrality disputed | Article may not be neutral |
| `{{POV section}}` | section neutrality | Section may not be neutral |
| `{{expand section}}` | expand section | Section is too brief |
| `{{empty section}}` | empty section | Section has no content |
| `{{stub}}` | stub | Very short article |
| `{{clarify}}` | clarify | Text is confusing |
| `{{when}}` | when | Time-sensitive statement (e.g., "recently") |
| `{{where}}` | where | Location is unclear |
| `{{who}}` | who | Vague attribution (e.g., "some say") |
| `{{according to whom}}` | according to whom | Attribution needed |
| `{{original research}}` | original research? | Unverified claim |
| `{{weasel inline}}` | weasel word | Vague phrasing (e.g., "many believe") |
| `{{dubious}}` | dubious | Discuss on talk page |
| `{{verify source}}` | verify source | Source may be misrepresented |
| `{{self-published source}}` | self-published | Source is not independently published |
| `{{primary source inline}}` | primary source inline | Needs secondary source |
| `{{third-party}}` | third-party | Needs independent source |
