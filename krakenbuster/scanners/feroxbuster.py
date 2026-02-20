"""Feroxbuster scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class FeroxbusterScanner(BaseScanner):
    """Scanner wrapper for feroxbuster."""

    @property
    def tool_name(self) -> str:
        return "feroxbuster"

    def build_command(self) -> list[str]:
        cmd = [
            "feroxbuster",
            "-u", self.target,
            "-w", self.wordlist,
        ]

        depth = self._get_opt("depth", "3")
        cmd.extend(["-d", depth])

        extensions = self._get_opt("extensions", "php,html,txt,js")
        if extensions:
            cmd.extend(["-x", extensions])

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        rate_limit = self._get_opt("rate_limit", "200")
        cmd.extend(["--rate-limit", rate_limit])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["-p", proxy])

        status_codes = self._get_opt("status_codes", "200,204,301,302,307,401,403")
        if status_codes:
            cmd.extend(["-s", status_codes])

        # Disable interactive mode for piped output
        cmd.append("--no-state")

        return cmd
