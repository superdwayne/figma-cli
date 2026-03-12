"""Configuration commands — set token, team ID, show config."""
import click

from cli_anything_figma.config import (
    load_config, set_token, set_team_id, get_token, get_team_id,
)
from cli_anything_figma.formatters import (
    output_json, output_table, output_success, output_error, output_warning,
)


@click.group("config")
@click.pass_context
def config_group(ctx):
    """Configure cli-anything-figma (token, team ID, etc.)."""
    ctx.ensure_object(dict)


@config_group.command("set-token")
@click.argument("token")
@click.pass_context
def cmd_set_token(ctx, token):
    """Store a Figma personal access token."""
    use_json = ctx.obj.get("json", False)
    set_token(token)
    if use_json:
        output_json({"status": "ok", "message": "Token saved"})
    else:
        output_success("Access token saved to ~/.config/cli-anything-figma/config.json")


@config_group.command("set-team")
@click.argument("team_id")
@click.pass_context
def cmd_set_team(ctx, team_id):
    """Store a default Figma team ID."""
    use_json = ctx.obj.get("json", False)
    set_team_id(team_id)
    if use_json:
        output_json({"status": "ok", "message": "Team ID saved"})
    else:
        output_success(f"Default team ID set to {team_id}")


@config_group.command("show")
@click.pass_context
def cmd_show(ctx):
    """Show current configuration."""
    use_json = ctx.obj.get("json", False)
    config = load_config()

    # Mask the token for display
    token = config.get("access_token", "")
    masked = f"{token[:6]}…{token[-4:]}" if token and len(token) > 10 else ("(set)" if token else "(not set)")

    result = {
        "access_token": masked,
        "team_id": config.get("team_id", "(not set)"),
    }

    if use_json:
        output_json(result)
    else:
        output_table(
            "Configuration",
            ["Setting", "Value"],
            [
                ["Access Token", masked],
                ["Team ID", config.get("team_id", "(not set)")],
            ],
        )


@config_group.command("check")
@click.pass_context
def cmd_check(ctx):
    """Verify the current token by calling /me."""
    use_json = ctx.obj.get("json", False)
    from cli_anything_figma.api import FigmaClient, FigmaAPIError
    try:
        client = FigmaClient()
        me = client.get_me()
        result = {
            "status": "ok",
            "user": me.get("handle"),
            "email": me.get("email"),
            "id": me.get("id"),
        }
        if use_json:
            output_json(result)
        else:
            output_success(f"Authenticated as {me.get('handle')} ({me.get('email')})")
    except FigmaAPIError as e:
        if use_json:
            output_json({"status": "error", "message": str(e)})
        else:
            output_error(str(e))
        raise SystemExit(1)
