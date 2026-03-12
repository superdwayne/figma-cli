"""Export operations — render nodes to PNG, SVG, PDF, JPG."""
import os
from pathlib import Path

import click
import requests

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table, output_success, output_error, output_info,
)


@click.group("export")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def export_group(ctx, file_key):
    """Export nodes as images (PNG, SVG, PDF, JPG)."""
    ctx.ensure_object(dict)
    ctx.obj["file_key"] = file_key


@export_group.command("render")
@click.option("--ids", "-i", required=True, help="Comma-separated node IDs to export.")
@click.option("--format", "-F", "fmt", default="png", type=click.Choice(["png", "svg", "pdf", "jpg"]), help="Image format.")
@click.option("--scale", "-s", default=2.0, type=float, help="Scale factor (default: 2).")
@click.option("--output-dir", "-o", default=".", type=click.Path(), help="Output directory.")
@click.option("--svg-include-id", is_flag=True, help="Include node IDs in SVG output.")
@click.option("--svg-simplify-stroke", is_flag=True, default=True, help="Simplify strokes in SVG.")
@click.option("--absolute-bounds", is_flag=True, help="Use absolute bounds.")
@click.pass_context
def export_render(ctx, ids, fmt, scale, output_dir, svg_include_id, svg_simplify_stroke, absolute_bounds):
    """Export nodes as image files to disk."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    node_ids = [n.strip() for n in ids.split(",")]

    try:
        client = FigmaClient()
        output_info(f"Requesting {fmt.upper()} export for {len(node_ids)} node(s)…")

        data = client.get_images(
            fk, node_ids,
            scale=scale,
            fmt=fmt,
            svg_include_id=svg_include_id,
            svg_simplify_stroke=svg_simplify_stroke,
            use_absolute_bounds=absolute_bounds,
        )

        images = data.get("images", {})
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        results = []
        for nid, url in images.items():
            if not url:
                output_error(f"No image URL for node {nid}")
                results.append({"node_id": nid, "status": "error", "message": "no URL"})
                continue

            safe_name = nid.replace(":", "-").replace("/", "_")
            filename = f"{safe_name}.{fmt}"
            filepath = out_path / filename

            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)

            size = len(resp.content)
            results.append({
                "node_id": nid,
                "file": str(filepath),
                "format": fmt,
                "size_bytes": size,
                "status": "ok",
            })
            output_success(f"Exported {filepath} ({size:,} bytes)")

        if use_json:
            output_json(results)
        elif not use_json:
            output_table(
                "Export Results",
                ["Node ID", "File", "Format", "Size"],
                [
                    [r["node_id"], r.get("file", "—"), r.get("format", "—"), f"{r.get('size_bytes', 0):,}"]
                    for r in results
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@export_group.command("urls")
@click.option("--ids", "-i", required=True, help="Comma-separated node IDs.")
@click.option("--format", "-F", "fmt", default="png", type=click.Choice(["png", "svg", "pdf", "jpg"]), help="Image format.")
@click.option("--scale", "-s", default=2.0, type=float, help="Scale factor.")
@click.pass_context
def export_urls(ctx, ids, fmt, scale):
    """Get temporary download URLs without saving to disk."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    node_ids = [n.strip() for n in ids.split(",")]

    try:
        client = FigmaClient()
        data = client.get_images(fk, node_ids, scale=scale, fmt=fmt)
        images = data.get("images", {})

        results = [{"node_id": nid, "url": url} for nid, url in images.items()]

        if use_json:
            output_json(results)
        else:
            output_table(
                "Export URLs",
                ["Node ID", "URL"],
                [[r["node_id"], r["url"][:100] + "…" if r["url"] and len(r["url"]) > 100 else r["url"] or "—"] for r in results],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@export_group.command("fills")
@click.pass_context
def export_fills(ctx):
    """Get download URLs for all image fills in the file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()
        data = client.get_image_fills(fk)
        images = data.get("meta", {}).get("images", {})

        if use_json:
            output_json(images)
        else:
            rows = [[ref, url[:100]] for ref, url in images.items()]
            output_table("Image Fills", ["Reference", "URL"], rows)
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
