"""Step 2: Tool selection screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Label, RadioButton, RadioSet, Static

TOOL_SUPPORT = {
    "directory": ["feroxbuster", "ffuf", "gobuster", "dirb", "wfuzz", "dirsearch"],
    "vhost": ["ffuf", "gobuster", "wfuzz"],
    "dns": ["gobuster", "amass", "subfinder"],
}

TOOL_DESCRIPTIONS = {
    "feroxbuster": "Fast, recursive, auto-calibrating, best for thorough directory scans",
    "ffuf": "Fastest and most flexible, excellent for vhost fuzzing and parameter discovery",
    "gobuster": "Fast, reliable, good multi-mode support including DNS",
    "dirb": "Simple and low-noise, good for quick scans on sensitive targets",
    "wfuzz": "Highly flexible, best when you need fine-grained response filtering",
    "dirsearch": "Good defaults and easy extension handling",
    "amass": "OWASP project, powerful passive and active subdomain enumeration",
    "subfinder": "Fast passive subdomain discovery using multiple sources",
}


class ToolSelectScreen(Screen):
    """Screen for selecting the scanning tool."""

    BINDINGS = [
        Binding("q", "quit_app", "Quit"),
        Binding("escape", "go_back", "Back"),
    ]

    _current_index: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        scan_type = getattr(self.app, "scan_type", "directory")

        with Vertical(id="tool-select-container"):
            yield Static(
                "[bold cyan]Step 2:[/bold cyan] Select Tool",
                id="tool-select-title",
            )

            supported = TOOL_SUPPORT.get(scan_type, [])
            with RadioSet(id="tool-radio"):
                for tool in supported:
                    available = self._is_available(tool)
                    desc = TOOL_DESCRIPTIONS.get(tool, "")
                    btn = RadioButton(
                        f"{tool}: {desc}",
                        id=f"tool-{tool}",
                    )
                    btn.disabled = not available
                    yield btn

            yield Label("", id="tool-select-description")
            with Center():
                yield Button("Continue", id="tool-select-continue-btn", variant="primary")
            yield Static(
                "[dim]Use arrow keys to browse, press Enter or click Continue to proceed, Escape to go back[/dim]",
                id="tool-select-hint",
            )

    def _is_available(self, tool: str) -> bool:
        available = getattr(self.app, "available_tools", {})
        return available.get(tool, False)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Confirm if user re-selected the same option (Enter on current selection)."""
        new_index = event.radio_set.pressed_index
        if new_index == self._current_index:
            self._confirm_selection()
        else:
            self._current_index = new_index

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tool-select-continue-btn":
            self._confirm_selection()

    def action_quit_app(self) -> None:
        self.app.exit()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def _confirm_selection(self) -> None:
        scan_type = getattr(self.app, "scan_type", "directory")
        supported = TOOL_SUPPORT.get(scan_type, [])
        try:
            radio = self.query_one("#tool-radio", RadioSet)
            index = radio.pressed_index
            if 0 <= index < len(supported):
                self.app.selected_tool = supported[index]
                self.app.go_to_target()
        except Exception:
            pass
