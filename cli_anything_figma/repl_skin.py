"""REPL (Read-Eval-Print Loop) skin for cli-anything-figma.

Provides an interactive shell with branded banner, command history,
styled prompts, and session state — matching CLI-Anything conventions.
"""
import shlex
import sys

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel

from cli_anything_figma import __version__
from cli_anything_figma.formatters import output_error

console = Console()

BANNER = f"""\
[bold blue]╔══════════════════════════════════════════════╗[/bold blue]
[bold blue]║[/bold blue]  [bold white]cli-anything-figma[/bold white]  v{__version__:<21s} [bold blue]║[/bold blue]
[bold blue]║[/bold blue]  [dim]Figma CLI for AI Agents[/dim]                    [bold blue]║[/bold blue]
[bold blue]╚══════════════════════════════════════════════╝[/bold blue]
"""

HELP_TEXT = """\
[dim]Commands:[/dim]
  [cyan]file[/cyan]        File operations (info, list-pages, tree)
  [cyan]export[/cyan]      Export nodes as images
  [cyan]component[/cyan]   Browse components & component sets
  [cyan]style[/cyan]       Browse styles
  [cyan]comment[/cyan]     List / post / delete comments
  [cyan]project[/cyan]     Browse team projects & files
  [cyan]version[/cyan]     File version history
  [cyan]variable[/cyan]    Variables & variable collections
  [cyan]config[/cyan]      Configure token, team ID, etc.
  [cyan]me[/cyan]          Current user info
  [cyan]help[/cyan]        Show this help
  [cyan]exit[/cyan]        Quit the REPL
"""


class FigmaREPL:
    """Interactive REPL for the Figma CLI."""

    def __init__(self, cli_group: click.Group, ctx: click.Context):
        self.cli_group = cli_group
        self.ctx = ctx
        self.file_key: str | None = None
        self.session = PromptSession(
            history=FileHistory(str(
                __import__("pathlib").Path.home() / ".config" / "cli-anything-figma" / "history"
            )),
            auto_suggest=AutoSuggestFromHistory(),
        )

    def _prompt_text(self) -> str:
        if self.file_key:
            return f"figma[{self.file_key}]> "
        return "figma> "

    def run(self):
        """Start the REPL loop."""
        console.print(BANNER)
        console.print(HELP_TEXT)

        while True:
            try:
                text = self.session.prompt(
                    HTML(f"<b>{self._prompt_text()}</b>"),
                ).strip()

                if not text:
                    continue

                if text.lower() in ("exit", "quit", "q"):
                    console.print("[dim]Goodbye! 👋[/dim]")
                    break

                if text.lower() == "help":
                    console.print(HELP_TEXT)
                    continue

                # Parse input into args
                try:
                    args = shlex.split(text)
                except ValueError as e:
                    output_error(f"Parse error: {e}")
                    continue

                # Inject --file if we have an active file context
                if self.file_key and "--file" not in args and "-f" not in args:
                    # Check if the subcommand accepts --file
                    if args[0] in ("file", "export", "comment", "component", "style", "version", "variable"):
                        args = [args[0], "--file", self.file_key] + args[1:]

                # Execute through Click
                try:
                    self.cli_group(args, standalone_mode=False, **self.ctx.params)
                except click.exceptions.UsageError as e:
                    output_error(str(e))
                except SystemExit:
                    pass
                except Exception as e:
                    output_error(f"Error: {e}")

            except KeyboardInterrupt:
                console.print("\n[dim]Use 'exit' to quit.[/dim]")
            except EOFError:
                console.print("[dim]Goodbye! 👋[/dim]")
                break
