"""DIRB scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class DirbScanner(BaseScanner):
    """Scanner wrapper for dirb."""

    @property
    def tool_name(self) -> str:
        return "dirb"

    def build_command(self) -> list[str]:
        cmd = [
            "dirb",
            self.target,
            self.wordlist,
        ]

        extensions = self._get_opt("extensions")
        if extensions:
            cmd.extend(["-X", ",".join(
                f".{e.strip('.')}" for e in extensions.split(",") if e.strip()
            )])

        case_insensitive = self._get_opt_bool("case_insensitive", False)
        if case_insensitive:
            cmd.append("-i")

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["-p", proxy])

        auth = self._get_opt("auth")
        if auth:
            cmd.extend(["-u", auth])

        non_recursive = self._get_opt_bool("non_recursive", False)
        if non_recursive:
            cmd.append("-r")

        # Silent banner for cleaner output
        cmd.append("-S")

        return cmd
