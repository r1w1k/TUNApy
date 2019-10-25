from lxml import etree as ET
import requests
import config

class Configuration:
	def __init__(self, environment='test'):
		prod = environment is 'production'
		self.environment = 'production' if prod else 'standardTest'
		self.curl = 'https://netaccess-test.transunion.com/' if prod else 'https://netaccess-test.transunion.com/'
		self.password = config.prod_password if prod else config.test_password
		self.market = config.prod_market if prod else config.test_market
		self.submarket = config.prod_submarket if prod else config.test_submarket
		self.industry_code = config.prod_industry_code if prod else config.test_industry_code
		self.member_code = config.prod_member_code if prod else config.test_member_code
		self.system_id = config.prod_system_id  if prod else config.test_system_id
		self.system_pw = config.prod_system_pw if prod else config.test_system_pw
		self.vendor_id = config.prod_vendor_id if prod else config.test_vendor_id
		self.vendor_name = config.prod_vendor_name if prod else config.test_vendor_name
		self.software_name = config.prod_software_name if prod else config.test_software_name
		self.software_version = config.prod_software_version if prod else config.test_software_version
		self.permissible_purpose = config.prod_permissible_purpose if prod else config.test_permissible_purpose
		self.end_user = config.prod_end_user if prod else config.test_end_user
		self.certificate_path = config.certificate_path
		self.key_path = config.key_path

class TransunionApi:
	def __init__(self,args):
		self.args = args
		self.config = Configuration(args["environment"])

	def get_request_xml(self):
		ns0 = '{http://www.netaccess.transunion.com/namespace}'
		ns1 = '{http://www.transunion.com/namespace}'

		parser = ET.XMLParser(remove_blank_text=True)
		tree = ET.parse('./request_template.xml', parser)
		root = tree.getroot()

		#Account config
		root.find(f'{ns0}systemId').text = self.config.system_id
		root.find(f'{ns0}systemPassword').text = self.config.system_pw

		creditBureau = root.find(f'{ns0}productrequest').find(f'{ns1}creditBureau')
		
		transactionControl = creditBureau.find(f'{ns1}transactionControl')
		product = creditBureau.find(f'{ns1}product')

		subscriber = transactionControl.find(f'{ns1}subscriber')
		options = transactionControl.find(f'{ns1}options')
		clientVendorSoftware = transactionControl.find(f'{ns1}clientVendorSoftware')

		subscriber.find(f'{ns1}industryCode').text = self.config.industry_code
		subscriber.find(f'{ns1}memberCode').text = self.config.member_code
		subscriber.find(f'{ns1}inquirySubscriberPrefixCode').text = self.config.market + self.config.submarket
		subscriber.find(f'{ns1}password').text = self.config.password

		options.find(f'{ns1}processingEnvironment').text = self.config.environment

		vendor = clientVendorSoftware.find(f'{ns1}vendor')
		vendor.find(f'{ns1}id').text = self.config.vendor_id
		vendor.find(f'{ns1}name').text = self.config.vendor_name

		software = clientVendorSoftware.find(f'{ns1}software')
		software.find(f'{ns1}name').text = self.config.software_name
		software.find(f'{ns1}version').text = self.config.software_version

		permissiblePurpose = product.find(f'{ns1}permissiblePurpose')
		permissiblePurpose.find(f'{ns1}code').text = self.config.permissible_purpose
		permissiblePurpose.find(f'{ns1}endUser').find(f'{ns1}unparsed').text = self.config.end_user

		#Subject of the report
		subject = product.find(f'{ns1}subject').find(f'{ns1}subjectRecord').find(f'{ns1}indicative')
		
		subjectName = subject.find(f'{ns1}name').find(f'{ns1}person')
		subjectName.find(f'{ns1}first').text = self.args['first']
		subjectName.find(f'{ns1}middle').text = self.args['middle']
		subjectName.find(f'{ns1}last').text = self.args['last']

		subjectAddress = subject.find(f'{ns1}address')
		subjectAddress.find(f'{ns1}street').find(f'{ns1}unparsed').text = self.args['address']
		subjectLocation = subjectAddress.find(f'{ns1}location')
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
		curl = self.config.curl
		certs = (self.config.certificate_path, self.config.key_path)
		r = requests.post(curl, headers = {'Content-Type': 'application/xml'}, data=self.request_xml, cert = certs, verify=False)
		return r.content
