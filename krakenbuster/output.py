"""Result parsing and file writing for KrakenBuster."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import aiofiles


@dataclass
class Finding:
    """A single finding from a scan."""

    status_code: int = 0
    url: str = ""
    size: int = 0
    words: int = 0
    lines: int = 0
    redirect: str = ""


@dataclass
class ScanResult:
    """Aggregated results from a scan."""

    tool: str = ""
    mode: str = ""
    target: str = ""
    wordlist: str = ""
    total_words: int = 0
    duration_seconds: float = 0.0
    findings: list[Finding] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)
    errors: int = 0

    @property
    def duration_formatted(self) -> str:
        minutes = int(self.duration_seconds) // 60
        seconds = int(self.duration_seconds) % 60
        return f"{minutes}m {seconds}s"

    @property
    def findings_by_status(self) -> dict[int, list[Finding]]:
        grouped: dict[int, list[Finding]] = {}
        for f in self.findings:
            grouped.setdefault(f.status_code, []).append(f)
        return grouped


def sanitise_hostname(target: str) -> str:
    """Sanitise a hostname for use in filenames."""
    cleaned = re.sub(r"https?://", "", target)
    cleaned = re.sub(r"[^a-zA-Z0-9]", "_", cleaned)
    cleaned = cleaned.strip("_")
    return cleaned


def generate_output_paths(
    target: str, tool: str, mode: str, output_dir: str = "./output"
) -> tuple[Path, Path]:
    """Generate output file paths for raw and JSON output."""
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    hostname = sanitise_hostname(target)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{hostname}_{tool}_{mode}_{timestamp}"

    raw_path = base / f"{prefix}.txt"
    json_path = base / f"{prefix}.json"
    return raw_path, json_path


async def append_raw_line(path: Path, line: str) -> None:
    """Append a single line to the raw output file."""
    async with aiofiles.open(path, "a") as fh:
        await fh.write(line + "\n")


async def write_json_results(path: Path, findings: list[Finding]) -> None:
    """Write findings as a JSON array."""
    data = [asdict(f) for f in findings]
    async with aiofiles.open(path, "w") as fh:
        await fh.write(json.dumps(data, indent=2))


def parse_status_code(line: str) -> int | None:
    """Extract HTTP status code from a tool output line."""
    # Common patterns across tools
    patterns = [
        r"\b(\d{3})\b.*\bhttps?://",       # status code before URL
        r"Status:\s*(\d{3})",               # feroxbuster style
        r"\[Status:\s*(\d{3})\]",           # bracketed status
        r"^\s*(\d{3})\s",                   # line starts with status
        r"\(Status:\s*(\d{3})\)",           # parenthesised status
        r"\b(\d{3})\s+\d+[A-Za-z]",        # status followed by size
        r"C=(\d{3})",                       # wfuzz/dirsearch style
        r"\|\s*(\d{3})\s*\|",              # pipe-delimited
    ]

    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            code = int(match.group(1))
            if 100 <= code <= 599:
                return code
    return None


def parse_url(line: str) -> str:
    """Extract URL from a tool output line."""
    match = re.search(r"(https?://\S+)", line)
    if match:
        return match.group(1).rstrip(",;])")
    return ""


def parse_size(line: str) -> int:
    """Extract response size from a tool output line."""
    patterns = [
        r"Size:\s*(\d+)",
        r"\b(\d+)[Bb]\b",
        r"\|\s*(\d+)\s*\|",
    ]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return int(match.group(1))
    return 0


def parse_finding(line: str) -> Finding | None:
    """Parse a single output line into a Finding, if it contains one."""
    status = parse_status_code(line)
    if status is None:
        return None

    url = parse_url(line)
    size = parse_size(line)

    return Finding(
        status_code=status,
        url=url,
        size=size,
    )
