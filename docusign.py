from flask import request
from mailmerge import MailMerge

import requests
import json
import base64
import time
from datetime import date
from os import getenv, remove

#TODO: Figure out how to store the template info in a more open-sourcey way
template_metadata = {
	"isa_full.docx":
	    {
	        "email_message": "PLACHOLDER email message",
	        "email_subject": "PLACHOLDER Email Subject",
	        "docusign_name": "PLACHOLDER Document Name"
	    }
}

class DocusignApi:
	def __init__(self, args):
		self.template = args["template"]
		self.name = args["name"]
		self.email = args["email"]
		self.file_name_path = args["document_file"]
		self.endpoint = "https://" + getenv("DS_PLATFORM") + ".docusign.net/restapi/v2/accounts/" + getenv("DS_ACCOUNT_ID") + "/envelopes?Content-Type=application/json"

		self.headers = {
			"X-DocuSign-Authentication": "{\"Username\":\"" + getenv("DS_USERNAME") + "\",\"Password\":\"" + getenv("DS_PASSWORD") + "\",\"IntegratorKey\": \"" + getenv("DS_INTEGRATOR_KEY") + "\"}",
			"Content-Type": "application/json"
		}

	def callout(self):
		res = requests.post(self.endpoint, headers = self.headers, json = self.json_data)
		print("Docusign response: ")
		print(res.content)
		return res

	def build_json(self):
		metadata = template_metadata[self.template]
		document = {
			"documentId": "1",
			"name": metadata["docusign_name"],
			"fileExtension": "docx",
			"documentBase64": self.get_base64_doc()
		}

		eventNotification = {
			"url": "listener",
			"includeCertificateOfCompletion": "false",
			"includeDocuments": "true",
			"includeDocumentFields": "true",
			"requireAcknowledgment": "true",
			"envelopeEvents": [{
				"envelopeEventStatusCode": "completed"
			}]
		}

		json_signers = []
		for i in range(0, 1):
			signHereTab = {
				"documentId": "1",
				"recipientId": str(i + 1),
				"anchorString": "conventional tuition",
				"anchorXOffset": "0",
				"anchorYOffset": "0"
			}

			dateSignedTab = {
				"documentId": "1",
				"recipientId": str(i + 1),
				"anchorString": "/d2/",
				"anchorXOffset": "0",
				"anchorYOffset": "0"
			}

			signer = {
				"tabs": {
					"signHereTabs": [signHereTab],
					"dateSignedTabs": [dateSignedTab]
				},
				"name": self.name,
				"email": self.email,
				"recipientId": str(i + 1),
				"clientUserId": "1000"
			}
			json_signers.append(signer)

		self.json_data = {
			"documents": [document],
			"eventNotification": eventNotification,
			"status": "sent",
			"emailSubject": metadata["email_subject"],
			"emailBlurb": metadata["email_message"],
			"recipients": {
				"signers" : json_signers
			}
		}
		return json.dumps(self.json_data)

	def get_base64_doc(self):
		with open(self.file_name_path, "rb") as file:
		    content_bytes = file.read()
		return base64.b64encode(content_bytes).decode('ascii')

def create_doc(request_json):
	dates_added = calculate_payment_dates(request_json)
	with MailMerge("./mailmerge_templates/" + dates_added["mailmerge_template"]) as document:
		document.merge(**request_json)
		filename = "output" + str(int(time.time() * 100000)) + ".docx"
		document.write(filename)
		return filename
	return "file not found"

def calculate_payment_dates(request_json):
	grad_month = int(request_json["graduation_month"])
	grad_year = int(request_json["graduation_year"])

	payment_yr_1_month = grad_month + 4 if grad_month + 4 <= 12 else (grad_month + 4)%12
	payment_yr_1_year = grad_year + int((grad_month + 4)/12)

	grace_period_start = date(grad_year, grad_month, 1)
	payment_yr_1 = date(payment_yr_1_year, payment_yr_1_month, 1)
	payment_yr_2 = date(payment_yr_1_year + 1, payment_yr_1_month, 1)
	payment_yr_3 = date(payment_yr_1_year + 2, payment_yr_1_month, 1)
	payment_yr_4 = date(payment_yr_1_year + 3, payment_yr_1_month, 1)
	payment_yr_5 = date(payment_yr_1_year + 4, payment_yr_1_month, 1)

	request_json["grace_period_start_Date"] = grace_period_start.strftime('%m/%d/%Y')
	request_json["yr_1_pmt_cap_date"] = payment_yr_1.strftime('%m/%d/%Y')
	request_json["yr_2_pmt_cap_date"] = payment_yr_2.strftime('%m/%d/%Y')
	request_json["yr_3_pmt_cap_date"] = payment_yr_3.strftime('%m/%d/%Y')
	request_json["yr_4_pmt_cap_date"] = payment_yr_4.strftime('%m/%d/%Y')
	request_json["yr_5_pmt_cap_date"] = payment_yr_5.strftime('%m/%d/%Y')

	return request_json

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
        remove(filename)
        return envelope.callout().json()
    else:
        return Response(status=403)
