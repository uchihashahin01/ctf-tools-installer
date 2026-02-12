#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import shutil
import time

# --- Configuration & Colors ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

TOOLS = {
    "essentials": [
        "unzip", "docker.io", "docker-compose", "git", "curl", "wget", "build-essential", "python3-pip", "python3-venv", "libssl-dev", "libffi-dev"
    ],
    "crypto": [
        "sagemath" 
    ],
    "reverse": [
        "radare2", "gdb", "strace", "ltrace", "wine", "wine32", "wine64", "mingw-w64", "gdb-multiarch"
    ],
    "pwn": [
        # pwntools is python, handled separately
    ],
    "forensics": [
        "binwalk", "tshark"
    ],
    "web": [
        "nikto", "gobuster", "sqlmap"
    ],
    "misc": [
        "net-tools", "nmap"
    ]
}

PYTHON_PACKAGES = {
    "crypto": ["pycryptodome", "z3-solver"],
    "pwn": ["pwntools"],
    "reverse": ["angr"],
    "web": ["requests"],
    "forensics": ["oletools"]
}

# Global logger callback
# Callback signature: func(message, type="INFO")
LOG_CALLBACK = None

def set_logger(callback):
    global LOG_CALLBACK
    LOG_CALLBACK = callback

# --- Helper Functions ---

def print_status(message, status="INFO"):
    # Send to external logger if registered
    if LOG_CALLBACK:
        LOG_CALLBACK(message, status)
    
    # Always print to stdout for redundancy/CLI usage
    if status == "INFO":
        print(f"{Colors.BLUE}[*]{Colors.ENDC} {message}")
    elif status == "SUCCESS":
        print(f"{Colors.GREEN}[+]{Colors.ENDC} {message}")
    elif status == "WARNING":
        print(f"{Colors.WARNING}[!]{Colors.ENDC} {message}")
    elif status == "ERROR":
        print(f"{Colors.FAIL}[-]{Colors.ENDC} {message}")
    elif status == "output":
        # Raw output, maybe just print it? Or formatted?
        # For CLI, just print. For Web, it sends "output" status.
        print(message)
    sys.stdout.flush()

def check_sudo():
    if os.geteuid() != 0:
        print_status("This script requires root privileges. Please run with sudo.", "ERROR")
        # If imported, we might not want to exit essentially, but for now we do.
        if __name__ == "__main__":
            sys.exit(1)
        else:
            raise PermissionError("Run with sudo")

def run_cmd(command, ignore_errors=False):
    print_status(f"Executing: {command}", "INFO")
    try:
        # Use Popen to capture output real-time
        process = subprocess.Popen(
            command, 
            shell=True, 
            executable='/bin/bash', 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )
        
        # Read output line by line
        for line in process.stdout:
            line = line.strip()
            if line:
                print_status(line, "output") # Use a specific type or just INFO
        
        process.wait()
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
            
        return True
    except subprocess.CalledProcessError:
        if not ignore_errors:
            print_status(f"Command failed: {command}", "ERROR")
        return False

def ensure_pip():
    """Ensures pip is available before trying to use it."""
    # print_status("Checking for python3-pip...", "INFO") # Too noisy
    if shutil.which("pip3") is None:
         print_status("pip3 not found. Installing python3-pip...", "WARNING")
         run_cmd("apt-get update && apt-get install -y python3-pip")

def is_apt_installed(package_name):
    try:
        # dpkg-query is cleaner than dpkg -l
        # 2>/dev/null to suppress error if not found
        cmd = f"dpkg-query -W -f='${{Status}}' {package_name} 2>/dev/null"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return "install ok installed" in result.stdout
    except:
        return False

def is_pip_installed(package_name):
    try:
        cmd = f"pip3 show {package_name}"
        # We don't want to log this check usually, keep it silent
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except:
        return False

