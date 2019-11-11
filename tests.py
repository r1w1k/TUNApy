from dotenv import load_dotenv
load_dotenv()

import os
from lxml import etree
from Transunion import TransunionApi
import app as main
from datetime import datetime, timezone

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
			os.getenv("KEY_PATH")
		)

# class test_docusign(unittest.TestCase):

# class test_mailmerge(unittest.TestCase):
class test_util(unittest.TestCase):
	def test_credentials_present(self):
		self.assertTrue(os.getenv("FERNET_KEY"))

	def test_symmetric_enc(self):
		original_message = "foo"
		encrypted = ""
		with main.app.test_request_context(path="/util/aes/en?message=" + original_message, method="GET"):
			encrypted = main.get_encrypted()["encrypted"]
			self.assertTrue(encrypted and encrypted != original_message)

		decrypted = ""
		with main.app.test_request_context(path="/util/aes/de?message=" + encrypted, method="GET"):
			decrypted = main.get_decrypted()["decrypted"]
			self.assertTrue(decrypted and decrypted == original_message)

	def test_unix_timestamp(self):
		month = "11"
		day = "12"
		year = "2019"
		path = "/util/hubspot_timestamp?month=" + month + "&day=" + day + "&year=" + year
		with main.app.test_request_context(path=path, method="GET"):
			timestamp = main.get_hubspot_timestamp()['timestamp']
			#make sure this works in reverse to get the original date we provided
			#also make sure it corresponds to time = 00:00:00, because Hubspot will annoyingly reject non-midnight values
			dt = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
			self.assertTrue(
				dt.day == 12 and dt.month == 11 and dt.year == 2019 and
				dt.hour == 0 and dt.minute == 0 and dt.second == 0
			)




if __name__ == '__main__':
	unittest.main()
