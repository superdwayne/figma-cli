"""Project operations — list team projects and project files."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table,
    output_error, truncate,
)


@click.group("project")
@click.pass_context
def project_group(ctx):
    """Browse team projects and project files."""
    ctx.ensure_object(dict)


@project_group.command("list")
@click.option("--team", "-t", "team_id", required=True, help="Team ID.")
@click.pass_context
def list_projects(ctx, team_id):
    """List projects in a team."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_team_projects(team_id)
        projects = data.get("projects", [])

        items = [
            {"id": p.get("id"), "name": p.get("name")}
            for p in projects
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Team Projects",
                ["ID", "Name"],
                [[i["id"], i["name"]] for i in items],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@project_group.command("files")
@click.option("--project-id", "-p", required=True, help="Project ID.")
@click.option("--branch-data", is_flag=True, help="Include branch data.")
@click.pass_context
def list_project_files(ctx, project_id, branch_data):
    """List files in a project."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_project_files(project_id, branch_data=branch_data)
        files = data.get("files", [])

        items = [
            {
                "key": f.get("key"),
                "name": f.get("name"),
                "last_modified": f.get("last_modified"),
                "thumbnail_url": f.get("thumbnail_url", ""),
            }
            for f in files
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Project Files",
                ["Key", "Name", "Last Modified"],
                [[i["key"], i["name"], i["last_modified"]] for i in items],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
