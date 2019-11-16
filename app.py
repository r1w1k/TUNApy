#installed libraries
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response, render_template
from flask_httpauth import HTTPBasicAuth
from os import getenv
from math import floor
from random import random

#custom modules
import docusign
import transunion
import aws
import mw_util

app = Flask(__name__)
auth = HTTPBasicAuth()
load_dotenv()

cachebuster = "?" + str(floor(random()*1000000000))

@app.route("/transunion", methods=["POST"])
def transunion_request():
    return transunion.transunion_request()

@app.route("/mailmerge/create_envelope", methods=["POST", "GET"])
def docusign_request():
    return docusign.docusign_request()

@app.route("/util/hubspot_timestamp", methods=["GET"])
def get_hubspot_timestamp():
    return mw_util.get_hubspot_timestamp()

@app.route("/util/aes/en", methods=["GET"])
def get_encrypted():
    return mw_util.get_encrypted()

@app.route("/util/aes/de", methods=["GET"])
@auth.login_required
def get_decrypted():
    return mw_util.get_decrypted()

@app.route("/s3/upload/<directory>", methods=["POST", "OPTIONS"])
def upload_file(directory):
    return aws.upload_file(directory)

@app.route("/s3/download/<user>/<filename>", methods=["GET", "OPTIONS"])
@auth.login_required
def download_file(user, filename):
    return aws.download_file(user, filename)

@app.route("/uploader", methods=["GET"])
def uploader():
    return render_template("uploader.html", cb=cachebuster)

@app.route("/downloader", methods=["GET"])
def downloader():
    user = request.args["user"]
    file_data = aws.get_file_data(user)
    return render_template("downloader.html", file_data=file_data, cb=cachebuster)

@auth.verify_password
def verify_password(username, password):
    return username == getenv("AUTH_USERNAME") and password == getenv("AUTH_PASSWORD")

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