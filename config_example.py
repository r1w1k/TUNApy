#add your credentials/account details and save as config.py
test_password = ''
test_market = '' 
test_submarket = ''
test_industry_code = ''
test_member_code = ''
test_system_id = ''
test_system_pw = ''
test_vendor_id = ''
test_vendor_name = ''
test_software_name = ''
test_software_version = ''
test_permissible_purpose = ''
test_end_user = ''

prod_password = ''
prod_market = '' 
prod_submarket = ''
prod_industry_code = ''
prod_member_code = ''
prod_system_id = ''
prod_system_pw = ''
prod_vendor_id = ''
prod_vendor_name = ''
prod_software_name = ''
prod_software_version = ''
prod_permissible_purpose = ''
prod_end_user = ''

#Transunion will issue a p12 file to use as a digital certificate.  Change it into two separate crt + key files:
# openssl pkcs12 -in original.p12 -out new.key -nocerts -nodes
# openssl pkcs12 -in original.p12 -out new.crt -clcerts -nokeys
#More here:
#https://stackoverflow.com/questions/32253909/curl-with-a-pkcs12-certificate-in-a-bash-script

#Local path to separate crt + key files
certificate_path = ''
key_path = ''