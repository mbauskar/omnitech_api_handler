# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import json
import frappe
from frappe import _
import handler
from frappe.utils import cstr, flt, getdate, comma_and, cint
from api_handler.validate_methods import validate_and_get_json_request
from response import build_response,report_error

def handle():
	"""
	Handler for `/api_name` methods
	**api_name = configured in api_hander hooks
	### Examples:

	`/api_name/{methodname}` will call a whitelisted method

	"""
	try:
		validate_and_get_json_request()
		return handler.handle()
	except Exception, e:
		import traceback
		print traceback.format_exc()
		frappe.response['X_ERROR_CODE'] = "03" if "XML Request" in cstr(e) else "01"
		frappe.response['X_ERROR_DESC'] = cstr(e)
		return build_response("xml")
