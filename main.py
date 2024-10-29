from flask import Flask, request, jsonify
import requests
from xml.etree import ElementTree as ET
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Used to encrypt session data
app.config['SESSION_COOKIE_NAME'] = 'my_session'  # Optional: customize session cookie name

# Transkribus API URLs
TRANSKRIBUS_LOGIN_URL = "https://transkribus.eu/TrpServer/rest/auth/login"
COLLECTIONS_URL = "https://transkribus.eu/TrpServer/rest/collections/list"
UPLOAD_DOCUMENT_URL = "https://transkribus.eu/TrpServer/rest/collections/{collection_id}/upload"
OCR_URL = "https://transkribus.eu/TrpServer/rest/recognition/ocr?collId={collection_id}&id={doc_id}&pages={page_number}"
JOB_STATUS_URL = "https://transkribus.eu/TrpServer/rest/jobs/{job_id}"

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    response = requests.post(TRANSKRIBUS_LOGIN_URL, data={"user": username, "pw": password})

    print(f"Login Response: {response.status_code} {response.text}")  # Log response

    if response.status_code != 200:
        return jsonify({"error": "Login failed", "details": response.text}), response.status_code

    xml_root = ET.fromstring(response.text)
    session_id = xml_root.findtext("sessionId")

    if not session_id:
        print("No session ID found in the response")  # Debugging line
        return jsonify({"error": "Session ID not found in the response"}), 500

    print(f"Session ID stored: {session_id}")  # Log the stored session ID
    return jsonify({"message": "Login successful", "session_id": session_id}), 200


@app.route('/collections', methods=['GET'])
def list_collections():
    session_id = request.args.get("session_id")
    print(f"Current Session ID: {session_id}")  # Log current session ID

    if not session_id:
        print("User not authenticated")  # Log authentication error
        return jsonify({"error": "User not authenticated"}), 403

    headers = {"Cookie": f"JSESSIONID={session_id}"}
    response = requests.get(COLLECTIONS_URL, headers=headers)

    print(f"Collections Response: {response.status_code} {response.text}")  # Log collections response

    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve collections", "details": response.text}), response.status_code

    return jsonify(response.json()), 200


@app.route('/collections/<collection_id>/upload', methods=['POST'])
@app.route('/collections/<collection_id>/<doc_id>/<page_number>/upload', methods=['POST'])
def upload_document(collection_id, doc_id, page_number):
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "User not authenticated"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check the content type of the uploaded file
    if file.content_type not in ["application/xml", "image/jpeg", "image/png"]:  # Add more types as needed
        return jsonify({"error": "Unsupported file type"}), 415

    # Use the correct content type for the upload
    files = {'file': (secure_filename(file.filename), file, file.content_type)}
    headers = {"Cookie": f"JSESSIONID={session_id}"}

    # Set the parameters for the upload request
    params = {
        'status': 'NEW',  # Example status, adjust as needed
        'overwrite': 'false'  # Always set overwrite to false
    }

    response = requests.post(
        f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{doc_id}/{page_number}/text",
        headers=headers,
        files=files,
        params=params
    )

    print(f"Upload Response: {response.status_code} {response.text}")  # Log upload response

    if response.status_code != 200:
        return jsonify({"error": "Document upload failed", "details": response.text}), response.status_code

    return jsonify({"message": "Document uploaded successfully", "doc_id": response.json().get("docId")}), 200


@app.route('/collections/<collection_id>/<doc_id>/<page_number>/ocr', methods=['POST'])
def perform_ocr(collection_id, doc_id, page_number):
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "User not authenticated"}), 403

    headers = {"Cookie": f"JSESSIONID={session_id}"}
    response = requests.post(OCR_URL.format(collection_id=collection_id, doc_id=doc_id, page_number=page_number), headers=headers)

    print(f"OCR Response: {response.status_code} {response.text}")  # Log OCR response

    if response.status_code != 200:
        return jsonify({"error": "OCR job start failed", "details": response.text}), response.status_code

    return jsonify({"message": "OCR job started", "job_id": response.json().get("jobId")}), 200


@app.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "User not authenticated"}), 403

    headers = {"Cookie": f"JSESSIONID={session_id}"}
    response = requests.get(JOB_STATUS_URL.format(job_id=job_id), headers=headers)

    print(f"Job Status Response: {response.status_code} {response.text}")  # Log job status response

    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve job status", "details": response.text}), response.status_code

    return jsonify(response.json()), 200


if __name__ == '__main__':
    app.run(debug=True)
