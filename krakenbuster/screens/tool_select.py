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
    "dns": ["gobuster"],
}

TOOL_DESCRIPTIONS = {
    "feroxbuster": "Fast, recursive, auto-calibrating, best for thorough directory scans",
    "ffuf": "Fastest and most flexible, excellent for vhost fuzzing and parameter discovery",
    "gobuster": "Fast, reliable, good multi-mode support including DNS",
    "dirb": "Simple and low-noise, good for quick scans on sensitive targets",
    "wfuzz": "Highly flexible, best when you need fine-grained response filtering",
    "dirsearch": "Good defaults and easy extension handling",
}


class ToolSelectScreen(Screen):
    """Screen for selecting the scanning tool."""

    BINDINGS = [
        Binding("q", "quit_app", "Quit"),
        Binding("escape", "go_back", "Back"),
    ]

    _current_index: int = 0
    _current_dir_index: int = 0
    _current_vhost_index: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        scan_type = getattr(self.app, "scan_type", "directory")

        with Vertical(id="tool-select-container"):
            yield Static(
                "[bold cyan]Step 2:[/bold cyan] Select Tool",
                id="tool-select-title",
            )

            if scan_type == "combined":
                yield Static(
                    "[bold]Directory scanning tool:[/bold]",
                    id="dir-tool-label",
                )
                with RadioSet(id="dir-tool-radio"):
                    for tool in TOOL_SUPPORT["directory"]:
                        available = self._is_available(tool)
                        desc = TOOL_DESCRIPTIONS[tool]
                        btn = RadioButton(
                            f"{tool}: {desc}",
                            id=f"dir-{tool}",
                        )
                        btn.disabled = not available
                        yield btn

                yield Static(
                    "[bold]Vhost fuzzing tool:[/bold]",
                    id="vhost-tool-label",
                )
                with RadioSet(id="vhost-tool-radio"):
                    for tool in TOOL_SUPPORT["vhost"]:
                        available = self._is_available(tool)
                        desc = TOOL_DESCRIPTIONS[tool]
                        btn = RadioButton(
                            f"{tool}: {desc}",
                            id=f"vhost-{tool}",
                        )
                        btn.disabled = not available
                        yield btn
            else:
                supported = TOOL_SUPPORT.get(scan_type, [])
                with RadioSet(id="tool-radio"):
                    for tool in supported:
                        available = self._is_available(tool)
                        desc = TOOL_DESCRIPTIONS[tool]
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
        radio_id = event.radio_set.id
        new_index = event.radio_set.pressed_index

        if radio_id == "dir-tool-radio":
            if new_index == self._current_dir_index:
                # Move focus to the vhost radio set for combined mode
                try:
                    self.query_one("#vhost-tool-radio", RadioSet).focus()
                except Exception:
                    pass
            else:
                self._current_dir_index = new_index
        elif radio_id == "vhost-tool-radio":
            if new_index == self._current_vhost_index:
                self._confirm_selection()
            else:
                self._current_vhost_index = new_index
        elif radio_id == "tool-radio":
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

        if scan_type == "combined":
            dir_radio = self.query_one("#dir-tool-radio", RadioSet)
            vhost_radio = self.query_one("#vhost-tool-radio", RadioSet)

            dir_index = dir_radio.pressed_index
            vhost_index = vhost_radio.pressed_index

            dir_tools = TOOL_SUPPORT["directory"]
            vhost_tools = TOOL_SUPPORT["vhost"]

            if 0 <= dir_index < len(dir_tools) and 0 <= vhost_index < len(vhost_tools):
                self.app.selected_tool = dir_tools[dir_index]
                self.app.selected_vhost_tool = vhost_tools[vhost_index]
                self.app.go_to_target()
        else:
            supported = TOOL_SUPPORT.get(scan_type, [])
            try:
                radio = self.query_one("#tool-radio", RadioSet)
                index = radio.pressed_index
                if 0 <= index < len(supported):
                    self.app.selected_tool = supported[index]
                    self.app.go_to_target()
            except Exception:
                pass
