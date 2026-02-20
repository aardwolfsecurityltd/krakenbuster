"""Gobuster scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class GobusterScanner(BaseScanner):
    """Scanner wrapper for gobuster."""

    @property
    def tool_name(self) -> str:
        return "gobuster"

    def build_command(self) -> list[str]:
        if self.mode == "vhost":
            return self._build_vhost_command()
        elif self.mode == "dns":
            return self._build_dns_command()
        return self._build_dir_command()

    def _build_dir_command(self) -> list[str]:
        cmd = [
            "gobuster", "dir",
            "-u", self.target,
            "-w", self.wordlist,
        ]

        extensions = self._get_opt("extensions", "php,html,txt,js")
        if extensions:
            cmd.extend(["-x", extensions])

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        status_codes = self._get_opt("status_codes", "200,204,301,302,307,401,403")
        if status_codes:
            cmd.extend(["-s", status_codes])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["--proxy", proxy])

        follow_redirects = self._get_opt_bool("follow_redirects", True)
        if follow_redirects:
            cmd.append("-r")

        expanded = self._get_opt_bool("expanded", False)
        if expanded:
            cmd.append("-e")

        # No colour codes for cleaner parsing
        cmd.append("--no-color")

        return cmd

    def _build_vhost_command(self) -> list[str]:
        cmd = [
            "gobuster", "vhost",
            "-u", self.target,
            "-w", self.wordlist,
        ]

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["--proxy", proxy])

        append_domain = self._get_opt_bool("append_domain", True)
        if append_domain:
            cmd.append("--append-domain")

        domain = self._get_opt("domain")
        if domain:
            cmd.extend(["--domain", domain])

        cmd.append("--no-color")

        return cmd

    def _build_dns_command(self) -> list[str]:
        cmd = [
            "gobuster", "dns",
            "-d", self.target,
            "-w", self.wordlist,
        ]

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        resolver = self._get_opt("resolver")
        if resolver:
            cmd.extend(["-r", resolver])

        show_ips = self._get_opt_bool("show_ips", True)
        if show_ips:
            cmd.append("-i")

        cmd.append("--no-color")

        return cmd
