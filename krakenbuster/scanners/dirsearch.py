"""dirsearch scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class DirsearchScanner(BaseScanner):
    """Scanner wrapper for dirsearch."""

    @property
    def tool_name(self) -> str:
        return "dirsearch"

    def build_command(self) -> list[str]:
        cmd = [
            "dirsearch",
            "-u", self.target,
            "-w", self.wordlist,
        ]

        extensions = self._get_opt("extensions", "php,html,txt,js")
        if extensions:
            cmd.extend(["-e", extensions])

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["--proxy", proxy])

        recursive = self._get_opt_bool("recursive", True)
        if recursive:
            cmd.append("-r")
            depth = self._get_opt("depth", "3")
            cmd.extend(["--max-recursion-depth", depth])

        filter_codes = self._get_opt("filter_codes", "400,404")
        if filter_codes:
            cmd.extend(["--exclude-status", filter_codes])

        random_agents = self._get_opt_bool("random_agents", True)
        if random_agents:
            cmd.append("--random-agent")

        return cmd
