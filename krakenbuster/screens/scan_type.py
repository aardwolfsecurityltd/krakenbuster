"""Step 1: Scan type selection screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Label, RadioButton, RadioSet, Static


SCAN_TYPES = {
    "directory": {
        "label": "Directory and file brute-forcing",
        "description": "Discover hidden directories and files on the target web server",
    },
    "vhost": {
        "label": "Vhost fuzzing",
        "description": "Enumerate virtual hosts on the target by fuzzing the Host header",
    },
    "dns": {
        "label": "DNS subdomain enumeration",
        "description": "Discover subdomains of the target domain via DNS resolution",
    },
}


class ScanTypeScreen(Screen):
    """Screen for selecting the scan type."""

    BINDINGS = [
        Binding("q", "quit_app", "Quit"),
    ]

    _current_index: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="scan-type-container"):
            yield Static(
                "[bold cyan]Step 1:[/bold cyan] Select Scan Type",
                id="scan-type-title",
            )
            with RadioSet(id="scan-type-radio"):
                for key, info in SCAN_TYPES.items():
                    yield RadioButton(info["label"], id=f"scan-{key}")
            yield Label("", id="scan-type-description")
            with Center():
                yield Button("Continue", id="scan-type-continue-btn", variant="primary")
            yield Static(
                "[dim]Use arrow keys to browse, press Enter or click Continue to proceed, Q to quit[/dim]",
                id="scan-type-hint",
            )

    def on_mount(self) -> None:
        """Select the first radio button by default and show its description."""
        radio_set = self.query_one("#scan-type-radio", RadioSet)
        radio_set.focus()
        self._current_index = 0
        self._update_description(0)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Update description, and confirm if user re-selected the same option."""
        new_index = event.radio_set.pressed_index
        if new_index == self._current_index:
            # User pressed Enter on the already-selected option: treat as confirm
            self._confirm_selection()
        else:
            self._current_index = new_index
            self._update_description(new_index)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan-type-continue-btn":
            self._confirm_selection()

    def _update_description(self, index: int) -> None:
        keys = list(SCAN_TYPES.keys())
        if 0 <= index < len(keys):
            desc = SCAN_TYPES[keys[index]]["description"]
            label = self.query_one("#scan-type-description", Label)
            label.update(f"[italic]{desc}[/italic]")

    def action_quit_app(self) -> None:
        self.app.exit()

    def _confirm_selection(self) -> None:
        radio_set = self.query_one("#scan-type-radio", RadioSet)
        index = radio_set.pressed_index
        keys = list(SCAN_TYPES.keys())
        if 0 <= index < len(keys):
            self.app.scan_type = keys[index]
            self.app.go_to_tool_select()
