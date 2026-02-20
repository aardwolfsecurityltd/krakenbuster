"""ffuf scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class FfufScanner(BaseScanner):
    """Scanner wrapper for ffuf."""

    @property
    def tool_name(self) -> str:
        return "ffuf"

    def build_command(self) -> list[str]:
        if self.mode == "vhost":
            return self._build_vhost_command()
        return self._build_dir_command()

    def _build_dir_command(self) -> list[str]:
        # Ensure target URL ends with /FUZZ
        target = self.target.rstrip("/")
        if "FUZZ" not in target:
            target = f"{target}/FUZZ"

        cmd = [
            "ffuf",
            "-u", target,
            "-w", self.wordlist,
        ]

        extensions = self._get_opt("extensions", "php,html,txt,js")
        if extensions:
            cmd.extend(["-e", ",".join(
                f".{e.strip('.')}" for e in extensions.split(",") if e.strip()
            )])

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        rate_limit = self._get_opt("rate_limit", "200")
        cmd.extend(["-rate", rate_limit])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["-x", proxy])

        filter_codes = self._get_opt("filter_codes", "400,404")
        if filter_codes:
            cmd.extend(["-fc", filter_codes])

        filter_size = self._get_opt("filter_size")
        if filter_size:
            cmd.extend(["-fs", filter_size])

        # Colourised output
        cmd.extend(["-c"])

        return cmd

    def _build_vhost_command(self) -> list[str]:
        domain = self._get_opt("domain", "")
        target = self.target

        cmd = [
            "ffuf",
            "-u", target,
            "-w", self.wordlist,
            "-H", f"Host: FUZZ.{domain}",
        ]

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        rate_limit = self._get_opt("rate_limit", "200")
        cmd.extend(["-rate", rate_limit])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["-x", proxy])

        filter_codes = self._get_opt("filter_codes", "400,404")
        if filter_codes:
            cmd.extend(["-fc", filter_codes])

        filter_size = self._get_opt("filter_size")
        if filter_size:
            cmd.extend(["-fs", filter_size])

        cmd.extend(["-c"])

        return cmd
