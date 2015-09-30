from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from api_handler.api_handler.doctype.request_log.create_log import get_json
from api_handler.utils import xml_to_json
from frappe import _

mandatory_fields = {
    'create_customer': ['P_TRXN_NO', 'P_CPR_CR', 'P_CUST_NAME', 'P_USER_NAME','P_CONTACT_NO', 'P_EMAIL', 'P_ORDER_NO', 'P_AUTHENTICATE', "P_CIRCUIT_NO"],
	'delete_customer': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO','P_AUTHENTICATE'],
	'create_service': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID','P_AUTHENTICATE'],
	'disconnect_service': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID','P_AUTHENTICATE'],
	'control_action': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_CREDIT_ACTION','P_AUTHENTICATE'],
}

def validate_request():
    req_params = xml_to_json(frappe.local.form_dict.data)
    validate_url()
    validate_mandatory_field(req_params)
    validate_authentication_token(req_params)
    validate_request_parameters(req_params)

def validate_url():
	path = frappe.request.path[1:].split("/",2)
	if len(path) == 2:
		frappe.local.form_dict.cmd = path[1]
	else:
		frappe.throw(_("Invalid URL"))

def validate_mandatory_field(req_params):
    data = req_params
    for key in mandatory_fields.get(frappe.local.form_dict.cmd):
        if not data.get(key):
            frappe.throw(_("{0} field is mandatory").format(key))
        elif key == "P_CREDIT_ACTION" and data.get(key) not in ["TOS","ROS","SUSPEND"]:
            frappe.throw(_("Invalid P_CREDIT_ACTION value"))

def validate_authentication_token(req_params):
    data = req_params
    auth_token = frappe.db.get_value('Global Defaults', None,'token')

    if auth_token:
    	if auth_token != data.get('P_AUTHENTICATE'):
    		frappe.throw(_('Invalid authentication token'))
    else:
    	frappe.throw(_('Authentication token has not been set, contact to support team'))

def validate_request_parameters(req_params):
    params = req_params
    cmd = frappe.local.form_dict.cmd

    if is_request_already_exists(cmd, params):
		err_msg = "Ignoring Request as the same request is already exists in scheduler queue"
		raise Exception(err_msg)

    if cmd == 'create_customer':
        is_customer_already_exsits(params)
    # elif cmd == 'delete_customer':pass
    elif cmd == 'create_service':
        domain_name = params.get("P_USER_NAME")
        if is_domain_name_already_exsits(domain_name):
            frappe.throw(_("{0} Domain already exist".format(domain_name)))
        else:
            validate_domain_name(domain_name)
    elif cmd == 'disconnect_service':
        domain_name = params.get("P_USER_NAME")
        if not is_domain_name_already_exsits(domain_name):
            frappe.throw(_("Requested Domain does not exist, Please check domain name in request".format(domain_name)))
    elif cmd == 'control_action':
        domain_name = params.get("P_USER_NAME")
        if not is_domain_name_already_exsits(domain_name):
            frappe.throw(_("Requested Domain does not exist, Please check domain name in request".format(domain_name)))

def is_customer_already_exsits(req_params):
    if frappe.db.get_value('Selling Settings', None, 'cust_master_name') == 'Customer Name':
        if frappe.db.get_value('Customer', req_params.get('P_CUST_NAME'), 'name'):
            frappe.throw(_("Customer {0} is already exist").format(req_params.get('P_CUST_NAME')))

def is_domain_name_already_exsits(domain_name):
    if frappe.db.get_value("Sites",domain_name, 'name'):
        return True
    else:
        return False

def validate_domain_name(domain_name):
    # validate the domain name
    # ^[w]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$
    # ^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$
    import re
    pattern = "^[w]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"
    if not re.match(pattern, domain_name):
        frappe.throw("Invalid Domain Name")

def validate_bench_path(doc, method):
    import os
    if not os.path.exists(doc.path):
        frappe.throw("<b>{0}</b><br>Directory does not exists, Please check the directory Path".format(doc.path))

def is_request_already_exists(service, req_params):
    query = """ SELECT request_data FROM `tabScheduler Task` WHERE method_name='%s' AND
                task_status<>'Completed'"""%(service)
    results = frappe.db.sql(query, as_list=True, debug=True)

    requests = [res[0] for res in results if json.loads(res[0]) == req_params]
    flag = False if not requests  else True
    return flag
