"""Subfinder scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class SubfinderScanner(BaseScanner):
    """Scanner wrapper for subfinder (passive subdomain discovery)."""

    @property
    def tool_name(self) -> str:
        return "subfinder"

    def build_command(self) -> list[str]:
        cmd = ["subfinder", "-d", self.target]

        if self.wordlist:
            cmd.extend(["-w", self.wordlist])

        threads = self._get_opt("threads", "30")
        cmd.extend(["-t", threads])

        timeout = self._get_opt("timeout", "30")
        cmd.extend(["-timeout", timeout])

        max_time = self._get_opt("max_time")
        if max_time:
            cmd.extend(["-max-time", max_time])

        resolver = self._get_opt("resolver")
        if resolver:
            cmd.extend(["-rL", resolver])

        all_sources = self._get_opt_bool("all_sources", True)
        if all_sources:
            cmd.append("-all")

        recursive = self._get_opt_bool("recursive", False)
        if recursive:
            cmd.append("-recursive")

        return cmd
