#!/usr/bin/env python3
"""
Grid Layout Preview — Generate CSS Grid configuration and visual preview.

Given grid parameters (column min/max widths, gap, number of items), this
script generates the CSS needed and optionally renders a text-based preview
of how the grid will look at various viewport widths.

Usage:
    python3 grid-layout-preview.py --min 150 --max 219 --gap 24
    python3 grid-layout-preview.py --items 12 --columns 3 --gap 16 --output-css
    python3 grid-layout-preview.py --min 200 --max 1fr --gap 32 --preview
"""

import argparse
import math
import sys
import textwrap


def generate_grid_css(col_min, col_max, gap, selector=".grid"):
    """Generate CSS Grid rules for the given configuration."""
    # Determine if max is a fixed value or fr unit
    if col_max.endswith("fr"):
        max_val = col_max
        template = f"repeat(auto-fit, minmax({col_min}, {max_val}))"
    else:
        template = f"repeat(auto-fit, minmax({col_min}, {col_max}))"
    
    css = f"""/* Auto-generated grid — {col_min} to {col_max}, gap {gap} */
{selector} {{
    display: grid;
    gap: {gap};
    margin: 1.5rem 0;
    grid-template-columns: {template};
}}"""
    return css


def estimate_columns(viewport_width, col_min_px, gap_px):
    """Estimate how many columns fit in a given viewport width."""
    # Each column takes at least col_min_px + gap
    # The first column has no left gap, the last has no right gap
    available = viewport_width - gap_px  # Account for one gap
    col_total = col_min_px + gap_px
    cols = max(1, available // col_total)
    return int(cols)


def generate_preview(col_min_px, col_max_px, gap_px, num_items):
    """Generate a text preview of the grid at different viewport widths."""
    viewports = [360, 480, 768, 1024, 1280, 1440]
    # Use the min width for preview calculation
    use_max = col_max_px if col_max_px > 0 else col_min_px * 2
    
    preview_lines = []
    preview_lines.append(f"Grid: min={col_min_px}px, max={use_max}px, gap={gap_px}px")
    preview_lines.append(f"Items: {num_items}")
    preview_lines.append("")
    
    for vp in viewports:
        cols = estimate_columns(vp, col_min_px, gap_px)
        rows = math.ceil(num_items / cols)
        
        label = f"Viewport: {vp}px"
        grid_repr = ""
        for r in range(rows):
            if r == 0:
                grid_repr += "┌"
            else:
                grid_repr += "├"
            
            for c in range(cols):
                item_idx = r * cols + c
                if item_idx < num_items:
                    grid_repr += "──■──"
                else:
                    grid_repr += "─────"
                
                if c < cols - 1:
                    if r == 0:
                        grid_repr += "┬"
                    else:
                        grid_repr += "┼"
            
            if r == 0:
                grid_repr += "┐"
            else:
                grid_repr += "┤"
        
        preview_lines.append(f"  {label} → {cols} cols × {rows} rows  {grid_repr}")
    
    return "\n".join(preview_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate and preview CSS Grid configurations",
    )
    parser.add_argument("--min", default="150px", help="Min column width (default: 150px)")
    parser.add_argument("--max", default="219px", help="Max column width (default: 219px)")
    parser.add_argument("--gap", default="1.5rem", help="Grid gap (default: 1.5rem)")
    parser.add_argument("--selector", default=".grid", help="CSS selector (default: .grid)")
    parser.add_argument("--items", type=int, default=12, help="Number of items for preview (default: 12)")
    parser.add_argument("--columns", type=int, help="Fixed number of columns (instead of auto-fit)")
    parser.add_argument("--output-css", action="store_true", help="Output CSS only")
    parser.add_argument("--preview", action="store_true", help="Show text preview")

    # Show help when invoked with no arguments (all have defaults)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    
    # Generate CSS
    if args.columns:
        css = f"""{args.selector} {{
    display: grid;
    gap: {args.gap};
    margin: 1.5rem 0;
    grid-template-columns: repeat({args.columns}, 1fr);
}}"""
    else:
        css = generate_grid_css(args.min, args.max, args.gap, args.selector)
    
    if args.output_css:
        print(css)
        return
    
    # Show info
    print("")
    print("╔══ Grid Layout Preview ════════════════════════")
    if args.columns:
        print(f"║  Fixed: {args.columns} columns")
    else:
        print(f"║  Responsive: auto-fit, minmax({args.min}, {args.max})")
    print(f"║  Gap: {args.gap}")
    print(f"║  Selector: {args.selector}")
    print(f"║  Items: {args.items}")
    print("╚═══════════════════════════════════════════════")
    print("")
    print(css)
    print("")
    
    if args.preview or not args.output_css:
        # Parse pixel values for preview
        import re
        
        def parse_px(val):
            m = re.match(r'(\d+(?:\.\d+)?)px', val)
            if m:
                return float(m.group(1))
            # Try rem (1rem ≈ 16px)
            m = re.match(r'(\d+(?:\.\d+)?)rem', val)
            if m:
                return float(m.group(1)) * 16
            return 0
        
        col_min_px = parse_px(args.min)
        col_max_px = parse_px(args.max) if not args.max.endswith("fr") else col_min_px * 3
        gap_px = parse_px(args.gap)
        
        if col_min_px > 0:
            print(generate_preview(int(col_min_px), int(col_max_px), int(gap_px), args.items))
        else:
            print("(Preview requires pixel or rem values)")


if __name__ == "__main__":
    main()
