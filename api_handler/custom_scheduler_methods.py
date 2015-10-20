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
    complete_request_logs()

def execute_web_serices():
    data = frappe.db.sql(''' select * from `tabScheduler Task`
                            where task_status = "Not Completed"''', as_dict=1)
    if data:
        for task_data in data:
            method = get_attr(task_data.method_name)
            result = frappe.call(method, task_data.request_data)
            update_status_of_method(task_data.name, is_completed=result)

def get_attr(cmd):
	"""get method object from cmd"""

	if '.' in cmd:
		method = frappe.get_attr(cmd)
	else:
		method = globals()[cmd]
	frappe.log("method:" + cmd)
	return method

def update_status_of_method(name, is_completed=False):
    obj = frappe.get_doc('Scheduler Task', name)
    obj.task_status = 'Completed' if is_completed else "Not Completed"
    obj.save(ignore_permissions=True)

def complete_request_logs():
    logs = frappe.db.get_values("Request Log",{"status":"Not Completed"},"name")
    for dn in logs:
        doc = frappe.get_doc("Request Log",dn[0])
        doc.save(ignore_permissions=True)

def audit_services():
    """Create csv and compare and cross check with CRM report"""
    # Read the incoming CSV
    # convert it into json (crm json)
    # read entries from customer master
    # compair the two json (erpnext)
    # validate the fields from crm json and erpnext json
    # update the status msg of each entries from bth crm and erpnext json
    now = frappe.dateutils.now_datetime()
    scheduler_date = get_scheduler_date()
    path = get_audit_dir_path()
    
    if now.date() == scheduler_date.date():
        pass

def set_next_scheduler_date():
    """set the next scheduler_date from the API Defaults"""
    pass

def get_scheduler_date():
    """get the scheduler date date from API defaults"""
    pass

def get_audit_dir_path():
    """get the audit dirctory path from the API Defaults"""