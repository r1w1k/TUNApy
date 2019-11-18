from os import getenv
import requests
import json

class Contact:
	def __init__(self, email):
		self.email = email
		self.properties = self.retrieve()
	
	def retrieve(self):
		url = "https://api.hubspot.com/contacts/v1/contact/email/{}/profile?hapikey={}".format(self.email, getenv("HUBSPOT_API_KEY"))
		response = requests.get(url)
		if response.status_code == 200:
			return response.json()["properties"]
		else:
			return None

	#TODO: I think there's a slicker **kwargs way to do this, but this is fine for now
	def get(self, property):
		if self.properties and self.properties.get(property):
			return self.properties.get(property).get("value")
		else:
			return "ERROR"

# if Hubspot has a contact with this email, it'll update it
# if it doesn't, a new contact will be created
def upsert_contact(email, properties):
	url = "https://api.hubapi.com/contacts/v1/contact/createOrUpdate/email/{}/?hapikey={}".format(email, getenv("HUBSPOT_API_KEY"))
	headers = {"content-type": "application/json"}
	json_request = { "properties": [{ "property": prop["key"], "value": str(prop["value"]) } for prop in properties] }
	return requests.post(url, json=json_request, headers=headers).json()
