from dotenv import load_dotenv
load_dotenv()

import html
import os
import time
from Transunion import TransunionApi
from docusign import DocusignApi
from mailmerge import MailMerge
from flask import Flask, jsonify, request, Response
from datetime import datetime, timezone
from cryptography.fernet import Fernet

app = Flask(__name__)

@app.route('/transunion', methods=['POST'])
def transunion_request():
	args = request.json
	for key in args:
		args[key] = html.escape(args[key].upper())
	t = TransunionApi(args)
	t.get_request_xml()
	return t.make_request()

@app.route('/mailmerge/create_envelope', methods=['POST', 'GET'])
def docusign_request():
    if request.method == 'POST':
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

# 	Hubspot requires the Unix timestamp in milliseconds for any updates to date/datetime fields,
# 	and Bubble has trouble with that sort of customization
@app.route('/util/hubspot_timestamp', methods=['GET'])
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

@app.route('/util/aes/en', methods=['GET'])
def get_encrypted():
    message = request.args["message"].encode()
    f = Fernet(os.getenv("FERNET_KEY").encode())
    encrypted = f.encrypt(message)
    return {
        "encrypted": encrypted.decode()
    }

@app.route('/util/aes/de', methods=['GET'])
def get_decrypted():
    message = request.args["message"].encode()
    f = Fernet(os.getenv("FERNET_KEY").encode())
    decrypted = f.decrypt(message)
    return {
        "decrypted": decrypted.decode()
    }

if __name__ == '__main__':
    app.run(debug=True)