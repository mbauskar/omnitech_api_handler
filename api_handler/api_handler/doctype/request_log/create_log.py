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
    req_log.error = error
    req_log.save(ignore_permissions=True)

def get_json(data):
    return json.loads(data)
