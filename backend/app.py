from flask import Flask, request, jsonify, session, send_file, render_template, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms, close_room
from flask_session import Session
from msal import ConfidentialClientApplication
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from queue_manager import queue_manager
from printer_manager import printer_manager
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time
from pathlib import Path
import base64
from jwt import decode as jwt_decode, get_unverified_header
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from functools import wraps
from printing_utils import extract_bambulab_estimated_time
from auth import validate_and_decode_jwt

load_dotenv()

 
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_key_for_dev_only")  # Replace for production!
socketio = SocketIO(app, cors_allowed_origins="*")
 
# Configuration
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'gcode', '3mf'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit file size to 10 MB


# MSAL Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = os.getenv("REDIRECT_PATH")
SCOPES = os.getenv("SCOPES")
JWKS_URI = f"{AUTHORITY}/discovery/v2.0/keys"
MICROSOFT_PUBLIC_KEYS = None


msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

 
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
    updated_task_infos = p_man.get_tasks_info()

    for printer_name, printer_info in updated_task_infos.items():
        printer_not_printing: bool = (printer_info["gcode_state"] == "FINISH" 
                                      or printer_info["gcode_state"] == "FAILED" 
                                      or printer_info["gcode_state"] == "IDLE")
        
        printer_plate_is_clean = p_man.printers[printer_name]._plate_clean
        if printer_not_printing and not printer_plate_is_clean:
            
            socketio.emit("request_plate_cleanup", {"msg": f"{printer_name} has status: {printer_info["gcode_state"]}. Please clean plate!", "printer_name": printer_name})


        elif printer_not_printing and printer_plate_is_clean:
            next_print = q_man.get_next_print()


            p_man.printers[printer_name]._currently_printing = {"print_id": None, "owner": None, "filename": None}

            if next_print:
                new_file_path = f'/cache/{q_man.prints[next_print]["file_path"].split("\\")[-1]}'
                
                p_man.upload_print(printer_name, q_man.prints[next_print]["file_path"], f"{new_file_path}")
                # time.sleep(1) Might need to let upload finish 
                print(f"trying to print, {next_print}")
                p_man.start_print_on_printer(printer_name, new_file_path)

                next_print_owner = q_man.prints[next_print]["owner"] 
                next_print_filename = q_man.prints[next_print]["file_path"].split("\\")[-1]
                
                p_man.printers[printer_name]._currently_printing = {"print_id": next_print, "owner": next_print_owner, "filename": next_print_filename}

                file_path_to_delete = Path(q_man.prints[next_print]["file_path"])
                file_path_to_delete.unlink()
                print_not_in_q = q_man.remove_print(next_print)

                if print_not_in_q:
                    print(f"Print, {next_print}, has been removed from queue.")

                p_man.printers[printer_name].plate_clean = False


    socketio.emit("update_printer_times", updated_task_infos)

@scheduler.scheduled_job('interval', seconds=10, kwargs={"q_man": q_man, "p_man":p_man})
def get_printer_states(q_man, p_man):
    tasks_info = p_man.get_tasks_info()

    task_times = {}
    for task_name, task_info in tasks_info.items():
        task_times[task_name] = task_info["time_remaining"]

    prelim_queue = q_man.get_prelim_queue(task_times)

    socketio.emit("prelim_queue", prelim_queue)


# === Routes ===
 
@app.route("/", methods=["GET"])
def index():
    """
    Home page.
    """
    token = session.get("id_token")
    if not token:
        return redirect(url_for("login"))

    try:
        user_info = validate_and_decode_jwt(token)
        return render_template("index.html", user_info=user_info)
    except ValueError:
        return redirect(url_for("login"))
 
@app.route('/about-us', methods=["GET"])
def about_us():
    return render_template('About-us.html')
 
@app.route('/account', methods=["GET"])
def account():
    return render_template('Account.html')

@app.route("/login", methods=["GET"])
def login():
    """
    Redirect to Microsoft Entra ID login page.
    """
    auth_url = msal_app.get_authorization_request_url(
        SCOPES,
        redirect_uri=url_for("auth_callback", _external=True),
    )
    return redirect(auth_url)


