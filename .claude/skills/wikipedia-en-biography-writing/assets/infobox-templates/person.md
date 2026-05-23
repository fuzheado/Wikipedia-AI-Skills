# Infobox Person

The most fundamental and general-purpose biography infobox. Use when no subject-specific infobox
(scientist, writer, artist, athlete, officeholder) is a better fit. This is the **default fallback**
for any person article.

## ⚠️  Golden Rule: Less Is More

**Most infoboxes do not use the vast majority of these fields.** The list is long
because it must cover the full diversity of human biography, not because every field
should be filled. Only include fields you are confident about and that convey
essential information about the subject.

> **When in doubt, leave it out.** An empty infobox field draws no attention.
> A wrong or poorly sourced field harms the article.

**Before adding any field, ask:**
1. Is this fact supported by a reliable source? (Verifiability)
2. Does this fact matter to the reader's understanding of the person? (Due weight)
3. Am I sure about the formatting conventions for this field? (MOS)

If the answer to any of these is 

```wikitext
{{Infobox person
| name          = <!-- defaults to article title when left blank -->
| image         = <!-- filename only, no "File:" or "Image:" prefix -->
| alt           = <!-- descriptive text for speech synthesis software -->
| caption       = 
| birth_name    = <!-- use only if different from name -->
| birth_date    = <!-- {{Birth date and age|YYYY|MM|DD}} for living people -->
| birth_place   = 
| death_date    = <!-- {{Death date and age|YYYY|MM|DD|YYYY|MM|DD}} -->
| death_place   = 
| other_names   = 
| occupation    = 
| years_active  = 
| known_for     = 
| notable_works = 
}}
```

## Full Template (all fields)

Only include fields that are pertinent and sourced. Remove unused parameters.

```wikitext
{{Infobox person
| honorific_prefix          = 
| name                      = <!-- defaults to article title when left blank -->
| honorific_suffix          = 
| native_name               = <!-- The person's name in their own language, if different -->
| native_name_lang          = <!-- ISO 639-1 code, e.g. "fr" for French -->
| image                     = <!-- filename only, no "File:" or "Image:" prefix -->
| image_upright             = 
| landscape                 = <!-- yes, if wide image -->
| alt                       = <!-- descriptive text for speech synthesis software -->
| caption                   = 
| pronunciation             = 
| birth_name                = <!-- use only if different from name -->
| birth_date                = <!-- {{Birth date and age|YYYY|MM|DD}} for living people -->
| birth_place               = 
| baptised                  = <!-- only when birth_date is unknown -->
| disappeared_date          = <!-- {{Disappeared date and age|YYYY|MM|DD|YYYY|MM|DD}} -->
| disappeared_place         = 
| disappeared_status        = 
| death_date                = <!-- {{Death date and age|YYYY|MM|DD|YYYY|MM|DD}} -->
| death_place               = 
| death_cause               = <!-- only when cause has significance for notability -->
| body_discovered           = 
| resting_place             = 
| resting_place_coordinates = <!-- {{coord|LAT|LONG|type:landmark|display=inline}} -->
| burial_place              = <!-- alternative to resting_place -->
| burial_coordinates        = <!-- {{coord|LAT|LONG|type:landmark|display=inline}} -->
| monuments                 = 
| other_names               = 
| siglum                    = 
| citizenship               = <!-- use only when necessary per WP:INFONAT -->
| education                 = 
| alma_mater                = 
| occupation                = 
| years_active              = 
| era                       = 
| employer                  = 
| organization              = 
| agent                     = <!-- discouraged; requires reliable source -->
| known_for                 = 
| notable_works             = <!-- use |credits= for "Notable credit(s)" label -->
| style                     = 
| television                = 
| height                    = <!-- "X cm", "X m" or "X ft Y in" -->
| title                     = <!-- formal/awarded/job title -->
| term                      = 
| predecessor               = 
| successor                 = 
| political_party           = 
| other_party               = 
| movement                  = 
| opponents                 = 
| boards                    = 
| criminal_charges          = <!-- requires citations from reliable sources -->
| criminal_penalty          = 
| criminal_status           = 
| spouse                    = <!-- use article title or common name -->
| partner                   = <!-- unmarried life partner in domestic partnership -->
| children                  = <!-- number, or names of independently notable children -->
| parents                   = <!-- overrides mother and father -->
| mother                    = <!-- may be used (optionally with father) in place of parents -->
| father                    = <!-- may be used (optionally with mother) in place of parents -->
| relatives                 = 
| family                    = 
| callsign                  = <!-- amateur radio, if relevant -->
| awards                    = 
| website                   = <!-- {{URL|example.com}} -->
| module                    = <!-- embed another infobox -->
| module2                   = 
| module3                   = 
| module4                   = 
| module5                   = 
| module6                   = 
| signature                 = 
| signature_type            = <!-- changes "Signature" label, e.g. "Seal" -->
| signature_size            = <!-- default 150px -->
| signature_alt             = 
| footnotes                 = 
}}
```

