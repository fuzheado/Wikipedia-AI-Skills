# mwparserfromhell Reference

[mwparserfromhell](https://github.com/earwig/mwparserfromhell) is an LL(1)-based parser for MediaWiki wikitext. It builds an Abstract Syntax Tree (AST) that you can traverse, filter, and mutate safely.

## Installation

```bash
pip install mwparserfromhell
```

## Core API

### Parsing

```python
import mwparserfromhell

code = mwparserfromhell.parse(wikitext_string)
# code is a Wikicode object — the root of the AST
```

### Node Types

| Node type | Description | Examples |
|-----------|-------------|----------|
| `Template` | `{{...}}` (including parser functions like `{{#if:}}`) | `{{Infobox}}, {{#expr:}}` |
| `Wikilink` | `[[...]]` | `[[Page]]`, `[[Page|text]]` |
| `ExternalLink` | `[...]` | `[https://example.com text]` |
| `Tag` | `<...>` or `<.../>` | `<ref>`, `<nowiki/>`, `<syntaxhighlight>` |
| `Heading` | `==...==`, `===...===`, etc. | `== Section ==` |
| `Comment` | `<!-- ... -->` | `<!-- hidden -->` |
| `Argument` | `{{{...}}}` | `{{{1}}}`, `{{{param\|default}}}` |
| `HTMLEntity` | `&...;` | `&amp;`, `&lt;`, `&nbsp;` |

### Filtering Methods

All return generators — wrap in `list()` if you need indexing:

```python
code.filter_templates()          # All templates
code.filter_templates(matches="Infobox")  # Name starts with "Infobox"
code.filter_templates(matches=lambda n: n.startswith("Infobox"))

code.filter_wikilinks()          # All [[...]]
code.filter_external_links()     # All [http...]
code.filter_tags()               # All <tag>...</tag>
code.filter_headings()           # All == headings ==
code.filter_comments()           # All <!-- comments -->
code.filter_arguments()          # All {{{...}}}
```

### Template Access

```python
template = code.filter_templates(matches="Infobox person")[0]

# Read a parameter
name = template.get("name").value          # Raises ValueError if missing
if template.has("birth_date"):
    bd = template.get("birth_date").value

# Iterate all parameters
for param in template.params:
    print(f"{param.name}: {param.value}")

# Modify a parameter
template.add("name", "New Value")          # Adds or replaces
template.add("name", "New", showkey=False) # Hides the key for positional params

# Remove a parameter
template.remove("obsolete_param")

# Parameter name normalization
# "Birth Date", "birth_date", "Birth date" all match the same param
```

### Wikilink Access

```python
for link in code.filter_wikilinks():
    title = link.title                     # Page title (without [[ ]])
    text = link.text                       # Display text (after |), or None
    # link.title has .strip() for whitespace handling
```

### Section Handling

```python
# Get sections by level
sections = code.get_sections(levels=[2])   # == Level 2 sections ==

# Get sections including all subsections
sections = code.get_sections(levels=[2], flat=False)

# Each section as its own Wikicode object
for section in code.get_sections():
    headings = list(section.filter_headings())
    if headings:
        print(f"Section: {headings[0].title}")
```

### String Conversion

```python
str(code)               # Full wikitext with all markup
code.strip_code()       # Plain text, no markup — removes templates, comments, tags
```

**⚠️ `strip_code()` removes:**
- HTML comments (`<!-- ... -->`)
- Templates (replaced with nothing)
- `<ref>` tags and their content
- All wiki markup

**`strip_code()` preserves:**
- Inter-word spacing
- External URLs
- Remaining plain text

### Node Tree Traversal

```python
# Get parent node
node.parent              # The Wikicode object containing this node

# Get index within parent
node.index               # Position in parent's nodes list

# Nodes within a node (e.g., templates within a template parameter)
for child in template.get("param").value.ifilter_templates():
    print(child.name)
```

## Common Patterns

### Extract Infobox Data

```python
code = mwparserfromhell.parse(wikitext)
infoboxes = code.filter_templates(matches=lambda n: n.startswith("Infobox"))

for ib in infoboxes:
    data = {}
    for param in ib.params:
        name = str(param.name).strip()
        value = str(param.value).strip()
        data[name] = value
    print(data)
```

### Extract All Citations

```python
code = mwparserfromhell.parse(wikitext)
citations = []
for tag in code.filter_tags():
    if hasattr(tag, "tag") and str(tag.tag).lower() == "ref":
        # Check for self-closing ref like <ref name="auto" />
        content = tag.contents if tag.contents else ""
        citations.append(content)
```

### Split Page into Sections

```python
code = mwparserfromhell.parse(wikitext)
sections = {}
current_heading = "Lead"

for node in code.nodes:
    if isinstance(node, mwparserfromhell.nodes.Heading):
        current_heading = str(node.title).strip()
        sections[current_heading] = []
    else:
        if current_heading not in sections:
            sections[current_heading] = []
        sections[current_heading].append(str(node))
```

### Find All Internal Links on a Page

```python
links = set()
for link in code.filter_wikilinks():
    title = str(link.title).strip()
    # Skip categories, files, interwiki links
    if not title.startswith(("Category:", "File:", "Image:", ":")):
        # Normalize underscores and first-letter capitalization
        title = title.replace("_", " ")
        links.add(title)
```

## Performance

- For very large pages (>500KB wikitext), parsing may take several seconds.
- Cache parsed Wikicode objects if you need to query them multiple times.
- Use generator-based `filter_*()` methods (lazy) rather than collecting lists unless you need indexing.
- `str(code)` forces a full serialization — avoid calling it repeatedly.

## Known Limitations

- Does **not** evaluate templates or parser functions — it only parses syntax, not semantics.
- Does **not** follow transclusions — `{{Foo}}` is a template call, but the parser won't expand it.
- The `strip_code()` output is not guaranteed to match the rendered page text (template expansion, magic words, etc. would require a full MediaWiki parse).
- Changes to the AST do not affect the original string — you must call `str(code)` to get updated wikitext.
