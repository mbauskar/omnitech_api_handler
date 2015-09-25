from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from frappe import _

def request_log(method, response, request_data, error=None):
    req_log = frappe.new_doc('Request Log')
    req_log.request_key = request_data.get('P_TRXN_NO')
    req_log.request = method
    req_log.request_parameters = json.dumps(request_data)
    req_log.response = response
    req_log.save(ignore_permissions=True)

def get_json(data):
    return json.loads(data)

# def test(doc, method):
#     # from suds.client import Client
#     url = "file:///home/makarand/Downloads/CRM_ACCEPTANCE_MSGService%281%29.wsdl"
#     client = Client(url)
#
#     # Request Data
#     # params = json.loads(doc.request_parameters)
#     P_CRM_ID = params.get("P_TRXN_NO")
#     P_CIRCUIT_NO = "SaaS"
#     P_SERVICE_TYPE = "17XXXXXXXX"
#     P_ACTION_TYPE = "00"
#     P_RETURN_CODE =
#     P_RETURN_MESG =
#     P_ATTRIBUTE1 = params.get("P_ATTRIBUTE1") or None
#     P_ATTRIBUTE2 = params.get("P_ATTRIBUTE2") or None
#     data = client.service.AcceptRequest(P_CRM_ID=12345,P_SERVICE_TYPE="SaaS", P_CIRCUIT_NO="01",P_ACTION_TYPE="Send", P_RETURN_CODE="02",P_RETURN_MESG="Error")
