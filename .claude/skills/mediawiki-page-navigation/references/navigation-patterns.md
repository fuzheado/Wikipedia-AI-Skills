# Navigation Pattern Catalog

Complete catalog of navigation patterns with ready-to-use wikitext.

---

## 1. Horizontal Menu Bar (AvoinGLAM style)

A horizontal bar of links rendered from a bullet list with Flexbox CSS.

### Wikitext
```wikitext
<div class="menu">
* [[Special:MyLanguage/Project|Home]]
* [[Special:MyLanguage/Project/About|About]]
* [[Special:MyLanguage/Project/Activities|Activities]]
* [[Special:MyLanguage/Project/Contact|Contact]]
</div>
```

### CSS
```css
.menu ul {
    display: flex;
    list-style: none;
    margin: 0;
    flex-wrap: wrap;
}
.menu ul li {
    font-weight: bold;
    padding: 1rem 0;
    margin-right: 1.5rem;
}
.menu ul li:hover {
    box-shadow: inset 0 -2px 0 #0E65C0;
}
```

---

## 2. Vertical Sidebar Menu

A vertical list of links, often used on content wikis.

### Wikitext
```wikitext
<div class="sidebar-menu">
* [[Project/Section1|Section 1]]
** [[Project/Section1/Sub1|Sub-section 1]]
** [[Project/Section1/Sub2|Sub-section 2]]
* [[Project/Section2|Section 2]]
* [[Project/Section3|Section 3]]
</div>
```

### CSS
```css
.sidebar-menu {
    font-family: "Montserrat", sans-serif;
}
.sidebar-menu ul {
    list-style: none;
    margin: 0;
    padding: 0;
}
.sidebar-menu ul li {
    padding: 0.3em 0;
}
.sidebar-menu ul li ul {
    padding-left: 1em;
}
.sidebar-menu a {
    text-decoration: none;
    color: #333;
}
.sidebar-menu a:hover {
    color: #0E65C0;
}
```

---

## 3. Tab Navigation

Horizontal tabs for switching between subpages.

### Wikitext
```wikitext
<div class="tabs">
{{#ifeq: {{SUBPAGENAME}} | Overview
| <span class="tab active">Overview</span>
| [[Project/{{BASEPAGENAME}}/Overview|<span class="tab">Overview</span>]]
}}
{{#ifeq: {{SUBPAGENAME}} | Details
| <span class="tab active">Details</span>
| [[Project/{{BASEPAGENAME}}/Details|<span class="tab">Details</span>]]
}}
</div>
```

### CSS
```css
.tabs {
    display: flex;
    border-bottom: 2px solid #0E65C0;
    margin: 1rem 0;
}
.tab {
    padding: 0.5rem 1.5rem;
    font-weight: bold;
    color: #666;
    text-decoration: none;
    border-radius: 8px 8px 0 0;
}
.tab.active {
    background: #0E65C0;
    color: white;
}
.tab:hover:not(.active) {
    background: #f1f4f6;
}
```

---

## 4. Dropdown Sub-Menus

Expandable sub-sections within a horizontal menu (pure CSS).

### Wikitext
```wikitext
<div class="dropdown-menu">
* [[Project/Home|Home]]
* [[Project/Activities|Activities]]
* <span class="dropdown">More ▾
* [[Project/About|About]]
* [[Project/Contact|Contact]]
* [[Project/Help|Help]]
</span>
</div>
```

### CSS
```css
.dropdown {
    position: relative;
    cursor: pointer;
}
.dropdown:hover ul {
    display: flex;
}
.dropdown ul {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    background: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    flex-direction: column;
    z-index: 100;
}
.dropdown ul li {
    padding: 0.5em 1em;
    white-space: nowrap;
}
```

---

## 5. Breadcrumb Trail

Shows the page hierarchy as a navigable trail.

### Template
```wikitext
<!-- Template:Project/Breadcrumbs -->
<div class="breadcrumb">
{{#if: {{#titleparts: {{FULLPAGENAME}} | -1 }}
| [[{{#titleparts: {{FULLPAGENAME}} | 1 }}|{{#titleparts: {{FULLPAGENAME}} | 1 }}]]
| {{#titleparts: {{FULLPAGENAME}} | 1 }}
}}
{{#if: {{#titleparts: {{FULLPAGENAME}} | 2 | 2 }}
| › {{#if: {{#titleparts: {{FULLPAGENAME}} | 3 | 3 }}
    | [[{{#titleparts: {{FULLPAGENAME}} | 2 }}|{{#titleparts: {{FULLPAGENAME}} | 2 | 2 }}]]
    | {{#titleparts: {{FULLPAGENAME}} | 2 | 2 }}
  }}
}}
{{#if: {{#titleparts: {{FULLPAGENAME}} | 3 | 3 }}
| › {{#titleparts: {{FULLPAGENAME}} | 3 | 3 }}
}}
</div>
```

