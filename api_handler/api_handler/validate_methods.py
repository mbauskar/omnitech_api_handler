from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from api_handler.api_handler.doctype.request_log.create_log import get_json
from frappe import _
import json

mandatory_fields = {
    'create_customer': ['P_TRXN_NO', 'P_CPR_CR', 'P_CUST_NAME', 'P_USER_NAME','P_CONTACT_NO', 'P_EMAIL', 'P_ORDER_NO', 'P_AUTHENTICATE'],
	'delete_customer': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO','P_AUTHENTICATE'],
	'create_service': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID','P_AUTHENTICATE'],
	'disconnect_service': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID','P_AUTHENTICATE'],
	'control_action': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_CREDIT_ACTION','P_AUTHENTICATE'],
}

def validate_url():
	path = frappe.request.path[1:].split("/",2)
	if len(path) == 2:
		frappe.local.form_dict.cmd = path[1]
	else:
		frappe.throw(_("Invalid URL"))

def validate_mandatory_field():
    # mandatory_field = {'create_customer':['P_TRXN_NO', 'P_CPR_CR', 'P_CUST_NAME', 'P_USER_NAME', 'P_CONTACT_NO', 'P_EMAIL', 'P_ORDER_NO', 'P_AUTHENTICATE']}
    data = get_json(frappe.local.form_dict.data)
    for key in mandatory_fields.get(frappe.local.form_dict.cmd):
        if not data.get(key):
            frappe.throw(_("{0} field is mandatory").format(key))

def validate_authentication_token():
	data = get_json(frappe.local.form_dict.data)
	auth_token = frappe.db.get_value('Global Defaults', None,'token')
	if auth_token:
		if auth_token != data.get('P_AUTHENTICATE'):
			frappe.throw(_('Invalid authentication token'))
	else:
		frappe.throw(_('Authentication token has not been set, contact to support team'))

def validate_customer_data():
	data = get_json(frappe.local.form_dict.data)
	if frappe.local.form_dict.cmd == 'create_customer':
		if frappe.db.get_value('Selling Settings', None, 'cust_master_name') == 'Customer Name':
			if frappe.db.get_value('Customer', data.get('P_CUST_NAME'), 'name'):
				frappe.throw(_("Customer {0} is already exist").format(data.get('P_CUST_NAME')))
