"""KrakenBuster Textual App class and screen orchestration."""

from __future__ import annotations

import shutil

from textual.app import App

from krakenbuster.screens.welcome import WelcomeScreen
from krakenbuster.screens.scan_type import ScanTypeScreen
from krakenbuster.screens.tool_select import ToolSelectScreen
from krakenbuster.screens.target import TargetScreen
from krakenbuster.screens.wordlist import WordlistScreen
from krakenbuster.screens.options import OptionsScreen
from krakenbuster.screens.confirm import ConfirmScreen


TOOLS = ["feroxbuster", "ffuf", "gobuster", "dirb", "wfuzz", "dirsearch", "amass", "subfinder"]

# Which tools support which modes
TOOL_SUPPORT = {
    "directory": ["feroxbuster", "ffuf", "gobuster", "dirb", "wfuzz", "dirsearch"],
    "vhost": ["ffuf", "gobuster", "wfuzz"],
    "dns": ["gobuster", "amass", "subfinder"],
}


class KrakenBusterApp(App):
    """Main KrakenBuster TUI application."""

    TITLE = "KrakenBuster"
    CSS_PATH = "styles.tcss"

    # Shared scan state
    available_tools: dict[str, bool] = {}
    scan_type: str = ""
    selected_tool: str = ""
    target: str = ""
    wordlist_path: str = ""
    scan_options: dict[str, str] = {}

    def on_mount(self) -> None:
        """Check tool availability and push the welcome screen."""
        self.available_tools = {
            tool: shutil.which(tool) is not None for tool in TOOLS
        }
        self.push_screen(WelcomeScreen())

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.exit()

    def go_to_scan_type(self) -> None:
        """Navigate to scan type selection."""
        self.push_screen(ScanTypeScreen())

    def go_to_tool_select(self) -> None:
        """Navigate to tool selection."""
        self.push_screen(ToolSelectScreen())

    def go_to_target(self) -> None:
        """Navigate to target input."""
        self.push_screen(TargetScreen())

    def go_to_wordlist(self) -> None:
        """Navigate to wordlist selection."""
        self.push_screen(WordlistScreen())

    def go_to_options(self) -> None:
        """Navigate to scan options."""
        self.push_screen(OptionsScreen())

    def go_to_confirm(self) -> None:
        """Navigate to confirmation screen."""
        self.push_screen(ConfirmScreen())

    def start_new_scan(self) -> None:
        """Reset state and return to scan type selection."""
        self.scan_type = ""
        self.selected_tool = ""
        self.target = ""
        self.wordlist_path = ""
        self.scan_options = {}
        # Pop all screens back to a clean slate
        while len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(ScanTypeScreen())
