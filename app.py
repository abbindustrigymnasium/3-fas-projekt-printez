from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms, close_room
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from backend.queue_manager import queue_manager
from backend.printer_manager import printer_manager
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time
from pathlib import Path
from jwt import decode as jwt_decode, get_unverified_header
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from functools import wraps
import requests
import base64
from msal import ConfidentialClientApplication
from flask_session import Session
from backend.printing_utils import extract_bambulab_estimated_time

load_dotenv()
 
app = Flask(__name__)
app.secret_key = "your-secret-key" 
socketio = SocketIO(app, cors_allowed_origins="*")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
 
# Configuration
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'gcode', '3mf'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit file size to 10 MB
#app.config["SESSION_COOKIE_SECURE"] = True  # Use HTTPS
#app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access
#app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Limit cross-origin use

user_rooms = {}
scheduler = BackgroundScheduler()
UID = os.getenv("UID")
ACCESS_TOKEN = os.getenv("CLOUD_ACCESS_TOKEN")
REGION = os.getenv("REGION")
p_man = printer_manager(UID, ACCESS_TOKEN, REGION)
q_man = queue_manager()

# MSAL Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/auth/callback"
SCOPES = ["email", "User.Read"]
JWKS_URI = f"{AUTHORITY}/discovery/v2.0/keys"
MICROSOFT_PUBLIC_KEYS = None


# MSAL Confidential Client
msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)


# === Helper functions ===

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def jwk_to_rsa_key(jwk):
    n = int.from_bytes(base64.urlsafe_b64decode(jwk["n"] + "=="), "big")
    e = int.from_bytes(base64.urlsafe_b64decode(jwk["e"] + "=="), "big")
    return rsa.RSAPublicNumbers(e, n).public_key(default_backend())


def get_public_keys():
    global MICROSOFT_PUBLIC_KEYS
    if MICROSOFT_PUBLIC_KEYS is None:
        response = requests.get(JWKS_URI)
        response.raise_for_status()
        MICROSOFT_PUBLIC_KEYS = response.json()["keys"]
    return MICROSOFT_PUBLIC_KEYS


def validate_and_decode_jwt(token):
    try:
        # Decode without signature verification for debugging
        unverified_token = jwt_decode(token, options={"verify_signature": False})
        print(f"Unverified token claims: {unverified_token}")

        # Fetch and match the JWKS keys
        get_public_keys()
        unverified_header = get_unverified_header(token)
        rsa_key = None

        for key in MICROSOFT_PUBLIC_KEYS:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = jwk_to_rsa_key(key)
                break

        if not rsa_key:
            raise ValueError("Unable to find a matching key for token validation.")

        # Decode and validate the token
        decoded_token = jwt_decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"{AUTHORITY}/v2.0",
        )
        print(f"Decoded token: {decoded_token}")
        return decoded_token

    except ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


# === Decorators ===
def authorized(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("id_token")
        if not token:
            return redirect(url_for("login"))

        try:
            validate_and_decode_jwt(token)
        except ValueError as e:
            return jsonify({"error": f"Unauthorized: {str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated_function



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
    token = session.get("id_token")
    if not token:
        return redirect(url_for("login"))

    try:
        user_info = validate_and_decode_jwt(token)
        return render_template("index.html", user_info=user_info)
    except ValueError:
        return redirect(url_for("login"))


@app.route("/login")
def login():
    auth_url = msal_app.get_authorization_request_url(
        SCOPES,
        redirect_uri=url_for("auth_callback", _external=True),
    )
    return redirect(auth_url)


@app.route(REDIRECT_PATH)
def auth_callback():
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


@app.route("/logout")
def logout():
    session.clear()
    logout_url = (
        f"{AUTHORITY}/logout"
        f"?post_logout_redirect_uri={url_for('index', _external=True)}"
    )
    return redirect(logout_url)
 
@app.route('/about-us')
def about_us():
    return render_template('About-us.html')
 
@app.route('/account')
def account():
    return render_template('Account.html')
 
@app.route("/upload", methods=["POST"])
@authorized
def upload_file():
    """
    Handle file uploads and associate them with the authenticated user.
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

    # File upload logic remains the same
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_uuid = q_man.get_uuid()
        filename_with_uuid = f"{os.path.splitext(filename)[0]}_{file_uuid}{os.path.splitext(filename)[1]}"
        filepath_with_uuid = os.path.join(app.config["UPLOAD_FOLDER"], filename_with_uuid)

        try:
            file.save(filepath_with_uuid)
        except Exception as e:
            return jsonify({"error": f"File saving error: {str(e)}"}), 500

        try:
            estimated_time = extract_bambulab_estimated_time(filepath_with_uuid)
            file_uuid, _ = q_man.add_new_print(owner, filepath_with_uuid, estimated_time)

            file_data = {"filename": filename_with_uuid, "owner": owner}
            print(file_data)
            print(owner)
            socketio.emit("file_added_to_queue", file_data, to="queue")
            return jsonify({"status": "File uploaded successfully", "filename": file.filename, "uuid": file_uuid}), 200

        except Exception as e:
            Path(filepath_with_uuid).unlink(missing_ok=True)
            return jsonify({"error": "Unable to add file to queue", "reason": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/cancel_print/<print_id>", methods=["POST"])
def cancel_print(print_id):
    id_token = session.get("id_token")
    if not id_token:
        return jsonify({"error": "User not authenticated"}), 401
    print(print_id)
    try:
        decoded_id_token = validate_and_decode_jwt(id_token)
        owner_email = decoded_id_token.get("email")
        if not owner_email:
            return jsonify({"error": "Unable to determine file owner from ID token"}), 400
    except ValueError as e:
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 401
    print("HERE PRINTING SAMUEL")
    print(q_man.prints)
    if print_id in q_man.prints:
        print_in_queue = q_man.prints[print_id]
        file_owner = print_in_queue.get("owner")

        if owner_email != file_owner:
            return jsonify({"error": "Unauthorized action, only the file owner can delete it"}), 403

        # Proceed with deleting the file and removing the print
        filepath_to_delete = Path(print_in_queue["file_path"])
        filepath_to_delete.unlink()

        q_man.remove_print(print_id)
        print("here")


        return "Print successfully removed"

    else:
        # If the print_id is not found in the queue, check other status
        printer_name, currently_printing, gcode_state = p_man.id_is_printing(print_id)
        if printer_name is False:
            return "Print not found"
        
        # Stop the print if it's currently printing
        plate_clean = p_man.stop_print_on_printers([printer_name])[printer_name]

        # Let the scheduled function handle starting prints
        p_man.printers[printer_name]._plate_clean = plate_clean
        return "Print successfully canceled"



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
    # id_token = data.get("id_token")
    # try:
    #     decoded_token = validate_and_decode_jwt(id_token)
    join_room("queue")
    #     emit("message", "You have joined the room.")
    # except ValueError as e:
    #     emit("error", {"error": str(e)})

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
    socketio.run(app, host="localhost", debug=True)
    time.sleep(1)
    p_man.disconnect_printers()