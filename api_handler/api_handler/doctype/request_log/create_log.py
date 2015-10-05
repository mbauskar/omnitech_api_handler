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

# TODO move pass_request_to_client_esb method to request_log.py ?
def pass_request_to_client_esb(doc, method):
    from suds.client import Client
    url = "file:///home/makarand/Desktop/Projects/omnitech/CRM_ACCEPTANCE_MSGService.wsdl"
    client = Client(url, cache=None)

    # Request and response data
    logged_request = json.loads(doc.request_parameters)
    logged_response = json.loads(doc.response)

    P_CRM_ID = logged_request.get("P_TRXN_NO")
    P_CIRCUIT_NO = "17XXXXXX"
    P_SERVICE_TYPE = "SaaS"
    P_ACTION_TYPE = "00"
    P_RETURN_CODE = logged_response.get("P_RETURN_CODE")
    P_RETURN_MESG = logged_response.get("P_RETURN_MESG")
    P_ATTRIBUTE1 = logged_request.get("P_ATTRIBUTE1") or None
    P_ATTRIBUTE2 = logged_request.get("P_ATTRIBUTE2") or None
    P_ATTRIBUTE3 = logged_request.get("P_ATTRIBUTE3") or None

    try:
        response = client.service.AcceptRequest(P_CRM_ID=P_CRM_ID,P_SERVICE_TYPE=P_SERVICE_TYPE,
                                                P_CIRCUIT_NO=P_CIRCUIT_NO,P_ACTION_TYPE=P_ACTION_TYPE,
                                                P_RETURN_CODE=P_RETURN_CODE,P_RETURN_MESG=P_RETURN_MESG,
                                                P_ATTRIBUTE1=P_ATTRIBUTE1,P_ATTRIBUTE2=P_ATTRIBUTE2,
                                                P_ATTRIBUTE3=P_ATTRIBUTE3)
        # TODO check response
        print response
    except Exception, e:
        frappe.db.rollback()
        print "env\n%s\n%s"%(e,client.last_sent().str())
        frappe.throw(str(e))
