from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.sessions
from response import build_response,report_error
import api_handler
import json
from rest_api_methods import create_customer, delete_customer, create_service, \
                            disconnect_service, control_action

def execute_scheduler_methods():
    execute_web_serices()

def execute_web_serices():
    data = frappe.db.sql(''' select * from `tabScheduler Task`
                            where task_status = "Not Completed"''', as_dict=1)
    if data:
        for task_data in data:
            method = get_attr(task_data.method_name)
            frappe.call(method, task_data.request_data)
            update_status_of_method(task_data.name)

def get_attr(cmd):
	"""get method object from cmd"""

	if '.' in cmd:
		method = frappe.get_attr(cmd)
	else:
		method = globals()[cmd]
	frappe.log("method:" + cmd)
	return method

def update_status_of_method(name):
    obj = frappe.get_doc('Scheduler Task', name)
    obj.task_status = 'Completed'
    obj.save(ignore_permissions=True)
