"""Bridge commands — single-command design creation in Figma via plugin bridge.

Every command auto-starts the relay server if needed — no second terminal required.
"""
import json
import time

import click
import requests as req

from cli_anything_figma.bridge import start_bridge, stop_bridge, send_command
from cli_anything_figma.formatters import (
    output_json, output_success, output_error, output_info, output_warning,
)


def _ensure_bridge(port: int = 9480):
    """Auto-start the relay server if it's not already running."""
    try:
        req.get(f"http://127.0.0.1:{port}/health", timeout=1)
    except Exception:
        start_bridge(port)
        time.sleep(0.2)


def _send(cmd_type: str, params: dict, port: int, use_json: bool, success_msg: str):
    """Ensure bridge is up, send command, handle output."""
    _ensure_bridge(port)
    result = send_command(cmd_type, params, port=port)
    if use_json:
        output_json(result)
    elif result.get("error"):
        output_error(result["error"])
    else:
        output_success(success_msg)
    return result


@click.group("bridge")
@click.pass_context
def bridge_group(ctx):
    """Figma Plugin Bridge — create designs directly in Figma.

    The relay server auto-starts when you run any command.
    Just have the companion Figma plugin open and connected.
    """
    ctx.ensure_object(dict)


@bridge_group.command("start")
@click.option("--port", "-p", default=9480, type=int, help="Relay server port (default: 9480).")
@click.pass_context
def bridge_start(ctx, port):
    """Start the bridge relay server (keeps running until Ctrl+C)."""
    use_json = ctx.obj.get("json", False)

    try:
        start_bridge(port)
        if use_json:
            output_json({"status": "running", "port": port, "url": f"http://127.0.0.1:{port}"})
        else:
            output_success(f"Bridge relay running on http://127.0.0.1:{port}")
            output_info("Open the Figma plugin → click Connect. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_bridge()
            output_info("Bridge stopped.")
    except OSError as e:
        output_error(f"Failed to start bridge: {e}")
        raise SystemExit(1)


@bridge_group.command("status")
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_status(ctx, port):
    """Check if the bridge relay is running."""
    use_json = ctx.obj.get("json", False)
    try:
        resp = req.get(f"http://127.0.0.1:{port}/health", timeout=3)
        data = resp.json()
        if use_json:
            output_json(data)
        else:
            output_success(f"Bridge is running (pending commands: {data.get('pending', 0)})")
    except Exception:
        if use_json:
            output_json({"status": "offline"})
        else:
            output_error("Bridge is not running. Start it with: figma-cli bridge start")


@bridge_group.command("create-frame")
@click.option("--name", "-n", required=True, help="Frame name.")
@click.option("--width", "-w", default=400, type=int, help="Width.")
@click.option("--height", "-h", default=300, type=int, help="Height.")
@click.option("--x", default=0, type=int)
@click.option("--y", default=0, type=int)
@click.option("--fill", default=None, help="Fill color hex (e.g. #FFFFFF).")
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_create_frame(ctx, name, width, height, x, y, fill, port):
    """Create a frame in Figma (auto-starts bridge)."""
    params = {"name": name, "width": width, "height": height, "x": x, "y": y}
    if fill:
        params["fill"] = fill
    _send("CREATE_FRAME", params, port, ctx.obj.get("json", False),
          f"Created frame '{name}' ({width}x{height}) in Figma")


@bridge_group.command("create-text")
@click.option("--content", "-c", required=True, help="Text content.")
@click.option("--x", default=0, type=int)
@click.option("--y", default=0, type=int)
@click.option("--font-size", default=16, type=int)
@click.option("--font-family", default="Inter")
@click.option("--fill", default="#000000", help="Text color.")
@click.option("--parent", default=None, help="Parent frame name or ID.")
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_create_text(ctx, content, x, y, font_size, font_family, fill, parent, port):
    """Create a text node in Figma (auto-starts bridge)."""
    params = {
        "content": content, "x": x, "y": y,
        "fontSize": font_size, "fontFamily": font_family, "fill": fill,
    }
    if parent:
        params["parent"] = parent
    _send("CREATE_TEXT", params, port, ctx.obj.get("json", False),
          f"Created text '{content[:40]}' in Figma")


@bridge_group.command("create-rect")
@click.option("--x", default=0, type=int)
@click.option("--y", default=0, type=int)
@click.option("--width", "-w", default=100, type=int)
@click.option("--height", "-h", default=100, type=int)
@click.option("--fill", default="#000000")
@click.option("--corner-radius", default=0, type=int)
@click.option("--name", "-n", default=None)
@click.option("--parent", default=None, help="Parent frame name or ID.")
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_create_rect(ctx, x, y, width, height, fill, corner_radius, name, parent, port):
    """Create a rectangle in Figma (auto-starts bridge)."""
    params = {
        "x": x, "y": y, "width": width, "height": height,
        "fill": fill, "cornerRadius": corner_radius,
    }
    if name:
        params["name"] = name
    if parent:
        params["parent"] = parent
    _send("CREATE_RECT", params, port, ctx.obj.get("json", False),
          f"Created rectangle '{name or 'rect'}' ({width}x{height}) in Figma")


@bridge_group.command("create-ellipse")
@click.option("--x", default=0, type=int)
@click.option("--y", default=0, type=int)
@click.option("--width", "-w", default=100, type=int)
@click.option("--height", "-h", default=100, type=int)
@click.option("--fill", default="#000000")
@click.option("--name", "-n", default=None)
@click.option("--parent", default=None)
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_create_ellipse(ctx, x, y, width, height, fill, name, parent, port):
    """Create an ellipse in Figma (auto-starts bridge)."""
    params = {"x": x, "y": y, "width": width, "height": height, "fill": fill}
    if name:
        params["name"] = name
    if parent:
        params["parent"] = parent
    _send("CREATE_ELLIPSE", params, port, ctx.obj.get("json", False),
          "Created ellipse in Figma")


@bridge_group.command("create-component")
@click.option("--type", "-t", "comp_type", required=True,
              type=click.Choice(["button", "card", "navbar", "hero", "input"]),
              help="Component type to create.")
@click.option("--props", required=True, help="JSON string of component properties.")
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_create_component(ctx, comp_type, props, port):
    """Create a pre-built component in Figma (auto-starts bridge)."""
    try:
        params = json.loads(props)
    except json.JSONDecodeError:
        output_error("Invalid JSON in --props")
        raise SystemExit(1)
    params["componentType"] = comp_type
    _send("CREATE_COMPONENT", params, port, ctx.obj.get("json", False),
          f"Created {comp_type} component in Figma")


@bridge_group.command("batch")
@click.option("--spec", "-s", required=True, type=click.Path(exists=True),
              help="JSON file with batch commands.")
@click.option("--port", "-p", default=9480, type=int)
@click.pass_context
def bridge_batch(ctx, spec, port):
    """Execute batch commands from a JSON spec file (auto-starts bridge).

    Format: [{"type": "CREATE_FRAME", "params": {...}}, ...]
    """
    use_json = ctx.obj.get("json", False)
    _ensure_bridge(port)

    with open(spec) as f:
        commands = json.load(f)

    if not isinstance(commands, list):
        output_error("Spec must be a JSON array of commands.")
        raise SystemExit(1)

    results = []
    for i, cmd in enumerate(commands):
        cmd_type = cmd.get("type", "")
        params = cmd.get("params", {})
        output_info(f"[{i+1}/{len(commands)}] {cmd_type}...")
        result = send_command(cmd_type, params, port=port)
        results.append(result)

    if use_json:
        output_json(results)
    else:
        ok_count = sum(1 for r in results if not r.get("error"))
        output_success(f"Executed {ok_count}/{len(results)} commands")
