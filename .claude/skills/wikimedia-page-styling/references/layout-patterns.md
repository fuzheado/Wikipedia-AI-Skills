# Layout Pattern Catalog

Reusable CSS Grid and Flexbox layout patterns for wiki pages. Each pattern includes the CSS (for TemplateStyles) and the wikitext to use it.

---

## 1. Responsive Card Grid

The foundational layout — a grid of equally-sized cards that auto-wrap.

### CSS
```css
.card-grid {
    display: grid;
    gap: 1.5rem;
    margin: 1.5rem 0;
    grid-template-columns: repeat(auto-fit, minmax(150px, 219px));
}
```

### Wikitext
```wikitext
<div class="card-grid">
{{Card|title=Item 1}}
{{Card|title=Item 2}}
{{Card|title=Item 3}}
</div>
```

### Variant: Wider Cards
```css
.card-grid-wide {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

### Variant: Equal Columns (no min/max)
```css
.card-grid-3col {
    grid-template-columns: repeat(3, 1fr);
}
@media (max-width: 600px) {
    .card-grid-3col {
        grid-template-columns: 1fr;
    }
}
```

---

## 2. Two-Column Content Layout

For side-by-side text blocks or feature comparisons.

### CSS
```css
.two-column {
    display: grid;
    gap: 2rem;
    grid-template-columns: 1fr 1fr;
}
@media (max-width: 600px) {
    .two-column {
        grid-template-columns: 1fr;
    }
}
```

### Wikitext
```wikitext
<div class="two-column">
<div>Left column content</div>
<div>Right column content</div>
</div>
```

### Variant: 60/40 Split
```css
.two-column-split {
    display: grid;
    gap: 2rem;
    grid-template-columns: 3fr 2fr;
}
```

---

## 3. Hero Banner Layout

A full-width hero image with overlaid text — the AvoinGLAM pattern.

### CSS
```css
.banner {
    position: relative;
    max-height: 450px;
    min-height: 200px;
    overflow-y: clip;
    width: 100%;
    background-color: black;
}
.bannerbackground {
    height: 100%;
    width: 100%;
    position: relative;
    display: flex;
    flex-direction: row;
    padding: 3rem 4rem;
    box-sizing: border-box;
    gap: 1em;
}
.bannertexts {
    font-family: "Montserrat", sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 1rem;
}
.bannertitle {
    font-weight: bold;
    font-size: 4rem;
}
.bannerbody {
    font-size: 2rem;
    line-height: 1.3;
}
.bannertime {
    font-size: 1rem;
    background: black;
    color: white;
    border-radius: 1em;
    padding: 0.1em 1em;
    width: max-content;
}
@media (max-width: 600px) {
    .bannerbackground {
        flex-direction: column;
        padding: 2rem;
    }
    .bannertitle { font-size: 2rem; }
    .bannerbody { font-size: 1rem; }
}
```

### Wikitext
```wikitext
<div class="banner">
<div class="mainimage">[[File:hero.jpg|1500px]]</div>
<div class="header">
<div class="bannerbackground">
<div class="bannertexts">
<div class="bannertitle">Project Title</div>
<div class="bannerbody">Subtitle or description</div>
<div class="bannertime">Date • Location</div>
</div></div></div></div>
```

---

## 4. Featured + Sidebar Layout

A main content area with a sidebar — useful for dashboards.

### CSS
```css
.featured-layout {
    display: grid;
    gap: 1.5rem;
    grid-template-columns: 2fr 1fr;
}
@media (max-width: 800px) {
    .featured-layout {
        grid-template-columns: 1fr;
    }
}
```

### Wikitext
```wikitext
<div class="featured-layout">
<div>
  {{FeaturedCard|title=Main Content}}
</div>
<div>
  {{Card|title=Sidebar 1}}
  {{Card|title=Sidebar 2}}
