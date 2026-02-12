# 🚩 CTF Tools Installer & Dashboard

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-green?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple)

A comprehensive, automated installer for Capture The Flag (CTF) tools, featuring a **CLI** and a **Cyberpunk-themed Web Dashboard**.

Designed for **WSL / Ubuntu / Debian** based systems.

## ✨ Features

*   **Cyberpunk Web Dashboard**: Install tools via a modern, dark-mode web interface.
*   **Real-time Logs**: Watch installation progress live in the web terminal (WebSockets).
*   **Smart Detection**: Checks if tools are already installed to avoid redundancy.
*   **Categorized Tools**: Essentials, Crypto, Reverse Engineering, Pwn, Forensics, Web, and Misc.
*   **WSL Support**: Automatically enables `i386` architecture for `wine32` support.

## 🚀 Installation

### Prerequisites
You need `python3` and `sudo` privileges.

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ctf-tools-installer.git
cd ctf-tools-installer

# Install Python dependencies
sudo apt-get install -y python3-pip
# Note: On newer systems (Ubuntu 24.04+), use --break-system-packages
sudo pip3 install flask flask-socketio eventlet --break-system-packages
```

## 🖥️ Usage

### Option A: Web Dashboard (Recommended)

Run the dashboard and access it via your browser.

```bash
sudo python3 app.py
```

*   Open your browser to: `http://localhost:5000`
*   Click on any category to view tools.
*   Click **Install** on individual tools or **Install All** for the entire category.

### Option B: Command Line Interface (CLI)

You can run the installer text-only if you prefer.

```bash
# Interactive Menu
sudo ./ctf_installer.py

# Install specific categories directly
sudo ./ctf_installer.py --pwn --reverse

# Install EVERYTHING
sudo ./ctf_installer.py --all
```

## 🛠️ Tool List

| Category | Tools Included |
|----------|----------------|
| **Essentials** | Docker, Git, Python3-pip, Unzip, Build-essential, Curl, Wget |
| **Crypto** | SageMath, PyCryptodome, Z3-Solver |
| **Reverse** | Radare2, GDB, Strace, Ltrace, Wine (32/64), Angr |
| **Pwn** | Pwntools, Pwndbg, WABT (wat2wasm) |
| **Forensics** | Binwalk, TShark, OleTools |
| **Web** | Nikto, Gobuster, SQLMap |
| **Misc** | Nmap, Net-tools |

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

[MIT](https://choosealicense.com/licenses/mit/)
