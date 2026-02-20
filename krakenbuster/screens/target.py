"""Step 3: Target input and validation screen."""

from __future__ import annotations

import re

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, Static


def validate_target(target: str, scan_type: str) -> str | None:
    """Validate the target input. Returns an error message or None if valid."""
    target = target.strip()
    if not target:
        return "Target cannot be empty"

    if scan_type == "dns":
        # DNS mode: must be a bare domain with no protocol
        if target.startswith("http://") or target.startswith("https://"):
            return "DNS mode requires a bare domain without protocol (e.g. example.com)"
        # Basic domain validation
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$", target):
            return "Invalid domain format"
    else:
        # Directory and vhost modes: must begin with http:// or https://
        if not (target.startswith("http://") or target.startswith("https://")):
            return "Target must begin with http:// or https://"
        # Basic URL validation
        url_pattern = r"^https?://[a-zA-Z0-9\-\.\:]+(/.*)?$"
        if not re.match(url_pattern, target):
            return "Invalid URL format"

    return None


class TargetScreen(Screen):
    """Screen for entering the target URL or domain."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "quit_app", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        scan_type = getattr(self.app, "scan_type", "directory")

        with Vertical(id="target-container"):
            yield Static(
                "[bold cyan]Step 3:[/bold cyan] Enter Target",
                id="target-title",
            )

            if scan_type == "dns":
                yield Static(
                    "[dim]Enter the target domain (e.g. example.com)[/dim]",
                    id="target-help",
                )
                yield Input(
                    placeholder="example.com",
                    id="target-input",
                )
            else:
                yield Static(
                    "[dim]Enter the target URL with protocol (e.g. https://target.com)[/dim]",
                    id="target-help",
                )
                yield Input(
                    placeholder="https://target.com",
                    id="target-input",
                )

            yield Label("", id="target-error")
            yield Button("Continue", id="target-continue-btn", variant="primary")
            yield Static(
                "[dim]Press Enter to submit, Escape to go back[/dim]",
                id="target-hint",
            )

    def on_mount(self) -> None:
        self.query_one("#target-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "target-input":
            self._validate_and_continue()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "target-continue-btn":
            self._validate_and_continue()

    def _validate_and_continue(self) -> None:
        target_input = self.query_one("#target-input", Input)
        target = target_input.value.strip()
        scan_type = getattr(self.app, "scan_type", "directory")

        error = validate_target(target, scan_type)
        error_label = self.query_one("#target-error", Label)

        if error:
            error_label.update(f"[bold red]{error}[/bold red]")
        else:
            error_label.update("")
            self.app.target = target
            self.app.go_to_wordlist()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.exit()
