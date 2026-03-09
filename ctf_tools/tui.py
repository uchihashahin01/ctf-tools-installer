"""Textual TUI application — the 'Linux app' interface."""

from __future__ import annotations

import threading
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    ListView,
    ListItem,
    RichLog,
    DataTable,
    Label,
    Button,
)
from rich.text import Text

from ctf_tools import __version__
from ctf_tools import core
from ctf_tools.updater import check_for_update


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class UpdateBanner(Static):
    """Shows an update notification when a newer version is available."""

    DEFAULT_CSS = """
    UpdateBanner {
        display: none;
        height: 1;
        background: $warning;
        color: $text;
        text-align: center;
    }
    UpdateBanner.visible {
        display: block;
    }
    """

    def show_update(self, current: str, latest: str) -> None:
        self.update(f" Update available: v{current} → v{latest}  |  Run: sudo ./ctf-tools update ")
        self.add_class("visible")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class CTFToolsApp(App):
    """CTF Tools Installer — Terminal UI."""

    TITLE = f"CTF Tools Installer v{__version__}"
    SUB_TITLE = "Select a category to manage tools"

    CSS = """
    #sidebar {
        width: 28;
        dock: left;
        background: $surface;
        border-right: tall $primary;
        padding: 1;
    }
    #sidebar-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }
    .cat-btn {
        width: 100%;
        margin-bottom: 1;
    }
    #action-buttons {
        padding-top: 1;
        align: center middle;
    }
    #main-area {
        width: 1fr;
    }
    #tools-table {
        height: 1fr;
        min-height: 10;
        border: tall $primary;
    }
    #log-panel {
        height: 14;
        border-top: tall $accent;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("u", "check_update", "Update Check"),
    ]

    current_category: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield UpdateBanner(id="update-banner")
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("⚑ CATEGORIES", id="sidebar-title")
                for cat in core.CATEGORIES:
                    yield Button(cat["name"], id=f"cat-{cat['id']}", classes="cat-btn")
                with Vertical(id="action-buttons"):
                    yield Button("Install ALL", id="install-all", variant="success")
                    yield Button("☢ Nuke All", id="nuke-all", variant="error")
            with Vertical(id="main-area"):
                yield DataTable(id="tools-table")
                yield RichLog(id="log-panel", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#tools-table", DataTable)
        table.add_columns("Tool", "Type", "Installed", "Health")
        table.cursor_type = "row"
        self._log_msg("System ready. Select a category.", "INFO")
        # Background update check
        threading.Thread(target=self._bg_update_check, daemon=True).start()
        # Wire core logger
        core.set_logger(self._log_msg)

    # ---- logging helper --------------------------------------------------

    def _log_msg(self, message: str, status: str = "INFO") -> None:
        style_map = {
            "INFO": "[blue]",
            "SUCCESS": "[green]",
            "WARNING": "[yellow]",
            "ERROR": "[bold red]",
            "output": "[dim]",
        }
        prefix_map = {
            "INFO": "[*]",
            "SUCCESS": "[+]",
            "WARNING": "[!]",
            "ERROR": "[-]",
            "output": "   ",
        }
        style = style_map.get(status, "")
        prefix = prefix_map.get(status, "[*]")
        end_style = "[/]" if style else ""
        try:
            log = self.query_one("#log-panel", RichLog)
            log.write(f"{style}{prefix} {message}{end_style}")
        except Exception:
            pass

    # ---- background update check -----------------------------------------

    def _bg_update_check(self) -> None:
        info = check_for_update()
        if info["update_available"]:
            self.call_from_thread(
                self._show_update_banner, info["current"], info["latest"]
            )

    def _show_update_banner(self, current: str, latest: str) -> None:
        banner = self.query_one("#update-banner", UpdateBanner)
        banner.show_update(current, latest)

    # ---- button handlers -------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("cat-"):
            cat_id = btn_id[4:]
            self.current_category = cat_id
            self._load_tools(cat_id)
        elif btn_id == "install-all":
            self._run_in_thread(core.install_all, "Installing all tools…")
        elif btn_id == "nuke-all":
            self._run_in_thread(core.nuke_all, "Nuking all tools…")
        elif btn_id and btn_id.startswith("install-tool-"):
            idx = int(btn_id.split("-")[-1])
            if self.current_category:
                tools = core.get_category_tools(self.current_category)
                if 0 <= idx < len(tools):
                    item = tools[idx]
                    self._run_in_thread(lambda: core.install_item(item), f"Installing {item[0]}…")

    # ---- table row selection → install ------------------------------------

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if self.current_category is None:
            return
        tools = core.get_category_tools(self.current_category)
        row_idx = event.cursor_row
        if 0 <= row_idx < len(tools):
            item = tools[row_idx]
            installed = core.is_tool_installed(item[0], item[1], item[2])
            if installed:
                self._run_in_thread(
                    lambda: core.uninstall_tool(item[0], item[1], item[2]),
                    f"Uninstalling {item[0]}…",
                )
            else:
                self._run_in_thread(lambda: core.install_item(item), f"Installing {item[0]}…")

    # ---- load tools into table -------------------------------------------

    def _load_tools(self, category_id: str) -> None:
        table = self.query_one("#tools-table", DataTable)
        table.clear()
        cat_name = next((c["name"] for c in core.CATEGORIES if c["id"] == category_id), category_id)
        self.sub_title = f"{cat_name} Tools  (Enter = install/uninstall)"
        tools = core.get_category_tools(category_id)
        for name, type_, real_name in tools:
            installed = core.is_tool_installed(name, type_, real_name)
            health = core.check_tool_health(name, type_, real_name) if installed else "missing"
            inst_text = Text("✓ yes", style="green") if installed else Text("✗ no", style="red")
            health_text = {
                "healthy": Text("healthy", style="green"),
                "installed_but_error": Text("error", style="yellow"),
                "missing": Text("—", style="dim"),
            }.get(health, Text(health))
            table.add_row(name, type_, inst_text, health_text)

    # ---- threading --------------------------------------------------------

    def _run_in_thread(self, fn, msg: str) -> None:
        self._log_msg(msg, "INFO")

        def _worker():
            try:
                fn()
                self.call_from_thread(self._after_operation)
            except Exception as exc:
                self._log_msg(str(exc), "ERROR")

        threading.Thread(target=_worker, daemon=True).start()

    def _after_operation(self) -> None:
        if self.current_category:
            self._load_tools(self.current_category)

    # ---- actions ----------------------------------------------------------

    def action_refresh(self) -> None:
        if self.current_category:
            self._load_tools(self.current_category)

    def action_check_update(self) -> None:
        self._log_msg("Checking for updates…", "INFO")
        threading.Thread(target=self._bg_update_check, daemon=True).start()


def run_tui() -> None:
    app = CTFToolsApp()
    app.run()
