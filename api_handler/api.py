# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import json
import frappe
from frappe import _
import handler
from frappe.utils import cstr, flt, getdate, comma_and, cint
from api_handler.validate_methods import validate_url, validate_mandatory_field, \
			validate_authentication_token, validate_customer_data
from response import build_response,report_error

def handle():
	"""
	Handler for `/api_name` methods
	**api_name = configured in api_hander hooks
	### Examples:

	`/api_name/{methodname}` will call a whitelisted method

	"""
	try:
		validate_request()
		return handler.handle()
	except Exception, e:
		frappe.response['X_ERROR_CODE'] = "01"
		frappe.response['X_ERROR_DESC'] = cstr(e)
		response = build_response("json")
		return response

def validate_request():
	validate_url()
	validate_mandatory_field()
	validate_authentication_token()
	validate_customer_data()
