"""Codegen commands — turn Figma designs into code.

The core agent workflow:
  figma-cli codegen --file <KEY> --node <ID> --format html -o ./output/
  figma-cli codegen --file <KEY> --node <ID> --format react-tailwind -o ./output/

One command: reads from Figma, extracts design data, generates code, saves to disk.
"""
import json
from pathlib import Path

import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.extractor import (
    extract_node, extract_colors_from_tree, extract_fonts_from_tree,
)
from cli_anything_figma.codegen import (
    generate_html, generate_react, generate_react_tailwind,
    generate_css_module,
)
from cli_anything_figma.formatters import (
    output_json, output_table, output_success, output_error, output_info,
)


@click.group("codegen")
@click.pass_context
def codegen_group(ctx):
    """Generate code from Figma designs — HTML, React, Tailwind."""
    ctx.ensure_object(dict)


@codegen_group.command("generate")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--node", "-n", "node_id", required=True, help="Node ID to generate code from.")
@click.option("--format", "-F", "fmt", default="html",
              type=click.Choice(["html", "react", "react-tailwind", "css", "json"]),
              help="Output format.")
@click.option("--output", "-o", "output_dir", default=".", type=click.Path(), help="Output directory.")
@click.option("--name", default=None, help="Component/file name (auto-derived from node name if omitted).")
@click.option("--depth", "-d", default=10, type=int, help="Max node tree depth to fetch.")
@click.pass_context
def cmd_generate(ctx, file_key, node_id, fmt, output_dir, name, depth):
    """Generate code from a Figma node — one command, full pipeline.

    \b
    Examples:
      figma-cli codegen generate -f abc123 -n "1:0" -F html -o ./output
      figma-cli codegen generate -f abc123 -n "1:0" -F react-tailwind -o ./components
    """
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()

        # 1. Fetch the node tree from Figma
        output_info(f"Fetching node {node_id} from Figma...")
        raw = client.get_file_nodes(file_key, [node_id])
        node_data = raw.get("nodes", {}).get(node_id, {})
        document = node_data.get("document")

        if not document:
            output_error(f"Node {node_id} not found in file {file_key}")
            raise SystemExit(1)

        # 2. Extract normalized design data
        output_info("Extracting design data...")
        extracted = extract_node(document)
        comp_name = name or _safe_component_name(document.get("name", "Design"))

        # 3. Generate code
        output_info(f"Generating {fmt}...")
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        files_written = []

        if fmt == "html":
            html = generate_html(extracted, title=comp_name)
            fp = out_path / f"{comp_name.lower()}.html"
            fp.write_text(html)
            files_written.append(str(fp))

        elif fmt == "react":
            jsx = generate_react(extracted, component_name=comp_name)
            css = generate_css_module(extracted)
            fp_jsx = out_path / f"{comp_name}.jsx"
            fp_css = out_path / f"{comp_name}.css"
            fp_jsx.write_text(jsx)
            fp_css.write_text(css)
            files_written.extend([str(fp_jsx), str(fp_css)])

        elif fmt == "react-tailwind":
            jsx = generate_react_tailwind(extracted, component_name=comp_name)
            fp = out_path / f"{comp_name}.jsx"
            fp.write_text(jsx)
            files_written.append(str(fp))

        elif fmt == "css":
            css = generate_css_module(extracted)
            fp = out_path / f"{comp_name.lower()}.css"
            fp.write_text(css)
            files_written.append(str(fp))

        elif fmt == "json":
            fp = out_path / f"{comp_name.lower()}.json"
            fp.write_text(json.dumps(extracted, indent=2))
            files_written.append(str(fp))

        if use_json:
            output_json({
                "node": node_id,
                "component": comp_name,
                "format": fmt,
                "files": files_written,
            })
        else:
            for f in files_written:
                output_success(f"Generated → {f}")

    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@codegen_group.command("inspect")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--node", "-n", "node_id", required=True, help="Node ID to inspect.")
@click.pass_context
def cmd_inspect(ctx, file_key, node_id):
    """Inspect a node's extracted design properties (colors, fonts, layout).

    Useful for agents to understand a design before generating code.
    """
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()
        raw = client.get_file_nodes(file_key, [node_id])
        node_data = raw.get("nodes", {}).get(node_id, {})
        document = node_data.get("document")

        if not document:
            output_error(f"Node {node_id} not found")
            raise SystemExit(1)

        extracted = extract_node(document)
        colors = sorted(extract_colors_from_tree(document))
        fonts = sorted(extract_fonts_from_tree(document))

        result = {
            "node": node_id,
            "name": document.get("name"),
            "type": document.get("type"),
            "width": extracted["width"],
            "height": extracted["height"],
            "colors": colors,
            "fonts": fonts,
            "children_count": len(extracted.get("children", [])),
            "layout": extracted.get("layout"),
        }

        if use_json:
            output_json(result)
        else:
            output_table(
                f"Node: {result['name']}",
                ["Property", "Value"],
                [
                    ["Type", result["type"]],
                    ["Size", f"{result['width']}×{result['height']}"],
                    ["Colors", ", ".join(colors) or "none"],
                    ["Fonts", ", ".join(fonts) or "none"],
                    ["Children", str(result["children_count"])],
                    ["Layout", str(result.get("layout") or "absolute")],
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@codegen_group.command("batch")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--nodes", "-n", required=True, help="Comma-separated node IDs.")
@click.option("--format", "-F", "fmt", default="html",
              type=click.Choice(["html", "react", "react-tailwind"]))
@click.option("--output", "-o", "output_dir", default=".", type=click.Path())
@click.pass_context
def cmd_batch(ctx, file_key, nodes, fmt, output_dir):
    """Generate code for multiple nodes at once."""
    use_json = ctx.obj.get("json", False)
    node_ids = [n.strip() for n in nodes.split(",")]

    try:
        client = FigmaClient()
        raw = client.get_file_nodes(file_key, node_ids)
        all_nodes = raw.get("nodes", {})
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        results = []
        for nid in node_ids:
            node_data = all_nodes.get(nid, {})
            document = node_data.get("document")
            if not document:
                results.append({"node": nid, "status": "error", "message": "not found"})
                continue

            extracted = extract_node(document)
            comp_name = _safe_component_name(document.get("name", "Design"))

            if fmt == "html":
                html = generate_html(extracted, title=comp_name)
                fp = out_path / f"{comp_name.lower()}.html"
                fp.write_text(html)
            elif fmt == "react":
                jsx = generate_react(extracted, component_name=comp_name)
                fp = out_path / f"{comp_name}.jsx"
                fp.write_text(jsx)
            elif fmt == "react-tailwind":
                jsx = generate_react_tailwind(extracted, component_name=comp_name)
                fp = out_path / f"{comp_name}.jsx"
                fp.write_text(jsx)

            results.append({"node": nid, "name": comp_name, "status": "ok", "file": str(fp)})
            output_success(f"Generated {comp_name} → {fp}")

        if use_json:
            output_json(results)

    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


def _safe_component_name(name: str) -> str:
    """Convert a Figma node name to a valid component name (PascalCase)."""
    cleaned = "".join(c if c.isalnum() or c == " " else " " for c in name)
    parts = cleaned.split()
    return "".join(p.capitalize() for p in parts) or "Design"
