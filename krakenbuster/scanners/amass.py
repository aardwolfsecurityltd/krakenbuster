"""Amass scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class AmassScanner(BaseScanner):
    """Scanner wrapper for amass (DNS subdomain enumeration)."""

    @property
    def tool_name(self) -> str:
        return "amass"

    def build_command(self) -> list[str]:
        cmd = ["amass", "enum", "-d", self.target]

        passive = self._get_opt_bool("passive", True)
        if passive:
            cmd.append("-passive")

        if self.wordlist:
            cmd.extend(["-w", self.wordlist])

        brute_force = self._get_opt_bool("brute_force", False)
        if brute_force:
            cmd.append("-brute")

        timeout = self._get_opt("timeout")
        if timeout:
            cmd.extend(["-timeout", timeout])

        resolver = self._get_opt("resolver")
        if resolver:
            cmd.extend(["-rf", resolver])

        max_dns = self._get_opt("max_dns_queries")
        if max_dns:
            cmd.extend(["-max-dns-queries", max_dns])

        return cmd
