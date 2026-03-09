# ⚔ CTForge

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple)
![Release](https://img.shields.io/github/v/release/uchihashahin01/ctf-tools-installer?label=Latest&color=green)
![Downloads](https://img.shields.io/github/downloads/uchihashahin01/ctf-tools-installer/total?color=blue)

**Forge your CTF arsenal.** A comprehensive, automated CTF tools installer for Linux with a **Desktop App**, **Web Dashboard**, and **CLI**. Ships as a single binary, `.deb` package, or `.AppImage` with built-in **auto-update**.

Designed for **Ubuntu / Debian** based systems (including WSL).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Desktop App** | Native Linux GUI powered by [pywebview](https://pywebview.flowrl.com/) (WebKit2GTK) — lightweight, ~10 MB RAM |
| **Web Dashboard** | Cyberpunk-themed browser UI with real-time WebSocket logs & integrated manual |
| **CLI** | Non-interactive scripting mode with Rich-formatted output |
| **Manual Guide** | Integrated in the dashboard + available as [MANUAL.md](MANUAL.md) |
| **Auto-Update** | Checks GitHub Releases for new versions; one-command self-update |
| **Multiple Formats** | Binary, `.deb`, and `.AppImage` — no Python/pip setup needed |
| **Smart Detection** | Skips already-installed tools, reports health status |

---

## 🚀 Quick Start

### Option 1 — `.deb` package (recommended for Ubuntu/Debian)

```bash
# Download the .deb from the latest release
sudo dpkg -i ctforge_*.deb

# Launch the desktop app
ctforge
```

### Option 2 — AppImage

```bash
chmod +x CTForge-*.AppImage
./CTForge-*.AppImage
```

### Option 3 — Standalone binary

```bash
curl -sL https://github.com/uchihashahin01/ctf-tools-installer/releases/latest/download/ctforge -o ctforge
chmod +x ctforge

# Desktop app (default)
./ctforge

# Web dashboard
./ctforge web

# CLI
./ctforge cli --all
```

### Option 4 — Run from source

```bash
git clone https://github.com/uchihashahin01/ctf-tools-installer.git
cd ctf-tools-installer
pip3 install -r requirements.txt

# Desktop app
python3 main.py

# Web dashboard
python3 main.py web

# CLI
python3 main.py cli --all
```

> **Note:** The desktop app requires `libwebkit2gtk-4.1-0` on your system. The `.deb` package installs this dependency automatically.

---

## 🖥️ Usage

```
ctforge [mode] [options]
```

| Mode | Description |
|------|-------------|
| *(none)* / `app` | Launch the desktop app |
| `web` | Start web dashboard (default port 5000) |
| `cli` | Rich CLI — interactive menu or flags |
| `update` | Check for updates & self-update |
| `manual` | Print manual installation commands |
| `-V` | Show version |

### CLI Flags

```bash
ctforge cli --all          # Install everything
ctforge cli --pwn --web    # Install specific categories
ctforge cli --status       # Show installed/health status
ctforge cli --nuke         # Uninstall all managed tools
ctforge cli --manual       # Display manual guide
```

### Web Dashboard

```bash
ctforge web --port 8080    # Custom port
```

Open `http://localhost:5000` (or your custom port) in a browser. The dashboard includes a **Manual** page with copy-paste commands for every tool.

---

## 🔄 Auto-Update

The app automatically checks for new releases on GitHub.

- **Desktop App / Web**: A notification banner appears when an update is available.
- **CLI**: An update notice is shown on launch.

```bash
ctforge update
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
│   ├── desktop.py             # Desktop GUI (pywebview)
│   ├── updater.py             # Auto-update logic
│   └── web/
│       ├── app.py             # Flask web dashboard
│       ├── static/            # CSS & JS
│       └── templates/         # HTML
├── packaging/
│   ├── ctforge.desktop        # Linux desktop entry
│   ├── ctforge.svg            # App icon
│   ├── build-deb.sh           # .deb build script
│   └── build-appimage.sh      # .AppImage build script
├── MANUAL.md                  # Manual installation guide
├── requirements.txt
├── pyproject.toml
├── .github/workflows/
│   └── release.yml            # CI/CD → binary + .deb + .AppImage
└── LICENSE
```

---

## 🏗️ Building from Source

```bash
pip install pyinstaller
pip install -r requirements.txt

# Build the binary
pyinstaller --onefile --name ctforge \
  --add-data "ctf_tools/web/templates:ctf_tools/web/templates" \
  --add-data "ctf_tools/web/static:ctf_tools/web/static" \
  --add-data "MANUAL.md:." \
  main.py

# Build .deb
bash packaging/build-deb.sh 2.0.0

# Build .AppImage
bash packaging/build-appimage.sh 2.0.0
```

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

[MIT](LICENSE)
