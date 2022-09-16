from app import *
import http.client
import config

def pd_incident(service_id):
	try:
		conn = http.client.HTTPSConnection("api.pagerduty.com")
		payload = """{ "incident": {   "title": "You are up in the draft!",    "service": {      "id": "placeholder",      "type": "service_reference"    },   "urgency": "low",    "body": {      "type": "incident_body",      "details": "You are up!"    }  }}"""
		new_payload = payload.replace("placeholder", service_id)

		headers = {
			"Content-Type": "application/json",
			"Accept": "application/vnd.pagerduty+json;version=2",
			"From": config.from_email,
			"Authorization": f"Token token={config.pd_api}"
		}

		test = conn.request("POST", "/incidents", new_payload, headers)
		res = conn.getresponse()
		data = res.read()
		return True
	except Exception as e:
		return e

	# print("response" + data.decode("utf-8"))
