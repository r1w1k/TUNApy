from lxml import etree as ET
from os import getenv
from flask import request
from io import BytesIO
from datetime import datetime
import requests
import html
import aws
import re

ns0 = '{http://www.netaccess.transunion.com/namespace}'
ns1 = '{http://www.transunion.com/namespace}'

def transunion_request(form):
    t = TransunionApi(form)
    t.get_request_xml()
    t.make_request()
    return form.get("email")

def not_none(text, fallback=""):
	return text if text else fallback

#This class makes dealing with etree syntax/namespacing a lot cleaner as long as you're only reading values, not modifying them in the DOM
#The error handling also lets you search for values in the DOM with impunity + without worrying about whether they exist or not
#Note: all child elements need to belong to the same xml namespace for this to work.
class XmlWrapper:
	def __init__(self, namespace, root, found=True):
		self.node = root
		self.found = found
		self.text = None if not found else root.text
		self.namespace = namespace

	def find(self, child_tag_name):
		if not self.found:
			return XmlWrapper(self.namespace, None, False)
		try:
			return XmlWrapper(self.namespace, self.node.find(f'{self.namespace}{child_tag_name}'))
		except:
			return XmlWrapper(self.namespace, None, False)

	def find_all(self, child_tag_name):
		if not self.found:
			return [XmlWrapper(self.namespace, None, False)]
		try:
			return [ XmlWrapper(self.namespace, wrapper) for wrapper in self.node.findall(f'{self.namespace}{child_tag_name}')]
		except:
			return [XmlWrapper(self.namespace, None, False)]

class TransunionApi:
	def __init__(self,form):
		self.email = form.get("email")
		self.firstname = form.get("firstname", "")
		self.middlename = form.get("middlename", "")
		self.lastname = form.get("lastname", "")
		self.address = form.get("address", "")
		self.city = form.get("city", "")
		self.state = form.get("state", "")
		self.zip = form.get("zip", "")
		self.dob = form.get("dob", "")
		self.ssn = re.sub(r"[^0-9]", "", form.get("ssn", ""))

	def get_request_xml(self):
		parser = ET.XMLParser(remove_blank_text=True)
		tree = ET.parse('./transunion_request_template.xml', parser)
		root = tree.getroot()

		root.find(f'{ns0}systemId').text = getenv("SYSTEM_ID")
		root.find(f'{ns0}systemPassword').text = getenv("SYSTEM_PW")

		creditBureau = root.find(f'{ns0}productrequest').find(f'{ns1}creditBureau')
		
		transactionControl = creditBureau.find(f'{ns1}transactionControl')
		product = creditBureau.find(f'{ns1}product')
		permissiblePurpose = product.find(f'{ns1}permissiblePurpose')
		subject = product.find(f'{ns1}subject').find(f'{ns1}subjectRecord').find(f'{ns1}indicative')
		subjectName = subject.find(f'{ns1}name').find(f'{ns1}person')
		subjectAddress = subject.find(f'{ns1}address')
		subjectLocation = subjectAddress.find(f'{ns1}location')

		subscriber = transactionControl.find(f'{ns1}subscriber')
		options = transactionControl.find(f'{ns1}options')
		clientVendorSoftware = transactionControl.find(f'{ns1}clientVendorSoftware')
		vendor = clientVendorSoftware.find(f'{ns1}vendor')

		subscriber.find(f'{ns1}industryCode').text = getenv("INDUSTRY_CODE")
		subscriber.find(f'{ns1}memberCode').text = getenv("MEMBER_CODE")
		subscriber.find(f'{ns1}inquirySubscriberPrefixCode').text = getenv("MARKET") + getenv("SUBMARKET")
		subscriber.find(f'{ns1}password').text = getenv("PASSWORD")

		options.find(f'{ns1}processingEnvironment').text = getenv("ENVIRONMENT")

		vendor.find(f'{ns1}id').text = getenv("VENDOR_ID")
		vendor.find(f'{ns1}name').text = getenv("VENDOR_NAME")

		software = clientVendorSoftware.find(f'{ns1}software')
		software.find(f'{ns1}name').text = getenv("SOFTWARE_NAME")
		software.find(f'{ns1}version').text = getenv("SOFTWARE_VERSION")

		permissiblePurpose.find(f'{ns1}code').text = getenv("PERMISSIBLE_PURPOSE")
		permissiblePurpose.find(f'{ns1}endUser').find(f'{ns1}unparsed').text = getenv("END_USER")

		subjectName.find(f'{ns1}first').text = self.firstname
		subjectName.find(f'{ns1}middle').text = self.middlename
		subjectName.find(f'{ns1}last').text = self.lastname
		subjectAddress.find(f'{ns1}street').find(f'{ns1}unparsed').text = self.address
		subjectLocation.find(f'{ns1}city').text = self.city
		subjectLocation.find(f'{ns1}state').text = self.state
		subjectLocation.find(f'{ns1}zipCode').text = self.zip

		subjectSSN = subject.find(f'{ns1}socialSecurity')
		subjectSSN.find(f'{ns1}number').text = self.ssn

		self.xml_request = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
		return self.xml_request

	def make_request(self):
		uri = getenv("TURI")
		certs = (getenv("CERTIFICATE_PATH"), getenv("KEY_PATH"))
		r = requests.post(uri, headers = {'Content-Type': 'application/xml'}, data=self.xml_request, cert = certs, verify=False)
		self.xml_response = r.text
		return self.secure_upload()

	def secure_upload(self):
		print(self.xml_response)
		encoded = bytes(self.xml_response.encode())
		#do this first so that we retain a copy of the file, regardless of what happens afterwards
		if self.email:
			filename = "{}.xml".format(datetime.now().strftime("%Y_%b_%d_%H_%M_%S"))
			print(filename)
			aws.do_upload("{}/credit".format(self.email), filename, encoded)