def install_apt_package(package_name):
    if is_apt_installed(package_name):
        print_status(f"{package_name} is already installed.", "SUCCESS")
        return

    print_status(f"Installing {package_name}...", "INFO")
    if run_cmd(f"apt-get install -y {package_name}"):
        print_status(f"Successfully installed {package_name}", "SUCCESS")
    else:
        print_status(f"Failed to install {package_name}", "ERROR")

def install_pip_package(package_name):
    ensure_pip() # Double check
    
    if is_pip_installed(package_name):
        print_status(f"Python package {package_name} is already installed.", "SUCCESS")
        return

    print_status(f"Installing Python package {package_name}...", "INFO")
    cmd = f"pip3 install {package_name}"
    
    # Try with --break-system-packages if needed (for newer Debian/Ubuntu)
    # First try normal
    if run_cmd(cmd, ignore_errors=True):
        print_status(f"Successfully installed {package_name}", "SUCCESS")
    else:
        print_status(f"Retrying with --break-system-packages for {package_name}...", "WARNING")
        if run_cmd(f"{cmd} --break-system-packages"):
             print_status(f"Successfully installed {package_name}", "SUCCESS")
        else:
            print_status(f"Failed to install Python package {package_name}", "ERROR")

def is_tool_installed(name, type_, real_name):
    if type_ == "apt":
        return is_apt_installed(real_name)
    elif type_ == "pip":
        return is_pip_installed(real_name)
    elif type_ == "custom":
        if real_name == "install_pwndbg":
             return os.path.exists("pwndbg")
    return False

def check_tool_health(name, type_, real_name):
    """
    Checks if a tool is operational by running a version command.
    Returns: 'healthy', 'installed_but_error', 'missing'
    """
    if not is_tool_installed(name, type_, real_name):
        return 'missing'

    # Define version commands for specific tools
    version_commands = {
        "radare2": "r2 -v",
        "gdb": "gdb --version",
        "strace": "strace -V",
        "ltrace": "ltrace -V",
        "wine": "wine --version",
        "python3": "python3 --version",
        "git": "git --version",
        "docker": "docker --version",
        "sage": "sage -v",
        "pwntools": "python3 -c 'import pwn'",
        "angr": "python3 -c 'import angr'", 
        "nikto": "nikto -Version",
        "gobuster": "gobuster version",
        "sqlmap": "sqlmap --version",
        "nmap": "nmap --version",
        "binwalk": "binwalk --version",
        "tshark": "tshark -v",
    }

    cmd = version_commands.get(real_name)
    
    # Generic fallback for simple binaries
    if not cmd and type_ == "apt":
        cmd = f"{real_name} --version"
    
    if not cmd:
        # If we don't know how to check health, just assume healthy if installed
        return 'healthy'

    try:
        # Run quickly, suppress output
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        return 'healthy'
    except:
        return 'installed_but_error'

def uninstall_tool(name, type_, real_name):
    if not is_tool_installed(name, type_, real_name):
        print_status(f"{name} is not installed.", "WARNING")
        return

    print_status(f"Uninstalling {name}...", "INFO")
    
    if type_ == "apt":
        run_cmd(f"apt-get remove -y {real_name}")
        run_cmd(f"apt-get autoremove -y")
    elif type_ == "pip":
        run_cmd(f"pip3 uninstall -y {real_name}")
        if run_cmd(f"pip3 uninstall -y {real_name} --break-system-packages", ignore_errors=True):
             pass
    elif type_ == "custom":
        if real_name == "install_pwndbg":
             if os.path.exists("pwndbg"):
                 shutil.rmtree("pwndbg")
                 print_status("Removed pwndbg directory", "SUCCESS")

def nuke_all():
    print_status("NUKING ALL INSTALLED TOOLS...", "WARNING")
    # Get all categories
    categories = [
        ("essentials", install_essentials),
        ("crypto", install_crypto), 
        ("reverse", install_reverse), 
        ("pwn", install_pwn), 
        ("forensics", install_forensics), 
        ("web", install_web), 
        ("misc", install_misc)
    ]
    
    for cat_name, _ in categories:
        tools = get_category_tools(cat_name)
        for _, type_, real_name in tools:
            uninstall_tool(_, type_, real_name)
            
    print_status("System Nuke Complete. I hope you know what you did.", "SUCCESS")

