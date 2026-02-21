"""Live scanning view screen."""

from __future__ import annotations

import asyncio
import os
import time
from collections import deque
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Header,
    Label,
    ProgressBar,
    RichLog,
    Static,
)

from krakenbuster.output import (
    Finding,
    ScanResult,
    append_raw_line,
    generate_output_paths,
    parse_finding,
    write_json_results,
)
from krakenbuster.scanners.base import ScanLine, create_scanner
from krakenbuster.wordlist import count_lines


class ScanOutputLine(Message):
    """Message posted when a scan produces output."""

    def __init__(self, line: ScanLine, scanner_id: str = "primary") -> None:
        super().__init__()
        self.line = line
        self.scanner_id = scanner_id


class ScanComplete(Message):
    """Message posted when a scan finishes."""

    def __init__(self, scanner_id: str = "primary") -> None:
        super().__init__()
        self.scanner_id = scanner_id


class ScanningScreen(Screen):
    """Live scanning view with progress, raw output, and findings table."""

    BINDINGS = [
        Binding("ctrl+c", "cancel_scan", "Cancel scan"),
        Binding("q", "cancel_scan", "Cancel"),
    ]

    _start_time: float = 0.0
    _total_words: int = 0
    _lines_received: int = 0
    _errors: int = 0
    _findings: list[Finding] = []
    _raw_lines: list[str] = []
    _stderr_lines: list[str] = []
    _rate_samples: deque = deque(maxlen=50)
    _scanner = None
    _vhost_scanner = None
    _scan_tasks: list[asyncio.Task] = []
    _raw_path: Path | None = None
    _json_path: Path | None = None
    _vhost_raw_path: Path | None = None
    _vhost_json_path: Path | None = None
    _vhost_findings: list[Finding] = []
    _vhost_lines_received: int = 0
    _vhost_raw_lines: list[str] = []
    _vhost_stderr_lines: list[str] = []
    _completed_scanners: int = 0
    _total_scanners: int = 1

    def compose(self) -> ComposeResult:
        scan_type = getattr(self.app, "scan_type", "directory")
        tool = getattr(self.app, "selected_tool", "")
        target = getattr(self.app, "target", "")
        wordlist = getattr(self.app, "wordlist_path", "")

        yield Header()

        with Vertical(id="scanning-outer"):
            # Top bar
            yield Static(
                f"[bold]{tool}[/bold] | {target} | {Path(wordlist).name} | Elapsed: 0s | 0 req/s",
                id="scan-top-bar",
            )

            # Main content area
            with Horizontal(id="scanning-main"):
                # Left column: progress + findings
                with Vertical(id="scanning-left"):
                    # Progress panel
                    with Vertical(id="progress-panel"):
                        yield ProgressBar(
                            total=100,
                            show_eta=False,
                            id="scan-progress",
                        )
                        yield Label("Progress: 0%  (0 / ?)", id="progress-label")
                        yield Label("Testing: ...", id="testing-label")
                        yield Label(
                            "Sent: 0   Rate: 0 req/s   ETA: --   Depth: --   Errors: 0",
                            id="stats-label",
                        )

                    # Findings table
                    with Vertical(id="findings-panel"):
                        yield Label("0 findings so far", id="findings-count")
                        yield DataTable(id="findings-table")

                    # Vhost progress and findings (combined mode)
                    if scan_type == "combined":
                        with Vertical(id="vhost-progress-panel"):
                            yield ProgressBar(
                                total=100,
                                show_eta=False,
                                id="vhost-scan-progress",
                            )
                            yield Label("Vhost progress: 0%", id="vhost-progress-label")
                            yield Label("0 vhost findings", id="vhost-findings-count")
                            yield DataTable(id="vhost-findings-table")

                # Right column: raw output
                with Vertical(id="scanning-right"):
                    yield RichLog(
                        highlight=True,
                        markup=True,
                        id="raw-output",
                    )
                    if scan_type == "combined":
                        yield RichLog(
                            highlight=True,
                            markup=True,
                            id="vhost-raw-output",
                        )

    def on_mount(self) -> None:
        """Initialise state and start the scan."""
        self._start_time = time.time()
        self._lines_received = 0
        self._errors = 0
        self._findings = []
        self._raw_lines = []
        self._stderr_lines = []
        self._rate_samples = deque(maxlen=50)
        self._scan_tasks = []
        self._completed_scanners = 0
        self._vhost_findings = []
        self._vhost_lines_received = 0
        self._vhost_raw_lines = []
        self._vhost_stderr_lines = []

        # Set up findings table
        table = self.query_one("#findings-table", DataTable)
        table.add_columns("Status", "Size", "Words", "Lines", "URL")
        table.fixed_columns = 5

        scan_type = getattr(self.app, "scan_type", "directory")
        if scan_type == "combined":
            self._total_scanners = 2
            try:
                vhost_table = self.query_one("#vhost-findings-table", DataTable)
                vhost_table.add_columns("Status", "Size", "Words", "Lines", "Vhost")
                vhost_table.fixed_columns = 5
            except Exception:
                pass

        # Start the periodic stats refresh
        self.set_interval(1.0, self._refresh_stats)

        # Start the scan
        self.run_worker(self._start_scan())

    async def _start_scan(self) -> None:
        """Start the scanning process."""
        app = self.app
        tool = getattr(app, "selected_tool", "")
        scan_type = getattr(app, "scan_type", "directory")
        target = getattr(app, "target", "")
        wordlist = getattr(app, "wordlist_path", "")
        options = getattr(app, "scan_options", {})

        effective_mode = scan_type if scan_type != "combined" else "directory"

        # Count total words
        wl_path = Path(wordlist)
        if wl_path.exists():
            self._total_words = await count_lines(wl_path)
            try:
                progress = self.query_one("#scan-progress", ProgressBar)
                progress.update(total=max(self._total_words, 1))
            except Exception:
                pass

        # Generate output paths
        from krakenbuster.config import load_config
        config = load_config()
        output_dir = config.get("general", "output_directory", fallback="./output")
        self._raw_path, self._json_path = generate_output_paths(
            target, tool, effective_mode, output_dir
        )

        # Create and run primary scanner
        self._scanner = create_scanner(tool, effective_mode, target, wordlist, options)
        primary_task = asyncio.create_task(
            self._run_scanner(self._scanner, "primary")
        )
        self._scan_tasks.append(primary_task)

        # Combined mode: also run vhost scanner
        if scan_type == "combined":
            vhost_tool = getattr(app, "selected_vhost_tool", "ffuf")
            vhost_options = getattr(app, "vhost_options", {})
            self._vhost_raw_path, self._vhost_json_path = generate_output_paths(
                target, vhost_tool, "vhost", output_dir
            )
            self._vhost_scanner = create_scanner(
                vhost_tool, "vhost", target, wordlist, vhost_options
            )
            vhost_task = asyncio.create_task(
                self._run_scanner(self._vhost_scanner, "vhost")
            )
            self._scan_tasks.append(vhost_task)

        # Wait for all scanners to complete
        await asyncio.gather(*self._scan_tasks, return_exceptions=True)

    async def _run_scanner(self, scanner, scanner_id: str) -> None:
        """Run a single scanner and post messages for each line."""
        try:
            async for scan_line in scanner.run_scan():
                self.post_message(ScanOutputLine(scan_line, scanner_id))
        except Exception as exc:
            self.post_message(
                ScanOutputLine(
                    ScanLine(raw=f"Scanner error: {exc}", is_stderr=True),
                    scanner_id,
                )
            )
        finally:
            self.post_message(ScanComplete(scanner_id))

    def on_scan_output_line(self, message: ScanOutputLine) -> None:
        """Handle a line of scanner output."""
        line = message.line
        scanner_id = message.scanner_id

        if line.is_stderr:
            if scanner_id == "vhost":
                self._vhost_stderr_lines.append(line.raw)
            else:
                self._stderr_lines.append(line.raw)
            return

        # Track raw lines
        if scanner_id == "vhost":
            self._vhost_lines_received += 1
            self._vhost_raw_lines.append(line.raw)
        else:
            self._lines_received += 1
            self._raw_lines.append(line.raw)
            self._rate_samples.append(time.time())

        # Write to raw output file
        raw_path = self._vhost_raw_path if scanner_id == "vhost" else self._raw_path
        if raw_path:
            self.run_worker(append_raw_line(raw_path, line.raw))

        # Parse and display
        status = self._detect_status(line.raw)
        colour = self._status_colour(status)

        # Update raw output log
        try:
            log_id = "vhost-raw-output" if scanner_id == "vhost" else "raw-output"
            raw_log = self.query_one(f"#{log_id}", RichLog)
            if status:
                raw_log.write(f"[{colour}][{status}][/{colour}] {line.raw}")
            else:
                raw_log.write(line.raw)
        except Exception:
            pass

        # Parse finding
        finding = parse_finding(line.raw)
        if finding:
            if scanner_id == "vhost":
                self._vhost_findings.append(finding)
                self._update_vhost_findings_table(finding)
            else:
                self._findings.append(finding)
                self._update_findings_table(finding)

        # Update testing label with current word
        if scanner_id != "vhost":
            try:
                testing = self.query_one("#testing-label", Label)
                # Truncate long lines
                display = line.raw[:80] + "..." if len(line.raw) > 80 else line.raw
                testing.update(f"Testing: {display}")
            except Exception:
                pass

    def on_scan_complete(self, message: ScanComplete) -> None:
        """Handle scan completion."""
        self._completed_scanners += 1

        if self._completed_scanners >= self._total_scanners:
            # All scanners done, write JSON and show summary
            self.run_worker(self._finalise())

    async def _finalise(self) -> None:
        """Write final output files and navigate to summary."""
        if self._json_path:
            await write_json_results(self._json_path, self._findings)
        if self._vhost_json_path:
            await write_json_results(self._vhost_json_path, self._vhost_findings)

        duration = time.time() - self._start_time

        result = ScanResult(
            tool=getattr(self.app, "selected_tool", ""),
            mode=getattr(self.app, "scan_type", "directory"),
            target=getattr(self.app, "target", ""),
            wordlist=getattr(self.app, "wordlist_path", ""),
            total_words=self._total_words,
            duration_seconds=duration,
            findings=self._findings + self._vhost_findings,
            raw_lines=self._raw_lines,
            stderr_lines=self._stderr_lines + self._vhost_stderr_lines,
            errors=self._errors,
        )

        # Store output paths for summary
        result._raw_path = self._raw_path
        result._json_path = self._json_path
        result._vhost_raw_path = self._vhost_raw_path
        result._vhost_json_path = self._vhost_json_path

        self.app.call_from_thread(self.app.go_to_summary, result)

    def _update_findings_table(self, finding: Finding) -> None:
        """Add a finding to the primary findings table."""
        try:
            table = self.query_one("#findings-table", DataTable)
            table.add_row(
                str(finding.status_code),
                str(finding.size),
                str(finding.words),
                str(finding.lines),
                finding.url or "N/A",
            )
            count_label = self.query_one("#findings-count", Label)
            count_label.update(f"{len(self._findings)} findings so far")
        except Exception:
            pass

    def _update_vhost_findings_table(self, finding: Finding) -> None:
        """Add a finding to the vhost findings table."""
        try:
            table = self.query_one("#vhost-findings-table", DataTable)
            table.add_row(
                str(finding.status_code),
                str(finding.size),
                str(finding.words),
                str(finding.lines),
                finding.url or "N/A",
            )
            count_label = self.query_one("#vhost-findings-count", Label)
            count_label.update(f"{len(self._vhost_findings)} vhost findings")
        except Exception:
            pass

    def _refresh_stats(self) -> None:
        """Update the top bar and progress stats every second."""
        elapsed = time.time() - self._start_time
        elapsed_str = self._format_elapsed(elapsed)

        # Calculate rate
        now = time.time()
        recent = [t for t in self._rate_samples if now - t <= 5.0]
        rate = len(recent) / 5.0 if recent else 0.0

        # Update top bar
        tool = getattr(self.app, "selected_tool", "")
        target = getattr(self.app, "target", "")
        wordlist = Path(getattr(self.app, "wordlist_path", "")).name

        try:
            top_bar = self.query_one("#scan-top-bar", Static)
            top_bar.update(
                f"[bold]{tool}[/bold] | {target} | {wordlist} | "
                f"Elapsed: {elapsed_str} | {rate:.0f} req/s"
            )
        except Exception:
            pass

        # Update progress
        if self._total_words > 0:
            pct = min(100, (self._lines_received / self._total_words) * 100)
            eta = self._estimate_eta(elapsed, self._lines_received, self._total_words)
        else:
            pct = 0
            eta = "--"

        try:
            progress = self.query_one("#scan-progress", ProgressBar)
            progress.update(progress=self._lines_received)
        except Exception:
            pass

        try:
            progress_label = self.query_one("#progress-label", Label)
            progress_label.update(
                f"Progress: {pct:.0f}%  ({self._lines_received:,} / {self._total_words:,})"
            )
        except Exception:
            pass

        try:
            stats_label = self.query_one("#stats-label", Label)
            stats_label.update(
                f"Sent: {self._lines_received:,}   Rate: {rate:.0f} req/s   "
                f"ETA: {eta}   Errors: {self._errors}"
            )
        except Exception:
            pass

    def _format_elapsed(self, seconds: float) -> str:
        """Format elapsed time."""
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        if mins > 0:
            return f"{mins}m {secs:02d}s"
        return f"{secs}s"

    def _estimate_eta(self, elapsed: float, done: int, total: int) -> str:
        """Estimate remaining time."""
        if done <= 0 or elapsed <= 0:
            return "--"
        rate = done / elapsed
        remaining = total - done
        eta_seconds = remaining / rate
        return self._format_elapsed(eta_seconds)

    def _detect_status(self, line: str) -> int | None:
        """Detect HTTP status code from line."""
        from krakenbuster.output import parse_status_code
        return parse_status_code(line)

    def _status_colour(self, code: int | None) -> str:
        """Return colour for a status code."""
        if code is None:
            return "white"
        if code == 200:
            return "green"
        elif code in (301, 302, 307):
            return "yellow"
        elif code in (401, 403):
            return "cyan"
        elif code >= 500:
            return "red"
        return "white"

    def action_cancel_scan(self) -> None:
        """Cancel the running scan."""
        if self._scanner:
            self.run_worker(self._scanner.cancel())
        if self._vhost_scanner:
            self.run_worker(self._vhost_scanner.cancel())

        for task in self._scan_tasks:
            if not task.done():
                task.cancel()

        self.notify("Scan cancelled", severity="warning")
