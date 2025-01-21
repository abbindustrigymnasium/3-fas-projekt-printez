from flask import Flask, request, jsonify, send_file, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms, close_room
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from queue_manager import queue_manager
from printer_manager import printer_manager
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time
from pathlib import Path

from printing_utils import extract_bambulab_estimated_time

load_dotenv()

 
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_key_for_dev_only")  # Replace for production!
socketio = SocketIO(app, cors_allowed_origins="*")
 
# Configuration
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'gcode', '3mf'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit file size to 10 MB


user_rooms = {}

 
scheduler = BackgroundScheduler()
UID = os.getenv("UID")
ACCESS_TOKEN = os.getenv("CLOUD_ACCESS_TOKEN")
REGION = os.getenv("REGION")
p_man = printer_manager(UID, ACCESS_TOKEN, REGION)
q_man = queue_manager()
 
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



# === Scheduled Functions ===

@scheduler.scheduled_job('interval', seconds=10, kwargs={"p_man": p_man, "q_man": q_man})
def emit_new_printer_times(p_man, q_man):
    # socketio.emit("update_printer_times", "Hello")
    updated_task_infos = p_man.get_tasks_info()
    # updated_task_infos["owner"] = q_man.get_owner_of_subtask()
    print(updated_task_infos)
    for printer_name, printer_info in updated_task_infos.items():
        printer_not_printing: bool = (printer_info["gcode_state"] == "FINISH" 
                                      or printer_info["gcode_state"] == "FAILED" 
                                      or printer_info["gcode_state"] == "IDLE" )

        if printer_not_printing and not p_man.printers[printer_name].plate_clean:
            socketio.emit("request_plate_cleanup", f"{printer_name} has status: {printer_info["gcode_state"]}. Please clean plate!", to="queue")

        elif printer_not_printing and p_man.printers[printer_name].plate_clean:
            next_print = q_man.get_next_print()

            if next_print:
                new_file_path = f'/cache/{q_man.prints[next_print]["file_path"].split("\\")[-1]}'
                
                p_man.upload_print(printer_name, q_man.prints[next_print]["file_path"], f"{new_file_path}")
                # time.sleep(1) Might need to let upload finsish 
                print(f"trying to print, {next_print}")
                p_man.start_print_on_printer(printer_name, new_file_path)

                file_path_to_delete = Path(q_man.prints[next_print]["file_path"])
                file_path_to_delete.unlink()
                print_not_in_q = q_man.remove_print(next_print)

                if print_not_in_q:
                    print(f"Print, {next_print}, has been removed from queue.")

                p_man.printers[printer_name].plate_clean = False


    socketio.emit("update_printer_times", updated_task_infos)

@scheduler.scheduled_job('interval', seconds=10, kwargs={"q_man": q_man, "p_man":p_man})
def get_printer_states(q_man, p_man):
    # printer_states = p_man.get_printer_states()
    tasks_info = p_man.get_tasks_info()
    # print(tasks_info)
    task_times = {}
    for task_name, task_info in tasks_info.items():
        task_times[task_name] = task_info["time_remaining"]

    prelim_queue = q_man.get_prelim_queue(task_times)
    print(prelim_queue)
    socketio.emit("prelim_queue", prelim_queue)


# === Routes ===
 
@app.route("/")
def index():
    """Serve the main HTML page."""
    return app.send_static_file("index.html")

 
@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Function to handle file uploads. 
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
 
    file = request.files["file"]
    # print(request.form)
    owner = request.form.get("owner")
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
 
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        # Try to save file to upload dir
        try:
            file_uuid = q_man.get_uuid()
            filepath_parts = filepath.split(".", 2)
            filepath_with_uuid = f".{filepath_parts[1]}_{str(file_uuid)}.{filepath_parts[2]}"

            file.save(filepath_with_uuid)
        
        except Exception as e:
            print(f"Failed to save file, {filename}. Reason: {str(e)}")
            # q_man.remove_print(file_uuid)
            # print("Removed file from queue")
            
            return jsonify({"error": f"File saving error: {str(e)}"}), 500

        try:
            estimated_time = extract_bambulab_estimated_time(filepath_with_uuid)
            file_uuid, _ = q_man.add_new_print(owner, filepath, estimated_time)

            file_data = {"filename": filename, "owner": owner}
            socketio.emit("file_added_to_queue", file_data)

            join_room("queue")

            return jsonify({"status": "File uploaded successfully", "file_path": filepath}), 200

        except Exception as e:
            print(f"Something went wrong adding file, {filename}, to queue. Failed. Error: {str(e)}")
            print(f"Deleting file from server")
            file_to_delete = Path(filepath_with_uuid)
            file_to_delete.unlink()
            if file_to_delete.is_file():
                print("*** WARNING ***")
                print("File not deleted???")

            else:
                print(f"File, {filename}, succcessfully deleted")

            return jsonify({"error": "Unable to add file to queue.", "reason": f"{str(e)}"}), 500
        
    # Needs to be updated when tokens are in use
    # **Ahem, Ahem** (zacke)
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/plate_is_clean/<id>", methods=["POST"])
def plate_clean_confirmation():
    """
    Confirm printing plate is clean
    """
    printer_name:str = id.replace("_", " ")
    p_man.printers[printer_name].clean_plate(True)

    socketio.emit("plate_is_clean", f"{printer_name}'s plate has been cleaned")

    return "Thank You +500 PrinterCredit"
 
 
# === SocketIO Events ===
 
@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    tasks_infos = p_man.get_tasks_info()
    # updated_task_infos["owner"] = q_man.get_owner_of_subtask()
    # print(updated_task_infos)

    task_times = {}
    for task_name, task_info in tasks_infos.items():
        task_times[task_name] = task_info["time_remaining"]

    prelim_queue = q_man.get_prelim_queue(task_times)
    emit("update_printer_times", tasks_infos)
    emit("prelim_queue", prelim_queue)
 
#
# I dont think this will be used, but maybe
#

# def broadcast_printer_status():
#     """Broadcast printer statuses to all connected clients."""
#     while True:
#         try:
#             statuses = p_man.print_states()
#             socketio.emit("printer_status_update", statuses)
#         except Exception as e:
#             socketio.emit("error", {"error": str(e)})
#         socketio.sleep(5)
 
 
 
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
 

    devices = p_man.get_devices()
    
    # Decide what printers to connect to, for testing purposes only using one
    printers_to_connect = []
    for device in devices:
        if device["name"][:2] == "S5":
            printers_to_connect.append(device)

    p_man.connect_printers(printers_to_connect)
    time.sleep(1) # Should always do after connecting printers 

    scheduler.start()
 
    # Run Flask app with SocketIO
    socketio.run(app, debug=True)
    time.sleep(1)
    p_man.disconnect_printers()