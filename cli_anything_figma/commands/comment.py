"""Comment operations — list, post, reply, delete."""
import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table,
    output_success, output_error, truncate,
)


@click.group("comment")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.pass_context
def comment_group(ctx, file_key):
    """Manage comments on a Figma file."""
    ctx.ensure_object(dict)
    ctx.obj["file_key"] = file_key


@comment_group.command("list")
@click.pass_context
def list_comments(ctx):
    """List all comments on the file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)
    try:
        client = FigmaClient()
        data = client.get_comments(fk)
        comments = data.get("comments", [])

        items = [
            {
                "id": c.get("id"),
                "user": c.get("user", {}).get("handle", "unknown"),
                "message": c.get("message", ""),
                "created_at": c.get("created_at"),
                "resolved_at": c.get("resolved_at"),
                "parent_id": c.get("parent_id", ""),
            }
            for c in comments
        ]

        if use_json:
            output_json(items)
        else:
            output_table(
                "Comments",
                ["ID", "User", "Message", "Created", "Resolved", "Parent"],
                [
                    [
                        i["id"], i["user"], truncate(i["message"], 40),
                        i["created_at"], i["resolved_at"] or "—", i["parent_id"] or "—",
                    ]
                    for i in items
                ],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@comment_group.command("post")
@click.option("--message", "-m", required=True, help="Comment text.")
@click.option("--x", type=float, default=None, help="X coordinate for pinned comment.")
@click.option("--y", type=float, default=None, help="Y coordinate for pinned comment.")
@click.option("--node-id", default=None, help="Node ID to attach comment to.")
@click.pass_context
def post_comment(ctx, message, x, y, node_id):
    """Post a new comment on the file."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)

    client_meta = None
    if x is not None and y is not None:
        if node_id:
            client_meta = {"node_id": node_id, "node_offset": {"x": x, "y": y}}
        else:
            client_meta = {"x": x, "y": y}

    try:
        client = FigmaClient()
        data = client.post_comment(fk, message, client_meta=client_meta)

        if use_json:
            output_json(data)
        else:
            output_success(f"Comment posted (ID: {data.get('id')})")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@comment_group.command("reply")
@click.option("--comment-id", "-c", required=True, help="Parent comment ID to reply to.")
@click.option("--message", "-m", required=True, help="Reply text.")
@click.pass_context
def reply_comment(ctx, comment_id, message):
    """Reply to an existing comment."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()
        data = client.post_comment(fk, message, comment_id=comment_id)

        if use_json:
            output_json(data)
        else:
            output_success(f"Reply posted (ID: {data.get('id')})")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@comment_group.command("delete")
@click.option("--comment-id", "-c", required=True, help="Comment ID to delete.")
@click.pass_context
def delete_comment(ctx, comment_id):
    """Delete a comment."""
    fk = ctx.obj["file_key"]
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()
        data = client.delete_comment(fk, comment_id)

        if use_json:
            output_json({"status": "deleted", "comment_id": comment_id})
        else:
            output_success(f"Deleted comment {comment_id}")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
