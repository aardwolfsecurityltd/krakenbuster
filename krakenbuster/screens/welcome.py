"""Welcome screen with tool availability check."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

BANNER = """\
[bold magenta]
  _  __          _               ____            _
 | |/ /_ __ __ _| | _____ _ __  | __ ) _   _ ___| |_ ___ _ __
 | ' /| '__/ _` | |/ / _ \\ '_ \\ |  _ \\| | | / __| __/ _ \\ '__|
 | . \\| | | (_| |   <  __/ | | || |_) | |_| \\__ \\ ||  __/ |
 |_|\\_\\_|  \\__,_|_|\\_\\___|_| |_||____/ \\__,_|___/\\__\\___|_|
[/bold magenta]
[bold cyan]         Web Enumeration Toolkit v1.0.0[/bold cyan]
[dim]      Guided scanner orchestration for pentesters[/dim]
"""

TOOL_INSTALL_HINTS = {
    "feroxbuster": "sudo apt install feroxbuster",
    "ffuf": "sudo apt install ffuf",
    "gobuster": "sudo apt install gobuster",
    "dirb": "sudo apt install dirb",
    "wfuzz": "sudo apt install wfuzz",
    "dirsearch": "sudo apt install dirsearch",
}


class WelcomeScreen(Screen):
    """Startup screen showing ASCII banner and tool availability."""

    BINDINGS = [
        Binding("enter", "continue", "Continue"),
        Binding("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="welcome-container"):
            yield Static(BANNER, id="banner")
            yield Static("", id="tool-status")
            with Center():
                yield Button("Continue", id="continue-btn", variant="primary")
            yield Static(
                "[dim]Press Enter to continue, Q to quit[/dim]",
                id="welcome-hint",
            )

    def on_mount(self) -> None:
        """Build and display the tool availability table."""
        app = self.app
        available = getattr(app, "available_tools", {})

        lines = ["[bold]Tool Availability[/bold]\n"]
        missing_any = False

        for tool_name in [
            "feroxbuster", "ffuf", "gobuster", "dirb", "wfuzz", "dirsearch"
        ]:
            is_available = available.get(tool_name, False)
            if is_available:
                icon = "[green]\u2714[/green]"
            else:
                icon = "[red]\u2718[/red]"
                missing_any = True
            lines.append(f"  {icon}  {tool_name}")

        if missing_any:
            lines.append("")
            lines.append("[dim]Install missing tools:[/dim]")
            for tool_name, hint in TOOL_INSTALL_HINTS.items():
                if not available.get(tool_name, False):
                    lines.append(f"  [dim]{hint}[/dim]")

        status_widget = self.query_one("#tool-status", Static)
        status_widget.update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue-btn":
            self._continue()

    def action_continue(self) -> None:
        self._continue()

    def action_quit_app(self) -> None:
        self.app.exit()

    def _continue(self) -> None:
        self.app.go_to_scan_type()