def install_essentials():
    print_status("Starting Essentials Installation...", "HEADER")
    run_cmd("apt-get update")
    for tool in TOOLS["essentials"]:
        install_apt_package(tool)
    ensure_pip()

def install_crypto():
    print_status("Starting Crypto Installation...", "HEADER")
    for tool in TOOLS["crypto"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["crypto"]:
        install_pip_package(pkg)

def install_reverse():
    print_status("Starting Reverse Engineering Installation...", "HEADER")
    print_status("Enabling i386 architecture...", "INFO")
    run_cmd("dpkg --add-architecture i386")
    run_cmd("apt-get update")

    for tool in TOOLS["reverse"]:
        install_apt_package(tool)
    
    for pkg in PYTHON_PACKAGES["reverse"]:
        install_pip_package(pkg)

def install_pwn():
    print_status("Starting Pwn Installation...", "HEADER")
    for pkg in PYTHON_PACKAGES["pwn"]:
        install_pip_package(pkg)
    
    # Install Pwndbg
    if not os.path.exists("pwndbg"):
        print_status("Cloning Pwndbg...", "INFO")
        run_cmd("git clone https://github.com/pwndbg/pwndbg")
        os.chdir("pwndbg")
        # Run setup.sh
        # Note: setup.sh might ask questions or use sudo.
        run_cmd("./setup.sh")
        os.chdir("..")
    else:
        print_status("Pwndbg folder already exists, skipping clone.", "WARNING")

    install_apt_package("wabt") 

def install_forensics():
    print_status("Starting Forensics Installation...", "HEADER")
    for tool in TOOLS["forensics"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["forensics"]:
        install_pip_package(pkg)

def install_web():
    print_status("Starting Web Installation...", "HEADER")
    for tool in TOOLS["web"]:
        install_apt_package(tool)
    for pkg in PYTHON_PACKAGES["web"]:
        install_pip_package(pkg)
        
def install_misc():
    print_status("Starting Misc Installation...", "HEADER")
    for tool in TOOLS["misc"]:
        install_apt_package(tool)

# --- Accessor for Dashboard ---

def get_category_tools(category):
    """Returns a combined list of apt and pip tools for a category."""
    apt_tools = TOOLS.get(category, [])
    pip_tools = PYTHON_PACKAGES.get(category, [])
    
    extra_items = []
    # Create a list of tuples (name, type, real_name)
    items = []
    for t in apt_tools: items.append((t, "apt", t))
    for t in pip_tools: items.append((t, "pip", t))
    
    if category == "pwn":
        items.append(("Pwndbg", "custom", "install_pwndbg"))
    
    return items

def install_item(item_tuple):
    name, type_, real_name = item_tuple
    if type_ == "apt":
        install_apt_package(real_name)
    elif type_ == "pip":
        install_pip_package(real_name)
    elif type_ == "custom":
        if real_name == "install_pwndbg":
            if not os.path.exists("pwndbg"):
                print_status("Cloning Pwndbg...", "INFO")
                run_cmd("git clone https://github.com/pwndbg/pwndbg")
                os.chdir("pwndbg")
                run_cmd("./setup.sh")
                os.chdir("..")
            else:
                print_status("Pwndbg folder already exists.", "WARNING")

# --- Interactive Menu ---

def category_menu(category_name, category_key):
    # Prepare items
    all_items = get_category_tools(category_key)
    # Special handling display
    display_items = all_items[:]

    while True:
        print(f"\n{Colors.CYAN}{Colors.BOLD}=== {category_name} Tools ==={Colors.ENDC}")
        print("1. Install All in Category")
        
        for idx, (name, type_, _) in enumerate(display_items, 1):
             print(f"{idx+1}. Install {name} ({type_})")
        
        print("0. Back to Main Menu")
        
        choice = input(f"{Colors.GREEN}Enter your choice: {Colors.ENDC}")
        
        if choice == '0':
            break
        elif choice == '1':
            print_status(f"Installing all {category_name} tools...", "INFO")
            if category_key == "reverse": 
                 print_status("Enabling i386 architecture...", "INFO")
                 run_cmd("dpkg --add-architecture i386")
                 run_cmd("apt-get update")
            
            for item in display_items:
                install_item(item)
            
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.ENDC}")
        else:
            try:
                idx = int(choice) - 2
                if 0 <= idx < len(display_items):
                    item = display_items[idx]
                    
                    if category_key == "reverse" and "wine" in item[2]:
                        print_status("Ensuring i386 architecture is available for Wine...", "INFO")
                        run_cmd("dpkg --add-architecture i386")
                        run_cmd("apt-get update")

                    install_item(item)
                    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.ENDC}")
                else:
                    print_status("Invalid selection.", "ERROR")
            except ValueError:
                print_status("Please enter a number.", "ERROR")

