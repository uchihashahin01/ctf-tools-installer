# 📖 CTF Tools — Manual Installation Guide

If you prefer to install tools yourself, use the commands below.
All commands assume **Ubuntu / Debian** based systems.

> **Tip:** Run `sudo apt-get update` before installing any `apt` packages.

---

## Essentials

```bash
sudo apt-get update
sudo apt-get install -y unzip
sudo apt-get install -y docker.io
sudo apt-get install -y docker-compose
sudo apt-get install -y git
sudo apt-get install -y curl
sudo apt-get install -y wget
sudo apt-get install -y build-essential
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-venv
sudo apt-get install -y libssl-dev
sudo apt-get install -y libffi-dev
```

---

## Crypto

```bash
sudo apt-get install -y sagemath
pip3 install pycryptodome
pip3 install z3-solver
```

> On newer systems (Ubuntu 24.04+) you may need `pip3 install --break-system-packages <pkg>`.

---

## Reverse Engineering

```bash
# Enable 32-bit architecture (needed for wine32)
sudo dpkg --add-architecture i386
sudo apt-get update

sudo apt-get install -y radare2
sudo apt-get install -y gdb
sudo apt-get install -y strace
sudo apt-get install -y ltrace
sudo apt-get install -y wine
sudo apt-get install -y wine32
sudo apt-get install -y wine64
sudo apt-get install -y mingw-w64
sudo apt-get install -y gdb-multiarch

pip3 install angr
```

---

## Pwn

```bash
pip3 install pwntools

# Pwndbg (GDB extension)
git clone https://github.com/pwndbg/pwndbg
cd pwndbg
./setup.sh
cd ..

sudo apt-get install -y wabt
```

---

## Forensics

```bash
sudo apt-get install -y binwalk
sudo apt-get install -y tshark
pip3 install oletools
```

---

## Web

```bash
sudo apt-get install -y nikto
sudo apt-get install -y gobuster
sudo apt-get install -y sqlmap
pip3 install requests
```

---

## Misc

```bash
sudo apt-get install -y net-tools
sudo apt-get install -y nmap
```

---

## Quick Install (Everything at Once)

```bash
sudo apt-get update && sudo dpkg --add-architecture i386 && sudo apt-get update

# Essentials
sudo apt-get install -y unzip docker.io docker-compose git curl wget build-essential python3-pip python3-venv libssl-dev libffi-dev

# Crypto
sudo apt-get install -y sagemath
pip3 install pycryptodome z3-solver

# Reverse
sudo apt-get install -y radare2 gdb strace ltrace wine wine32 wine64 mingw-w64 gdb-multiarch
pip3 install angr

# Pwn
pip3 install pwntools
git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh && cd ..
sudo apt-get install -y wabt

# Forensics
sudo apt-get install -y binwalk tshark
pip3 install oletools

# Web
sudo apt-get install -y nikto gobuster sqlmap
pip3 install requests

# Misc
sudo apt-get install -y net-tools nmap
```

---

## Notes

- **SageMath** is large (~2 GB). Install only if needed.
- **Wine** requires `i386` architecture to be enabled first.
- **angr** installs many dependencies and may take a while.
- On systems with PEP 668 (externally managed environments), append `--break-system-packages` to `pip3 install` commands or use a virtual environment.
