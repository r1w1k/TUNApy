from dotenv import load_dotenv
load_dotenv()

import html
from Transunion import TransunionApi
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

@app.route('/transunion', methods=['POST'])
def handle_request():
	args = request.json
	for key in args:
		args[key] = html.escape(args[key].upper())
	t = TransunionApi(args)
	t.get_request_xml()
	return t.make_request()

if __name__ == '__main__':
    app.run(debug=True)