### CSS
```css
.breadcrumb {
    font-size: 0.9rem;
    color: #666;
    margin: 0.5em 0;
}
.breadcrumb a {
    color: #0E65C0;
    text-decoration: none;
}
```

---

## 6. Year-Based Temporal Navigation

Auto-advancing year navigation.

### Wikitext
```wikitext
<div class="year-nav">
{{#ifexist: Project/{{#expr: {{CURRENTYEAR}} - 1 }}
| [[Project/{{#expr: {{CURRENTYEAR}} - 1 }}|◀ {{#expr: {{CURRENTYEAR}} - 1 }}]]
}}
<strong>[[Project/{{CURRENTYEAR}}|{{CURRENTYEAR}}]]</strong>
{{#ifexist: Project/{{#expr: {{CURRENTYEAR}} + 1 }}
| [[Project/{{#expr: {{CURRENTYEAR}} + 1 }}|{{#expr: {{CURRENTYEAR}} + 1 }} ▶]]
}}
</div>
```

---

## 7. Language Switching Menu

A dropdown or list for switching between translated versions.

### Wikitext
```wikitext
<div class="lang-menu">
* [[{{FULLPAGENAME}}/en|English]]
* [[{{FULLPAGENAME}}/fi|Suomi]]
* [[{{FULLPAGENAME}}/fr|Français]]
* [[{{FULLPAGENAME}}/de|Deutsch]]
</div>
```

### CSS
```css
.lang-menu ul {
    display: flex;
    list-style: none;
    gap: 0.5em;
    flex-wrap: wrap;
}
.lang-menu ul li {
    padding: 0.2em 0.6em;
    border-radius: 1em;
    background: #f1f4f6;
    font-size: 0.9em;
}
```

---

## 8. Pagination (Page Numbers)

For multi-page documents or galleries.

### Wikitext
```wikitext
<div class="pagination">
[[Project/Page1|1]]
[[Project/Page2|2]]
<strong>3</strong>
[[Project/Page4|4]]
[[Project/Page5|5]]
</div>
```

### CSS
```css
.pagination {
    display: flex;
    gap: 0.3em;
    justify-content: center;
    margin: 1em 0;
}
.pagination a, .pagination strong {
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    text-decoration: none;
}
.pagination strong {
    background: #0E65C0;
    color: white;
}
.pagination a {
    color: #0E65C0;
    border: 1px solid #ddd;
}
```

---

## 9. Search + Filter Bar

A combined search input and filter dropdown (requires VisualEditor or JS).

### Wikitext
```wikitext
<div class="search-bar">
<input type="search" placeholder="Search..." />
<select><option>All</option><option>Category 1</option></select>
</div>
```

### CSS
```css
.search-bar {
    display: flex;
    gap: 0.5em;
    background: #f1f4f6;
    padding: 1em;
    border-radius: 8px;
    margin: 1em 0;
}
.search-bar input, .search-bar select {
    padding: 0.5em;
    border: 1px solid #ddd;
    border-radius: 4px;
    flex: 1;
}
```

---

## 10. Multi-Level Accordion Navigation

Expandable categories with sub-items (revealed on hover).

### Wikitext
```wikitext
<div class="accordion-nav">
<div class="nav-group">
<div class="nav-header">Category 1</div>
<div class="nav-items">[[Page 1]], [[Page 2]]</div>
</div>
<div class="nav-group">
<div class="nav-header">Category 2</div>
<div class="nav-items">[[Page 3]], [[Page 4]]</div>
</div>
</div>
```

### CSS
```css
.nav-group { margin: 0.5em 0; }
.nav-header {
    font-weight: bold;
    cursor: pointer;
    padding: 0.3em 0;
}
.nav-items {
    display: none;
    padding-left: 1em;
}
.nav-group:hover .nav-items {
    display: block;
}
```