def fetch_report(email, filename):
	return parse_response(aws.download_file(email, "credit/{}".format(filename), True))

def parse_response(xml_file):
	#the goal here is to turn the XML into something JSON-compatible that can be rendered nicely on the front end
	root = XmlWrapper(ns1, ET.parse(xml_file).getroot())

	#Parse out all the stuff we care about into variables
	subject = root.find("product").find("subject")
	subject_record = subject.find("subjectRecord")

	file_summary = subject_record.find("fileSummary")
	file_hit_indicator = file_summary.find("fileHitIndicator")
	ssn_match = file_summary.find("ssnMatchIndicator")
	consumer_statement = file_summary.find("consumerStatementIndicator")

	credit_data_status = file_summary.find("creditDataStatus")
	freeze = credit_data_status.find("freeze").find("indicator")
	is_minor = credit_data_status.find("minor")

	indicative = subject_record.find("indicative")
	names = indicative.find_all("name")
	addresses = indicative.find_all("address")
	employment_records = indicative.find_all("employment")
	dob = indicative.find("dateOfBirth")

	credit_info = subject_record.find("custom").find("credit")
	tradelines = credit_info.find_all("trade")
	inquiries = credit_info.find_all("inquiry")

	#used to identify tradelines whose rating code is 02 through 09, which are various forms of derogatory
	past_due_regex = re.compile("0[2-9]")

	#and now put this all into a format that a front-end template will like working with
	json_report = {
		"hit": file_hit_indicator.text,
		"ssn_match": not_none(ssn_match.text, "Unknown"),
		"consumer_statement": consumer_statement.text,
		"freeze": freeze.text == "true",
		"is_minor": is_minor.text,
		"names": [
			{ 
				"first": not_none(name.find("person").find("first").text),
				"last": not_none(name.find("person").find("last").text)
			} for name in names
		],
		"addresses": [
			{
				"number": not_none(address.find("street").find("number").text),
				"predirectional": not_none(address.find("street").find("preDirectional").text),
				"street": not_none(address.find("street").find("name").text),
				"type": not_none(address.find("street").find("type").text),
				"city": not_none(address.find("location").find("city").text),
				"state": not_none(address.find("location").find("state").text),
				"zip": not_none(address.find("location").find("zipCode").text),
			} for address in addresses
		],
		"dob": dob.text,
		"employment_records": [
			{
				"employer": not_none(employment.find("employer").find("unparsed").text, "Unknown"),
				"first_reported": not_none(employment.find("dateOnFileSince").text, "Unknown"),
				"date_hired": not_none(employment.find("dateHired").text, "Unknown"),
				"job_title": not_none(employment.find("occupation").text, "Unknown"),
			} for employment in employment_records
		],
		"tradelines": [
			{
				"subscriber": not_none(trade.find("subscriber").find("name").find("unparsed").text, "Unknown"),
				"ecoa": not_none(trade.find("ECOADesignator").text, "Unknown"),
				"account_rating": not_none(trade.find("accountRating").text, "Unknown"),
				"payment_history": not_none(trade.find("paymentHistory").text, "Unknown"),
				"past_due": trade.find("pastDue").text,
				"class": "satisfactory" if not past_due_regex.fullmatch(not_none(trade.find("accountRating").text)) else "problem"
			} for trade in tradelines
		],
		"inquiries": [
			{
				"ecoa": not_none(inquiry.find("ECOADesignator").text, "Unknown"),
				"subscriber": not_none(inquiry.find("subscriber").find("name").find("unparsed").text, "Unknown"),
				"date": not_none(inquiry.find("date").text, "Unknown")
			} for inquiry in inquiries
		]
	}
	return json_report