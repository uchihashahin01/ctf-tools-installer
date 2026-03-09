"""Core installer engine for CTForge.

Provides all installation, detection, health-check, and uninstall logic.
This module is interface-agnostic — Desktop, Web, and CLI all use it.
"""

import os
import subprocess
import shutil
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: dict[str, list[str]] = {
    "essentials": [
        "unzip", "docker.io", "docker-compose", "git", "curl", "wget",
        "build-essential", "python3-pip", "python3-venv", "libssl-dev", "libffi-dev",
    ],
    "crypto": ["sagemath"],
    "reverse": [
        "radare2", "gdb", "strace", "ltrace", "wine", "wine32", "wine64",
        "mingw-w64", "gdb-multiarch",
    ],
    "pwn": [],
    "forensics": ["binwalk", "tshark"],
    "web": ["nikto", "gobuster", "sqlmap"],
    "misc": ["net-tools", "nmap"],
}

PYTHON_PACKAGES: dict[str, list[str]] = {
    "crypto": ["pycryptodome", "z3-solver"],
    "pwn": ["pwntools"],
    "reverse": ["angr"],
    "web": ["requests"],
    "forensics": ["oletools"],
}

CATEGORIES = [
    {"id": "essentials", "name": "Essentials", "desc": "Docker, Git, Python…"},
    {"id": "crypto", "name": "Crypto", "desc": "SageMath, Z3, PyCrypto"},
    {"id": "reverse", "name": "Reverse", "desc": "Radare2, GDB, Wine, Angr"},
    {"id": "pwn", "name": "Pwn", "desc": "Pwntools, Pwndbg, WABT"},
    {"id": "forensics", "name": "Forensics", "desc": "Binwalk, TShark, OleTools"},
    {"id": "web", "name": "Web", "desc": "Nikto, Gobuster, SQLMap"},
    {"id": "misc", "name": "Misc", "desc": "Nmap, Net-tools"},
]

# Manual install commands for the guide
MANUAL_COMMANDS: dict[str, list[tuple[str, str]]] = {
    "essentials": [
        ("unzip", "sudo apt-get install -y unzip"),
        ("docker.io", "sudo apt-get install -y docker.io"),
        ("docker-compose", "sudo apt-get install -y docker-compose"),
        ("git", "sudo apt-get install -y git"),
        ("curl", "sudo apt-get install -y curl"),
        ("wget", "sudo apt-get install -y wget"),
        ("build-essential", "sudo apt-get install -y build-essential"),
        ("python3-pip", "sudo apt-get install -y python3-pip"),
        ("python3-venv", "sudo apt-get install -y python3-venv"),
        ("libssl-dev", "sudo apt-get install -y libssl-dev"),
        ("libffi-dev", "sudo apt-get install -y libffi-dev"),
    ],
    "crypto": [
        ("sagemath", "sudo apt-get install -y sagemath"),
        ("pycryptodome", "pip3 install pycryptodome"),
        ("z3-solver", "pip3 install z3-solver"),
    ],
    "reverse": [
        ("Enable i386", "sudo dpkg --add-architecture i386 && sudo apt-get update"),
        ("radare2", "sudo apt-get install -y radare2"),
        ("gdb", "sudo apt-get install -y gdb"),
        ("strace", "sudo apt-get install -y strace"),
        ("ltrace", "sudo apt-get install -y ltrace"),
        ("wine", "sudo apt-get install -y wine"),
        ("wine32", "sudo apt-get install -y wine32"),
        ("wine64", "sudo apt-get install -y wine64"),
        ("mingw-w64", "sudo apt-get install -y mingw-w64"),
        ("gdb-multiarch", "sudo apt-get install -y gdb-multiarch"),
        ("angr", "pip3 install angr"),
    ],
    "pwn": [
        ("pwntools", "pip3 install pwntools"),
        ("pwndbg", "git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh"),
        ("wabt", "sudo apt-get install -y wabt"),
    ],
    "forensics": [
        ("binwalk", "sudo apt-get install -y binwalk"),
        ("tshark", "sudo apt-get install -y tshark"),
        ("oletools", "pip3 install oletools"),
    ],
    "web": [
        ("nikto", "sudo apt-get install -y nikto"),
        ("gobuster", "sudo apt-get install -y gobuster"),
        ("sqlmap", "sudo apt-get install -y sqlmap"),
        ("requests", "pip3 install requests"),
    ],
    "misc": [
        ("net-tools", "sudo apt-get install -y net-tools"),
        ("nmap", "sudo apt-get install -y nmap"),
    ],
}

