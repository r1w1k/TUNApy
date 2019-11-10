from dotenv import load_dotenv
load_dotenv()

import os
from lxml import etree
from Transunion import TransunionApi

import unittest


class test_transunion(unittest.TestCase):
	def test_xml(self):
		args = {
			'first': 'first',
			'middle': 'middle',
			'last': 'last',
			'address': 'address',
			'city': 'city',
			'state': 'state',
			'zip': '99999',
			'ssn': '123456789'
		}
		t = TransunionApi(args)
		t.get_request_xml()
		#make sure we're always creating a valid XML doc
		self.assertTrue(etree.fromstring(t.request_xml) is not None)

	def test_credentials_present(self):
		self.assertTrue(
			os.getenv("SYSTEM_ID") and
			os.getenv("ENVIRONMENT") and
			os.getenv("TURI") and
			os.getenv("PASSWORD") and
			os.getenv("MARKET") and
			os.getenv("SUBMARKET") and
			os.getenv("INDUSTRY_CODE") and
			os.getenv("MEMBER_CODE") and
			os.getenv("SYSTEM_PW") and
			os.getenv("VENDOR_ID") and
			os.getenv("VENDOR_NAME") and
			os.getenv("SOFTWARE_NAME") and
			os.getenv("SOFTWARE_VERSION") and
			os.getenv("PERMISSIBLE_PURPOSE") and
			os.getenv("END_USER") and
			os.getenv("CERTIFICATE_PATH") and
			os.getenv("KEY_PATH"))

# class test_docusign(unittest.TestCase):

# class test_mailmerge(unittest.TestCase):

if __name__ == '__main__':
	unittest.main()
