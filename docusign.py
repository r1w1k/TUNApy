import requests
import json
import base64
import os

template_metadata = {
	"All Documents merge.docx":
	    {
	        "email_message": "Here is FD email message",
	        "email_subject": "MW Final Disclosure",
	        "docusign_name": "Mentorworks Final Disclosure"
	    }
}

class DocusignApi:
	def __init__(self, args):
		self.template = args["template"]
		self.name = args["name"]
		self.email = args["email"]
		self.file_name_path = args["document_file"]
		self.endpoint = "https://" + os.getenv("DS_PLATFORM") + ".docusign.net/restapi/v2/accounts/" + os.getenv("DS_ACCOUNT_ID") + "/envelopes?Content-Type=application/json"

		self.headers = {
			"X-DocuSign-Authentication": "{\"Username\":\"" + os.getenv("DS_USERNAME") + "\",\"Password\":\"" + os.getenv("DS_PASSWORD") + "\",\"IntegratorKey\": \"" + os.getenv("DS_INTEGRATOR_KEY") + "\"}",
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
