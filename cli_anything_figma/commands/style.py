"""Style operations — list and inspect published styles."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table, output_panel,
    output_error, truncate,
)


@click.group("style")
@click.pass_context
def style_group(ctx):
    """Browse published styles."""
    ctx.ensure_object(dict)


@style_group.command("list")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def list_styles(ctx, file_key):
    """List published styles in a file."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file_styles(file_key)
        meta = data.get("meta", {}).get("styles", [])

        items = [
            {
                "key": s.get("key"),
                "name": s.get("name"),
                "style_type": s.get("style_type"),
                "description": s.get("description", ""),
            }
            for s in meta
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Styles",
                ["Key", "Name", "Type", "Description"],
                [
                    [i["key"], i["name"], i["style_type"], truncate(i["description"], 40)]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@style_group.command("get")
@click.option("--key", "-k", required=True, help="Style key.")
@click.pass_context
def get_style(ctx, key):
    """Get details of a single style by key."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_style(key)
        meta = data.get("meta", {})

        if use_json:
            output_json(meta)
        else:
            output_panel(
                f"Style: {meta.get('name')}",
                f"Key:         {meta.get('key')}\n"
                f"Type:        {meta.get('style_type')}\n"
                f"File Key:    {meta.get('file_key')}\n"
                f"Node ID:     {meta.get('node_id')}\n"
                f"Description: {meta.get('description', '—')}\n"
                f"Created:     {meta.get('created_at')}\n"
                f"Updated:     {meta.get('updated_at')}",
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@style_group.command("team-list")
@click.option("--team", "-t", "team_id", required=True, help="Team ID.")
@click.option("--page-size", default=30, help="Results per page.")
@click.option("--cursor", default=None, help="Pagination cursor.")
@click.pass_context
def team_styles(ctx, team_id, page_size, cursor):
    """List team library styles."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_team_styles(team_id, page_size=page_size, cursor=cursor)
        meta = data.get("meta", {}).get("styles", [])

        items = [
            {
                "key": s.get("key"),
                "name": s.get("name"),
                "style_type": s.get("style_type"),
                "description": s.get("description", ""),
                "file_key": s.get("file_key", ""),
            }
            for s in meta
        ]

        if use_json:
            output_json({"styles": items})
        else:
            output_table(
                "Team Styles",
                ["Key", "Name", "Type", "Description", "File"],
                [
                    [i["key"], i["name"], i["style_type"], truncate(i["description"], 25), i["file_key"]]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
