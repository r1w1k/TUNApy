from dotenv import load_dotenv
load_dotenv()

import mimetypes
mimetypes.init()

import html
import os
from io import BytesIO
import time
import boto3
from Transunion import TransunionApi
from docusign import DocusignApi
from mailmerge import MailMerge

from flask import Flask, jsonify, request, Response, send_file, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.wsgi import FileWrapper

from datetime import datetime, timezone
from cryptography.fernet import Fernet

app = Flask(__name__)
auth = HTTPBasicAuth()

@app.route("/transunion", methods=["POST"])
def transunion_request():
    args = request.json
    for key in args:
        args[key] = html.escape(args[key].upper())
    t = TransunionApi(args)
    t.get_request_xml()
    return t.make_request()

@app.route("/mailmerge/create_envelope", methods=["POST", "GET"])
def docusign_request():
    if request.method == "POST":
        filename = create_doc(request.json)
        docusign_params = {
            "name": request.json["docusign_name"],
            "email": request.json["docusign_email"],
            "template": request.json["mailmerge_template"],
            "document_file": filename
        }
        envelope = DocusignApi(docusign_params)
        envelope.build_json()
        os.remove(filename)
        return envelope.callout().json()
    else:
        return Response(status=403)

def create_doc(request_json):
    with MailMerge("./mailmerge_templates/" + request_json["mailmerge_template"]) as document:
        document.merge(**request_json)
        filename = "output" + str(int(time.time() * 100000)) + ".docx"
        document.write(filename)
        return filename
    return "file not found"

#   Hubspot requires the Unix timestamp in milliseconds for any updates to date/datetime fields,
#   and Bubble has trouble with that sort of customization
@app.route("/util/hubspot_timestamp", methods=["GET"])
def get_hubspot_timestamp():
    params = request.args
    year = int(params["year"])
    month = int(params["month"])
    day = int(params["day"])
    try:
        timestamp = int(datetime(year, month, day, 0, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        return {
            "timestamp": timestamp
        }
    except E:
        return {
            "timestamp": 0
        }

@app.route("/util/aes/en", methods=["GET"])
def get_encrypted():
    message = request.args["message"].encode()
    fernet = Fernet(os.getenv("FERNET_KEY").encode())
    encrypted = fernet.encrypt(message)
    return {
        "encrypted": encrypted.decode()
    }

@app.route("/util/aes/de", methods=["GET"])
@auth.login_required
def get_decrypted():
    message = request.args["message"].encode()
    fernet = Fernet(os.getenv("FERNET_KEY").encode())
    decrypted = fernet.decrypt(message)
    return {
        "decrypted": decrypted.decode()
    }

@app.route("/util/s3/upload/<directory>", methods=["POST", "OPTIONS"])
def upload_file(directory):
    if request.method == "POST":
        uploaded_bytes = request.files["file"].read()
        s3_file_path = "dropzone/" + directory + "/" + request.files["file"].filename

        s3 = boto3.client("s3")
        s3_response = s3.put_object(
                        Bucket = os.getenv("S3_BUCKET"),
                        Key=s3_file_path,
                        Body=uploaded_bytes,
                        SSECustomerKey=bytes(os.getenv("S3_KEY").encode()),
                        SSECustomerAlgorithm="AES256")
        return { "message": "file successfully encrypted + uploaded" }

    if request.method == "OPTIONS":
        return { "message": "returning requested CORS headers" }

@app.route("/util/s3/download/<user>/<filename>", methods=["GET", "OPTIONS"])
@auth.login_required
def get_file(user, filename):
    s3 = boto3.client("s3")
    s3_response = s3.get_object(
                    Bucket = os.getenv("S3_BUCKET"),
                    Key = "dropzone/" + user + "/" + filename,
                    SSECustomerKey = bytes(os.getenv("S3_KEY").encode()),
                    SSECustomerAlgorithm = "AES256")
    returned_file = BytesIO(s3_response["Body"].read())

    filename, file_extension = os.path.splitext(filename)
    headers = {"Content-Type": mimetypes.types_map[file_extension]}
    return Response(FileWrapper(returned_file), headers=headers, direct_passthrough=True)

@app.route("/uploader", methods=["GET"])
def uploader():
    return render_template("uploader.html")

def get_file_names(user):
    full_directory = "dropzone/" + user + "/"
    s3 = boto3.client("s3")
    files = s3.list_objects(Bucket=os.getenv("S3_BUCKET"), Prefix=full_directory)["Contents"]
    filenames = [os.path.basename(file["Key"]) for file in files]
    return { "user": user, "files": filenames}

@app.route("/downloader", methods=["GET"])
def downloader():
    user = request.args["user"]
    file_data = get_file_names(user)
    return render_template("downloader.html", file_data=file_data)

@auth.verify_password
def verify_password(username, password):
    return username == os.getenv("AUTH_USERNAME") and password  == os.getenv("AUTH_PASSWORD")

@auth.error_handler
def unauthorized():
    response = jsonify({"status": 401, "error": "unauthorized", "message": "Please authenticate to access this API."})
    response.status_code = 401
    return response

@app.after_request
def add_security_headers(res):
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Headers"] = "cache-control,x-requested-with"
    res.headers["Access-Control-Request-Method"] = "POST"
    return res


if __name__ == "__main__":
    app.run(debug=True)