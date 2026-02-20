"""wfuzz scanner implementation."""

from __future__ import annotations

from krakenbuster.scanners.base import BaseScanner


class WfuzzScanner(BaseScanner):
    """Scanner wrapper for wfuzz."""

    @property
    def tool_name(self) -> str:
        return "wfuzz"

    def build_command(self) -> list[str]:
        if self.mode == "vhost":
            return self._build_vhost_command()
        return self._build_dir_command()

    def _build_dir_command(self) -> list[str]:
        # Ensure target URL has FUZZ placeholder
        target = self.target.rstrip("/")
        if "FUZZ" not in target:
            target = f"{target}/FUZZ"

        cmd = [
            "wfuzz",
            "-w", self.wordlist,
            "--url", target,
        ]

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        hide_codes = self._get_opt("hide_codes", "404")
        if hide_codes:
            cmd.extend(["--hc", hide_codes])

        filter_lines = self._get_opt("filter_lines")
        if filter_lines:
            cmd.extend(["--hl", filter_lines])

        filter_words = self._get_opt("filter_words")
        if filter_words:
            cmd.extend(["--hw", filter_words])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["-p", proxy])

        extensions = self._get_opt("extensions")
        if extensions:
            ext_list = ",".join(
                f".{e.strip('.')}" for e in extensions.split(",") if e.strip()
            )
            # wfuzz uses -z for payloads; for extensions we modify the URL
            target_with_ext = target.replace("FUZZ", "FUZZ{ext}")
            cmd = [
                "wfuzz",
                "-w", self.wordlist,
                "-z", f"list,{ext_list}",
                "--url", target_with_ext,
                "-t", threads,
            ]
            if hide_codes:
                cmd.extend(["--hc", hide_codes])
            if proxy:
                cmd.extend(["-p", proxy])

        # Colourised output
        cmd.extend(["-c"])

        return cmd

    def _build_vhost_command(self) -> list[str]:
        domain = self._get_opt("domain", "")

        cmd = [
            "wfuzz",
            "-w", self.wordlist,
            "--url", self.target,
            "-H", f"Host: FUZZ.{domain}",
        ]

        threads = self._get_opt("threads", "50")
        cmd.extend(["-t", threads])

        hide_codes = self._get_opt("hide_codes", "404")
        if hide_codes:
            cmd.extend(["--hc", hide_codes])

        filter_lines = self._get_opt("filter_lines")
        if filter_lines:
            cmd.extend(["--hl", filter_lines])

        filter_words = self._get_opt("filter_words")
        if filter_words:
            cmd.extend(["--hw", filter_words])

        proxy = self._get_opt("proxy")
        if proxy:
            cmd.extend(["-p", proxy])

        cmd.extend(["-c"])

        return cmd
