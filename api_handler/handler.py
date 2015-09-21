# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.sessions
from response import build_response,report_error
import api_handler
import json
from rest_api_methods import create_customer

def handle():
	try:
		frappe.response['X_ERROR_CODE'] = 02
		frappe.response['X_ERROR_DESC'] = "Successfully Accept request"
		response = build_response("json")
		create_scheduler_task(frappe.local.form_dict.cmd, frappe.local.form_dict.data)
		return response
	except Exception, e:
		pass

def create_scheduler_task(method_name, request_data):
	schedule_task = frappe.new_doc('Scheduler Task')
	schedule_task.method_name = method_name
	schedule_task.request_data = request_data
	schedule_task.save(ignore_permissions=True)
