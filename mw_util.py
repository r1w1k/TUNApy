from flask import request
from datetime import datetime, timezone
from os import getenv
from cryptography.fernet import Fernet

#   Hubspot requires the Unix timestamp in milliseconds for any updates to date/datetime fields,
#   and Bubble has trouble with that sort of customization
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

def get_encrypted():
    message = request.args["message"].encode()
    fernet = Fernet(getenv("FERNET_KEY").encode())
    encrypted = fernet.encrypt(message)
    return {
        "encrypted": encrypted.decode()
    }

def get_decrypted():
    message = request.args["message"].encode()
    fernet = Fernet(getenv("FERNET_KEY").encode())
    decrypted = fernet.decrypt(message)
    return {
        "decrypted": decrypted.decode()
    }