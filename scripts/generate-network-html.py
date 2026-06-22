#!/usr/bin/env python3
"""Convert skills-network.dot to an interactive HTML force-directed graph."""
import re, json

with open("docs/skills-network.dot") as f:
    dot = f.read()

# Parse nodes
nodes = {}
for m in re.finditer(r'"([^"]+)"\s*\[label="([^"]+)",\s*fillcolor="([^"]+)",', dot):
    name = m.group(1)
    nodes[name] = {"id": name, "label": m.group(2), "color": m.group(3)}

# Parse edges
edges = []
for m in re.finditer(r'"([^"]+)"\s*->\s*"([^"]+)"', dot):
    edges.append({"source": m.group(1), "target": m.group(2)})

# Build domain groups
domains = {}
for name in nodes:
    # Extract domain for grouping
    if name.startswith("wikimedia-api") or name.startswith("wikimedia-auth") or name.startswith("wikimedia-security") or name.startswith("wikipedia-error") or name.startswith("wikimedia-diffs"):
        d = "APIs & Auth"
    elif name.startswith("wikidata") or name.startswith("wikimedia-search") or name.startswith("wikimedia-pageviews") or name.startswith("wikimedia-page-assessment"):
        d = "Wikidata & Search"
    elif name.startswith("wikimedia-commons") or name.startswith("commons-file"):
        d = "Commons"
    elif name.startswith("wikimedia-toolforge") or name.startswith("toolforge") or name.startswith("wikimedia-database") or name.startswith("wikimedia-eventstreams") or name.startswith("wikimedia-i18n") or name.startswith("wikimedia-ml") or name.startswith("wikimedia-cdn") or name.startswith("wikimedia-phabricator"):
        d = "Toolforge & Infra"
    elif name.startswith("wikipedia-cat") or name.startswith("wikipedia-cit") or name.startswith("wikipedia-page") or name.startswith("wikipedia-talk") or name.startswith("wikipedia-templ") or name.startswith("wikipedia-wiki") or name.startswith("wikipedia-en") or name.startswith("wikipedia-notab") or name.startswith("wikipedia-ref"):
        d = "Content & Editing"
    elif name.startswith("mediawiki") or name.startswith("pywikibot") or name.startswith("wiktionary"):
        d = "Tools & Special"
    else:
        d = "Other"
    domains[name] = d

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wikipedia AI Skills — Interactive Network (45 skills, 227 edges)</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif; background: #1a1a2e; overflow: hidden; }}
svg {{ width: 100vw; height: 100vh; }}
.links line {{ stroke: #555; stroke-opacity: 0.4; }}
.links line.highlighted {{ stroke: #ff6b6b; stroke-opacity: 0.8; stroke-width: 1.5; }}
.nodes circle {{ stroke: #fff; stroke-width: 1; cursor: pointer; }}
.nodes circle.highlighted {{ stroke: #ff6b6b; stroke-width: 2.5; }}
.labels text {{ font-size: 9px; fill: #ddd; pointer-events: none; text-anchor: middle; }}
.labels text.highlighted {{ fill: #ff6b6b; font-weight: bold; font-size: 10px; }}
.tooltip {{
    position: absolute; background: rgba(0,0,0,0.85); color: #fff; padding: 8px 12px;
    border-radius: 6px; font-size: 12px; pointer-events: none; max-width: 280px;
    border: 1px solid rgba(255,255,255,0.2); line-height: 1.5;
}}
.legend {{ position: absolute; top: 15px; right: 15px; background: rgba(0,0,0,0.7); padding: 10px 14px; border-radius: 8px; font-size: 11px; color: #ccc; }}
.legend-item {{ display: flex; align-items: center; margin: 4px 0; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }}
.stats {{ position: absolute; bottom: 15px; left: 15px; color: #888; font-size: 11px; }}
</style>
</head>
<body>
<svg></svg>
<div class="tooltip" style="display:none"></div>
<div class="legend">
  <div class="legend-item"><span class="legend-dot" style="background:#e3f2fd"></span> APIs & Auth</div>
  <div class="legend-item"><span class="legend-dot" style="background:#e8f5e9"></span> Wikidata & Search</div>
  <div class="legend-item"><span class="legend-dot" style="background:#fff3e0"></span> Commons</div>
  <div class="legend-item"><span class="legend-dot" style="background:#fce4ec"></span> Toolforge & Infra</div>
  <div class="legend-item"><span class="legend-dot" style="background:#e1bee7"></span> Content & Editing</div>
  <div class="legend-item"><span class="legend-dot" style="background:#c8e6c9"></span> Tools & Special</div>
</div>
<div class="stats">45 skills · 227 cross-references · Drag to explore · Scroll to zoom</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {{
  nodes: {json.dumps([{"id": n["id"], "label": n["label"], "color": n["color"], "domain": domains[n["id"]]} for n in nodes.values()])},
  links: {json.dumps(edges)}
}};

const W = window.innerWidth, H = window.innerHeight;

const svg = d3.select("svg"),
      tooltip = d3.select(".tooltip");

const g = svg.append("g");

svg.call(d3.zoom().scaleExtent([0.2, 4]).on("zoom", (e) => g.attr("transform", e.transform)));

const sim = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(120))
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(W/2, H/2))
    .force("collision", d3.forceCollide().radius(30));

// Group forces by domain
const domains = [...new Set(data.nodes.map(d => d.domain))];
const domainCenters = domains.map((d, i) => {{
    const angle = (2 * Math.PI * i) / domains.length;
    return {{ domain: d, x: W/2 + 300 * Math.cos(angle), y: H/2 + 200 * Math.sin(angle) }};
}});
sim.force("x", d3.forceX(d => domainCenters.find(dc => dc.domain === d.domain)?.x || W/2).strength(0.05));
sim.force("y", d3.forceY(d => domainCenters.find(dc => dc.domain === d.domain)?.y || H/2).strength(0.05));

const link = g.append("g").attr("class", "links").selectAll("line")
    .data(data.links).join("line");

const node = g.append("g").attr("class", "nodes").selectAll("circle")
    .data(data.nodes).join("circle")
    .attr("r", d => 4 + (data.links.filter(l => l.source.id === d.id || l.target.id === d.id).length) * 1.2)
    .attr("fill", d => d.color)
    .call(d3.drag()
        .on("start", (e, d) => {{ if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
        .on("drag", (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
        .on("end", (e, d) => {{ if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

const label = g.append("g").attr("class", "labels").selectAll("text")
    .data(data.nodes).join("text")
    .text(d => d.label)
    .attr("dy", d => 4 + (data.links.filter(l => l.source.id === d.id || l.target.id === d.id).length) * 1.2 + 10);

node.on("mouseover", function(e, d) {{
    tooltip.style("display", "block")
        .html(`<strong>${{d.id}}</strong><br>Domain: ${{d.domain}}<br>Links: ${{data.links.filter(l => l.source.id === d.id).length}} out, ${{data.links.filter(l => l.target.id === d.id).length}} in`);
    // Highlight connected
    const connected = new Set();
    data.links.forEach(l => {{ if (l.source.id === d.id) connected.add(l.target.id); if (l.target.id === d.id) connected.add(l.source.id); }});
    connected.add(d.id);
    node.classed("highlighted", n => connected.has(n.id));
    label.classed("highlighted", n => connected.has(n.id));
    link.classed("highlighted", l => l.source.id === d.id || l.target.id === d.id);
}}).on("mousemove", function(e) {{
    tooltip.style("left", (e.pageX + 15) + "px").style("top", (e.pageY - 10) + "px");
}}).on("mouseout", function() {{
    tooltip.style("display", "none");
    node.classed("highlighted", false);
    label.classed("highlighted", false);
    link.classed("highlighted", false);
}});

sim.on("tick", () => {{
    link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    node.attr("cx", d => d.x).attr("cy", d => d.y);
    label.attr("x", d => d.x).attr("y", d => d.y);
}});
</script>
</body>
</html>"""

with open("docs/skills-network.html", "w") as f:
    f.write(html)

print(f"Generated skills-network.html — {len(nodes)} nodes, {len(edges)} edges")
