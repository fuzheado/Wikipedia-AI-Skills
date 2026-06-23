# Wikivoyage Article Skeletons — Section Maps

## Continent (`{{subst:continent skeleton}}`)

```
{{pagebanner|...}}
'''...''' is a continent...
==Destinations==
...
==Other destinations==
* ...
==Understand==
==Get in==
==Get around==
==Stay safe==
==Stay healthy==
==Go next==
```

## Country (`{{subst:country skeleton}}`)

```
{{pagebanner|...}}
{{quickbar}}
'''...''' is a country in...
==Cities==
* ...
==Other destinations==
* ...
==Understand==
===History===
===People===
===Climate===
===Holidays===
==Get in==
===By plane===
===By train===
===By car===
===By bus===
===By boat===
==Get around==
==Talk==
==See==
==Do==
==Buy==
===Money===
===Costs===
==Eat==
==Drink==
==Sleep==
==Stay safe==
==Stay healthy==
==Respect==
==Connect==
==Go next==
```

## Region (`{{subst:region skeleton}}`)

```
{{pagebanner|...}}
'''...''' is a region in...
==Cities==
* ...
==Other destinations==
* ...
==Understand==
==Get in==
==Get around==
==See==
==Do==
==Eat==
==Drink==
==Sleep==
==Stay safe==
==Go next==
```

## Small City (`{{subst:smallcity skeleton}}`)

```
{{pagebanner|...}}
'''...''' is a city in...
==Understand==
===Orientation===
===Climate===
==Get in==
===By plane===
===By train===
===By car===
===By bus===
===By boat===
==Get around==
===By foot===
===By public transit===
===By taxi===
===By car===
==See==
==Do==
==Buy==
==Eat==
==Drink==
==Sleep==
==Connect==
==Go next==
```

## Big City (`{{subst:bigcity skeleton}}`)

Same as Small City plus optional:
```
==Districts==
...
```

## Huge City (`{{subst:hugecity skeleton}}`)

```
{{pagebanner|...}}
{{printDistricts}}
'''...''' is the...
==Districts==
{{Mapframe|...}}
{{Mapshapes|...}}
{{Regionlist
| region1name=...
| region1color=...
| region1description=...
}}
==Understand==
==Get in==
==Get around==
==See==
==Do==
==Buy==
==Eat==
==Drink==
==Sleep==
==Connect==
==Go next==
```

## Park (`{{subst:park skeleton}}`)

```
{{pagebanner|...}}
'''...''' is a national park in...
==Understand==
===History===
===Landscape===
===Flora and fauna===
===Climate===
==Get in==
===Fees and permits===
==Get around==
==See==
==Do==
==Buy==
==Eat==
==Drink==
==Sleep==
===Lodging===
===Camping===
===Backcountry===
==Stay safe==
==Go next==
```

## Travel Topic (`{{subst:Topic article template}}`)

```
{{pagebanner|...}}
'''...''' is a travel topic about...
==Understand==
==Prepare==
==Get in==
==Get around==
==See==
==Do==
==Buy==
==Eat==
==Drink==
==Sleep==
==Stay safe==
==Go next==
```

## Itinerary (`{{subst:Itinerary skeleton}}`)

```
{{pagebanner|...}}
'''...''' is an itinerary...
==Understand==
==Prepare==
==Go==
===Day 1===
===Day 2===
===Day 3===
...
==Stay safe==
==Go next==
```

## Phrasebook (`{{subst:Phrasebook skeleton}}`)

```
{{pagebanner|...}}
'''...''' is a phrasebook covering...
==Pronunciation guide==
===Vowels===
===Consonants===
===Common diphthongs===
==Phrase list==
===Basics===
===Problems===
===Numbers===
===Time===
===Transportation===
===Eating===
===Directions===
...
```

## Common Closing Templates

Every destination article ends with:

```wikitext
{{status_template}}     <!-- {{Usablecity}}, {{Guidecity}}, {{Starcity}}, etc. -->
{{IsPartOf|Parent}}     <!-- Breadcrumb -->
{{geo|lat|long|zoom}}   <!-- Geographic center -->
```

## Quick Decision Tree

```
Is this a destination with hotels/restaurants?
  ├── Is it a single city/town?
  │     ├── Very small? → Small city skeleton
  │     ├── Lots to do? → Big city skeleton
  │     └── Districts needed? → Huge city skeleton
  ├── Is it a collection of places in nature?
  │     ├── Designated park? → Park skeleton
  │     └── Scattered rural? → Rural area skeleton
  ├── Is it a major transit hub?
  │     ├── Airport of city-scale? → Airport skeleton
  │     └── Train/bus station of city-scale? → Station skeleton
  └── Is it a dive site? → Dive site skeleton

Is this NOT a destination?
  ├── General travel advice? → Travel topic skeleton
  ├── Day-by-day route? → Itinerary skeleton
  ├── Language guide? → Phrasebook skeleton
  └── Event? → Event skeleton
```
