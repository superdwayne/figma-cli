"""Main CLI entry point for cli-anything-figma.

Dual-mode interface:
  - Subcommand mode:  figma-cli file --file <KEY> info --json
  - REPL mode:        figma-cli  (no subcommand → enters interactive shell)
"""
import sys

import click

from cli_anything_figma import __version__
from cli_anything_figma.commands.file import file_group
from cli_anything_figma.commands.export import export_group
from cli_anything_figma.commands.component import component_group
from cli_anything_figma.commands.style import style_group
from cli_anything_figma.commands.comment import comment_group
from cli_anything_figma.commands.project import project_group
from cli_anything_figma.commands.version import version_group
from cli_anything_figma.commands.variable import variable_group
from cli_anything_figma.commands.webhook import webhook_group
from cli_anything_figma.commands.config_cmd import config_group


class FigmaCLI(click.Group):
    """Custom group that enters REPL when invoked with no subcommand."""

    def invoke(self, ctx):
        if not ctx.protected_args and not ctx.invoked_subcommand:
            # No subcommand → launch REPL
            from cli_anything_figma.repl_skin import FigmaREPL
            repl = FigmaREPL(self, ctx)
            repl.run()
            return
        return super().invoke(ctx)


@click.group(cls=FigmaCLI, invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, default=False, help="Output as structured JSON.")
@click.option("--version", is_flag=True, help="Show version and exit.")
@click.pass_context
def cli(ctx, use_json, version):
    """cli-anything-figma — Figma CLI for AI Agents.

    Run without arguments to enter interactive REPL mode.
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json

    if version:
        click.echo(f"cli-anything-figma v{__version__}")
        raise SystemExit(0)


# ── me command (top-level) ───────────────────────────────────

@cli.command("me")
@click.pass_context
def cmd_me(ctx):
    """Show the current authenticated user."""
    from cli_anything_figma.api import FigmaClient, FigmaAPIError
    from cli_anything_figma.formatters import output_json, output_panel, output_error

    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        me = client.get_me()
        result = {
            "id": me.get("id"),
            "handle": me.get("handle"),
            "email": me.get("email"),
            "img_url": me.get("img_url"),
        }
        if use_json:
            output_json(result)
        else:
            output_panel(
                "Current User",
                f"Handle: {result['handle']}\n"
                f"Email:  {result['email']}\n"
                f"ID:     {result['id']}",
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


# ── Register command groups ──────────────────────────────────

cli.add_command(file_group)
cli.add_command(export_group)
cli.add_command(component_group)
cli.add_command(style_group)
cli.add_command(comment_group)
cli.add_command(project_group)
cli.add_command(version_group)
cli.add_command(variable_group)
cli.add_command(webhook_group)
cli.add_command(config_group)


def main():
    """Entry point for console_scripts."""
    cli(obj={})


if __name__ == "__main__":
    main()
