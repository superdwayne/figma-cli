"""Design data extractor — pull structured design information from Figma nodes.

Extracts colors, typography, spacing, layout, and component structure
into a normalized format that codegen and create commands can consume.
"""
from typing import Any


def extract_color(figma_color: dict) -> str:
    """Convert Figma RGBA dict to hex string."""
    if not figma_color or not isinstance(figma_color, dict):
        return "#000000"
    r = int(figma_color.get("r", 0) * 255)
    g = int(figma_color.get("g", 0) * 255)
    b = int(figma_color.get("b", 0) * 255)
    a = figma_color.get("a", 1.0)
    if a < 1.0:
        return f"rgba({r}, {g}, {b}, {a:.2f})"
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_fills(node: dict) -> list[str]:
    """Extract fill colors from a Figma node."""
    fills = []
    for fill in node.get("fills", []):
        if fill.get("type") == "SOLID" and fill.get("visible", True):
            fills.append(extract_color(fill.get("color", {})))
        elif fill.get("type") == "GRADIENT_LINEAR":
            stops = fill.get("gradientStops", [])
            colors = [extract_color(s.get("color", {})) for s in stops]
            fills.append(f"linear-gradient({', '.join(colors)})")
    return fills


def extract_typography(node: dict) -> dict | None:
    """Extract typography info from a TEXT node."""
    if node.get("type") != "TEXT":
        return None
    style = node.get("style", {})
    return {
        "content": node.get("characters", ""),
        "font_family": style.get("fontFamily", "Inter"),
        "font_size": style.get("fontSize", 16),
        "font_weight": style.get("fontWeight", 400),
        "font_style": style.get("fontStyle", "Regular"),
        "text_align": style.get("textAlignHorizontal", "LEFT").lower(),
        "line_height": style.get("lineHeightPx"),
        "letter_spacing": style.get("letterSpacing", 0),
        "color": extract_fills(node)[0] if extract_fills(node) else "#000000",
    }


def extract_layout(node: dict) -> dict:
    """Extract layout/positioning info from a node."""
    bbox = node.get("absoluteBoundingBox", {})
    return {
        "x": bbox.get("x", 0),
        "y": bbox.get("y", 0),
        "width": bbox.get("width", 0),
        "height": bbox.get("height", 0),
        "layout_mode": node.get("layoutMode"),
        "padding_top": node.get("paddingTop", 0),
        "padding_right": node.get("paddingRight", 0),
        "padding_bottom": node.get("paddingBottom", 0),
        "padding_left": node.get("paddingLeft", 0),
        "item_spacing": node.get("itemSpacing", 0),
        "corner_radius": node.get("cornerRadius", 0),
        "clips_content": node.get("clipsContent", False),
    }


def extract_node(node: dict, parent_bbox: dict | None = None) -> dict:
    """Extract a normalized representation of a Figma node."""
    bbox = node.get("absoluteBoundingBox", {})
    layout = extract_layout(node)

    # Calculate position relative to parent
    rel_x = bbox.get("x", 0) - (parent_bbox.get("x", 0) if parent_bbox else 0)
    rel_y = bbox.get("y", 0) - (parent_bbox.get("y", 0) if parent_bbox else 0)

    result = {
        "id": node.get("id"),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "x": rel_x,
        "y": rel_y,
        "width": layout["width"],
        "height": layout["height"],
        "fills": extract_fills(node),
        "corner_radius": layout["corner_radius"],
        "opacity": node.get("opacity", 1.0),
        "visible": node.get("visible", True),
    }

    # Layout properties for auto-layout frames
    if layout["layout_mode"]:
        result["layout"] = {
            "mode": layout["layout_mode"],
            "padding": [layout["padding_top"], layout["padding_right"],
                        layout["padding_bottom"], layout["padding_left"]],
            "gap": layout["item_spacing"],
        }

    # Stroke
    strokes = node.get("strokes", [])
    if strokes:
        result["stroke"] = extract_color(strokes[0].get("color", {}))
        result["stroke_weight"] = node.get("strokeWeight", 1)

    # Text-specific
    if node.get("type") == "TEXT":
        result["typography"] = extract_typography(node)

    # Children
    children = node.get("children", [])
    if children:
        result["children"] = [
            extract_node(child, bbox) for child in children
            if child.get("visible", True)
        ]

    return result


def extract_colors_from_tree(node: dict, colors: set | None = None) -> set[str]:
    """Recursively collect all unique colors from a node tree."""
    if colors is None:
        colors = set()
    for c in extract_fills(node):
        if c.startswith("#"):
            colors.add(c)
    for child in node.get("children", []):
        extract_colors_from_tree(child, colors)
    return colors


def extract_fonts_from_tree(node: dict, fonts: set | None = None) -> set[str]:
    """Recursively collect all unique font families from a node tree."""
    if fonts is None:
        fonts = set()
    style = node.get("style", {})
    if style.get("fontFamily"):
        fonts.add(style["fontFamily"])
    for child in node.get("children", []):
        extract_fonts_from_tree(child, fonts)
    return fonts
