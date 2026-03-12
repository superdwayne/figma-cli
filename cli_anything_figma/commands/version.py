"""Version history operations."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table,
    output_error, truncate,
)


@click.group("version")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def version_group(ctx, file_key):
    """File version history."""
    ctx.ensure_object(dict)
    ctx.obj["file_key"] = file_key


@version_group.command("list")
@click.pass_context
def list_versions(ctx):
    """List version history of a file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_file_versions(fk)
        versions = data.get("versions", [])

        items = [
            {
                "id": v.get("id"),
                "label": v.get("label", ""),
                "description": v.get("description", ""),
                "user": v.get("user", {}).get("handle", "unknown"),
                "created_at": v.get("created_at"),
            }
            for v in versions
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Version History",
                ["ID", "Label", "Description", "User", "Created"],
                [
                    [
                        i["id"],
                        i["label"] or "—",
                        truncate(i["description"], 30) or "—",
                        i["user"],
                        i["created_at"],
                    ]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
