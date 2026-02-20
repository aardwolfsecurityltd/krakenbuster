"""Results summary screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from rich.table import Table
from rich.console import Console
from rich.text import Text
from io import StringIO

from krakenbuster.output import ScanResult


class SummaryScreen(Screen):
    """Screen showing scan results summary."""

    BINDINGS = [
        Binding("n", "new_scan", "New Scan"),
        Binding("q", "quit_app", "Quit"),
    ]

    def __init__(self, result: ScanResult) -> None:
        super().__init__()
        self._result = result

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="summary-container"):
            yield Static("", id="summary-content")
            yield Static("", id="summary-findings")
            yield Static("", id="summary-files")
            yield Static("", id="summary-stderr")
            with Horizontal(id="summary-buttons"):
                yield Button("New Scan", id="new-scan-btn", variant="primary")
                yield Button("Quit", id="quit-btn", variant="error")

    def on_mount(self) -> None:
        """Build the summary display."""
        result = self._result
        from pathlib import Path

        wordlist_name = Path(result.wordlist).name if result.wordlist else "N/A"

        # Main summary
        lines = [
            "[bold cyan]Scan Complete[/bold cyan]",
            "",
            f"[bold]Tool:[/bold]           {result.tool}",
            f"[bold]Scan mode:[/bold]      {result.mode}",
            f"[bold]Target:[/bold]         {result.target}",
            f"[bold]Wordlist:[/bold]       {wordlist_name}",
            f"[bold]Words tested:[/bold]   {result.total_words:,}",
            f"[bold]Duration:[/bold]       {result.duration_formatted}",
            f"[bold green]Total findings:[/bold green]  {len(result.findings)}",
        ]

        summary_widget = self.query_one("#summary-content", Static)
        summary_widget.update("\n".join(lines))

        # Findings breakdown table
        if result.findings:
            findings_markup = self._build_findings_table(result)
            findings_widget = self.query_one("#summary-findings", Static)
            findings_widget.update(findings_markup)

        # Output files
        file_lines = ["", "[bold]Output files:[/bold]"]
        raw_path = getattr(result, "_raw_path", None)
        json_path = getattr(result, "_json_path", None)
        vhost_raw_path = getattr(result, "_vhost_raw_path", None)
        vhost_json_path = getattr(result, "_vhost_json_path", None)

        if raw_path:
            file_lines.append(f"  Raw:  {raw_path}")
        if json_path:
            file_lines.append(f"  JSON: {json_path}")
        if vhost_raw_path:
            file_lines.append(f"  Vhost raw:  {vhost_raw_path}")
        if vhost_json_path:
            file_lines.append(f"  Vhost JSON: {vhost_json_path}")

        files_widget = self.query_one("#summary-files", Static)
        files_widget.update("\n".join(file_lines))

        # Stderr warnings
        if result.stderr_lines:
            stderr_lines = [
                "",
                "[bold red]Warnings and errors:[/bold red]",
            ]
            for line in result.stderr_lines[-20:]:
                stderr_lines.append(f"  [red]{line}[/red]")
            stderr_widget = self.query_one("#summary-stderr", Static)
            stderr_widget.update("\n".join(stderr_lines))

    def _build_findings_table(self, result: ScanResult) -> str:
        """Build a Rich table markup for findings breakdown."""
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=100)

        table = Table(title="Findings Breakdown", border_style="cyan")
        table.add_column("Status Code", style="cyan", width=12, justify="center")
        table.add_column("Count", style="green", width=8, justify="right")
        table.add_column("Example URL", style="white", min_width=40)

        for status, items in sorted(result.findings_by_status.items()):
            example = items[0].url if items[0].url else "N/A"
            table.add_row(str(status), str(len(items)), example)

        console.print(table)
        return buf.getvalue()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-scan-btn":
            self.app.start_new_scan()
        elif event.button.id == "quit-btn":
            self.app.exit()

    def action_new_scan(self) -> None:
        self.app.start_new_scan()

    def action_quit_app(self) -> None:
        self.app.exit()
