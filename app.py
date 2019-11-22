#installed libraries
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response, render_template, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from os import getenv
from math import floor
from random import random

#custom modules
import docusign
import transunion
import aws
import hubspot
import mw_util

print("starting app")
app = Flask(__name__)
print("done starting app")
auth = HTTPBasicAuth()
load_dotenv()

cachebuster = "?" + str(floor(random()*1000000000))

@app.route("/", methods=["GET"])
def root():
    return render_template("base.html")

@app.route("/credit_pull_form/<email>", methods=["GET"])
def credit_pull(email):
    contact = hubspot.Contact(email).properties if email else {}
    return render_template("credit_pull.html", contact=contact)

@app.route("/pull_transunion", methods=["POST"])
def pull_transunion():
    email = transunion.transunion_request(request.form)
    print("redirect to:")
    print(url_for("credit_history", email=email))
    return redirect(url_for("credit_history", email=email))

@app.route("/credit_history/<email>", methods=["GET"])
def credit_history(email):
    contact = hubspot.Contact(email).properties if email else {}
    file_data = aws.get_file_data(email, "credit/")
    return render_template("credit_history.html", email=email, contact=contact, file_data=file_data)

@app.route("/credit_report/<email>/<filename>", methods=["GET"])
def credit_report(email, filename):
    report = transunion.fetch_report(email, filename)
    return render_template("credit_report.html", report=report)

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
    return aws.upload_file_dropzone(directory)

@app.route("/s3/download/<email>/<filepath>", methods=["GET", "OPTIONS"])
@auth.login_required
def download_file(email, filepath):
    return aws.download_file(email, filepath)

@app.route("/uploader", methods=["GET"])
def uploader():
    c = hubspot.Contact(request.args["email"])
    docs = c.properties.get("underwriting_docs_requested", "").split(";")
    return render_template("uploader.html", cb=cachebuster, docs=docs)

@app.route("/downloader", methods=["GET"])
def downloader():
    user = request.args["user"]
    file_data = aws.get_file_data(user)
    return render_template("downloader.html", file_data=file_data, cb=cachebuster)

@app.route("/hubspot/upsert_contact/<email>", methods=["POST"])
def upsert_contact(email):
    properties = request.json["properties"]
    return hubspot.upsert_contact(email, properties)

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