</div>
</div>
```

---

## 5. Flexible Box Row

A horizontal row of unequally-sized elements that wrap.

### CSS
```css
.flex-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin: 1.5rem 0;
    align-items: flex-start;
}
.flex-row > .quarter {
    flex: 1 1 26%;
    min-width: 200px;
}
.flex-row > .third {
    flex: 1 1 30%;
    min-width: 200px;
}
.flex-row > .half {
    flex: 1 1 45%;
    min-width: 250px;
}
```

### Wikitext
```wikitext
<div class="flex-row">
<div class="half">{{Card|title=Big Feature}}</div>
<div class="quarter">{{Card|title=Small 1}}</div>
<div class="quarter">{{Card|title=Small 2}}</div>
</div>
```

---

## 6. Blog / Magazine Layout

A featured first item spanning full width, followed by a grid of smaller items.

### CSS
```css
.blog-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 1.5rem 0;
}
.blog-grid > div:first-child {
    grid-column: 1 / -1;
}
```

### Wikitext
```wikitext
<div class="blog-grid">
<div>{{BlogCard|title=Featured Article|...}}</div>
<div>{{BlogCard|title=Article 1}}</div>
<div>{{BlogCard|title=Article 2}}</div>
<div>{{BlogCard|title=Article 3}}</div>
</div>
```

---

## 7. Icon + Text Row

For contact lists, metadata rows, or social links.

### CSS
```css
.icon-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
    align-items: center;
}
.icon-row img {
    width: 1.2em;
    height: 1.2em;
    vertical-align: middle;
}
```

### Wikitext
```wikitext
<div class="icon-row">
<span>[[File:Mail icon.svg|20px]] email@example.org</span>
<span>[[File:Globe icon.svg|20px]] website.org</span>
</div>
```

---

## 8. Button Group

Horizontally centered pill buttons.

### CSS
```css
.button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin: 1rem 0;
}
```

### Wikitext
```wikitext
<div class="button-group">
[[Project/Page1|<span class="btn bluebtn">Option 1</span>]]
[[Project/Page2|<span class="btn whitebtn">Option 2</span>]]
</div>
```

---

## 9. Avatar + Details Layout

For contact cards or user profiles.

### CSS
```css
.avatar-row {
    display: flex;
    gap: 1em;
    align-items: center;
}
.avatar-row img {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
}
.avatar-details {
    display: flex;
    flex-direction: column;
}
.avatar-name {
    font-weight: bold;
}
.avatar-role {
    color: #666;
    font-size: 0.9em;
}
```

### Wikitext
```wikitext
<div class="avatar-row">
[[File:Portrait.jpg|60px]]
<div class="avatar-details">
<div class="avatar-name">Name</div>
<div class="avatar-role">Role / Title</div>
</div>
</div>
```

---

## 10. Accordion / Expandable Section

A clickable row that reveals content on hover.

### CSS
```css
.expand-row {
    border-radius: 8px;
    padding: 1em;
    cursor: pointer;
}
.expand-row:hover {
    background: #f1f4f6;
}
.expand-row-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
}
.expand-row-body {
    display: none;
    margin-top: 1em;
}
.expand-row:hover .expand-row-body {
    display: block;
}
```

### Wikitext
```wikitext
<div class="expand-row">
<div class="expand-row-header">
<span>Section Title</span>
<span>▶</span>
</div>
<div class="expand-row-body">
Hidden content revealed on hover.
</div>
</div>
```

---

## 11. Responsive Logo Wall

A flex layout for partner/organization logos.

### CSS
```css
.logo-wall {
    display: flex;
    gap: 2em;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
    margin: 1.5em 0;
}
.logo-wall img {
    max-height: 60px;
    max-width: 150px;
    object-fit: contain;
}
```

### Wikitext
```wikitext
<div class="logo-wall">
[[File:Logo1.png|150px]]
[[File:Logo2.png|150px]]
[[File:Logo3.png|150px]]
</div>
```

---

## 12. Table-Alternative: Grid Data Display

Use CSS Grid as an alternative to `<table>` for structured data.

### CSS
```css
.data-grid {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 0.5em;
    margin: 1em 0;
}
.data-grid .label {
    font-weight: bold;
    color: #666;
}
```

### Wikitext
```wikitext
<div class="data-grid">
<span class="label">Founded</span><span>2012</span>
<span class="label">Members</span><span>42</span>
<span class="label">Location</span><span>Helsinki, Finland</span>
</div>
```
