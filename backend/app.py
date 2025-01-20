from flask import Flask, request, jsonify, send_file, render_template
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from queue_manager import queue_manager
from printer_manager import printer_manager
from dotenv import load_dotenv
 
 
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_key_for_dev_only")  # Replace for production!
socketio = SocketIO(app, cors_allowed_origins="*")
 
# Configuration
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'gcode', '3mf'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit file size to 10 MB
 
 
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
 
 
# === Routes ===
 
@app.route("/")
def index():
    """Serve the main HTML page."""
    return app.send_static_file("index.html")
 
 
@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads from the client."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
 
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
 
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(filepath)
            return jsonify({"status": "File uploaded successfully", "file_path": filepath}), 200
        except Exception as e:
            return jsonify({"error": f"File saving error: {str(e)}"}), 500
 
    return jsonify({"error": "Invalid file type"}), 400
 
 
#Combine with previous
@app.route("/add-to-queue", methods=["POST"])
def add_to_queue():
    """Add a new print to the queue."""
    data = request.get_json()
    owner = data.get("owner")
    file_path = data.get("file_path")
    estimated_time = data.get("estimated_time")
 
    if not owner or not file_path or not estimated_time:
        return jsonify({"error": "Missing required fields (owner, file_path, estimated_time)"}), 400
 
    try:
        print_id, success = q_man.add_new_print(owner, file_path, estimated_time)
        if success:
            return jsonify({"status": "Print added to queue", "print_id": str(print_id)}), 200
        return jsonify({"error": "Failed to add print to queue"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to add print: {str(e)}"}), 500
 
#No call from client
@app.route("/get-next-print", methods=["GET"])
def get_next_print():
    """Retrieve the next print in the queue."""
    try:
        next_print = q_man.get_next_print()
        if next_print:
            return jsonify({"next_print": q_man.prints[next_print]}), 200
        return jsonify({"error": "No prints in the queue"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to get next print: {str(e)}"}), 500
 
#No call from client
@app.route("/start-print", methods=["POST"])
def start_print():
    """Start a print job on a specific printer."""
    data = request.get_json()
    printer_name = data.get("printer_name")
    filename = data.get("filename")
 
    if not printer_name or not filename:
        return jsonify({"error": "Missing required fields (printer_name, filename)"}), 400
 
    try:
        success = p_man.start_print_on_printer(printer_name, filename)
        if success:
            return jsonify({"status": "Print started successfully"}), 200
        return jsonify({"error": "Failed to start print"}), 500
    except Exception as e:
        return jsonify({"error": f"Start print failed: {str(e)}"}), 500
 
#Client should call with 10 seconds delay,
@app.route("/printer-status", methods=["GET"])
def printer_status():
    """Get the status of all printers."""
    try:
        statuses = p_man.print_states()
        return jsonify(statuses), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get printer statuses: {str(e)}"}), 500
 
#No call from client
@app.route("/upload-to-printer", methods=["POST"])
def upload_to_printer():
    """Upload a file to a specific printer."""
    data = request.get_json()
    printer_name = data.get("printer_name")
    local_file_path = data.get("file_path")
    printer_file_path = data.get("printer_file_path")
 
    if not printer_name or not local_file_path or not printer_file_path:
        return jsonify({"error": "Missing required fields (printer_name, file_path, printer_file_path)"}), 400
 
    try:
        response = p_man.upload_print(printer_name, local_file_path, printer_file_path)
        return jsonify({"status": response}), 200
    except Exception as e:
        return jsonify({"error": f"Upload to printer failed: {str(e)}"}), 500
 
 
# === SocketIO Events ===
 
@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    emit("message", {"data": "Connected to Flask-SocketIO server"})
 
 
def broadcast_printer_status():
    """Broadcast printer statuses to all connected clients."""
    while True:
        try:
            statuses = p_man.print_states()
            socketio.emit("printer_status_update", statuses)
        except Exception as e:
            socketio.emit("error", {"error": str(e)})
        socketio.sleep(5)
 
 
# Start the background thread to broadcast printer statuses
socketio.start_background_task(broadcast_printer_status)
 
 
if __name__ == "__main__":
    # Connect printers on startup (customize as needed)
    # Load environment variables
    load_dotenv()
 
    # Flask and SocketIO setup
 
# Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
 
# Initialize the printer and queue managers
    UID = os.getenv("UID")
    ACCESS_TOKEN = os.getenv("CLOUD_ACCESS_TOKEN")
    REGION = os.getenv("REGION")
    p_man = printer_manager(UID, ACCESS_TOKEN, REGION)
    q_man = queue_manager()
    devices = p_man.get_devices()
    printers_to_connect = [device for device in devices if device["name"]]
    p_man.connect_printers(printers_to_connect)
 
    # Run Flask app with SocketIO
    socketio.run(app, debug=True)