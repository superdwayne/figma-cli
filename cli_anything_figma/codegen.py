"""Code generation engine — turn extracted Figma node data into HTML/CSS/React.

This is the core of the agent design workflow:
  Figma file → extract node tree → generate code → preview locally
"""
import json
from typing import Any

from cli_anything_figma.extractor import extract_node, extract_color, extract_fills


# ── HTML/CSS Generator ──────────────────────────────────────

def _css_props(node: dict) -> dict[str, str]:
    """Convert extracted node data to CSS properties."""
    css = {}

    if node.get("width"):
        css["width"] = f"{node['width']}px"
    if node.get("height"):
        css["height"] = f"{node['height']}px"

    fills = node.get("fills", [])
    if fills:
        bg = fills[0]
        if bg.startswith("linear-gradient"):
            css["background"] = bg
        else:
            css["background-color"] = bg

    if node.get("corner_radius"):
        css["border-radius"] = f"{node['corner_radius']}px"

    if node.get("stroke"):
        css["border"] = f"{node.get('stroke_weight', 1)}px solid {node['stroke']}"

    if node.get("opacity", 1.0) < 1.0:
        css["opacity"] = str(node["opacity"])

    layout = node.get("layout")
    if layout:
        mode = layout["mode"]
        if mode == "HORIZONTAL":
            css["display"] = "flex"
            css["flex-direction"] = "row"
        elif mode == "VERTICAL":
            css["display"] = "flex"
            css["flex-direction"] = "column"

        pad = layout.get("padding", [0, 0, 0, 0])
        if any(p > 0 for p in pad):
            css["padding"] = f"{pad[0]}px {pad[1]}px {pad[2]}px {pad[3]}px"

        gap = layout.get("gap", 0)
        if gap > 0:
            css["gap"] = f"{gap}px"

    typo = node.get("typography")
    if typo:
        css["font-family"] = f"'{typo['font_family']}', sans-serif"
        css["font-size"] = f"{typo['font_size']}px"
        css["font-weight"] = str(typo["font_weight"])
        css["color"] = typo["color"]
        if typo.get("line_height"):
            css["line-height"] = f"{typo['line_height']}px"
        if typo.get("letter_spacing"):
            css["letter-spacing"] = f"{typo['letter_spacing']}px"
        css["text-align"] = typo.get("text_align", "left")

    return css


def _css_string(props: dict[str, str], indent: int = 2) -> str:
    """Format CSS properties as a string."""
    pad = " " * indent
    return "\n".join(f"{pad}{k}: {v};" for k, v in props.items())


def _safe_class(name: str) -> str:
    """Convert a Figma node name to a valid CSS class name."""
    return (
        name.lower()
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "-")
        .replace(":", "-")
        .replace(".", "-")
        .replace("#", "")
        .strip("-")
    ) or "element"


def _node_to_html(node: dict, classes: dict, depth: int = 0) -> str:
    """Recursively convert an extracted node to HTML."""
    indent = "  " * depth
    cls = _safe_class(node.get("name", "element"))

    # Ensure unique class names
    base_cls = cls
    counter = 1
    while cls in classes and classes[cls] != node.get("id"):
        cls = f"{base_cls}-{counter}"
        counter += 1
    classes[cls] = node.get("id")

    css = _css_props(node)

    ntype = node.get("type", "")
    typo = node.get("typography")

    if ntype == "TEXT" and typo:
        content = typo.get("content", "")
        font_size = typo.get("font_size", 16)
        font_weight = typo.get("font_weight", 400)

        if font_size >= 32 or font_weight >= 700:
            tag = "h1" if font_size >= 48 else "h2" if font_size >= 32 else "h3"
        elif font_size >= 20:
            tag = "h3"
        else:
            tag = "p"

        return f'{indent}<{tag} class="{cls}">{content}</{tag}>'

    children = node.get("children", [])
    if not children:
        return f'{indent}<div class="{cls}"></div>'

    child_html = "\n".join(
        _node_to_html(c, classes, depth + 1)
        for c in children
        if c.get("visible", True)
    )
    return f'{indent}<div class="{cls}">\n{child_html}\n{indent}</div>'


def generate_html(extracted_node: dict, title: str = "Design") -> str:
    """Generate a complete HTML file from an extracted Figma node."""
    classes: dict[str, str] = {}
    body_html = _node_to_html(extracted_node, classes, depth=2)

    # Build CSS
    all_css = []
    _collect_css(extracted_node, classes, all_css, set())

    css_text = "\n\n".join(all_css)

    fonts = set()
    _collect_fonts(extracted_node, fonts)
    font_links = ""
    if fonts:
        families = "|".join(f.replace(" ", "+") for f in fonts)
        font_links = f'    <link href="https://fonts.googleapis.com/css2?family={families}:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
{font_links}
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; }}

{css_text}
    </style>
