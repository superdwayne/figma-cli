"""SVG generation engine for cli-anything-figma.

Creates SVG designs from structured commands — frames, text, shapes, 
layouts, and complete pages that can be imported into Figma.
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SVGNode:
    """Represents a node in the SVG design tree."""
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    text: str | None = None

    def to_element(self) -> ET.Element:
        el = ET.Element(self.tag, self.attrs)
        if self.text:
            el.text = self.text
        for child in self.children:
            el.append(child.to_element())
        return el


class SVGCanvas:
    """Build an SVG design programmatically."""

    def __init__(self, width: int = 1440, height: int = 900, bg: str = "#FFFFFF"):
        self.width = width
        self.height = height
        self.bg = bg
        self.nodes: list[SVGNode] = []
        self._defs: list[SVGNode] = []
        self._id_counter = 0

    def _next_id(self, prefix: str = "node") -> str:
        self._id_counter += 1
        return f"{prefix}-{self._id_counter}"

    # ── Primitives ───────────────────────────────────────────

    def rect(
        self,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
        fill: str = "#000000",
        stroke: str | None = None,
        stroke_width: float = 0,
        corner_radius: float = 0,
        opacity: float = 1.0,
        name: str | None = None,
    ) -> str:
        nid = self._next_id("rect")
        attrs = {
            "id": nid,
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
            "fill": fill,
            "opacity": str(opacity),
        }
        if corner_radius > 0:
            attrs["rx"] = str(corner_radius)
            attrs["ry"] = str(corner_radius)
        if stroke:
            attrs["stroke"] = stroke
            attrs["stroke-width"] = str(stroke_width or 1)
        if name:
            attrs["data-name"] = name
        self.nodes.append(SVGNode("rect", attrs))
        return nid

    def ellipse(
        self,
        cx: float = 50,
        cy: float = 50,
        rx: float = 50,
        ry: float = 50,
        fill: str = "#000000",
        stroke: str | None = None,
        stroke_width: float = 0,
        opacity: float = 1.0,
        name: str | None = None,
    ) -> str:
        nid = self._next_id("ellipse")
        attrs = {
            "id": nid,
            "cx": str(cx),
            "cy": str(cy),
            "rx": str(rx),
            "ry": str(ry),
            "fill": fill,
            "opacity": str(opacity),
        }
        if stroke:
            attrs["stroke"] = stroke
            attrs["stroke-width"] = str(stroke_width or 1)
        if name:
            attrs["data-name"] = name
        self.nodes.append(SVGNode("ellipse", attrs))
        return nid

    def line(
        self,
        x1: float = 0,
        y1: float = 0,
        x2: float = 100,
        y2: float = 0,
        stroke: str = "#000000",
        stroke_width: float = 1,
        name: str | None = None,
    ) -> str:
        nid = self._next_id("line")
        attrs = {
            "id": nid,
            "x1": str(x1),
            "y1": str(y1),
            "x2": str(x2),
            "y2": str(y2),
            "stroke": stroke,
            "stroke-width": str(stroke_width),
        }
        if name:
            attrs["data-name"] = name
        self.nodes.append(SVGNode("line", attrs))
        return nid

    def text(
        self,
        content: str,
        x: float = 0,
        y: float = 0,
        font_size: float = 16,
        font_family: str = "Inter",
        font_weight: str = "400",
        fill: str = "#000000",
        text_anchor: str = "start",
        opacity: float = 1.0,
        line_height: float | None = None,
        name: str | None = None,
    ) -> str:
        nid = self._next_id("text")
        attrs = {
            "id": nid,
            "x": str(x),
            "y": str(y),
            "font-size": str(font_size),
            "font-family": font_family,
            "font-weight": font_weight,
            "fill": fill,
            "text-anchor": text_anchor,
            "opacity": str(opacity),
        }
        if line_height:
            attrs["line-height"] = str(line_height)
        if name:
            attrs["data-name"] = name
        self.nodes.append(SVGNode("text", attrs, text=content))
        return nid

    def group(
        self,
        x: float = 0,
        y: float = 0,
        name: str | None = None,
    ) -> "SVGGroup":
        nid = self._next_id("group")
        attrs = {
            "id": nid,
            "transform": f"translate({x},{y})",
        }
        if name:
            attrs["data-name"] = name
        group = SVGGroup(nid, attrs, self)
        return group

    def image(
        self,
        href: str,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
        name: str | None = None,
    ) -> str:
        nid = self._next_id("image")
        attrs = {
            "id": nid,
            "href": href,
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
        }
        if name:
            attrs["data-name"] = name
        self.nodes.append(SVGNode("image", attrs))
        return nid

    # ── Higher-level components ──────────────────────────────

    def button(
        self,
        label: str,
        x: float = 0,
        y: float = 0,
        width: float = 160,
        height: float = 48,
        bg: str = "#000000",
        text_color: str = "#FFFFFF",
        font_size: float = 16,
        corner_radius: float = 8,
        name: str | None = None,
    ) -> str:
        g = self.group(x, y, name=name or f"Button: {label}")
        g.rect(0, 0, width, height, fill=bg, corner_radius=corner_radius)
        g.text(
            label,
            x=width / 2,
            y=height / 2 + font_size * 0.35,
            font_size=font_size,
            fill=text_color,
            text_anchor="middle",
            font_weight="600",
        )
        return g.finish()

    def card(
        self,
        title: str,
        body: str = "",
        x: float = 0,
        y: float = 0,
        width: float = 320,
        height: float = 200,
        bg: str = "#FFFFFF",
        border: str = "#E0E0E0",
        corner_radius: float = 12,
        name: str | None = None,
    ) -> str:
        g = self.group(x, y, name=name or f"Card: {title}")
        g.rect(0, 0, width, height, fill=bg, stroke=border, stroke_width=1, corner_radius=corner_radius)
        g.text(title, x=24, y=40, font_size=20, font_weight="700", fill="#111111")
        if body:
            g.text(body, x=24, y=68, font_size=14, font_weight="400", fill="#666666")
        return g.finish()

    def navbar(
        self,
        brand: str,
        links: list[str] | None = None,
        x: float = 0,
        y: float = 0,
        width: float | None = None,
        height: float = 64,
        bg: str = "#000000",
        text_color: str = "#FFFFFF",
        name: str | None = None,
    ) -> str:
        w = width or self.width
        links = links or ["Home", "About", "Contact"]
        g = self.group(x, y, name=name or "Navbar")
        g.rect(0, 0, w, height, fill=bg)
        g.text(brand, x=24, y=height / 2 + 6, font_size=18, font_weight="700", fill=text_color)
        link_x = w - 24
        for link in reversed(links):
            g.text(link, x=link_x, y=height / 2 + 5, font_size=14, fill=text_color, text_anchor="end")
            link_x -= len(link) * 9 + 32
        return g.finish()

    def hero(
        self,
        headline: str,
        subtext: str = "",
        cta_label: str = "",
        x: float = 0,
        y: float = 0,
        width: float | None = None,
        height: float = 500,
        bg: str = "#F5F5F5",
        name: str | None = None,
    ) -> str:
        w = width or self.width
        g = self.group(x, y, name=name or "Hero")
        g.rect(0, 0, w, height, fill=bg)
        g.text(
            headline,
            x=w / 2, y=height * 0.38,
            font_size=56, font_weight="800", fill="#111111",
            text_anchor="middle",
        )
        if subtext:
            g.text(
                subtext,
                x=w / 2, y=height * 0.38 + 48,
                font_size=18, font_weight="400", fill="#666666",
                text_anchor="middle",
            )
        if cta_label:
            btn_w, btn_h = 200, 52
            g_inner = g.sub_group(w / 2 - btn_w / 2, height * 0.38 + 80)
            g_inner.rect(0, 0, btn_w, btn_h, fill="#111111", corner_radius=8)
            g_inner.text(
                cta_label,
                x=btn_w / 2, y=btn_h / 2 + 6,
                font_size=16, font_weight="600", fill="#FFFFFF",
                text_anchor="middle",
            )
            g_inner.finish()
        return g.finish()

    def grid(
        self,
        items: list[dict],
        x: float = 0,
        y: float = 0,
        columns: int = 3,
        gap: float = 24,
        card_width: float = 320,
        card_height: float = 200,
        name: str | None = None,
    ) -> str:
        g = self.group(x, y, name=name or "Grid")
        for i, item in enumerate(items):
            col = i % columns
            row = i // columns
            cx = col * (card_width + gap)
            cy = row * (card_height + gap)
            g_card = g.sub_group(cx, cy, name=item.get("name"))
            g_card.rect(
                0, 0, card_width, card_height,
                fill=item.get("bg", "#FFFFFF"),
                stroke=item.get("border", "#E0E0E0"),
                stroke_width=1,
                corner_radius=item.get("corner_radius", 12),
            )
            if item.get("title"):
                g_card.text(item["title"], x=24, y=40, font_size=20, font_weight="700", fill="#111111")
            if item.get("body"):
                g_card.text(item["body"], x=24, y=68, font_size=14, fill="#666666")
            g_card.finish()
        return g.finish()

    # ── Render ───────────────────────────────────────────────

    def render(self) -> str:
        """Render the canvas to an SVG string."""
        root = ET.Element("svg", {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(self.width),
            "height": str(self.height),
            "viewBox": f"0 0 {self.width} {self.height}",
        })

        # Background
        bg = ET.SubElement(root, "rect", {
            "width": str(self.width),
            "height": str(self.height),
            "fill": self.bg,
        })

        # Defs
        if self._defs:
            defs = ET.SubElement(root, "defs")
            for d in self._defs:
                defs.append(d.to_element())

        # Nodes
        for node in self.nodes:
            root.append(node.to_element())

        ET.indent(root, space="  ")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")

    def save(self, path: str):
        """Save the SVG to a file."""
        from pathlib import Path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(self.render())
        return path


class SVGGroup:
    """Builder for SVG groups (<g> elements)."""

    def __init__(self, nid: str, attrs: dict, canvas: SVGCanvas):
        self.nid = nid
        self.attrs = attrs
        self.canvas = canvas
        self.children: list[SVGNode] = []

    def rect(self, x, y, width, height, **kwargs) -> str:
        nid = self.canvas._next_id("rect")
        attrs = {
            "id": nid,
            "x": str(x), "y": str(y),
            "width": str(width), "height": str(height),
            "fill": kwargs.get("fill", "#000"),
            "opacity": str(kwargs.get("opacity", 1.0)),
        }
        cr = kwargs.get("corner_radius", 0)
        if cr:
            attrs["rx"] = str(cr)
            attrs["ry"] = str(cr)
        if kwargs.get("stroke"):
            attrs["stroke"] = kwargs["stroke"]
            attrs["stroke-width"] = str(kwargs.get("stroke_width", 1))
        self.children.append(SVGNode("rect", attrs))
        return nid

    def ellipse(self, cx, cy, rx, ry, **kwargs) -> str:
        nid = self.canvas._next_id("ellipse")
        attrs = {
            "id": nid,
            "cx": str(cx), "cy": str(cy),
            "rx": str(rx), "ry": str(ry),
            "fill": kwargs.get("fill", "#000"),
        }
        self.children.append(SVGNode("ellipse", attrs))
        return nid

    def text(self, content, x, y, **kwargs) -> str:
        nid = self.canvas._next_id("text")
        attrs = {
            "id": nid,
            "x": str(x), "y": str(y),
            "font-size": str(kwargs.get("font_size", 16)),
            "font-family": kwargs.get("font_family", "Inter"),
            "font-weight": str(kwargs.get("font_weight", "400")),
            "fill": kwargs.get("fill", "#000"),
            "text-anchor": kwargs.get("text_anchor", "start"),
        }
        self.children.append(SVGNode("text", attrs, text=content))
        return nid

    def line(self, x1, y1, x2, y2, **kwargs) -> str:
        nid = self.canvas._next_id("line")
        attrs = {
            "id": nid,
            "x1": str(x1), "y1": str(y1),
            "x2": str(x2), "y2": str(y2),
            "stroke": kwargs.get("stroke", "#000"),
            "stroke-width": str(kwargs.get("stroke_width", 1)),
        }
        self.children.append(SVGNode("line", attrs))
        return nid

    def sub_group(self, x: float = 0, y: float = 0, name: str | None = None) -> "SVGGroup":
        nid = self.canvas._next_id("group")
        attrs = {"id": nid, "transform": f"translate({x},{y})"}
        if name:
            attrs["data-name"] = name
        g = SVGGroup(nid, attrs, self.canvas)
        g._parent_group = self
        return g

    def finish(self) -> str:
        """Finalize the group and add it to parent."""
        node = SVGNode("g", self.attrs, self.children)
        if hasattr(self, "_parent_group"):
            self._parent_group.children.append(node)
        else:
            self.canvas.nodes.append(node)
        return self.nid
