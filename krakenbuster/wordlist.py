"""Wordlist discovery, tree building, and utility functions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

WORDLIST_DIRS = [
    Path("/usr/share/wordlists"),
    Path("/usr/share/seclists"),
    Path("/usr/share/dirb/wordlists"),
    Path("/usr/share/dirbuster/wordlists"),
]

RECOMMENDED = {
    "directory": [
        "raft-medium-words.txt",
        "common.txt",
    ],
    "vhost": [
        "subdomains-top1million-5000.txt",
    ],
    "dns": [
        "subdomains-top1million-5000.txt",
    ],
}


def human_readable_size(size_bytes: int) -> str:
    """Convert byte count to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


@dataclass
class WordlistFile:
    """A single wordlist file."""

    path: Path
    size: int = 0
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.path.name
        if self.size == 0 and self.path.exists():
            try:
                self.size = self.path.stat().st_size
            except OSError:
                pass

    @property
    def size_human(self) -> str:
        return human_readable_size(self.size)

    def is_recommended(self, scan_type: str) -> bool:
        """Check if this wordlist is recommended for the given scan type."""
        recommended_names = RECOMMENDED.get(scan_type, [])
        return self.name in recommended_names


@dataclass
class WordlistDir:
    """A directory containing wordlists, possibly with subdirectories."""

    path: Path
    name: str = ""
    files: list[WordlistFile] = field(default_factory=list)
    subdirs: list[WordlistDir] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.path.name

    @property
    def total_count(self) -> int:
        """Total number of wordlist files in this directory and all subdirectories."""
        count = len(self.files)
        for subdir in self.subdirs:
            count += subdir.total_count
        return count


def _scan_directory(base_path: Path) -> WordlistDir | None:
    """Scan a directory for wordlist files, building a tree structure."""
    if not base_path.exists() or not base_path.is_dir():
        return None

    root = WordlistDir(path=base_path, name=base_path.name)

    try:
        entries = sorted(base_path.iterdir())
    except PermissionError:
        return root

    for entry in entries:
        if entry.is_file() and entry.suffix == ".txt":
            try:
                wf = WordlistFile(path=entry, size=entry.stat().st_size)
                root.files.append(wf)
            except (OSError, PermissionError):
                pass
        elif entry.is_dir():
            subdir = _scan_directory(entry)
            if subdir and subdir.total_count > 0:
                root.subdirs.append(subdir)

    return root


async def discover_wordlists() -> list[WordlistDir]:
    """Discover all wordlist directories in background thread."""
    results: list[WordlistDir] = []

    def _scan_all() -> list[WordlistDir]:
        dirs = []
        for base in WORDLIST_DIRS:
            result = _scan_directory(base)
            if result and result.total_count > 0:
                dirs.append(result)
        return dirs

    results = await asyncio.to_thread(_scan_all)
    return results


async def count_lines(wordlist_path: Path) -> int:
    """Count lines in a wordlist file without blocking."""

    def _count() -> int:
        count = 0
        try:
            with open(wordlist_path, "r", errors="ignore") as fh:
                for _ in fh:
                    count += 1
        except (OSError, PermissionError):
            pass
        return count

    return await asyncio.to_thread(_count)


def get_all_files(dirs: list[WordlistDir]) -> list[WordlistFile]:
    """Flatten all wordlist directories into a single list of files."""
    files: list[WordlistFile] = []

    def _collect(d: WordlistDir) -> None:
        files.extend(d.files)
        for sub in d.subdirs:
            _collect(sub)

    for d in dirs:
        _collect(d)
    return files