</head>
<body>
{body_html}
</body>
</html>"""


def _collect_css(node: dict, classes: dict, result: list, seen: set):
    """Recursively collect CSS rules for all nodes."""
    cls = None
    for c, nid in classes.items():
        if nid == node.get("id"):
            cls = c
            break

    if cls and cls not in seen:
        seen.add(cls)
        css = _css_props(node)
        if css:
            result.append(f"        .{cls} {{\n{_css_string(css, 12)}\n        }}")

    for child in node.get("children", []):
        _collect_css(child, classes, result, seen)


def _collect_fonts(node: dict, fonts: set):
    """Recursively collect font families."""
    typo = node.get("typography")
    if typo and typo.get("font_family"):
        fonts.add(typo["font_family"])
    for child in node.get("children", []):
        _collect_fonts(child, fonts)


# ── React/JSX Generator ─────────────────────────────────────

def _node_to_jsx(node: dict, depth: int = 0) -> str:
    """Convert extracted node to JSX."""
    indent = "  " * depth
    cls = _safe_class(node.get("name", "element"))
    ntype = node.get("type", "")
    typo = node.get("typography")

    if ntype == "TEXT" and typo:
        content = typo.get("content", "")
        font_size = typo.get("font_size", 16)
        font_weight = typo.get("font_weight", 400)

        if font_size >= 32 or font_weight >= 700:
            tag = "h1" if font_size >= 48 else "h2" if font_size >= 32 else "h3"
        elif font_size >= 20:
            tag = "h3"
        else:
            tag = "p"

        return f'{indent}<{tag} className="{cls}">{content}</{tag}>'

    children = node.get("children", [])
    if not children:
        return f'{indent}<div className="{cls}" />'

    child_jsx = "\n".join(
        _node_to_jsx(c, depth + 1)
        for c in children
        if c.get("visible", True)
    )
    return f'{indent}<div className="{cls}">\n{child_jsx}\n{indent}</div>'


def _node_to_tailwind(node: dict, depth: int = 0) -> str:
    """Convert extracted node to JSX with Tailwind classes."""
    indent = "  " * depth
    ntype = node.get("type", "")
    typo = node.get("typography")
    tw = _tailwind_classes(node)

    if ntype == "TEXT" and typo:
        content = typo.get("content", "")
        font_size = typo.get("font_size", 16)
        font_weight = typo.get("font_weight", 400)

        if font_size >= 32 or font_weight >= 700:
            tag = "h1" if font_size >= 48 else "h2" if font_size >= 32 else "h3"
        elif font_size >= 20:
            tag = "h3"
        else:
            tag = "p"

        return f'{indent}<{tag} className="{tw}">{content}</{tag}>'

    children = node.get("children", [])
    if not children:
        return f'{indent}<div className="{tw}" />'

    child_jsx = "\n".join(
        _node_to_tailwind(c, depth + 1)
        for c in children
        if c.get("visible", True)
    )
    return f'{indent}<div className="{tw}">\n{child_jsx}\n{indent}</div>'


def _tailwind_classes(node: dict) -> str:
    """Map node properties to Tailwind utility classes."""
    classes = []

    layout = node.get("layout")
    if layout:
        mode = layout["mode"]
        if mode == "HORIZONTAL":
            classes.append("flex flex-row")
        elif mode == "VERTICAL":
            classes.append("flex flex-col")

        gap = layout.get("gap", 0)
        if gap > 0:
            classes.append(f"gap-[{gap}px]")

        pad = layout.get("padding", [0, 0, 0, 0])
        if all(p == pad[0] for p in pad) and pad[0] > 0:
            classes.append(f"p-[{pad[0]}px]")
        else:
            if pad[0]:
                classes.append(f"pt-[{pad[0]}px]")
            if pad[1]:
                classes.append(f"pr-[{pad[1]}px]")
            if pad[2]:
                classes.append(f"pb-[{pad[2]}px]")
            if pad[3]:
                classes.append(f"pl-[{pad[3]}px]")

    fills = node.get("fills", [])
    if fills and fills[0].startswith("#"):
        classes.append(f"bg-[{fills[0]}]")

    cr = node.get("corner_radius", 0)
    if cr > 0:
        classes.append(f"rounded-[{cr}px]")

    if node.get("stroke"):
        classes.append(f"border border-[{node['stroke']}]")

    typo = node.get("typography")
    if typo:
        fs = typo.get("font_size", 16)
        classes.append(f"text-[{fs}px]")

        fw = typo.get("font_weight", 400)
        weight_map = {100: "font-thin", 200: "font-extralight", 300: "font-light",
                      400: "font-normal", 500: "font-medium", 600: "font-semibold",
                      700: "font-bold", 800: "font-extrabold", 900: "font-black"}
        classes.append(weight_map.get(fw, "font-normal"))

        color = typo.get("color", "#000000")
        classes.append(f"text-[{color}]")

        align = typo.get("text_align", "left")
        if align != "left":
            classes.append(f"text-{align}")

    if node.get("opacity", 1.0) < 1.0:
        classes.append(f"opacity-[{node['opacity']}]")

    return " ".join(classes)


def generate_react(extracted_node: dict, component_name: str = "Design") -> str:
    """Generate a React component from an extracted Figma node."""
    jsx = _node_to_jsx(extracted_node, depth=2)

    classes: dict[str, str] = {}
    _node_to_html(extracted_node, classes)

    all_css = []
    _collect_css(extracted_node, classes, all_css, set())
    css_text = "\n\n".join(all_css)

    return f"""import React from 'react';
import './{ component_name }.css';

export default function {component_name}() {{
  return (
{jsx}
  );
}}
"""


def generate_react_tailwind(extracted_node: dict, component_name: str = "Design") -> str:
    """Generate a React component with Tailwind CSS classes."""
    jsx = _node_to_tailwind(extracted_node, depth=2)

    return f"""export default function {component_name}() {{
  return (
{jsx}
  );
}}
"""


def generate_css_module(extracted_node: dict) -> str:
    """Generate a standalone CSS file for the extracted design."""
    classes: dict[str, str] = {}
    _node_to_html(extracted_node, classes)

    all_css = []
    _collect_css(extracted_node, classes, all_css, set())
    return "\n\n".join(all_css)
