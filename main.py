#!/usr/bin/env python3
"""CTForge — unified entry point.

Usage:
    ctforge                     Launch desktop app (default)
    ctforge app                 Launch desktop app
    ctforge web                 Launch web dashboard
    ctforge cli                 Interactive CLI menu
    ctforge cli --all           Install everything (non-interactive)
    ctforge update              Check for updates & self-update
    ctforge manual              Print manual install guide
"""

import argparse
import sys

from ctf_tools import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ctforge",
        description="CTForge — Desktop App, Web Dashboard & CLI",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    sub = parser.add_subparsers(dest="mode")

    # --- app (desktop GUI) -------------------------------------------------
    sub.add_parser("app", help="Launch the desktop app (default)")

    # --- web ---------------------------------------------------------------
    web_p = sub.add_parser("web", help="Launch the web dashboard")
    web_p.add_argument("--port", type=int, default=5000, help="Port (default 5000)")

    # --- cli ---------------------------------------------------------------
    cli_p = sub.add_parser("cli", help="Command-line interface")
    cli_p.add_argument("--all", action="store_true", help="Install all tools")
    cli_p.add_argument("--essentials", action="store_true")
    cli_p.add_argument("--crypto", action="store_true")
    cli_p.add_argument("--reverse", action="store_true")
    cli_p.add_argument("--pwn", action="store_true")
    cli_p.add_argument("--forensics", action="store_true")
    cli_p.add_argument("--web", action="store_true")
    cli_p.add_argument("--misc", action="store_true")
    cli_p.add_argument("--nuke", action="store_true", help="Remove all tools")
    cli_p.add_argument("--status", action="store_true", help="Show tool status")
    cli_p.add_argument("--manual", action="store_true", help="Show manual guide")

    # --- update ------------------------------------------------------------
    sub.add_parser("update", help="Check for & apply updates")

    # --- manual ------------------------------------------------------------
    sub.add_parser("manual", help="Print manual installation guide")

    args = parser.parse_args()

    # Default → desktop app
    if args.mode is None:
        args.mode = "app"

    if args.mode == "app":
        from ctf_tools.desktop import run_desktop
        run_desktop()

    elif args.mode == "web":
        from ctf_tools.web.app import run_web
        run_web(args.port)

    elif args.mode == "cli":
        from ctf_tools.cli import run_cli
        run_cli(args)

    elif args.mode == "update":
        _handle_update()

    elif args.mode == "manual":
        _print_manual()


def _handle_update() -> None:
    from rich.console import Console
    from ctf_tools.updater import check_for_update, perform_update

    console = Console()
    console.print("[cyan]Checking for updates…[/]")
    info = check_for_update()

    if not info["update_available"]:
        console.print(f"[green]You are on the latest version (v{info['current']}).[/]")
        return

    console.print(
        f"[yellow]Update available:[/] v{info['current']} → v{info['latest']}"
    )
    if info["release_notes"]:
        console.print(f"[dim]{info['release_notes'][:300]}[/]")

    if info["download_url"]:
        ans = console.input("[cyan]Download and apply update? (y/n): [/]").strip().lower()
        if ans == "y":
            console.print("[cyan]Downloading…[/]")
            if perform_update(info["download_url"]):
                console.print("[green]Update applied! Restart the tool to use the new version.[/]")
            else:
                console.print("[red]Update failed. Try downloading manually from GitHub releases.[/]")
    else:
        console.print(
            "[yellow]No binary asset found. Update manually from "
            "https://github.com/uchihashahin01/ctf-tools-installer/releases[/]"
        )


def _print_manual() -> None:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from ctf_tools.core import MANUAL_COMMANDS

    console = Console()
    console.print("\n[bold cyan]CTForge — Manual Installation Guide[/]\n")
    console.print("[dim]Copy-paste these commands to install tools manually.[/]\n")

    for cat_id, commands in MANUAL_COMMANDS.items():
        table = Table(
            title=cat_id.capitalize(),
            box=box.SIMPLE_HEAVY,
            border_style="cyan",
        )
        table.add_column("Tool", style="white", min_width=16)
        table.add_column("Command", style="green")
        for tool_name, cmd in commands:
            table.add_row(tool_name, cmd)
        console.print(table)
        console.print()


if __name__ == "__main__":
    main()
