"""Webhook operations — list, create, delete team webhooks."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table,
    output_success, output_error, truncate,
)


@click.group("webhook")
@click.pass_context
def webhook_group(ctx):
    """Manage team webhooks."""
    ctx.ensure_object(dict)


@webhook_group.command("list")
@click.option("--team", "-t", "team_id", required=True, help="Team ID.")
@click.pass_context
def list_webhooks(ctx, team_id):
    """List webhooks for a team."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_team_webhooks(team_id)
        webhooks = data.get("webhooks", [])

        items = [
            {
                "id": w.get("id"),
                "event_type": w.get("event_type"),
                "endpoint": w.get("endpoint"),
                "status": w.get("status"),
                "description": w.get("description", ""),
            }
            for w in webhooks
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Webhooks",
                ["ID", "Event", "Endpoint", "Status", "Description"],
                [
                    [i["id"], i["event_type"], truncate(i["endpoint"], 40), i["status"], truncate(i["description"], 25)]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@webhook_group.command("create")
@click.option("--team", "-t", "team_id", required=True, help="Team ID.")
@click.option("--event", "-e", required=True, help="Event type (e.g. FILE_UPDATE, LIBRARY_PUBLISH).")
@click.option("--endpoint", "-u", required=True, help="Callback URL.")
@click.option("--passcode", "-p", required=True, help="Verification passcode.")
@click.option("--description", "-d", default="", help="Webhook description.")
@click.pass_context
def create_webhook(ctx, team_id, event, endpoint, passcode, description):
    """Create a new webhook."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.create_webhook(team_id, event, endpoint, passcode, description)

        if use_json:
            output_json(data)
        else:
            output_success(f"Webhook created (ID: {data.get('id')})")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@webhook_group.command("delete")
@click.option("--webhook-id", "-w", required=True, help="Webhook ID to delete.")
@click.pass_context
def delete_webhook(ctx, webhook_id):
    """Delete a webhook."""
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        client.delete_webhook(webhook_id)

        if use_json:
            output_json({"status": "deleted", "webhook_id": webhook_id})
        else:
            output_success(f"Deleted webhook {webhook_id}")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
