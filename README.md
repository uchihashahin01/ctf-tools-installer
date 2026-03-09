# 🚩 CTF Tools Installer

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple)
![Release](https://img.shields.io/github/v/release/uchihashahin01/ctf-tools-installer?label=Latest&color=green)
![Downloads](https://img.shields.io/github/downloads/uchihashahin01/ctf-tools-installer/total?color=blue)

A comprehensive, automated **CTF tools installer** for Linux with **three interfaces**: a modern **Terminal UI (TUI)**, a **Web Dashboard**, and a traditional **CLI**. Ships as a single downloadable binary with built-in **auto-update**.

Designed for **Ubuntu / Debian** based systems (including WSL).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Terminal UI (TUI)** | Beautiful interactive app built with [Textual](https://textual.textualize.io/) — keyboard & mouse driven, uses minimal RAM |
| **Web Dashboard** | Cyberpunk-themed browser UI with real-time WebSocket logs |
| **CLI** | Non-interactive scripting mode with Rich-formatted output |
| **Manual Guide** | Full copy-paste command reference ([MANUAL.md](MANUAL.md)) |
| **Auto-Update** | Checks GitHub Releases for new versions; one-command self-update |
| **Single Binary** | Download from Releases — no Python/pip setup needed |
| **Smart Detection** | Skips already-installed tools, reports health status |

---

## 🚀 Quick Start

### Option 1 — Download the binary (recommended)

```bash
# Download latest release
curl -sL https://github.com/uchihashahin01/ctf-tools-installer/releases/latest/download/ctf-tools -o ctf-tools
chmod +x ctf-tools

# Launch TUI (default)
sudo ./ctf-tools

# Or launch web dashboard
sudo ./ctf-tools web

# Or use CLI
sudo ./ctf-tools cli --all
```

### Option 2 — Run from source

```bash
git clone https://github.com/uchihashahin01/ctf-tools-installer.git
cd ctf-tools-installer

pip3 install -r requirements.txt

# Launch TUI
sudo python3 main.py

# Launch web dashboard
sudo python3 main.py web

# CLI mode
sudo python3 main.py cli --all
```

---

## 🖥️ Usage

```
sudo ./ctf-tools [mode] [options]
```

| Mode | Description |
|------|-------------|
| *(none)* / `tui` | Launch the Terminal UI app |
| `web` | Start web dashboard (default port 5000) |
| `cli` | Rich CLI — interactive menu or flags |
| `update` | Check for updates & self-update |
| `manual` | Print manual installation commands |
| `-V` | Show version |

### CLI Flags

```bash
sudo ./ctf-tools cli --all          # Install everything
sudo ./ctf-tools cli --pwn --web    # Install specific categories
sudo ./ctf-tools cli --status       # Show installed/health status
sudo ./ctf-tools cli --nuke         # Uninstall all managed tools
sudo ./ctf-tools cli --manual       # Display manual guide
```

### Web Dashboard

```bash
sudo ./ctf-tools web --port 8080    # Custom port
```

Open `http://localhost:5000` (or your custom port) in a browser.

---

## 🔄 Auto-Update

The app automatically checks for new releases on GitHub.

- **In TUI**: A yellow banner appears at the top when an update is available.
- **In Web Dashboard**: A notification bar appears.
- **In CLI**: An update notice is shown on launch.

To update:

```bash
sudo ./ctf-tools update
```

---

## 🛠️ Tool List

| Category | Tools |
|----------|-------|
| **Essentials** | Docker, Docker-Compose, Git, Python3-pip, Unzip, Build-essential, Curl, Wget, libssl-dev, libffi-dev |
| **Crypto** | SageMath, PyCryptodome, Z3-Solver |
| **Reverse** | Radare2, GDB, Strace, Ltrace, Wine (32/64), mingw-w64, gdb-multiarch, Angr |
| **Pwn** | Pwntools, Pwndbg, WABT |
| **Forensics** | Binwalk, TShark, OleTools |
| **Web** | Nikto, Gobuster, SQLMap, Requests |
| **Misc** | Nmap, Net-tools |

> See [MANUAL.md](MANUAL.md) for copy-paste install commands for each tool.

---

## 📁 Project Structure

```
ctf-tools-installer/
├── main.py                    # Unified entry point
├── ctf_tools/
│   ├── __init__.py            # Version & constants
│   ├── core.py                # Installer engine
│   ├── cli.py                 # Rich CLI interface
│   ├── tui.py                 # Textual TUI app
│   ├── updater.py             # Auto-update logic
│   └── web/
│       ├── app.py             # Flask web dashboard
│       ├── static/            # CSS & JS
│       └── templates/         # HTML
├── MANUAL.md                  # Manual installation guide
├── requirements.txt
├── pyproject.toml
├── .github/workflows/
│   └── release.yml            # CI/CD → binary release
└── LICENSE
```

---

## 🏗️ Building from Source

```bash
pip install pyinstaller
pyinstaller --onefile --name ctf-tools \
  --add-data "ctf_tools/web/templates:ctf_tools/web/templates" \
  --add-data "ctf_tools/web/static:ctf_tools/web/static" \
  main.py
# Binary → dist/ctf-tools
```

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

[MIT](LICENSE)
