"""Self-update mechanism using GitHub Releases API."""

import json
import os
import stat
import sys
import urllib.request
import urllib.error
from ctf_tools import __version__, GITHUB_REPO

RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_latest_release() -> dict | None:
    """Fetch latest release info from GitHub. Returns None on failure."""
    try:
        req = urllib.request.Request(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "ctf-tools-installer"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def parse_version(tag: str) -> tuple[int, ...]:
    """'v1.2.3' -> (1, 2, 3)"""
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def check_for_update() -> dict:
    """Returns {'update_available': bool, 'current': str, 'latest': str, 'download_url': str|None, 'release_notes': str}."""
    result = {
        "update_available": False,
        "current": __version__,
        "latest": __version__,
        "download_url": None,
        "release_notes": "",
    }
    release = get_latest_release()
    if not release:
        return result

    latest_tag = release.get("tag_name", "")
    result["latest"] = latest_tag.lstrip("v")
    result["release_notes"] = release.get("body", "")

    try:
        if parse_version(latest_tag) > parse_version(__version__):
            result["update_available"] = True
            # Find the Linux binary asset
            for asset in release.get("assets", []):
                name = asset.get("name", "")
                if "linux" in name.lower() or name == "ctf-tools":
                    result["download_url"] = asset.get("browser_download_url")
                    break
    except (ValueError, TypeError):
        pass

    return result


def perform_update(download_url: str | None = None) -> bool:
    """Download the latest release binary and replace the current executable."""
    if download_url is None:
        info = check_for_update()
        if not info["update_available"]:
            return False
        download_url = info.get("download_url")

    if not download_url:
        return False

    current_exe = os.path.abspath(sys.argv[0])
    tmp_path = current_exe + ".new"

    try:
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "ctf-tools-installer"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        # Make executable
        st = os.stat(tmp_path)
        os.chmod(tmp_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Atomic-ish replace
        backup = current_exe + ".bak"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(current_exe, backup)
        os.rename(tmp_path, current_exe)
        return True
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False
