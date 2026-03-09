"""Flask web dashboard for CTF Tools Installer."""

import os
import sys

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from ctf_tools import __version__
from ctf_tools import core
from ctf_tools.updater import check_for_update

# Resolve paths so PyInstaller frozen builds find templates/static
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(_base, "templates"),
    static_folder=os.path.join(_base, "static"),
)
app.config["SECRET_KEY"] = os.urandom(24).hex()
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")


# --- Logger binding -------------------------------------------------------

def _socket_logger(message: str, status: str = "INFO") -> None:
    socketio.emit("log_message", {"message": message, "status": status})

core.set_logger(_socket_logger)


# --- Routes ---------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", version=__version__)


@app.route("/api/version")
def api_version():
    return jsonify({"version": __version__})


@app.route("/api/check-update")
def api_check_update():
    return jsonify(check_for_update())


@app.route("/api/categories")
def get_categories():
    return jsonify(core.CATEGORIES)


@app.route("/api/tools/<category>")
def get_tools(category):
    tools_raw = core.get_category_tools(category)
    tools = []
    for name, type_, real_name in tools_raw:
        installed = core.is_tool_installed(name, type_, real_name)
        health = core.check_tool_health(name, type_, real_name) if installed else "missing"
        tools.append({
            "name": name,
            "type": type_,
            "real_name": real_name,
            "installed": installed,
            "health": health,
        })
    return jsonify(tools)


@app.route("/api/install/category/<category>", methods=["POST"])
def install_category_endpoint(category):
    def run_install():
        socketio.emit("install_start", {"target": category})
        try:
            if category == "all":
                core.install_all()
            else:
                core.install_category(category)
            socketio.emit("install_complete", {"status": "success", "target": category})
        except Exception as e:
            socketio.emit("log_message", {"message": str(e), "status": "ERROR"})
            socketio.emit("install_complete", {"status": "error", "target": category})

    socketio.start_background_task(run_install)
    return jsonify({"status": "started", "message": f"Installation started for {category}"})


@app.route("/api/install/tool", methods=["POST"])
def install_tool_endpoint():
    data = request.json
    tool_name = data.get("name")
    tool_type = data.get("type")
    real_name = data.get("real_name")
    item_tuple = (tool_name, tool_type, real_name)

    def run_install():
        socketio.emit("install_start", {"target": tool_name})
        try:
            core.install_item(item_tuple)
            socketio.emit("install_complete", {"status": "success", "target": tool_name})
        except Exception as e:
            socketio.emit("log_message", {"message": str(e), "status": "ERROR"})
            socketio.emit("install_complete", {"status": "error", "target": tool_name})

    socketio.start_background_task(run_install)
    return jsonify({"status": "started", "message": f"Installation started for {tool_name}"})


@app.route("/api/uninstall/tool", methods=["POST"])
def uninstall_tool_endpoint():
    data = request.json
    tool_name = data.get("name")
    tool_type = data.get("type")
    real_name = data.get("real_name")

    def run_uninstall():
        socketio.emit("log_message", {"message": f"Uninstalling {tool_name}…", "status": "WARNING"})
        try:
            core.uninstall_tool(tool_name, tool_type, real_name)
            socketio.emit("log_message", {"message": f"Uninstalled {tool_name}", "status": "SUCCESS"})
            socketio.emit("install_complete", {"status": "success", "target": tool_name})
        except Exception as e:
            socketio.emit("log_message", {"message": str(e), "status": "ERROR"})

    socketio.start_background_task(run_uninstall)
    return jsonify({"status": "started", "message": f"Uninstallation started for {tool_name}"})


@app.route("/api/nuke", methods=["POST"])
def nuke_endpoint():
    def run_nuke():
        socketio.emit("log_message", {"message": "INITIATING SYSTEM NUKE…", "status": "WARNING"})
        try:
            core.nuke_all()
            socketio.emit("log_message", {"message": "SYSTEM NUKE COMPLETE", "status": "SUCCESS"})
            socketio.emit("install_complete", {"status": "success", "target": "System Nuke"})
        except Exception as e:
            socketio.emit("log_message", {"message": str(e), "status": "ERROR"})

    socketio.start_background_task(run_nuke)
    return jsonify({"status": "started", "message": "Nuke started"})


def run_web(port: int = 5000) -> None:
    """Start the web dashboard."""
    if not core.check_sudo():
        print("Please run with sudo!")
        raise SystemExit(1)
    print(f"Starting Dashboard on http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
