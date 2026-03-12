"""Design token operations — create/update variables via Figma Variables REST API."""
import json
from pathlib import Path

import click

from cli_anything_figma.api import FigmaClient, FigmaAPIError
from cli_anything_figma.formatters import (
    output_json, output_table, output_success, output_error, output_info,
)


def _parse_color(hex_color: str) -> dict:
    """Parse a hex color (#RRGGBB or #RRGGBBAA) to Figma RGBA dict."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = 255
    elif len(h) == 8:
        r, g, b, a = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
    else:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return {"r": r / 255, "g": g / 255, "b": b / 255, "a": a / 255}


@click.group("token")
@click.pass_context
def token_group(ctx):
    """Create and manage design tokens (Figma Variables)."""
    ctx.ensure_object(dict)


@token_group.command("create-collection")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--name", "-n", required=True, help="Collection name.")
@click.option("--modes", "-m", default="Default", help="Comma-separated mode names (e.g. 'Light,Dark').")
@click.pass_context
def create_collection(ctx, file_key, name, modes):
    """Create a new variable collection."""
    use_json = ctx.obj.get("json", False)
    mode_list = [m.strip() for m in modes.split(",")]

    try:
        client = FigmaClient()

        payload = {
            "variableCollections": [
                {
                    "action": "CREATE",
                    "id": f"temp_collection_{name.replace(' ', '_')}",
                    "name": name,
                    "initialModeId": f"temp_mode_{mode_list[0].replace(' ', '_')}",
                }
            ],
            "variableModes": [],
        }

        # First mode is created with the collection
        # Additional modes need separate entries
        for i, mode_name in enumerate(mode_list):
            if i == 0:
                payload["variableModes"].append({
                    "action": "UPDATE",
                    "id": f"temp_mode_{mode_name.replace(' ', '_')}",
                    "name": mode_name,
                    "variableCollectionId": f"temp_collection_{name.replace(' ', '_')}",
                })
            else:
                payload["variableModes"].append({
                    "action": "CREATE",
                    "id": f"temp_mode_{mode_name.replace(' ', '_')}",
                    "name": mode_name,
                    "variableCollectionId": f"temp_collection_{name.replace(' ', '_')}",
                })

        data = client._post(f"/files/{file_key}/variables", payload)

        if use_json:
            output_json(data)
        else:
            output_success(f"Created collection '{name}' with modes: {', '.join(mode_list)}")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@token_group.command("create-color")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--collection", "-c", required=True, help="Collection ID.")
@click.option("--name", "-n", required=True, help="Variable name (e.g. 'primary-500').")
@click.option("--value", "-v", required=True, help="Color hex value (e.g. '#FF5500').")
@click.option("--mode", "-m", default=None, help="Mode ID (uses first mode if not specified).")
@click.option("--description", "-d", default="", help="Variable description.")
@click.pass_context
def create_color(ctx, file_key, collection, name, value, mode, description):
    """Create a COLOR variable (design token)."""
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()
        color = _parse_color(value)

        # If no mode specified, get the first mode from the collection
        if not mode:
            var_data = client.get_local_variables(file_key)
            coll = var_data.get("meta", {}).get("variableCollections", {}).get(collection, {})
            modes = coll.get("modes", [])
            if modes:
                mode = modes[0].get("modeId")
            else:
                output_error("Could not determine mode ID. Specify --mode explicitly.")
                raise SystemExit(1)

        payload = {
            "variables": [
                {
                    "action": "CREATE",
                    "id": f"temp_var_{name.replace(' ', '_').replace('/', '_')}",
                    "name": name,
                    "variableCollectionId": collection,
                    "resolvedType": "COLOR",
                    "description": description,
                }
            ],
            "variableModeValues": [
                {
                    "variableId": f"temp_var_{name.replace(' ', '_').replace('/', '_')}",
                    "modeId": mode,
                    "value": color,
                }
            ],
        }

        data = client._post(f"/files/{file_key}/variables", payload)

        if use_json:
            output_json({"name": name, "value": value, "rgba": color, "response": data})
        else:
            output_success(f"Created color token '{name}' = {value}")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@token_group.command("create-number")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--collection", "-c", required=True, help="Collection ID.")
@click.option("--name", "-n", required=True, help="Variable name (e.g. 'spacing/md').")
@click.option("--value", "-v", required=True, type=float, help="Numeric value.")
@click.option("--mode", "-m", default=None, help="Mode ID.")
@click.option("--description", "-d", default="", help="Variable description.")
@click.pass_context
def create_number(ctx, file_key, collection, name, value, mode, description):
    """Create a FLOAT variable (spacing, sizing, etc.)."""
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()

        if not mode:
            var_data = client.get_local_variables(file_key)
            coll = var_data.get("meta", {}).get("variableCollections", {}).get(collection, {})
            modes = coll.get("modes", [])
            if modes:
                mode = modes[0].get("modeId")
            else:
                output_error("Could not determine mode ID. Specify --mode explicitly.")
                raise SystemExit(1)

        payload = {
            "variables": [
                {
                    "action": "CREATE",
                    "id": f"temp_var_{name.replace(' ', '_').replace('/', '_')}",
                    "name": name,
                    "variableCollectionId": collection,
                    "resolvedType": "FLOAT",
                    "description": description,
                }
            ],
            "variableModeValues": [
                {
                    "variableId": f"temp_var_{name.replace(' ', '_').replace('/', '_')}",
                    "modeId": mode,
                    "value": value,
                }
            ],
        }

        data = client._post(f"/files/{file_key}/variables", payload)

        if use_json:
            output_json({"name": name, "value": value, "response": data})
        else:
            output_success(f"Created number token '{name}' = {value}")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@token_group.command("create-string")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--collection", "-c", required=True, help="Collection ID.")
@click.option("--name", "-n", required=True, help="Variable name.")
@click.option("--value", "-v", required=True, help="String value.")
@click.option("--mode", "-m", default=None, help="Mode ID.")
@click.option("--description", "-d", default="", help="Variable description.")
@click.pass_context
def create_string(ctx, file_key, collection, name, value, mode, description):
    """Create a STRING variable."""
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()

        if not mode:
            var_data = client.get_local_variables(file_key)
            coll = var_data.get("meta", {}).get("variableCollections", {}).get(collection, {})
            modes = coll.get("modes", [])
            if modes:
                mode = modes[0].get("modeId")
            else:
                output_error("Could not determine mode ID. Specify --mode explicitly.")
                raise SystemExit(1)

        payload = {
            "variables": [
                {
                    "action": "CREATE",
                    "id": f"temp_var_{name.replace(' ', '_').replace('/', '_')}",
                    "name": name,
                    "variableCollectionId": collection,
                    "resolvedType": "STRING",
                    "description": description,
                }
            ],
            "variableModeValues": [
                {
                    "variableId": f"temp_var_{name.replace(' ', '_').replace('/', '_')}",
                    "modeId": mode,
                    "value": value,
                }
            ],
        }

        data = client._post(f"/files/{file_key}/variables", payload)

        if use_json:
            output_json({"name": name, "value": value, "response": data})
        else:
            output_success(f"Created string token '{name}' = \"{value}\"")
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@token_group.command("import")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--collection", "-c", required=True, help="Collection ID.")
@click.option("--from-file", "-i", "input_file", required=True, type=click.Path(exists=True),
              help="JSON file with tokens to import.")
@click.option("--mode", "-m", default=None, help="Mode ID.")
@click.pass_context
def import_tokens(ctx, file_key, collection, input_file, mode):
    """Bulk import tokens from a JSON file.

    JSON format:
    {
      "colors": {
        "primary-500": "#FF5500",
        "neutral-100": "#F5F5F5"
      },
      "numbers": {
        "spacing/sm": 8,
        "spacing/md": 16,
        "spacing/lg": 24
      },
      "strings": {
        "font/heading": "Inter",
        "font/body": "Inter"
      }
    }
    """
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()

        with open(input_file) as f:
            tokens = json.load(f)

        if not mode:
            var_data = client.get_local_variables(file_key)
            coll = var_data.get("meta", {}).get("variableCollections", {}).get(collection, {})
            modes = coll.get("modes", [])
            if modes:
                mode = modes[0].get("modeId")
            else:
                output_error("Could not determine mode ID. Specify --mode explicitly.")
                raise SystemExit(1)

        variables = []
        mode_values = []
        created = []

        # Colors
        for name, hex_val in tokens.get("colors", {}).items():
            temp_id = f"temp_var_c_{name.replace(' ', '_').replace('/', '_')}"
            variables.append({
                "action": "CREATE",
                "id": temp_id,
                "name": name,
                "variableCollectionId": collection,
                "resolvedType": "COLOR",
            })
            mode_values.append({
                "variableId": temp_id,
                "modeId": mode,
                "value": _parse_color(hex_val),
            })
            created.append({"name": name, "type": "COLOR", "value": hex_val})

        # Numbers
        for name, num_val in tokens.get("numbers", {}).items():
            temp_id = f"temp_var_n_{name.replace(' ', '_').replace('/', '_')}"
            variables.append({
                "action": "CREATE",
                "id": temp_id,
                "name": name,
                "variableCollectionId": collection,
                "resolvedType": "FLOAT",
            })
            mode_values.append({
                "variableId": temp_id,
                "modeId": mode,
                "value": float(num_val),
            })
            created.append({"name": name, "type": "FLOAT", "value": num_val})

        # Strings
        for name, str_val in tokens.get("strings", {}).items():
            temp_id = f"temp_var_s_{name.replace(' ', '_').replace('/', '_')}"
            variables.append({
                "action": "CREATE",
                "id": temp_id,
                "name": name,
                "variableCollectionId": collection,
                "resolvedType": "STRING",
            })
            mode_values.append({
                "variableId": temp_id,
                "modeId": mode,
                "value": str_val,
            })
            created.append({"name": name, "type": "STRING", "value": str_val})

        if not variables:
            output_error("No tokens found in file.")
            raise SystemExit(1)

        payload = {
            "variables": variables,
            "variableModeValues": mode_values,
        }

        data = client._post(f"/files/{file_key}/variables", payload)

        if use_json:
            output_json({"created": created, "count": len(created), "response": data})
        else:
            output_success(f"Imported {len(created)} tokens into collection")
            output_table(
                "Imported Tokens",
                ["Name", "Type", "Value"],
                [[t["name"], t["type"], str(t["value"])] for t in created],
            )
    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)


@token_group.command("export")
@click.option("--file", "-f", "file_key", required=True, help="Figma file key.")
@click.option("--output", "-o", "output_file", default=None, help="Output JSON file path.")
@click.option("--format", "-F", "fmt", default="json", type=click.Choice(["json", "css", "tailwind"]),
              help="Export format.")
@click.pass_context
def export_tokens(ctx, file_key, output_file, fmt):
    """Export all variables from a file as JSON, CSS, or Tailwind config."""
    use_json = ctx.obj.get("json", False)

    try:
        client = FigmaClient()
        data = client.get_local_variables(file_key)
        meta = data.get("meta", {})
        variables = meta.get("variables", {})
        collections = meta.get("variableCollections", {})

        if fmt == "json":
            export = {"collections": {}}
            for cid, coll in collections.items():
                coll_data = {"name": coll.get("name"), "modes": [], "tokens": {}}
                for m in coll.get("modes", []):
                    coll_data["modes"].append(m.get("name"))
                for vid, var in variables.items():
                    if var.get("variableCollectionId") == cid:
                        coll_data["tokens"][var.get("name")] = {
                            "type": var.get("resolvedType"),
                            "description": var.get("description", ""),
                            "values": var.get("valuesByMode", {}),
                        }
                export["collections"][coll.get("name")] = coll_data

            if output_file:
                Path(output_file).write_text(json.dumps(export, indent=2))
                output_success(f"Exported tokens → {output_file}")
            elif use_json:
                output_json(export)
            else:
                output_json(export)

        elif fmt == "css":
            lines = [":root {"]
            for vid, var in variables.items():
                name = var.get("name", "").replace("/", "-").replace(" ", "-").lower()
                vtype = var.get("resolvedType")
                values = var.get("valuesByMode", {})
                for mode_id, val in values.items():
                    if vtype == "COLOR" and isinstance(val, dict):
                        r = int(val.get("r", 0) * 255)
                        g = int(val.get("g", 0) * 255)
                        b = int(val.get("b", 0) * 255)
                        a = val.get("a", 1)
                        if a < 1:
                            lines.append(f"  --{name}: rgba({r}, {g}, {b}, {a:.2f});")
                        else:
                            lines.append(f"  --{name}: #{r:02x}{g:02x}{b:02x};")
                    elif vtype == "FLOAT":
                        lines.append(f"  --{name}: {val}px;")
                    elif vtype == "STRING":
                        lines.append(f"  --{name}: \"{val}\";")
                    break  # Just first mode for CSS
            lines.append("}")
            css_text = "\n".join(lines)

            if output_file:
                Path(output_file).write_text(css_text)
                output_success(f"Exported CSS variables → {output_file}")
            else:
                click.echo(css_text)

        elif fmt == "tailwind":
            config = {"theme": {"extend": {"colors": {}, "spacing": {}, "fontFamily": {}}}}
            for vid, var in variables.items():
                name = var.get("name", "").replace("/", "-").replace(" ", "-").lower()
                vtype = var.get("resolvedType")
                values = var.get("valuesByMode", {})
                for mode_id, val in values.items():
                    if vtype == "COLOR" and isinstance(val, dict):
                        r = int(val.get("r", 0) * 255)
                        g = int(val.get("g", 0) * 255)
                        b = int(val.get("b", 0) * 255)
                        config["theme"]["extend"]["colors"][name] = f"#{r:02x}{g:02x}{b:02x}"
                    elif vtype == "FLOAT":
                        config["theme"]["extend"]["spacing"][name] = f"{val}px"
                    elif vtype == "STRING" and "font" in name.lower():
                        config["theme"]["extend"]["fontFamily"][name] = [val]
                    break

            # Clean empty keys
            config["theme"]["extend"] = {k: v for k, v in config["theme"]["extend"].items() if v}

            tw_text = json.dumps(config, indent=2)
            if output_file:
                Path(output_file).write_text(tw_text)
                output_success(f"Exported Tailwind config → {output_file}")
            elif use_json:
                output_json(config)
            else:
                click.echo(tw_text)

    except FigmaAPIError as e:
        output_error(str(e))
        raise SystemExit(1)
