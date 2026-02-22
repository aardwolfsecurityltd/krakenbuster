"""Step 5: Scan options form screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, Static, Switch


# Option definitions per tool and mode
# Each entry: (key, label, default, widget_type)
# widget_type: "input" or "switch"

TOOL_OPTIONS = {
    "feroxbuster": {
        "directory": [
            ("depth", "Recursion depth", "3", "input"),
            ("extensions", "File extensions", "php,html,txt,js", "input"),
            ("threads", "Threads", "50", "input"),
            ("rate_limit", "Rate limit (req/s)", "200", "input"),
            ("proxy", "Proxy", "", "input"),
            ("status_codes", "Status codes to include", "200,204,301,302,307,401,403", "input"),
        ],
    },
    "ffuf": {
        "directory": [
            ("extensions", "File extensions", "php,html,txt,js", "input"),
            ("threads", "Threads", "50", "input"),
            ("rate_limit", "Rate limit", "200", "input"),
            ("proxy", "Proxy", "", "input"),
            ("filter_codes", "Filter status codes", "400,404", "input"),
            ("filter_size", "Filter response size", "", "input"),
        ],
        "vhost": [
            ("domain", "Base domain for Host header", "", "input"),
            ("threads", "Threads", "50", "input"),
            ("rate_limit", "Rate limit", "200", "input"),
            ("proxy", "Proxy", "", "input"),
            ("filter_codes", "Filter status codes", "400,404", "input"),
            ("filter_size", "Filter response size", "", "input"),
        ],
    },
    "gobuster": {
        "directory": [
            ("extensions", "File extensions", "php,html,txt,js", "input"),
            ("threads", "Threads", "50", "input"),
            ("status_codes", "Status codes", "200,204,301,302,307,401,403", "input"),
            ("proxy", "Proxy", "", "input"),
            ("follow_redirects", "Follow redirects", "true", "switch"),
            ("expanded", "Expanded output", "false", "switch"),
        ],
        "vhost": [
            ("domain", "Base domain", "", "input"),
            ("threads", "Threads", "50", "input"),
            ("proxy", "Proxy", "", "input"),
            ("append_domain", "Append domain to wordlist entries", "true", "switch"),
        ],
        "dns": [
            ("resolver", "Custom resolver", "", "input"),
            ("show_ips", "Show IPs", "true", "switch"),
            ("threads", "Threads", "50", "input"),
        ],
    },
    "dirb": {
        "directory": [
            ("extensions", "File extensions", "", "input"),
            ("case_insensitive", "Case insensitive", "false", "switch"),
            ("proxy", "Proxy", "", "input"),
            ("auth", "Basic auth (user:pass)", "", "input"),
            ("non_recursive", "Non-recursive", "false", "switch"),
        ],
    },
    "wfuzz": {
        "directory": [
            ("threads", "Threads", "50", "input"),
            ("hide_codes", "Hide status codes", "404", "input"),
            ("filter_lines", "Filter lines", "", "input"),
            ("filter_words", "Filter words", "", "input"),
            ("proxy", "Proxy", "", "input"),
            ("extensions", "File extensions", "", "input"),
        ],
        "vhost": [
            ("domain", "Base domain for Host header", "", "input"),
            ("threads", "Threads", "50", "input"),
            ("hide_codes", "Hide status codes", "404", "input"),
            ("filter_lines", "Filter lines", "", "input"),
            ("filter_words", "Filter words", "", "input"),
            ("proxy", "Proxy", "", "input"),
        ],
    },
    "dirsearch": {
        "directory": [
            ("extensions", "File extensions", "php,html,txt,js", "input"),
            ("threads", "Threads", "50", "input"),
            ("proxy", "Proxy", "", "input"),
            ("recursive", "Recursive", "true", "switch"),
            ("depth", "Recursion depth", "3", "input"),
            ("filter_codes", "Filter status codes", "400,404", "input"),
            ("random_agents", "Random user agents", "true", "switch"),
        ],
    },
    "amass": {
        "dns": [
            ("passive", "Passive mode only", "true", "switch"),
            ("timeout", "Timeout (minutes)", "30", "input"),
            ("resolver", "Custom resolver file", "", "input"),
            ("max_dns_queries", "Max DNS queries", "", "input"),
            ("brute_force", "Enable brute forcing", "false", "switch"),
        ],
    },
    "subfinder": {
        "dns": [
            ("threads", "Threads", "30", "input"),
            ("timeout", "Timeout (seconds)", "30", "input"),
            ("max_time", "Max enumeration time (minutes)", "10", "input"),
            ("resolver", "Custom resolver file", "", "input"),
            ("all_sources", "Use all sources", "true", "switch"),
            ("recursive", "Recursive enumeration", "false", "switch"),
        ],
    },
}


class OptionsScreen(Screen):
    """Screen for configuring scan options."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        tool = getattr(self.app, "selected_tool", "feroxbuster")
        scan_type = getattr(self.app, "scan_type", "directory")

        with Vertical(id="options-container"):
            yield Static(
                f"[bold cyan]Step 5:[/bold cyan] Configure {tool} Options ({scan_type} mode)",
                id="options-title",
            )

            options = self._get_options(tool, scan_type)
            for key, label, default, widget_type in options:
                with Horizontal(classes="option-row"):
                    yield Label(f"{label}:", classes="option-label")
                    if widget_type == "switch":
                        sw = Switch(
                            value=(default.lower() in ("true", "1", "yes", "on")),
                            id=f"opt-{key}",
                        )
                        yield sw
                    else:
                        placeholder = "required" if key == "domain" and not default else ""
                        yield Input(
                            value=default,
                            placeholder=placeholder,
                            id=f"opt-{key}",
                        )

            yield Label("", id="options-error")
            with Horizontal(id="options-buttons"):
                yield Button("Continue", id="options-continue-btn", variant="primary")
                yield Button("Back", id="options-back-btn")
            yield Static(
                "[dim]Tab through fields, modify as needed. Press Continue when ready.[/dim]",
                id="options-hint",
            )

    def _get_options(self, tool: str, mode: str) -> list[tuple[str, str, str, str]]:
        """Get the option definitions for a tool and mode."""
        tool_opts = TOOL_OPTIONS.get(tool, {})
        return tool_opts.get(mode, [])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "options-continue-btn":
            self._collect_and_continue()
        elif event.button.id == "options-back-btn":
            self.app.pop_screen()

    def _collect_and_continue(self) -> None:
        """Collect all option values and navigate to confirmation."""
        tool = getattr(self.app, "selected_tool", "feroxbuster")
        scan_type = getattr(self.app, "scan_type", "directory")

        options = self._get_options(tool, scan_type)
        collected: dict[str, str] = {}

        for key, label, default, widget_type in options:
            widget_id = f"opt-{key}"
            try:
                if widget_type == "switch":
                    widget = self.query_one(f"#{widget_id}", Switch)
                    collected[key] = str(widget.value).lower()
                else:
                    widget = self.query_one(f"#{widget_id}", Input)
                    collected[key] = widget.value
            except Exception:
                collected[key] = default

        # Validate required fields
        if "domain" in collected and not collected["domain"] and scan_type == "vhost":
            error_label = self.query_one("#options-error", Label)
            error_label.update("[bold red]Base domain is required for vhost mode[/bold red]")
            return

        self.app.scan_options = collected
        self.app.go_to_confirm()

    def action_go_back(self) -> None:
        self.app.pop_screen()
