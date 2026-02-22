"""Base scanner class with asyncio subprocess logic."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ScanLine:
    """A single line of output from a scanner."""

    raw: str
    is_stderr: bool = False


class BaseScanner(ABC):
    """Abstract base class for all scanner implementations."""

    def __init__(
        self,
        mode: str,
        target: str,
        wordlist: str,
        options: dict[str, str] | None = None,
    ) -> None:
        self.mode = mode
        self.target = target
        self.wordlist = wordlist
        self.options = options or {}
        self._process: asyncio.subprocess.Process | None = None

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool's executable name."""
        ...

    @abstractmethod
    def build_command(self) -> list[str]:
        """Build the command-line arguments list."""
        ...

    async def run_scan(self) -> AsyncIterator[ScanLine]:
        """Run the scan and yield output lines as they arrive.

        Uses asyncio.create_subprocess_exec with piped stdout/stderr.
        Reads stdout line by line without blocking the event loop.
        """
        command = self.build_command()

        # Use a large line buffer limit (4MB) to handle tools like dirsearch
        # that output ANSI progress bars using carriage returns without newlines,
        # creating extremely long "lines" that exceed asyncio's default 64KB limit.
        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=4 * 1024 * 1024,
        )

        assert self._process.stdout is not None
        assert self._process.stderr is not None

        # Read stdout line by line
        async for raw_line in self._process.stdout:
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            if line:
                yield ScanLine(raw=line, is_stderr=False)

        # After stdout is done, read any remaining stderr
        stderr_data = await self._process.stderr.read()
        if stderr_data:
            for line in stderr_data.decode("utf-8", errors="replace").splitlines():
                if line.strip():
                    yield ScanLine(raw=line.strip(), is_stderr=True)

        await self._process.wait()

    async def cancel(self) -> None:
        """Cancel the running scan."""
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.sleep(0.5)
                if self._process.returncode is None:
                    self._process.kill()
            except ProcessLookupError:
                pass

    @property
    def return_code(self) -> int | None:
        """Return the process exit code, or None if still running."""
        if self._process:
            return self._process.returncode
        return None

    def _get_opt(self, key: str, default: str = "") -> str:
        """Get an option value with a default."""
        return self.options.get(key, default)

    def _get_opt_int(self, key: str, default: int = 0) -> int:
        """Get an option value as an integer."""
        val = self.options.get(key, str(default))
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def _get_opt_bool(self, key: str, default: bool = False) -> bool:
        """Get an option value as a boolean."""
        val = self.options.get(key, str(default)).lower()
        return val in ("true", "1", "yes", "on")


def create_scanner(
    tool: str,
    mode: str,
    target: str,
    wordlist: str,
    options: dict[str, str] | None = None,
) -> BaseScanner:
    """Factory function to create the appropriate scanner instance."""
    from krakenbuster.scanners.feroxbuster import FeroxbusterScanner
    from krakenbuster.scanners.ffuf import FfufScanner
    from krakenbuster.scanners.gobuster import GobusterScanner
    from krakenbuster.scanners.dirb import DirbScanner
    from krakenbuster.scanners.wfuzz import WfuzzScanner
    from krakenbuster.scanners.dirsearch import DirsearchScanner
    from krakenbuster.scanners.amass import AmassScanner
    from krakenbuster.scanners.subfinder import SubfinderScanner

    scanners: dict[str, type[BaseScanner]] = {
        "feroxbuster": FeroxbusterScanner,
        "ffuf": FfufScanner,
        "gobuster": GobusterScanner,
        "dirb": DirbScanner,
        "wfuzz": WfuzzScanner,
        "dirsearch": DirsearchScanner,
        "amass": AmassScanner,
        "subfinder": SubfinderScanner,
    }

    scanner_class = scanners.get(tool)
    if scanner_class is None:
        raise ValueError(f"Unknown tool: {tool}")

    return scanner_class(mode=mode, target=target, wordlist=wordlist, options=options)
