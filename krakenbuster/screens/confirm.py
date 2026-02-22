"""Step 6: Confirmation and command preview screen."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from krakenbuster.scanners.base import create_scanner


class ConfirmScreen(Screen):
    """Screen showing scan configuration summary and command preview."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="confirm-container"):
            yield Static(
                "[bold cyan]Step 6:[/bold cyan] Confirm and Run",
                id="confirm-title",
            )
            with Horizontal(id="confirm-panels"):
                yield Static("", id="confirm-summary")
                yield Static("", id="confirm-command")
            with Horizontal(id="confirm-buttons"):
                yield Button("Run Scan", id="run-btn", variant="success")
                yield Button("Go Back", id="back-btn")

    def on_mount(self) -> None:
        """Build the summary and command preview."""
        self._build_summary()
        self._build_command_preview()

    def _build_summary(self) -> None:
        """Build the options summary panel."""
        app = self.app
        scan_type = getattr(app, "scan_type", "")
        tool = getattr(app, "selected_tool", "")
        target = getattr(app, "target", "")
        wordlist = getattr(app, "wordlist_path", "")
        options = getattr(app, "scan_options", {})

        lines = [
            "[bold]Scan Configuration[/bold]",
            "",
            f"[bold]Scan type:[/bold]  {scan_type}",
            f"[bold]Tool:[/bold]       {tool}",
            f"[bold]Target:[/bold]     {target}",
            f"[bold]Wordlist:[/bold]   {Path(wordlist).name if wordlist else 'N/A'}",
            "",
        ]

        if options:
            lines.append("[bold]Options:[/bold]")
            for key, value in options.items():
                if value:
                    display_key = key.replace("_", " ").title()
                    lines.append(f"  {display_key}: {value}")

        summary = self.query_one("#confirm-summary", Static)
        summary.update("\n".join(lines))

    def _build_command_preview(self) -> None:
        """Build the command preview panel."""
        app = self.app
        tool = getattr(app, "selected_tool", "")
        scan_type = getattr(app, "scan_type", "")
        target = getattr(app, "target", "")
        wordlist = getattr(app, "wordlist_path", "")
        options = getattr(app, "scan_options", {})

        lines = ["[bold]Command Preview[/bold]", ""]

        try:
            scanner = create_scanner(tool, scan_type, target, wordlist, options)
            command = scanner.build_command()
            cmd_str = " ".join(command)
            lines.append(f"[bold white]$ {cmd_str}[/bold white]")
        except Exception as exc:
            lines.append(f"[red]Error building command: {exc}[/red]")

        command_widget = self.query_one("#confirm-command", Static)
        command_widget.update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self._run_in_terminal()
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def _run_in_terminal(self) -> None:
        """Build the command and exit the TUI so it runs in the real terminal."""
        app = self.app
        tool = getattr(app, "selected_tool", "")
        scan_type = getattr(app, "scan_type", "")
        target = getattr(app, "target", "")
        wordlist = getattr(app, "wordlist_path", "")
        options = getattr(app, "scan_options", {})

        commands: list[list[str]] = []
        try:
            scanner = create_scanner(tool, scan_type, target, wordlist, options)
            commands.append(scanner.build_command())
        except Exception:
            pass

        if commands:
            self.app.exit(result=commands)

    def action_go_back(self) -> None:
        self.app.pop_screen()
