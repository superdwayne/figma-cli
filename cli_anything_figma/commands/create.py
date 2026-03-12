"""Create commands — generate SVG designs from CLI commands."""
import json
from pathlib import Path

import click

from cli_anything_figma.svg_engine import SVGCanvas
from cli_anything_figma.formatters import (
    output_json, output_success, output_error, output_info,
)


@click.group("create")
@click.option("--width", "-w", default=1440, type=int, help="Canvas width (default: 1440).")
@click.option("--height", "-h", default=900, type=int, help="Canvas height (default: 900).")
@click.option("--bg", default="#FFFFFF", help="Background color (default: white).")
@click.option("--output", "-o", "output_path", default="./design.svg", help="Output SVG path.")
@click.pass_context
def create_group(ctx, width, height, bg, output_path):
    """Create designs as SVG — frames, text, shapes, layouts, pages."""
    ctx.ensure_object(dict)
    ctx.obj["canvas"] = SVGCanvas(width=width, height=height, bg=bg)
    ctx.obj["output_path"] = output_path


@create_group.command("rect")
@click.option("--x", default=0.0, type=float)
@click.option("--y", default=0.0, type=float)
@click.option("--width", "w", default=100.0, type=float)
@click.option("--height", "h", default=100.0, type=float)
@click.option("--fill", default="#000000")
@click.option("--stroke", default=None)
@click.option("--stroke-width", default=1.0, type=float)
@click.option("--corner-radius", default=0.0, type=float)
@click.option("--name", default=None)
@click.pass_context
def create_rect(ctx, x, y, w, h, fill, stroke, stroke_width, corner_radius, name):
    """Create a rectangle."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    nid = canvas.rect(x=x, y=y, width=w, height=h, fill=fill, stroke=stroke,
                      stroke_width=stroke_width, corner_radius=corner_radius, name=name)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "rect", "file": path})
    else:
        output_success(f"Created rectangle '{name or nid}' → {path}")


@create_group.command("ellipse")
@click.option("--cx", default=50.0, type=float)
@click.option("--cy", default=50.0, type=float)
@click.option("--rx", default=50.0, type=float)
@click.option("--ry", default=50.0, type=float)
@click.option("--fill", default="#000000")
@click.option("--name", default=None)
@click.pass_context
def create_ellipse(ctx, cx, cy, rx, ry, fill, name):
    """Create an ellipse / circle."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    nid = canvas.ellipse(cx=cx, cy=cy, rx=rx, ry=ry, fill=fill, name=name)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "ellipse", "file": path})
    else:
        output_success(f"Created ellipse '{name or nid}' → {path}")


@create_group.command("text")
@click.option("--content", "-c", required=True, help="Text content.")
@click.option("--x", default=0.0, type=float)
@click.option("--y", default=24.0, type=float)
@click.option("--font-size", default=16.0, type=float)
@click.option("--font-family", default="Inter")
@click.option("--font-weight", default="400")
@click.option("--fill", default="#000000")
@click.option("--anchor", default="start", type=click.Choice(["start", "middle", "end"]))
@click.option("--name", default=None)
@click.pass_context
def create_text(ctx, content, x, y, font_size, font_family, font_weight, fill, anchor, name):
    """Create a text element."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    nid = canvas.text(content, x=x, y=y, font_size=font_size, font_family=font_family,
                      font_weight=font_weight, fill=fill, text_anchor=anchor, name=name)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "text", "content": content, "file": path})
    else:
        output_success(f"Created text '{content[:30]}' → {path}")


@create_group.command("button")
@click.option("--label", "-l", required=True, help="Button label.")
@click.option("--x", default=0.0, type=float)
@click.option("--y", default=0.0, type=float)
@click.option("--width", "w", default=160.0, type=float)
@click.option("--height", "h", default=48.0, type=float)
@click.option("--bg", default="#000000", help="Button background color.")
@click.option("--text-color", default="#FFFFFF")
@click.option("--font-size", default=16.0, type=float)
@click.option("--corner-radius", default=8.0, type=float)
@click.pass_context
def create_button(ctx, label, x, y, w, h, bg, text_color, font_size, corner_radius):
    """Create a button component."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    nid = canvas.button(label, x=x, y=y, width=w, height=h, bg=bg,
                        text_color=text_color, font_size=font_size, corner_radius=corner_radius)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "button", "label": label, "file": path})
    else:
        output_success(f"Created button '{label}' → {path}")


@create_group.command("card")
@click.option("--title", "-t", required=True, help="Card title.")
@click.option("--body", "-b", default="", help="Card body text.")
@click.option("--x", default=0.0, type=float)
@click.option("--y", default=0.0, type=float)
@click.option("--width", "w", default=320.0, type=float)
@click.option("--height", "h", default=200.0, type=float)
@click.option("--bg", default="#FFFFFF")
@click.option("--border", default="#E0E0E0")
@click.option("--corner-radius", default=12.0, type=float)
@click.pass_context
def create_card(ctx, title, body, x, y, w, h, bg, border, corner_radius):
    """Create a card component."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    nid = canvas.card(title, body=body, x=x, y=y, width=w, height=h,
                      bg=bg, border=border, corner_radius=corner_radius)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "card", "title": title, "file": path})
    else:
        output_success(f"Created card '{title}' → {path}")


@create_group.command("navbar")
@click.option("--brand", "-b", required=True, help="Brand / logo text.")
@click.option("--links", "-l", default="Home,About,Contact", help="Comma-separated nav links.")
@click.option("--bg", default="#000000")
@click.option("--text-color", default="#FFFFFF")
@click.option("--height", "h", default=64.0, type=float)
@click.pass_context
def create_navbar(ctx, brand, links, bg, text_color, h):
    """Create a navigation bar."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    link_list = [l.strip() for l in links.split(",")]
    nid = canvas.navbar(brand, links=link_list, bg=bg, text_color=text_color, height=h)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "navbar", "brand": brand, "links": link_list, "file": path})
    else:
        output_success(f"Created navbar '{brand}' with {len(link_list)} links → {path}")


