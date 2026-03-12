"""Output formatters for cli-anything-figma.

Supports two modes:
  - JSON (--json flag): structured machine-readable output
  - Table/Rich: human-readable coloured tables
"""
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich import box

console = Console(stderr=False)
err_console = Console(stderr=True)


def output_json(data: Any):
    """Print data as formatted JSON to stdout."""
    click.echo(json.dumps(data, indent=2, default=str))


def output_table(title: str, columns: list[str], rows: list[list[str]]):
    """Print a Rich table to stdout."""
    table = Table(title=title, box=box.ROUNDED, show_lines=False)
    for col in columns:
        table.add_column(col, style="cyan")
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def output_tree(title: str, items: list[dict], key_field: str = "name", id_field: str = "id"):
    """Print a Rich tree view."""
    tree = Tree(f"[bold]{title}[/bold]")
    for item in items:
        name = item.get(key_field, "unnamed")
        item_id = item.get(id_field, "")
        tree.add(f"[cyan]{name}[/cyan]  [dim]({item_id})[/dim]")
    console.print(tree)


def output_panel(title: str, content: str):
    """Print a Rich panel."""
    console.print(Panel(content, title=title, border_style="blue"))


def output_success(message: str):
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def output_error(message: str):
    """Print an error message to stderr."""
    err_console.print(f"[red]✗[/red] {message}")


def output_warning(message: str):
    """Print a warning message to stderr."""
    err_console.print(f"[yellow]⚠[/yellow] {message}")


def output_info(message: str):
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def truncate(text: str, length: int = 60) -> str:
    """Truncate a string with ellipsis."""
    if not text:
        return ""
    return text[:length] + "…" if len(text) > length else text