@app.route(REDIRECT_PATH)
def auth_callback():
    """ 
    Handle the OAuth callback.
    """
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization failed. No code provided."}), 400

    try:
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPES,
            redirect_uri=url_for("auth_callback", _external=True),
        )

        if "id_token" in result:
            session["access_token"] = result["access_token"]
            session["id_token"] = result.get("id_token")
            print(f"Access Token: {result['id_token'][:50]}...")
            return redirect(url_for("index"))

        return jsonify({"error": "Failed to acquire access token."}), 400

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    logout_url = (
        f"{AUTHORITY}/logout"
        f"?post_logout_redirect_uri={url_for('index', _external=True)}"
    )
    return redirect(logout_url)

 
@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Function to handle file uploads. 
    """

    id_token = session.get("id_token")
    if not id_token:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        decoded_id_token = validate_and_decode_jwt(id_token)
        owner = decoded_id_token.get("email") or decoded_id_token.get("preferred_username") or decoded_id_token.get("sub")
        print(owner)
        if not owner:
            return jsonify({"error": "Unable to determine file owner from ID token"}), 400
    except ValueError as e:
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 401
    

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files["file"]
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
            
            return jsonify({"error": f"File saving error: {str(e)}"}), 500

        try:
            estimated_time = extract_bambulab_estimated_time(filepath_with_uuid)

            file_uuid, _ = q_man.add_new_print(owner, filepath, estimated_time, file_uuid)
            file_data = {"filename": filename, "owner": owner}

            socketio.emit("file_added_to_queue", file_data)
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


@app.route("/cancel/<print_id>", methods=["POST"])
def cancel_print(print_id):
    if print_id in q_man.prints:
        print_in_queue = q_man.prints[print_id]

        # needs to verify that owner sent request

        filepath_to_delete = Path(print_in_queue["file_path"])
        filepath_to_delete.unlink()
        
        q_man.remove_print(print_id)

        return "Print succesfully removed"

    else:
        printer_name, currently_printing, gcode_state = p_man.id_is_printing(print_id)
        if printer_name is False:
            return "print not found"
        
        # Stop print
        plate_clean = p_man.stop_print_on_printers([printer_name])[printer_name]

        # Let the scheduled function handle starting prints
        p_man.printers[printer_name]._plate_clean = plate_clean
        


@app.route("/plate_is_clean/<printer_name>", methods=["POST"])
def plate_clean_confirmation(printer_name):
    """
    Confirm printing plate is clean
    """
    printer_name:str = printer_name.replace("_", " ")

    try:
        p_man.printers[printer_name]._plate_clean = True
        p_man.printers[printer_name]._currently_printing = {"print_id": None, "owner": None, "filename": None}

        socketio.emit("plate_is_clean", {"msg": f"{printer_name}'s plate has been cleaned", "printer_name": printer_name})

        return "Thank You. +500 PrintEzCredit"
    
    except KeyError:
        return "No printer with that name connected", 400
    
    except Exception as e:
        print(f"Something fucked up when recieving plate is clean.\n Error: {e}")
        return f"Something went wrong, no one knows what, heres an error: {e}", 500 
 
 
# === SocketIO Events ===
 
@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    tasks_infos = p_man.get_tasks_info()

    task_times = {}
    for task_name, task_info in tasks_infos.items():
        task_times[task_name] = task_info["time_remaining"]

    prelim_queue = q_man.get_prelim_queue(task_times)
    emit("update_printer_times", tasks_infos)
    emit("prelim_queue", prelim_queue)
 
 
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
 

    devices = p_man.get_devices()
    
    # Decide what printers to connect to, for testing purposes only using one
    printers_to_connect = []
    for device in devices:
        if device["name"][:2] == "S4":
            printers_to_connect.append(device)

    p_man.connect_printers(printers_to_connect)
    time.sleep(1) # Should always do after connecting printers 


    scheduler.start()
 
    # Run Flask app with SocketIO
    socketio.run(app, debug=True, host="localhost")
    time.sleep(1)
    p_man.disconnect_printers()



    ######
    # Note to self, when gcode state is FAILED time remaining isnt reset to 0