from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random
import os
import shutil

app = Flask(__name__)
 
# Configuration
app.secret_key = "fallback_key_for_dev_only"  # Use a secure key for production!
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'gcode', '3mf'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit file size to 10 MB
 
# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
 
 
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
 
 
@app.route("/")
def index():
    return app.send_static_file("index.html")
 
 
@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
 
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
 
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
       
        try:
            # Save the file temporarily
            file.save(filepath)
 
            # Placeholder for processing the file (currently logs success)
            # e.g., send the file to another service or system
            print(f"File '{filename}' received and logged successfully.")
 
            # Remove the file after processing
            os.remove(filepath)
            return jsonify({"status": "File uploaded and processed successfully"}), 200
 
        except Exception as e:
            # Log errors (placeholder for logging)
            return jsonify({"error": f"File processing error: {str(e)}"}), 500
 
    return jsonify({"error": "Invalid file type"}), 400
 
@app.route("/cancel", methods=["POST"])
def cancel_print():
    """Handle cancellation of a print job."""
    try:
        data = request.get_json()
        print_id = data.get("printId")

        if not print_id:
            return jsonify({"error": "Print ID is required"}), 400

        # Log or handle the cancellation action
        print(f"Cancellation received for Print ID: {print_id}")

        # Optionally, update the state of the print job in your backend logic or database

        return jsonify({"status": f"Print ID {print_id} canceled successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle large file uploads."""
    return jsonify({"error": "File too large. Maximum size is 10MB."}), 413
 

"""
Comment by Samuel
Increadibly unsafe???
A user shouldt decide what file to delete???
"""
@app.route("/remove", methods=["POST"])
def remove_file():
    """Handle file removal from the queue."""
    data = request.get_json()
    filename = data.get("filename")
 
    if not filename:
        return jsonify({"error": "Filename is required"}), 400
 
    # Log the removal for now (or implement further logic if needed)
    print(f"File '{filename}' removed from the queue.")
    return jsonify({"status": f"File '{filename}' removed successfully."}), 200
 
"""
Comment by Samuel:
Why would a user have access to this functionality???
"""
@app.route("/cleanup", methods=["POST"])
def cleanup_uploads():
    """Utility to clean up the upload folder (optional endpoint for maintenance)."""
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        return jsonify({"status": "Upload folder cleaned."}), 200
    except Exception as e:
        return jsonify({"error": f"Cleanup failed: {str(e)}"}), 500


@app.route("/status", methods=['GET'])
def get_status():
    """Send dummy status and a randomly generated countdown time."""
    try:
        random_minutes = random.randint(5, 120)  # Random minutes between 1 and 120
        generated_time = datetime.utcnow() + timedelta(minutes=random_minutes)

        current_time = datetime.utcnow()
        time_left_seconds = int((generated_time - current_time).total_seconds())

        status_data = {
            "status": "Processing completed successfully",
            "total_seconds": time_left_seconds,
            "generated_time": generated_time.isoformat()
        }

        return jsonify(status_data), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/takeout", methods=["POST"])
def takeout():
    data = request.get_json()
    print_id = data.get("printId")
    if not print_id:
        return jsonify({"error": "Print ID is required"}), 400
    
    # Log or perform an action for the takeout request
    print(f"Takeout action confirmed for Print ID: {print_id}")
    return jsonify({"status": "Takeout action received successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
 
 