VERSION_COMMANDS: dict[str, str] = {
    "radare2": "r2 -v",
    "gdb": "gdb --version",
    "strace": "strace -V",
    "ltrace": "ltrace -V",
    "wine": "wine --version",
    "python3": "python3 --version",
    "git": "git --version",
    "docker.io": "docker --version",
    "docker-compose": "docker-compose --version",
    "sagemath": "sage -v",
    "pwntools": "python3 -c 'import pwn'",
    "angr": "python3 -c 'import angr'",
    "nikto": "nikto -Version",
    "gobuster": "gobuster version",
    "sqlmap": "sqlmap --version",
    "nmap": "nmap --version",
    "binwalk": "binwalk --version",
    "tshark": "tshark -v",
    "pycryptodome": "python3 -c 'import Crypto'",
    "z3-solver": "python3 -c 'import z3'",
    "oletools": "python3 -c 'import oletools'",
    "requests": "python3 -c 'import requests'",
}

# ---------------------------------------------------------------------------
# Logger callback
# ---------------------------------------------------------------------------

_log_callback: Optional[Callable[[str, str], None]] = None


def set_logger(callback: Callable[[str, str], None]) -> None:
    global _log_callback
    _log_callback = callback


def log(message: str, status: str = "INFO") -> None:
    if _log_callback:
        _log_callback(message, status)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def check_sudo() -> bool:
    return os.geteuid() == 0


def run_cmd(command: str, ignore_errors: bool = False) -> bool:
    # When not running as root, prefix system commands with sudo
    if os.geteuid() != 0:
        prefixes = ("apt-get ", "dpkg ", "dpkg-", "add-apt")
        if any(command.lstrip().startswith(p) for p in prefixes):
            command = f"sudo {command}"
    log(f"Executing: {command}", "INFO")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in process.stdout:
            stripped = line.strip()
            if stripped:
                log(stripped, "output")
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        return True
    except subprocess.CalledProcessError:
        if not ignore_errors:
            log(f"Command failed: {command}", "ERROR")
        return False


def ensure_pip() -> None:
    if shutil.which("pip3") is None:
        log("pip3 not found — installing python3-pip…", "WARNING")
        run_cmd("apt-get update && apt-get install -y python3-pip")


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def is_apt_installed(package_name: str) -> bool:
    try:
        cmd = f"dpkg-query -W -f='${{Status}}' {package_name} 2>/dev/null"
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return "install ok installed" in result.stdout
    except Exception:
        return False


