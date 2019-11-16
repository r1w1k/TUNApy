from lxml import etree as ET
from os import getenv
from flask import request
import requests
import html

class TransunionApi:
	def __init__(self,args):
		self.args = args

	def get_request_xml(self):
		ns0 = '{http://www.netaccess.transunion.com/namespace}'
		ns1 = '{http://www.transunion.com/namespace}'

		parser = ET.XMLParser(remove_blank_text=True)
		tree = ET.parse('./transunion_request_template.xml', parser)
		root = tree.getroot()

		#Account config
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

		#Subject of the report
		subjectName.find(f'{ns1}first').text = self.args['first']
		subjectName.find(f'{ns1}middle').text = self.args['middle']
		subjectName.find(f'{ns1}last').text = self.args['last']

		subjectAddress.find(f'{ns1}street').find(f'{ns1}unparsed').text = self.args['address']
		subjectLocation.find(f'{ns1}city').text= self.args['city']
		subjectLocation.find(f'{ns1}state').text = self.args['state']
		subjectLocation.find(f'{ns1}zipCode').text = self.args['zip']

		subjectSSN = subject.find(f'{ns1}socialSecurity')
		subjectSSN.find(f'{ns1}number').text = self.args['ssn']

		self.request_xml = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
		return self.request_xml

	def make_request(self):
		print('sending:')
		print(self.request_xml)
		uri = getenv("TURI")
		certs = (getenv("CERTIFICATE_PATH"), getenv("KEY_PATH"))
		r = requests.post(uri, headers = {'Content-Type': 'application/xml'}, data=self.request_xml, cert = certs, verify=False)
		return r.content

def transunion_request():
    args = request.json
    for key in args:
        args[key] = html.escape(args[key].upper())
    t = TransunionApi(args)
    t.get_request_xml()
    return t.make_request()