@create_group.command("hero")
@click.option("--headline", required=True, help="Hero headline text.")
@click.option("--subtext", default="", help="Supporting subtext.")
@click.option("--cta", default="", help="Call-to-action button label.")
@click.option("--bg", default="#F5F5F5")
@click.option("--height", "h", default=500.0, type=float)
@click.pass_context
def create_hero(ctx, headline, subtext, cta, bg, h):
    """Create a hero section."""
    canvas = ctx.obj["canvas"]
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    nid = canvas.hero(headline, subtext=subtext, cta_label=cta, bg=bg, height=h)
    path = canvas.save(out)

    if use_json:
        output_json({"id": nid, "type": "hero", "headline": headline, "file": path})
    else:
        output_success(f"Created hero section → {path}")


@create_group.command("page")
@click.option("--spec", "-s", required=True, type=click.Path(exists=True), help="JSON spec file for a full page layout.")
@click.pass_context
def create_page(ctx, spec):
    """Create a full page from a JSON specification file.

    Spec format:
    {
      "width": 1440, "height": 2000, "bg": "#FFFFFF",
      "elements": [
        {"type": "navbar", "brand": "Acme", "links": ["Home","About"]},
        {"type": "hero", "headline": "Welcome", "subtext": "...", "cta": "Get Started"},
        {"type": "grid", "y": 600, "items": [
          {"title": "Feature 1", "body": "Description"},
          {"title": "Feature 2", "body": "Description"}
        ]}
      ]
    }
    """
    out = ctx.obj["output_path"]
    use_json = ctx.obj.get("json", False)

    with open(spec) as f:
        data = json.load(f)

    canvas = SVGCanvas(
        width=data.get("width", 1440),
        height=data.get("height", 2000),
        bg=data.get("bg", "#FFFFFF"),
    )

    created = []
    y_cursor = 0

    for el in data.get("elements", []):
        el_type = el.get("type")
        el_y = el.get("y", y_cursor)

        if el_type == "navbar":
            nid = canvas.navbar(
                el.get("brand", "Brand"),
                links=el.get("links"),
                y=el_y,
                bg=el.get("bg", "#000000"),
                text_color=el.get("text_color", "#FFFFFF"),
                height=el.get("height", 64),
            )
            y_cursor = el_y + el.get("height", 64)

        elif el_type == "hero":
            nid = canvas.hero(
                el.get("headline", "Headline"),
                subtext=el.get("subtext", ""),
                cta_label=el.get("cta", ""),
                y=el_y,
                bg=el.get("bg", "#F5F5F5"),
                height=el.get("height", 500),
            )
            y_cursor = el_y + el.get("height", 500)

        elif el_type == "text":
            nid = canvas.text(
                el.get("content", ""),
                x=el.get("x", 24),
                y=el_y + el.get("font_size", 16),
                font_size=el.get("font_size", 16),
                font_family=el.get("font_family", "Inter"),
                font_weight=str(el.get("font_weight", "400")),
                fill=el.get("fill", "#000000"),
            )
            y_cursor = el_y + el.get("font_size", 16) + 16

        elif el_type == "rect":
            nid = canvas.rect(
                x=el.get("x", 0), y=el_y,
                width=el.get("width", 100), height=el.get("height", 100),
                fill=el.get("fill", "#000000"),
                corner_radius=el.get("corner_radius", 0),
            )
            y_cursor = el_y + el.get("height", 100)

        elif el_type == "button":
            nid = canvas.button(
                el.get("label", "Button"),
                x=el.get("x", 0), y=el_y,
                width=el.get("width", 160), height=el.get("height", 48),
                bg=el.get("bg", "#000000"),
                text_color=el.get("text_color", "#FFFFFF"),
                corner_radius=el.get("corner_radius", 8),
            )
            y_cursor = el_y + el.get("height", 48)

        elif el_type == "card":
            nid = canvas.card(
                el.get("title", "Card"),
                body=el.get("body", ""),
                x=el.get("x", 0), y=el_y,
                width=el.get("width", 320), height=el.get("height", 200),
            )
            y_cursor = el_y + el.get("height", 200)

        elif el_type == "grid":
            items = el.get("items", [])
            nid = canvas.grid(
                items, x=el.get("x", 0), y=el_y,
                columns=el.get("columns", 3),
                gap=el.get("gap", 24),
                card_width=el.get("card_width", 320),
                card_height=el.get("card_height", 200),
            )
            rows = (len(items) + el.get("columns", 3) - 1) // el.get("columns", 3)
            y_cursor = el_y + rows * (el.get("card_height", 200) + el.get("gap", 24))

        else:
            continue

        created.append({"id": nid, "type": el_type})

    path = canvas.save(out)

    if use_json:
        output_json({"file": path, "elements": created, "width": canvas.width, "height": canvas.height})
    else:
        output_success(f"Created page with {len(created)} elements → {path}")
