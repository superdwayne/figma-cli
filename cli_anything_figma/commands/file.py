"""File operations — info, list-pages, tree, nodes."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table, output_tree, output_panel,
    output_success, output_error, truncate,
)


@click.group("file")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def file_group(ctx, file_key):
    """File operations — inspect structure, pages, and nodes."""
    ctx.ensure_object(dict)
    ctx.obj["file_key"] = file_key


@file_group.command("info")
@click.pass_context
def file_info(ctx):
    """Get file metadata (name, last modified, version, pages count)."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file(fk, depth=1)
        doc = data.get("document", {})
        pages = doc.get("children", [])

        result = {
            "name": data.get("name"),
            "last_modified": data.get("lastModified"),
            "version": data.get("version"),
            "role": data.get("role"),
            "pages": len(pages),
            "page_names": [p.get("name") for p in pages],
            "thumbnail_url": data.get("thumbnailUrl"),
        }

        if use_json:
            output_json(result)
        else:
            output_table(
                f"File: {result['name']}",
                ["Property", "Value"],
                [
                    ["Name", result["name"]],
                    ["Last Modified", result["last_modified"]],
                    ["Version", result["version"]],
                    ["Role", result["role"]],
                    ["Pages", str(result["pages"])],
                    ["Thumbnail", truncate(result["thumbnail_url"] or "", 80)],
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@file_group.command("list-pages")
@click.pass_context
def list_pages(ctx):
    """List all pages in a file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file(fk, depth=1)
        pages = data.get("document", {}).get("children", [])

        items = [
            {"id": p.get("id"), "name": p.get("name"), "type": p.get("type")}
            for p in pages
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Pages",
                ["#", "ID", "Name"],
                [[str(i + 1), it["id"], it["name"]] for i, it in enumerate(items)],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@file_group.command("tree")
@click.option("--depth", "-d", default=2, help="Tree depth (default: 2).")
@click.option("--page", "-p", default=None, help="Specific page name or ID to show.")
@click.pass_context
def file_tree(ctx, depth, page):
    """Show the node tree of a file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file(fk, depth=depth)
        doc = data.get("document", {})
        pages = doc.get("children", [])

        if page:
            pages = [
                p for p in pages
                if p.get("name") == page or p.get("id") == page
            ]
            if not pages:
                output_error(f"Page not found: {page}")
                raise SystemExit(1)

        def flatten(node, level=0, result=None):
            if result is None:
                result = []
            indent = "  " * level
            result.append({
                "indent": indent,
                "id": node.get("id", ""),
                "name": node.get("name", ""),
                "type": node.get("type", ""),
            })
            for child in node.get("children", []):
                flatten(child, level + 1, result)
            return result

        all_nodes = []
        for p in pages:
            all_nodes.extend(flatten(p))

        if use_json:
            output_json(all_nodes)
        else:
            output_table(
                "Node Tree",
                ["", "ID", "Name", "Type"],
                [
                    [n["indent"] + "├─", n["id"], n["name"], n["type"]]
                    for n in all_nodes
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@file_group.command("nodes")
@click.option("--ids", "-i", required=True, help="Comma-separated node IDs.")
@click.pass_context
def file_nodes(ctx, ids):
    """Get specific nodes by ID."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    node_ids = [n.strip() for n in ids.split(",")]
    try:
        client = FigmaClient()
        data = client.get_file_nodes(fk, node_ids)
        nodes = data.get("nodes", {})

        if use_json:
            output_json(nodes)
        else:
            for nid, ndata in nodes.items():
                doc = ndata.get("document", {})
                output_panel(
                    f"Node {nid}",
                    f"Name: {doc.get('name')}\n"
                    f"Type: {doc.get('type')}\n"
                    f"Children: {len(doc.get('children', []))}",
                )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
