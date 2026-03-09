"""Rich-powered CLI interface for CTF Tools Installer."""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from ctf_tools import __version__
from ctf_tools import core
from ctf_tools.updater import check_for_update

console = Console()


def _setup_logger() -> None:
    """Wire core log messages to Rich console output."""
    def _log(message: str, status: str = "INFO") -> None:
        style_map = {
            "INFO": "blue",
            "SUCCESS": "green",
            "WARNING": "yellow",
            "ERROR": "bold red",
            "output": "dim",
        }
        style = style_map.get(status, "")
        prefix_map = {
            "INFO": "[*]",
            "SUCCESS": "[+]",
            "WARNING": "[!]",
            "ERROR": "[-]",
            "output": "   ",
        }
        prefix = prefix_map.get(status, "[*]")
        console.print(f"{prefix} {message}", style=style)

    core.set_logger(_log)


def _print_banner() -> None:
    banner = Text()
    banner.append("CTF Tools Installer", style="bold cyan")
    banner.append(f"  v{__version__}", style="dim")
    console.print(Panel(banner, border_style="cyan", box=box.DOUBLE))


def _check_update_banner() -> None:
    info = check_for_update()
    if info["update_available"]:
        console.print(
            Panel(
                f"[bold yellow]Update available![/] v{info['current']} → v{info['latest']}\n"
                f"Run: [cyan]sudo ./ctf-tools update[/]",
                border_style="yellow",
                title="Update",
            )
        )


def _show_status() -> None:
    """Print a table of all tools and their status."""
    for cat in core.CATEGORIES:
        table = Table(
            title=f"  {cat['name']}  ",
            box=box.ROUNDED,
            title_style="bold cyan",
            border_style="bright_black",
            show_lines=False,
        )
        table.add_column("Tool", style="white", min_width=18)
        table.add_column("Type", style="dim", width=6)
        table.add_column("Installed", justify="center", width=10)
        table.add_column("Health", justify="center", width=14)

        tools = core.get_category_tools(cat["id"])
        for name, type_, real_name in tools:
            installed = core.is_tool_installed(name, type_, real_name)
            health = core.check_tool_health(name, type_, real_name) if installed else "missing"
            inst_str = "[green]✓[/]" if installed else "[red]✗[/]"
            health_map = {
                "healthy": "[green]healthy[/]",
                "installed_but_error": "[yellow]error[/]",
                "missing": "[dim]—[/]",
            }
            health_str = health_map.get(health, health)
            table.add_row(name, type_, inst_str, health_str)

        console.print(table)
        console.print()


def _show_manual() -> None:
    """Display the manual installation commands for all categories."""
    console.print(Panel("[bold cyan]Manual Installation Guide[/]", border_style="cyan"))
    for cat_id, commands in core.MANUAL_COMMANDS.items():
        cat_name = cat_id.capitalize()
        table = Table(title=cat_name, box=box.SIMPLE, border_style="bright_black")
        table.add_column("Tool", style="white", min_width=16)
        table.add_column("Command", style="green")
        for tool_name, cmd in commands:
            table.add_row(tool_name, cmd)
        console.print(table)
        console.print()


def run_cli(args) -> None:
    """Main entry for CLI mode."""
    _setup_logger()
    _print_banner()

    if not core.check_sudo():
        console.print("[bold red]This tool requires root privileges. Please run with sudo.[/]")
        sys.exit(1)

    _check_update_banner()

    if getattr(args, "status", False):
        _show_status()
        return

    if getattr(args, "manual", False):
        _show_manual()
        return

    # Determine which categories to install
    any_selected = False
    if getattr(args, "all", False):
        core.install_all()
        any_selected = True
    else:
        for cat in core.CATEGORY_INSTALLERS:
            if getattr(args, cat, False):
                core.install_category(cat)
                any_selected = True

    if getattr(args, "nuke", False):
        core.nuke_all()
        any_selected = True

    if not any_selected:
        # Interactive category selection
        _interactive_menu()


def _interactive_menu() -> None:
    """Rich-powered interactive menu."""
    while True:
        console.print()
        table = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Category", style="white")
        for i, cat in enumerate(core.CATEGORIES, 1):
            table.add_row(str(i), f"{cat['name']}  [dim]({cat['desc']})[/]")
        table.add_row("8", "Install EVERYTHING")
        table.add_row("9", "[bold]Show Status[/]")
        table.add_row("m", "[bold]Manual Guide[/]")
        table.add_row("0", "Exit")
        console.print(table)

        choice = console.input("[cyan]Choose> [/]").strip()

        if choice == "0":
            break
        elif choice == "9":
            _show_status()
        elif choice == "m":
            _show_manual()
        elif choice == "8":
            core.install_all()
            console.print("[green]All tools installed![/]")
        elif choice.isdigit() and 1 <= int(choice) <= 7:
            cat = core.CATEGORIES[int(choice) - 1]
            _category_submenu(cat)
        else:
            console.print("[red]Invalid choice.[/]")


def _category_submenu(cat: dict) -> None:
    tools = core.get_category_tools(cat["id"])
    while True:
        console.print(f"\n[bold cyan]=== {cat['name']} Tools ===[/]")
        console.print("[cyan]1.[/] Install All in Category")
        for idx, (name, type_, _) in enumerate(tools, 2):
            console.print(f"[cyan]{idx}.[/] Install {name} ({type_})")
        console.print("[cyan]0.[/] Back")

        choice = console.input("[cyan]Choose> [/]").strip()
        if choice == "0":
            break
        elif choice == "1":
            core.install_category(cat["id"])
        elif choice.isdigit():
            idx = int(choice) - 2
            if 0 <= idx < len(tools):
                core.install_item(tools[idx])
            else:
                console.print("[red]Invalid.[/]")
        else:
            console.print("[red]Invalid.[/]")
