from flask import request, Response
from io import BytesIO
from werkzeug.wsgi import FileWrapper
from os import path, getenv
import boto3
import mimetypes
mimetypes.init()

def upload_file_dropzone(directory):
    if request.method == "POST":
        uploaded_bytes = request.files["file"].read()
        filename = request.files["file"].filename
        return do_upload(directory, filename, uploaded_bytes)

    if request.method == "OPTIONS":
        return { "message": "returning requested CORS headers" }

def do_upload(directory, filename, body):
    s3_file_path = "MentorWorks/{}/{}".format(directory, filename)
    s3 = boto3.client("s3")
    s3_response = s3.put_object(
        Bucket = getenv("S3_BUCKET"),
        Key=s3_file_path,
        Body=body,
        SSECustomerKey=bytes(getenv("S3_KEY").encode()),
        SSECustomerAlgorithm="AES256")
    return { "message": "file successfully encrypted + uploaded" }

def download_file(email, filepath, raw=False):
    s3 = boto3.client("s3")
    s3_response = s3.get_object(
        Bucket = getenv("S3_BUCKET"),
        Key = "MentorWorks/{}/{}".format(email, filepath),
        SSECustomerKey = bytes(getenv("S3_KEY").encode()),
        SSECustomerAlgorithm = "AES256")
    
    if raw:
        return s3_response["Body"]
    else:
        returned_file = BytesIO(s3_response["Body"].read())

        filename, file_extension = path.splitext(filepath)
        mimetype = mimetypes.types_map[file_extension]
        headers = {"Content-Type": mimetype}
        if mimetype == "application/xml":
            headers["Content-Disposition"] = "attachment"
        return Response(FileWrapper(returned_file), headers=headers, direct_passthrough=True)

def get_file_data(email, subdirectory=""):
    contact_directory = "MentorWorks/{}/{}".format(email, subdirectory)
    s3 = boto3.client("s3")
    files = s3.list_objects(Bucket=getenv("S3_BUCKET"), Prefix=contact_directory)["Contents"]
    filenames = [path.basename(file["Key"]) for file in files]
    return { "email": email, "files": filenames}

def delete_file(user, filename):
    #TODO: this
    return "deleted"