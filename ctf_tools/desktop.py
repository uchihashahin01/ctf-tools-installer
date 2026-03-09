"""CTForge Desktop GUI — native window wrapping the web dashboard.

Uses pywebview with the system WebKit2GTK backend (very low RAM usage).
Falls back to opening in the default browser if pywebview is not available.
"""

import os
import socket
import sys
import threading
import time


def _find_free_port() -> int:
    """Find a free TCP port to avoid collisions."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 15.0) -> bool:
    """Block until the Flask server is accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def run_desktop() -> None:
    """Launch CTForge as a desktop GUI application."""
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Start the Flask/SocketIO server in a background thread
    def _start_server():
        # Import here so eventlet monkey-patching happens in the thread
        import eventlet
        eventlet.monkey_patch()
        from ctf_tools.web.app import app, socketio
        socketio.run(app, host="127.0.0.1", port=port, allow_unsafe_werkzeug=True)

    server_thread = threading.Thread(target=_start_server, daemon=True)
    server_thread.start()

    if not _wait_for_server(port):
        print("Failed to start the internal server.", file=sys.stderr)
        raise SystemExit(1)

    # Try native webview window, fall back to browser
    try:
        import webview
        webview.create_window(
            "CTForge",
            url,
            width=1280,
            height=820,
            min_size=(900, 600),
        )
        webview.start(gui="gtk")  # Uses WebKit2GTK on Linux
    except Exception:
        import webbrowser
        print(f"Opening CTForge in your browser at {url}")
        print("Press Ctrl+C to stop the server.")
        webbrowser.open(url)
        try:
            server_thread.join()
        except KeyboardInterrupt:
            pass
