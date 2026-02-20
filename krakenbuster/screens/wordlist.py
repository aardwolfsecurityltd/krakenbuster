"""Step 4: Hierarchical wordlist browser screen."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Header,
    Input,
    Label,
    Static,
    Tree,
)
from textual.widgets.tree import TreeNode

from krakenbuster.wordlist import (
    WordlistDir,
    WordlistFile,
    discover_wordlists,
    get_all_files,
    human_readable_size,
    RECOMMENDED,
    count_lines,
)


class WordlistScreen(Screen):
    """Screen for selecting a wordlist file via a hierarchical browser."""

    BINDINGS = [
        Binding("enter", "confirm", "Confirm", show=False),
        Binding("m", "manual_input", "Manual path"),
        Binding("escape", "go_back", "Back"),
    ]

    _wordlist_dirs: list[WordlistDir] = []
    _all_files: list[WordlistFile] = []
    _selected_path: str = ""
    _manual_mode: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wordlist-container"):
            yield Static(
                "[bold cyan]Step 4:[/bold cyan] Select Wordlist",
                id="wordlist-title",
            )
            yield Input(
                placeholder="Type to filter wordlists...",
                id="wordlist-search",
            )
            with Horizontal(id="wordlist-browser"):
                yield Tree("Wordlists", id="wordlist-tree")
                with Vertical(id="wordlist-preview"):
                    yield Static("", id="wordlist-preview-content")
            yield Input(
                placeholder="Or type a custom wordlist path here...",
                id="wordlist-manual-input",
            )
            yield Label("", id="wordlist-error")
            yield Button("Continue", id="wordlist-continue-btn", variant="primary")
            yield Static(
                "[dim]Select a file from the tree, or press M for manual path entry. Escape to go back.[/dim]",
                id="wordlist-hint",
            )

    def on_mount(self) -> None:
        """Start async wordlist discovery."""
        manual_input = self.query_one("#wordlist-manual-input", Input)
        manual_input.display = False
        self.query_one("#wordlist-search", Input).focus()
        self._load_wordlists()

    def _load_wordlists(self) -> None:
        """Kick off background wordlist discovery."""
        self.run_worker(self._discover(), exclusive=True)

    async def _discover(self) -> None:
        """Discover wordlists in background."""
        self._wordlist_dirs = await discover_wordlists()
        self._all_files = get_all_files(self._wordlist_dirs)
        self._build_tree()

    def _build_tree(self, filter_text: str = "") -> None:
        """Build or rebuild the tree widget from discovered wordlists."""
        tree = self.query_one("#wordlist-tree", Tree)
        tree.clear()
        tree.root.expand()

        scan_type = getattr(self.app, "scan_type", "directory")
        recommended = RECOMMENDED.get(scan_type, [])

        for wdir in self._wordlist_dirs:
            self._add_dir_node(tree.root, wdir, filter_text, recommended)

    def _add_dir_node(
        self,
        parent: TreeNode,
        wdir: WordlistDir,
        filter_text: str,
        recommended: list[str],
    ) -> bool:
        """Add a directory node to the tree. Returns True if any children matched."""
        has_match = False

        # Check if any files in this dir match
        matching_files = []
        for wf in wdir.files:
            if not filter_text or filter_text.lower() in wf.name.lower():
                matching_files.append(wf)
                has_match = True

        # Check subdirectories recursively
        matching_subdirs = []
        for sub in wdir.subdirs:
            if self._dir_has_match(sub, filter_text):
                matching_subdirs.append(sub)
                has_match = True

        if not has_match and filter_text:
            return False

        dir_label = f"{wdir.name} [{wdir.total_count} wordlists]"
        dir_node = parent.add(dir_label, expand=bool(filter_text))

        for wf in matching_files:
            star = " \u2605" if wf.name in recommended else ""
            label = f"{wf.name} ({wf.size_human}){star}"
            dir_node.add_leaf(label, data=str(wf.path))

        for sub in matching_subdirs:
            self._add_dir_node(dir_node, sub, filter_text, recommended)

        return True

    def _dir_has_match(self, wdir: WordlistDir, filter_text: str) -> bool:
        """Check if any file in the directory tree matches the filter."""
        if not filter_text:
            return True
        for wf in wdir.files:
            if filter_text.lower() in wf.name.lower():
                return True
        for sub in wdir.subdirs:
            if self._dir_has_match(sub, filter_text):
                return True
        return False

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter tree as user types in the search box."""
        if event.input.id == "wordlist-search":
            self._build_tree(filter_text=event.value)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle selection of a tree node."""
        node = event.node
        if node.data:
            self._selected_path = str(node.data)
            self._update_preview(self._selected_path)

    def _update_preview(self, path_str: str) -> None:
        """Update the preview panel with file information."""
        preview = self.query_one("#wordlist-preview-content", Static)
        path = Path(path_str)

        scan_type = getattr(self.app, "scan_type", "directory")
        recommended = RECOMMENDED.get(scan_type, [])
        is_rec = path.name in recommended

        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        lines = [
            f"[bold]Path:[/bold] {path}",
            f"[bold]Size:[/bold] {human_readable_size(size)}",
        ]

        if is_rec:
            lines.append("[bold green]Recommended for this scan type[/bold green]")
        else:
            lines.append("[dim]Not a recommended wordlist for this scan type[/dim]")

        preview.update("\n".join(lines))

        # Count lines in background
        self.run_worker(self._count_and_update(path_str))

    async def _count_and_update(self, path_str: str) -> None:
        """Count lines and update the preview."""
        path = Path(path_str)
        line_count = await count_lines(path)
        if self._selected_path == path_str:
            preview = self.query_one("#wordlist-preview-content", Static)
            current = preview.renderable
            if isinstance(current, str):
                preview.update(
                    current + f"\n[bold]Lines:[/bold] {line_count:,}"
                )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle manual path submission."""
        if event.input.id == "wordlist-manual-input":
            self._validate_manual_path(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wordlist-continue-btn":
            self._try_continue()

    def _try_continue(self) -> None:
        """Validate selection and navigate forward."""
        if self._manual_mode:
            manual_input = self.query_one("#wordlist-manual-input", Input)
            self._validate_manual_path(manual_input.value)
        elif self._selected_path:
            self.app.wordlist_path = self._selected_path
            self.app.go_to_options()
        else:
            error_label = self.query_one("#wordlist-error", Label)
            error_label.update("[bold red]Please select a wordlist file[/bold red]")

    def _validate_manual_path(self, path_str: str) -> None:
        """Validate a manually entered wordlist path."""
        error_label = self.query_one("#wordlist-error", Label)
        path = Path(path_str.strip())

        if not path_str.strip():
            error_label.update("[bold red]Path cannot be empty[/bold red]")
            return

        if not path.exists():
            error_label.update(f"[bold red]File not found: {path}[/bold red]")
            return

        if not path.is_file():
            error_label.update(f"[bold red]Not a file: {path}[/bold red]")
            return

        error_label.update("")
        self.app.wordlist_path = str(path)
        self.app.go_to_options()

    def action_confirm(self) -> None:
        self._try_continue()

    def action_manual_input(self) -> None:
        """Toggle manual path input mode."""
        self._manual_mode = not self._manual_mode
        manual_input = self.query_one("#wordlist-manual-input", Input)
        tree = self.query_one("#wordlist-tree", Tree)
        search = self.query_one("#wordlist-search", Input)

        if self._manual_mode:
            manual_input.display = True
            tree.display = False
            search.display = False
            manual_input.focus()
        else:
            manual_input.display = False
            tree.display = True
            search.display = True
            search.focus()

    def action_go_back(self) -> None:
        self.app.pop_screen()