def interactive_menu():
    while True:
        print(f"\n{Colors.CYAN}{Colors.BOLD}CTF Tools Installer{Colors.ENDC}")
        print("1. Essentials")
        print("2. Crypto")
        print("3. Reverse")
        print("4. Pwn")
        print("5. Forensics")
        print("6. Web")
        print("7. Misc")
        print("8. Install EVERYTHING")
        print("0. Exit")
        
        choice = input(f"{Colors.GREEN}Enter your choice: {Colors.ENDC}")
        
        if choice == '1': category_menu("Essentials", "essentials")
        elif choice == '2': category_menu("Crypto", "crypto")
        elif choice == '3': category_menu("Reverse", "reverse")
        elif choice == '4': category_menu("Pwn", "pwn")
        elif choice == '5': category_menu("Forensics", "forensics")
        elif choice == '6': category_menu("Web", "web")
        elif choice == '7': category_menu("Misc", "misc")
        elif choice == '8':
            confirm = input(f"{Colors.WARNING}This will install ALL tools from ALL categories. Continue? (y/n): {Colors.ENDC}")
            if confirm.lower() == 'y':
                install_essentials()
                install_crypto()
                install_reverse() 
                install_pwn()
                install_forensics()
                install_web()
                install_misc()
                print_status("All tools installed!", "SUCCESS")
                input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.ENDC}")
        elif choice == '0':
            print("Exiting...")
            break
        else:
            print_status("Invalid choice!", "ERROR")

def main():
    check_sudo()
    
    parser = argparse.ArgumentParser(description="CTF Tools Installer")
    parser.add_argument("--all", action="store_true", help="Install all tools")
    parser.add_argument("--essentials", action="store_true", help="Install essential tools")
    parser.add_argument("--crypto", action="store_true", help="Install crypto tools")
    parser.add_argument("--reverse", action="store_true", help="Install reverse engineering tools")
    parser.add_argument("--pwn", action="store_true", help="Install pwn tools")
    parser.add_argument("--forensics", action="store_true", help="Install forensics tools")
    parser.add_argument("--web", action="store_true", help="Install web tools")
    parser.add_argument("--misc", action="store_true", help="Install misc tools")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        interactive_menu()
        return

    # Ensure pip before CLI args if possible, though specific functions handle it.
    if args.all:
        install_essentials()
        install_crypto()
        install_reverse()
        install_pwn()
        install_forensics()
        install_web()
        install_misc()
        return

    if args.essentials: install_essentials()
    if args.crypto: install_crypto()
    if args.reverse: install_reverse()
    if args.pwn: install_pwn()
    if args.forensics: install_forensics()
    if args.web: install_web()
    if args.misc: install_misc()

if __name__ == "__main__":
    main()
