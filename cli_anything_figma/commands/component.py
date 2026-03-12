"""Component and component set operations."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table, output_panel,
    output_success, output_error, truncate,
)


@click.group("component")
@click.pass_context
def component_group(ctx):
    """Browse components and component sets."""
    ctx.ensure_object(dict)


@component_group.command("list")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def list_components(ctx, file_key):
    """List published components in a file."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file_components(file_key)
        meta = data.get("meta", {}).get("components", [])

        items = [
            {
                "key": c.get("key"),
                "name": c.get("name"),
                "description": c.get("description", ""),
                "containing_frame": c.get("containing_frame", {}).get("name", ""),
            }
            for c in meta
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Components",
                ["Key", "Name", "Description", "Frame"],
                [
                    [i["key"], i["name"], truncate(i["description"], 40), i["containing_frame"]]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@component_group.command("list-sets")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def list_component_sets(ctx, file_key):
    """List published component sets in a file."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file_component_sets(file_key)
        meta = data.get("meta", {}).get("component_sets", [])

        items = [
            {
                "key": c.get("key"),
                "name": c.get("name"),
                "description": c.get("description", ""),
            }
            for c in meta
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Component Sets",
                ["Key", "Name", "Description"],
                [[i["key"], i["name"], truncate(i["description"], 50)] for i in items],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@component_group.command("get")
@click.option("--key", "-k", required=True, help="Component key.")
@click.pass_context
def get_component(ctx, key):
    """Get details of a single component by key."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_component(key)
        meta = data.get("meta", {})

        if use_json:
            output_json(meta)
        else:
            output_panel(
                f"Component: {meta.get('name')}",
                f"Key:         {meta.get('key')}\n"
                f"File Key:    {meta.get('file_key')}\n"
                f"Node ID:     {meta.get('node_id')}\n"
                f"Description: {meta.get('description', '—')}\n"
                f"Created:     {meta.get('created_at')}\n"
                f"Updated:     {meta.get('updated_at')}",
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@component_group.command("get-set")
@click.option("--key", "-k", required=True, help="Component set key.")
@click.pass_context
def get_component_set(ctx, key):
    """Get details of a single component set by key."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_component_set(key)
        meta = data.get("meta", {})

        if use_json:
            output_json(meta)
        else:
            output_panel(
                f"Component Set: {meta.get('name')}",
                f"Key:         {meta.get('key')}\n"
                f"File Key:    {meta.get('file_key')}\n"
                f"Node ID:     {meta.get('node_id')}\n"
                f"Description: {meta.get('description', '—')}\n"
                f"Created:     {meta.get('created_at')}\n"
                f"Updated:     {meta.get('updated_at')}",
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@component_group.command("team-list")
@click.option("--team", "-t", "team_id", required=True, help="Team ID.")
@click.option("--page-size", default=30, help="Results per page.")
@click.option("--cursor", default=None, help="Pagination cursor.")
@click.pass_context
def team_components(ctx, team_id, page_size, cursor):
    """List team library components."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_team_components(team_id, page_size=page_size, cursor=cursor)
        meta = data.get("meta", {}).get("components", [])
        pagination = data.get("meta", {}).get("cursor", {})

        items = [
            {
                "key": c.get("key"),
                "name": c.get("name"),
                "description": c.get("description", ""),
                "file_key": c.get("file_key", ""),
            }
            for c in meta
        ]

        if use_json:
            output_json({"components": items, "cursor": pagination})
        else:
            output_table(
                "Team Components",
                ["Key", "Name", "Description", "File"],
                [
                    [i["key"], i["name"], truncate(i["description"], 30), i["file_key"]]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
