from flask import request, Response
from io import BytesIO
from werkzeug.wsgi import FileWrapper
from os import path, getenv
import boto3
import mimetypes
mimetypes.init()

def upload_file(directory):
    if request.method == "POST":
        uploaded_bytes = request.files["file"].read()
        s3_file_path = "dropzone/{}/{}".format(directory, request.files["file"].filename)

        s3 = boto3.client("s3")
        s3_response = s3.put_object(
                        Bucket = getenv("S3_BUCKET"),
                        Key=s3_file_path,
                        Body=uploaded_bytes,
                        SSECustomerKey=bytes(getenv("S3_KEY").encode()),
                        SSECustomerAlgorithm="AES256")
        return { "message": "file successfully encrypted + uploaded" }

    if request.method == "OPTIONS":
        return { "message": "returning requested CORS headers" }

def download_file(user, filename):
    s3 = boto3.client("s3")
    s3_response = s3.get_object(
                    Bucket = getenv("S3_BUCKET"),
                    Key = "dropzone/{}/{}".format(user, filename),
                    SSECustomerKey = bytes(getenv("S3_KEY").encode()),
                    SSECustomerAlgorithm = "AES256")
    returned_file = BytesIO(s3_response["Body"].read())

    filename, file_extension = path.splitext(filename)
    headers = {"Content-Type": mimetypes.types_map[file_extension]}
    return Response(FileWrapper(returned_file), headers=headers, direct_passthrough=True)

def get_file_data(user):
    user_directory = "dropzone/{}/".format(user)
    s3 = boto3.client("s3")
    files = s3.list_objects(Bucket=getenv("S3_BUCKET"), Prefix=user_directory)["Contents"]
    filenames = [path.basename(file["Key"]) for file in files]
    return { "user": user, "files": filenames}

def delete_file(user, filename):
    return "deleted"