# Design Theme Examples

Complete color palettes and CSS theme examples for wiki page design systems.

---

## Theme 1: Blue Professional (AvoinGLAM style)

A clean, professional blue-and-white theme suitable for project documentation.

### Palette
```
Primary blue:    #0E65C0
Light bg:        #F1F4F6
White:           #FFFFFF
Alert yellow:    #f8eb79
Link blue:       #0E65C0
Dark text:       #333333
```

### CSS
```css
/* Box themes */
.bluebox {
    background: #0E65C0;
    color: white;
}
.bluebox a, .bluebox a:visited {
    color: white;
}
.whitebox {
    background: #F1F4F6;
}
.alertbox {
    background: #f8eb79;
}

/* Buttons */
.btn {
    padding: 0.7rem 1.3rem;
    border-radius: 2rem;
    display: inline-block;
    font-weight: bold;
    white-space: nowrap;
}
.bluebox .btn, .whitebtn {
    color: #0E65C0;
    background: white;
}
.whitebox .btn, .bluebtn {
    color: white;
    background: #0E65C0;
}
.bluebox .btn:hover {
    background: none;
    outline: 2px solid white;
}
.whitebox .btn:hover {
    background: none;
    outline: 2px solid #0E65C0;
    color: #0E65C0;
}

/* Links */
a, a:visited {
    color: #0E65C0;
}

/* Navigation active state */
.menu a.mw-selflink {
    color: #0E65C0;
}
.menu ul li:hover {
    box-shadow: inset 0 -2px 0 #0E65C0;
}
```

---

## Theme 2: Warm Earthy (Community)

A warm, inviting palette for community-oriented pages.

### Palette
```
Warm brown:     #8B5E3C
Light sand:     #F5F0E8
Accent orange:  #D4764E
Green accent:   #5A8F6A
Dark brown:     #4A3525
```

### CSS
```css
/* Box themes */
.earthbox {
    background: #8B5E3C;
    color: white;
}
.sandbox {
    background: #F5F0E8;
}
.accentbox {
    background: #D4764E;
    color: white;
}

/* Buttons */
.earthbox .btn {
    background: #F5F0E8;
    color: #8B5E3C;
}
.sandbox .btn {
    background: #8B5E3C;
    color: white;
}
.earthbox .btn:hover {
    background: none;
    outline: 2px solid #F5F0E8;
}

/* Typography */
h1, h2, h3 {
    font-family: Georgia, serif;
    color: #4A3525;
}
```

---

## Theme 3: Dark Dashboard

A dark theme suitable for dashboards, data displays, or minimal-chrome pages.

### Palette
```
Dark bg:        #1A1D23
Card bg:        #2D3139
Accent teal:    #00B4D8
Accent purple:  #7B2CBF
Text white:     #E8E8E8
Text gray:      #9CA3AF
```

### CSS
```css
.darkbox {
    background: #2D3139;
    color: #E8E8E8;
}
.darkbox h2, .darkbox h3 {
    color: white;
}
.accent-teal {
    background: #00B4D8;
    color: white;
}
.accent-purple {
    background: #7B2CBF;
    color: white;
}

/* Page background override */
body.skin-vector {
    background: #1A1D23 !important;
}

/* Buttons */
.darkbox .btn {
    background: #00B4D8;
    color: white;
}
.darkbox .btn:hover {
    background: none;
    outline: 2px solid #00B4D8;
}
```

---

## Theme 4: High Contrast (Accessibility)

Meets WCAG AA/AAA contrast requirements.

### Palette
```
Background:     #FFFFFF
Text:           #000000
Links:          #1A0DAB (or #0033CC)
Visited:        #6600CC
Focus ring:     #FFBF00 (3px)
Borders:        #000000
```

### CSS
```css
/* High contrast theme */
.hc-box {
    background: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
}

.hc-box a, .hc-box a:visited {
    color: #1A0DAB;
    text-decoration: underline;
}

.hc-btn {
    background: #000000;
    color: #FFFFFF;
    border: 2px solid #000000;
    padding: 0.5rem 1rem;
    font-weight: bold;
}

.hc-btn:hover {
    background: #FFFFFF;
    color: #000000;
}

/* Focus indicators */
*:focus-visible {
    outline: 3px solid #FFBF00;
    outline-offset: 2px;
}
```

---

## Theme 5: Colorful Columns (Calendar / Program)

For programs, timelines, or category displays with many color-coded sections.

### CSS
```css
.col1 { background: #f6b264; }
.col2 { background: #bb5e2d; }
.col3 { background: #b6d0c0; }
.col4 { background: #25a3ac; }
.col5 { background: #045a70; color: white; }
.col6 { background: #e98036; }
.col7 { background: #f0d4aa; }
.col8 { background: #4eacb7; }
```

### Usage
```wikitext
<div class="col1">Phase 1</div>
<div class="col2">Phase 2</div>
```

---

## ⚠️ Using Web Fonts

TemplateStyles supports `@font-face` but the font file must be hosted on Wikimedia servers (not a CDN like Google Fonts).

To use Montserrat (as AvoinGLAM does):

1. Upload the font `.woff2` file to Commons
2. Declare it in your CSS:

```css
@font-face {
    font-family: 'Montserrat';
    src: url('//commons.wikimedia.org/w/index.php?title=File:Montserrat-Regular.woff2') format('woff2');
    font-weight: normal;
}
@font-face {
    font-family: 'Montserrat';
    src: url('//commons.wikimedia.org/w/index.php?title=File:Montserrat-Bold.woff2') format('woff2');
    font-weight: bold;
}
```

Alternatively, use system fonts which are always available:

```css
font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
```