def is_pip_installed(package_name: str) -> bool:
    try:
        result = subprocess.run(
            f"pip3 show {package_name}",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def is_tool_installed(name: str, type_: str, real_name: str) -> bool:
    if type_ == "apt":
        return is_apt_installed(real_name)
    elif type_ == "pip":
        return is_pip_installed(real_name)
    elif type_ == "custom":
        if real_name == "install_pwndbg":
            return os.path.exists("pwndbg")
    return False


def check_tool_health(name: str, type_: str, real_name: str) -> str:
    """Returns 'healthy', 'installed_but_error', or 'missing'."""
    if not is_tool_installed(name, type_, real_name):
        return "missing"

    cmd = VERSION_COMMANDS.get(real_name)
    if not cmd and type_ == "apt":
        cmd = f"{real_name} --version"
    if not cmd:
        return "healthy"

    try:
        subprocess.run(
            cmd, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5,
        )
        return "healthy"
    except Exception:
        return "installed_but_error"


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

def install_apt_package(package_name: str) -> None:
    if is_apt_installed(package_name):
        log(f"{package_name} is already installed.", "SUCCESS")
        return
    log(f"Installing {package_name}…", "INFO")
    if run_cmd(f"apt-get install -y {package_name}"):
        log(f"Successfully installed {package_name}", "SUCCESS")
    else:
        log(f"Failed to install {package_name}", "ERROR")


def install_pip_package(package_name: str) -> None:
    ensure_pip()
    if is_pip_installed(package_name):
        log(f"Python package {package_name} is already installed.", "SUCCESS")
        return
    log(f"Installing Python package {package_name}…", "INFO")
    cmd = f"pip3 install {package_name}"
    if run_cmd(cmd, ignore_errors=True):
        log(f"Successfully installed {package_name}", "SUCCESS")
    else:
        log(f"Retrying with --break-system-packages…", "WARNING")
        if run_cmd(f"{cmd} --break-system-packages"):
            log(f"Successfully installed {package_name}", "SUCCESS")
        else:
            log(f"Failed to install Python package {package_name}", "ERROR")


def install_item(item_tuple: tuple[str, str, str]) -> None:
    name, type_, real_name = item_tuple
    if type_ == "apt":
        install_apt_package(real_name)
    elif type_ == "pip":
        install_pip_package(real_name)
    elif type_ == "custom":
        if real_name == "install_pwndbg":
            if not os.path.exists("pwndbg"):
                log("Cloning Pwndbg…", "INFO")
                run_cmd("git clone https://github.com/pwndbg/pwndbg")
                run_cmd("cd pwndbg && ./setup.sh")
            else:
                log("Pwndbg folder already exists.", "WARNING")


# ---------------------------------------------------------------------------
# Category installers
# ---------------------------------------------------------------------------

def install_essentials() -> None:
    log("Starting Essentials Installation…", "INFO")
    run_cmd("apt-get update")
    for tool in TOOLS["essentials"]:
        install_apt_package(tool)
    ensure_pip()


def install_crypto() -> None:
    log("Starting Crypto Installation…", "INFO")
    for tool in TOOLS["crypto"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["crypto"]:
        install_pip_package(pkg)


def install_reverse() -> None:
    log("Starting Reverse Engineering Installation…", "INFO")
    log("Enabling i386 architecture…", "INFO")
    run_cmd("dpkg --add-architecture i386")
    run_cmd("apt-get update")
    for tool in TOOLS["reverse"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["reverse"]:
        install_pip_package(pkg)


def install_pwn() -> None:
    log("Starting Pwn Installation…", "INFO")
    for pkg in PYTHON_PACKAGES["pwn"]:
        install_pip_package(pkg)
    # Pwndbg
    if not os.path.exists("pwndbg"):
        log("Cloning Pwndbg…", "INFO")
        run_cmd("git clone https://github.com/pwndbg/pwndbg")
        run_cmd("cd pwndbg && ./setup.sh")
    else:
        log("Pwndbg folder already exists, skipping clone.", "WARNING")
    install_apt_package("wabt")


def install_forensics() -> None:
    log("Starting Forensics Installation…", "INFO")
    for tool in TOOLS["forensics"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["forensics"]:
        install_pip_package(pkg)


def install_web() -> None:
    log("Starting Web Installation…", "INFO")
    for tool in TOOLS["web"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["web"]:
        install_pip_package(pkg)


def install_misc() -> None:
    log("Starting Misc Installation…", "INFO")
    for tool in TOOLS["misc"]:
        install_apt_package(tool)


CATEGORY_INSTALLERS = {
    "essentials": install_essentials,
    "crypto": install_crypto,
    "reverse": install_reverse,
    "pwn": install_pwn,
    "forensics": install_forensics,
    "web": install_web,
    "misc": install_misc,
}


def install_category(category: str) -> None:
    fn = CATEGORY_INSTALLERS.get(category)
    if fn:
        fn()
    else:
        log(f"Unknown category: {category}", "ERROR")


def install_all() -> None:
    for fn in CATEGORY_INSTALLERS.values():
        fn()


# ---------------------------------------------------------------------------
# Uninstallation
# ---------------------------------------------------------------------------

def uninstall_tool(name: str, type_: str, real_name: str) -> None:
    if not is_tool_installed(name, type_, real_name):
        log(f"{name} is not installed.", "WARNING")
        return
    log(f"Uninstalling {name}…", "INFO")
    if type_ == "apt":
        run_cmd(f"apt-get remove -y {real_name}")
        run_cmd("apt-get autoremove -y")
    elif type_ == "pip":
        run_cmd(f"pip3 uninstall -y {real_name}", ignore_errors=True)
        run_cmd(f"pip3 uninstall -y {real_name} --break-system-packages", ignore_errors=True)
    elif type_ == "custom":
        if real_name == "install_pwndbg" and os.path.exists("pwndbg"):
            shutil.rmtree("pwndbg")
            log("Removed pwndbg directory", "SUCCESS")


def nuke_all() -> None:
    log("NUKING ALL INSTALLED TOOLS…", "WARNING")
    for cat_name in CATEGORY_INSTALLERS:
        tools = get_category_tools(cat_name)
        for name, type_, real_name in tools:
            uninstall_tool(name, type_, real_name)
    log("System Nuke Complete.", "SUCCESS")


# ---------------------------------------------------------------------------
# Accessor
# ---------------------------------------------------------------------------

def get_category_tools(category: str) -> list[tuple[str, str, str]]:
    """Returns list of (display_name, type, real_name) tuples."""
    apt_tools = TOOLS.get(category, [])
    pip_tools = PYTHON_PACKAGES.get(category, [])
    items: list[tuple[str, str, str]] = []
    for t in apt_tools:
        items.append((t, "apt", t))
    for t in pip_tools:
        items.append((t, "pip", t))
    if category == "pwn":
        items.append(("Pwndbg", "custom", "install_pwndbg"))
    return items