**Use when:** Subject is a person and no subject-specific infobox (scientist, writer, artist, athlete, officeholder) is more appropriate.

**Key fields:** `name`, `birth_date`, `birth_place`, `occupation`, `known_for`

## Field Guidelines

| Field | Guidance |
|---|---|
| `honorific_prefix` | For knighthoods, "The Honourable", "His/Her Excellency" — not routine titles like "Dr." or "Ms." |
| `honorific_suffix` | For national orders and non-honorary doctorates (e.g., `OBE`) |
| `birth_date` | Use `{{Birth date and age|YYYY|MM|DD}}` for living, `{{Birth date|YYYY|MM|DD}}` for deceased. For living people, supply only the year unless the exact date is widely published (per WP:DOB). |
| `death_cause` | Only include when the cause has significance for **notability** (e.g., James Dean, John Lennon). Not for routine deaths from old age or illness. |
| `death_place` | Use the place name at time of death. Follow MOS:USA ("US" not "USA"). |
| `birth_place` | Use the name of the birthplace **at the time of birth** (e.g., Saigon prior to 1976). Do not use flag templates. |
| `citizenship` | Rarely needed — omit if same as birth country. Per WP:INFONAT. |
| `spouse` | Use format `Name (m. 1950)` or `Name (m. 1970–1999)`. Use `{{marriage}}` template for clean formatting. |
| `children` | Typically just the **number** (e.g., `3`). Only list names of independently notable children. For privacy, omit names of living children unless notable. |
| `education` vs `alma_mater` | Use `education` for detailed credentials (institution + degree). Use `alma_mater` as concise alternative (linked institution name only). Do not use both. |
| `module` | For embedding other infoboxes (e.g., `{{Infobox musical artist}}` with `embed=yes`) |
| `notable_works` | For works by the subject. Alternative labels: `credits` → "Notable credit(s)", `works` → "Works", `label_name` → "Label(s)". |

## When to Use This vs. Subject-Specific Infoboxes

| Subject type | Use infobox | File |
|---|---|---|
| General person (no specific category fits) | `Infobox person` | `person.md` ⬅️ **this one** |
| Academic, researcher, scientist | `Infobox scientist` | `scientist.md` |
| Author, journalist, poet | `Infobox writer` | `writer.md` |
| Visual artist, sculptor, photographer | `Infobox artist` | `artist.md` |
| Athlete, coach, sports figure | `Infobox sportsperson` | `athlete.md` |
| Politician, government official, diplomat, judge | `Infobox officeholder` | `officeholder.md` |

## Important Restrictions

- **`religion=` and `ethnicity=` were removed** from this template per community RfCs (2016). Do not add them.
- **Do not use flag templates** for birth/death place or citizenship.
- **Do not use `<br />` markup** for lists — use `{{hlist}}`, `{{flatlist}}`, or `{{plainlist}}` instead.
- **Signature images** should use filename only (no "File:" prefix). Default size is 150px.
- The template generates an **hCard microformat** automatically. Do not remove the `fn`, `bday`, `locality`, etc. classes.
