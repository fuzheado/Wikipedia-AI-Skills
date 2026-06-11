# Wiktionary Entry Structure Reference

## Heading Hierarchy

A Wiktionary page contains entries for one word in multiple languages, separated
by `----` (5 hyphens) lines:

```
==Language 1==              # Level 2: Language section
===Etymology===             # Level 3: Etymology
===Pronunciation===         # Level 3: Pronunciation
  {{a|dialect}} {{IPA|lang|/pron/}}
  {{audio|lang|filename.ogg|Label}}
===Part of speech 1===      # Level 3: POS (Noun, Verb, etc.)
  {{template}}              # Inflection template
  # Definition 1            # Level 4: Numbered definition
  #: Example sentence.      # Level 5: Example (indented with #:)
  # Definition 2
  #: Another example.
  ====Usage notes====       # Level 4: Subsection
  ====Synonyms====
  ====Derived terms====
  ====Related terms====
  ====Translations====
    {{trans-top|label}}
    {{t|lang|word}}
    {{trans-bottom}}
===Part of speech 2===
  ...

----                        # 5 hyphens separate language sections

==Language 2==
...
```

---

## Common POS Headings

| Heading | Abbreviation | For |
|---------|-------------|-----|
| `===Noun===` | n | Nouns |
| `===Verb===` | v | Verbs |
| `===Adjective===` | adj | Adjectives |
| `===Adverb===` | adv | Adverbs |
| `===Pronoun===` | pron | Pronouns |
| `===Preposition===` | prep | Prepositions |
| `===Conjunction===` | conj | Conjunctions |
| `===Interjection===` | interj | Interjections |
| `===Article===` | art | Articles |
| `===Determiner===` | det | Determiners |
| `===Numeral===` | num | Numerals |
| `===Particle===` | particle | Particles |
| `===Prefix===` | prefix | Prefixes |
| `===Suffix===` | suffix | Suffixes |
| `===Proper noun===` | proper | Proper nouns |
| `===Phrase===` | phrase | Phrases |
| `===Idiom===` | idiom | Idiomatic expressions |
| `===Proverb===` | proverb | Proverbs |
| `===Symbol===` | symbol | Symbols |
| `===Punctuation mark===` | punct | Punctuation |

---

## Common Subsections

| Subsection | Content |
|------------|---------|
| `====Etymology====` | Word origin, root language, historical development |
| `====Pronunciation====` | IPA, audio files, rhyme, homophones, hyphenation |
| `====Usage notes====` | Grammar, register, dialect notes |
| `====Synonyms====` | Words with similar meaning ({{syn}}) |
| `====Antonyms====` | Words with opposite meaning ({{ant}}) |
| `====Hypernyms====` | Broader categories ({{hyper}}) |
| `====Hyponyms====` | Specific instances ({{hypo}}) |
| `====Holonyms====` | Larger wholes ({{holo}}) |
| `====Meronyms====` | Component parts ({{mero}}) |
| `====Coordinate terms====` | Sibling terms ({{coordinate terms}}) |
| `====Derived terms====` | Words derived from this word ({{der}}) |
| `====Related terms====` | Etymologically related words |
| `====Descendants====` | Words in other languages descended from this one |
| `====Translations====` | {{trans-top}} / {{t}} / {{trans-bottom}} |
| `====See also====` | Related words for comparison |

---

## Template Families

### Inflection Templates (by Language)

| Language | Noun | Verb | Adjective |
|----------|------|------|-----------|
| English | {{en-noun}} | {{en-verb}} | {{en-adj}} |
| French | {{fr-noun}} | {{fr-verb}} | {{fr-adj}} |
| Spanish | {{es-noun}} | {{es-verb}} | {{es-adj}} |
| German | {{de-noun}} | {{de-verb}} | {{de-adj}} |
| Italian | {{it-noun}} | {{it-verb}} | {{it-adj}} |
| Portuguese | {{pt-noun}} | {{pt-verb}} | {{pt-adj}} |
| Russian | {{ru-noun}} | {{ru-verb}} | {{ru-adj}} |
| Latin | {{la-noun}} | {{la-verb}} | {{la-adj}} |
| Ancient Greek | {{grc-noun}} | {{grc-verb}} | {{grc-adj}} |

### Etymology Templates

| Template | Meaning | Example |
|----------|---------|---------|
| {{der|en|la|verbum}} | Derived from Latin | English "word" ← Latin "verbum" |
| {{bor|en|fr|mot}} | Borrowed from French | |
| {{inh|en|ang|word}} | Inherited from Old English | |
| {{cog|de|Wort}} | Cognate with German | |
| {{etyl|la|en}} | Etymon language (deprecated) | |
| {{m|en|word|gloss}} | Mention a word inline | |

### Pronunciation Templates

| Template | Purpose |
|----------|---------|
| {{IPA|lang|/ˈwɜːd/}} | IPA pronunciation |
| {{audio|lang|filename.ogg|label}} | Audio pronunciation file |
| {{rhyme|lang|rhyme}} | Rhymes with |
| {{homophones|lang|word1|word2}} | Homophones |
| {{hyphenation|lang|word}} | Syllable breaks |

### Translation Templates

| Template | Purpose |
|----------|---------|
| {{trans-top|meaning}} | Start translation table |
| {{trans-mid}} | Separator (LTR / RTL languages) |
| {{trans-bottom}} | End translation table |
| {{t|lang|word}} | Translation (full) |
| {{t+|lang|word}} | Translation (links to Wiktionary entry) |
| {{qualifier}} | Context label (archaic, formal, slang) |
| {{sense}} | Sense disambiguator |

---

## Language Codes

Wiktionary uses ISO 639 language codes for templates and sections:

| Code | Language | Example Section Header |
|------|----------|-----------------------|
| en | English | `==English==` |
| fr | French | `==French==` |
| de | German | `==German==` |
| es | Spanish | `==Spanish==` |
| it | Italian | `==Italian==` |
| pt | Portuguese | `==Portuguese==` |
| ru | Russian | `==Russian==` |
| zh | Chinese | `==Chinese==` |
| ja | Japanese | `==Japanese==` |
| ar | Arabic | `==Arabic==` |

Section headers use the **English name** of the language, not the ISO code.
Template parameters use the **ISO code** (e.g., `{{t|fr|mot}}` for French).

---

## API Response Shape

```json
{
  "parse": {
    "title": "word",
    "pageid": 12345,
    "wikitext": {
      "*": "==English==\n===Noun===\n{{en-noun}}\n# A unit of language..."
    },
    "langlinks": [
      {"lang": "fr", "url": "...", "*": "mot"},
      {"lang": "es", "url": "...", "*": "palabra"}
    ],
    "categories": [
      {"sortkey": "word", "*": "English nouns"}
    ]
  }
}
```
