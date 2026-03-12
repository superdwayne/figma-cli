"""Variable operations — list variables and variable collections."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table, output_panel,
    output_error, truncate,
)


@click.group("variable")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def variable_group(ctx, file_key):
    """Variables and variable collections."""
    ctx.ensure_object(dict)
    ctx.obj["file_key"] = file_key


@variable_group.command("list")
@click.option("--published", is_flag=True, help="Show only published variables.")
@click.pass_context
def list_variables(ctx, published):
    """List variables in the file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        if published:
            data = client.get_published_variables(fk)
        else:
            data = client.get_local_variables(fk)

        meta = data.get("meta", {})
        variables = meta.get("variables", {})
        collections = meta.get("variableCollections", {})

        items = []
        for vid, v in variables.items():
            collection_id = v.get("variableCollectionId", "")
            collection_name = collections.get(collection_id, {}).get("name", "")
            items.append({
                "id": vid,
                "name": v.get("name"),
                "resolved_type": v.get("resolvedType"),
                "collection": collection_name,
                "collection_id": collection_id,
                "description": v.get("description", ""),
                "remote": v.get("remote", False),
            })

        if use_json:
            output_json({"variables": items, "collections": list(collections.values())})
        else:
            output_table(
                f"Variables ({'Published' if published else 'Local'})",
                ["Name", "Type", "Collection", "Description"],
                [
                    [i["name"], i["resolved_type"], i["collection"], truncate(i["description"], 30)]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@variable_group.command("collections")
@click.option("--published", is_flag=True, help="Show only published collections.")
@click.pass_context
def list_collections(ctx, published):
    """List variable collections in the file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        if published:
            data = client.get_published_variables(fk)
        else:
            data = client.get_local_variables(fk)

        meta = data.get("meta", {})
        collections = meta.get("variableCollections", {})

        items = [
            {
                "id": cid,
                "name": c.get("name"),
                "modes": [m.get("name") for m in c.get("modes", [])],
                "variable_count": len(c.get("variableIds", [])),
                "remote": c.get("remote", False),
            }
            for cid, c in collections.items()
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Variable Collections",
                ["ID", "Name", "Modes", "Variables"],
                [
                    [i["id"], i["name"], ", ".join(i["modes"]), str(i["variable_count"])]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
