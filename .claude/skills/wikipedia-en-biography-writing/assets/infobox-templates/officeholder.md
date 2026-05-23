# Infobox Officeholder

For politicians, government officials, diplomats, judges, and military officers who have held public office.

```wikitext
{{Infobox officeholder
| honorific_prefix          = 
| name                      = <!-- defaults to article title when left blank -->
| native_name               = <!-- The person's name in their own language, if different -->
| native_name_lang          = <!-- ISO 639-1 code, e.g. "fr" for French -->
| honorific_suffix          = 
| image                     = 
| image_size                = 
| image_upright             = 
| alt                       = 
| caption                   = 

<!-- Office 1 — repeat up to 16 times by incrementing the number -->
| order                     = 
| office                    = 
| status                    = <!-- If specified, overrides "Incumbent" -->
| term_start                = 
| term_end                  = <!-- Add data only when term has actually ended -->
| subterm                   = 
| suboffice                 = 
| alongside                 = <!-- For two or more people serving in same position -->
| monarch                   = 
| president                 = 
| governor_general          = 
| prime_minister            = 
| chancellor                = 
| taoiseach                 = 
| governor                  = 
| co_leader                 = 
| vice_president            = 
| vice_prime_minister       = 
| deputy                    = 
| lieutenant                = 
| succeeding                = <!-- For President-elect or equivalent -->
| parliamentary_group       = 
| constituency              = 
| majority                  = 
| predecessor               = 
| successor                 = <!-- Should not be filled until successor takes office -->
| prior_term                = <!-- For redistricted politicians -->

<!-- Repeat for office2 through office16 as needed -->
<!-- e.g. | office2 = | term_start2 = | term_end2 = | predecessor2 = | successor2 = -->
<!-- See the "Personal data" fields below (always include) -->
}}
```

### Personal Data (always include after office fields)

```wikitext
| pronunciation             = 
| birth_name                = <!-- only use if different from name -->
| birth_date                = <!-- {{Birth date and age|YYYY|MM|DD}} -->
| birth_place               = 
| death_date                = <!-- {{Death date and age|YYYY|MM|DD|YYYY|MM|DD}} -->
| death_place               = 
| death_cause               = <!-- only when cause has significance for notability -->
| resting_place             = 
| resting_place_coordinates = 
| citizenship               = <!-- use only when necessary per WP:INFONAT -->
| party                     = 
| other_party               = <!-- For additional political affiliations -->
| height                    = <!-- "X cm", "X m" or "X ft Y in" -->
| spouse                    = 
| partner                   = <!-- For domestic partners (not married) -->
| relations                 = 
| children                  = 
| parents                   = <!-- overrides mother and father parameters -->
| mother                    = <!-- may be used (optionally with father) in place of parents -->
| father                    = <!-- may be used (optionally with mother) in place of parents -->
| relatives                 = 
| education                 = 
| alma_mater                = 
| occupation                = 
| profession                = 
| known_for                 = 
| salary                    = 
| cabinet                   = 
| committees                = 
| portfolio                 = 
| awards                    = <!-- Civilian awards -->
| signature                 = 
| signature_alt             = 
| website                   = 
| nickname                  = 

<!-- Military service (optional, uncomment if applicable) -->
<!-- 
| allegiance                = 
| branch                    = 
| service_years             = 
| rank                      = 
| unit                      = 
| commands                  = 
| battles                   = 
| mawards                   = <!-- Military awards -->
-->
}}
```

### Variant: Ambassador

For diplomats serving as ambassadors to a foreign country.

```wikitext
{{Infobox ambassador
| honorific_prefix = 
| name             = 
| honorific_suffix = 
| image            = 
| alt              = 
| caption          = 
| order            = <!-- Can be repeated up to 16 times -->
| ambassador_from  = <!-- Can be repeated up to 16 times -->
| country          = <!-- Can be repeated up to 16 times -->
| term_start       = <!-- Can be repeated up to 16 times -->
| term_end         = <!-- Can be repeated up to 16 times -->
| predecessor      = <!-- Can be repeated up to 16 times -->
| successor        = <!-- Can be repeated up to 16 times -->
| president        = <!-- Can be repeated up to 16 times -->
}}
<!-- Then add Personal data fields from above -->
```

### Variant: Assembly Member (Legislator)

For members of a legislative assembly, parliament, or congress.

```wikitext
{{Infobox AM
| honorific_prefix  = 
| name              = 
| honorific_suffix  = 
| image             = 
| alt               = 
| caption           = 
| constituency_AM   = <!-- Can be repeated up to 8 times -->
| assembly          = <!-- Can be repeated up to 16 times -->
| majority          = <!-- Can be repeated up to 16 times -->
| term_start        = <!-- Can be repeated up to 16 times -->
| term_end          = <!-- Can be repeated up to 16 times -->
| predecessor       = <!-- Can be repeated up to 16 times -->
| successor         = <!-- Can be repeated up to 16 times -->
| prior_term        = 
}}
<!-- Then add Personal data fields from above -->
```

### Variant: Governor

For state/provincial governors.

```wikitext
{{Infobox governor
| honorific_prefix = 
| name             = 
| honorific_suffix = 
| image            = 
| alt              = 
| caption          = 
| order            = <!-- Can be repeated up to 16 times -->
| office           = <!-- Can be repeated up to 16 times -->
| term_start       = <!-- Can be repeated up to 16 times -->
| term_end         = <!-- Can be repeated up to 16 times -->
| lieutenant       = <!-- Can be repeated up to 16 times -->
| predecessor      = <!-- Can be repeated up to 16 times -->
| successor        = <!-- Can be repeated up to 16 times -->
| president        = <!-- Add if appointed by a president -->
}}
<!-- Then add Personal data fields from above -->
```

**Use when:** Subject is a politician, government official, diplomat, judge, or military officer who has held public office.

**Key fields:** `office`, `term_start`, `term_end`, `party`, `predecessor`, `successor`, `constituency`

**Guidelines:**
- Up to **16 offices** can be listed by incrementing the number suffix (e.g., `office2`, `term_start2`, etc.)
- The `|order=` parameter is used for ordinal numbering (e.g., "42nd President"). Only use when well-established in reliable sources.
- Do not fill `|successor=` until the successor actually takes office (per RfC consensus).
- For *incumbent* officeholders, do not include an end date or an elected successor who has not yet taken office.
- Use `{{Birth date and age|YYYY|MM|DD}}` and `{{Death date and age|YYYY|MM|DD|YYYY|MM|DD}}` for dates.
- The `Infobox ambassador`, `Infobox AM`, and `Infobox governor` are redirects that render as `Infobox officeholder` — use whichever is semantically appropriate.
- Military service section is optional; only include if the subject has a notable military career.
- `|death_cause=` should only be included when the cause of death has significance for the subject's notability.
- Use `|native_name=` when the person's name is commonly written in their native script alongside the English version.
