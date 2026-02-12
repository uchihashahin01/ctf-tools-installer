import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import ctf_installer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Allow CORS just in case, though logically same origin
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# --- Logic Binding ---
def socket_logger(message, status="INFO"):
    socketio.emit('log_message', {'message': message, 'status': status})

# Register the logger
ctf_installer.set_logger(socket_logger)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = [
        {"id": "essentials", "name": "Essentials", "desc": "Docker, Git, Python..."},
        {"id": "crypto", "name": "Crypto", "desc": "SageMath, Z3, PyCrypto"},
        {"id": "reverse", "name": "Reverse", "desc": "Radare2, GDB, Wine, Angr"},
        {"id": "pwn", "name": "Pwn", "desc": "Pwntools, Pwndbg, WABT"},
        {"id": "forensics", "name": "Forensics", "desc": "Binwalk, TShark, OleTools"},
        {"id": "web", "name": "Web", "desc": "Nikto, Gobuster, SQLMap"},
        {"id": "misc", "name": "Misc", "desc": "Nmap, Net-tools"}
    ]
    return jsonify(categories)

@app.route('/api/tools/<category>', methods=['GET'])
def get_tools(category):
    # Returns [(name, type, real_name), ...]
    tools_raw = ctf_installer.get_category_tools(category)
    tools = []
    for item in tools_raw:
        # Check basic installation
        is_installed = ctf_installer.is_tool_installed(item[0], item[1], item[2])
        # Check health if installed
        health = "missing"
        if is_installed:
            health = ctf_installer.check_tool_health(item[0], item[1], item[2])
            
        tools.append({
            "name": item[0],
            "type": item[1],
            "real_name": item[2],
            "installed": is_installed,
            "health": health
        })
    return jsonify(tools)

@app.route('/api/install/category/<category>', methods=['POST'])
def install_category_endpoint(category):
    def run_install():
        socketio.emit('install_start', {'target': category})
        try:
            if category == "essentials": ctf_installer.install_essentials()
            elif category == "crypto": ctf_installer.install_crypto()
            elif category == "reverse": ctf_installer.install_reverse()
            elif category == "pwn": ctf_installer.install_pwn()
            elif category == "forensics": ctf_installer.install_forensics()
            elif category == "web": ctf_installer.install_web()
            elif category == "misc": ctf_installer.install_misc()
            elif category == "all":
                ctf_installer.install_essentials()
                ctf_installer.install_crypto()
                ctf_installer.install_reverse()
                ctf_installer.install_pwn()
                ctf_installer.install_forensics()
                ctf_installer.install_web()
                ctf_installer.install_misc()
            
            socketio.emit('install_complete', {'status': 'success', 'target': category})
        except Exception as e:
            socketio.emit('log_message', {'message': str(e), 'status': 'ERROR'})
            socketio.emit('install_complete', {'status': 'error', 'target': category})

    # Run in background task compatible with eventlet
    socketio.start_background_task(run_install)
    return jsonify({"status": "started", "message": f"Installation started for {category}"})

@app.route('/api/install/tool', methods=['POST'])
def install_tool_endpoint():
    data = request.json
    tool_name = data.get('name')
    tool_type = data.get('type')
    real_name = data.get('real_name')
    
    item_tuple = (tool_name, tool_type, real_name)
    
    def run_install():
        socketio.emit('install_start', {'target': tool_name})
        try:
            ctf_installer.install_item(item_tuple)
            socketio.emit('install_complete', {'status': 'success', 'target': tool_name})
        except Exception as e:
            socketio.emit('log_message', {'message': str(e), 'status': 'ERROR'})
            socketio.emit('install_complete', {'status': 'error', 'target': tool_name})

    socketio.start_background_task(run_install)
    return jsonify({"status": "started", "message": f"Installation started for {tool_name}"})

@app.route('/api/uninstall/tool', methods=['POST'])
def uninstall_tool_endpoint():
    data = request.json
    tool_name = data.get('name')
    tool_type = data.get('type')
    real_name = data.get('real_name')
    
    def run_uninstall():
        socketio.emit('log_message', {'message': f"Uninstalling {tool_name}...", 'status': 'WARNING'})
        try:
            ctf_installer.uninstall_tool(tool_name, tool_type, real_name)
            socketio.emit('log_message', {'message': f"Uninstalled {tool_name}", 'status': 'SUCCESS'})
            # We don't really have a specific event for uninstall complete to update UI yet, 
            # but user can refresh. Or we reuse install_complete with a specific flag.
            socketio.emit('install_complete', {'status': 'success', 'target': tool_name}) 
        except Exception as e:
            socketio.emit('log_message', {'message': str(e), 'status': 'ERROR'})

    socketio.start_background_task(run_uninstall)
    return jsonify({"status": "started", "message": f"Uninstallation started for {tool_name}"})

@app.route('/api/nuke', methods=['POST'])
def nuke_endpoint():
    def run_nuke():
        socketio.emit('log_message', {'message': "INITIATING SYSTEM NUKE...", 'status': 'WARNING'})
        try:
            ctf_installer.nuke_all()
            socketio.emit('log_message', {'message': "SYSTEM NUKE COMPLETE", 'status': 'SUCCESS'})
            # Trigger UI refresh
            socketio.emit('install_complete', {'status': 'success', 'target': 'System Nuke'})
        except Exception as e:
            socketio.emit('log_message', {'message': str(e), 'status': 'ERROR'})

    socketio.start_background_task(run_nuke)
    return jsonify({"status": "started", "message": "Nuke started"})

if __name__ == '__main__':
    # Check sudo
    if os.geteuid() != 0:
        print("Please run with sudo!")
        exit(1)
    
    print("Starting Dashboard on http://localhost:5000")
    # Eventlet is handled by socketio.run
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
