from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.sessions
from response import build_response,report_error
import api_handler
import json
from rest_api_methods import create_customer, delete_customer, create_service, \
                            disconnect_service, control_action
from datetime import datetime
from frappe.utils.dateutils import get_user_date_format

def execute_scheduler_methods():
    execute_web_serices()
    complete_request_logs()

def execute_web_serices():
    data = frappe.db.sql('''select * from `tabScheduler Task`
                            where task_status = "Not Completed" limit 30''', as_dict=1)
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
    from reconcile_transaction import reconsile_transactions

    error_code = "02"
    error_desc = "Success"
    result = None
    try:
        now = frappe.utils.now_datetime()
        scheduler_date = get_scheduler_date()
        path = get_audit_dir_path()

        # if now.date() == scheduler_date:
        if True:
            response = reconcile_transactions(path)
            if response.get("X_ERROR_CODE") == 02:
                pass
            else:
                raise Exception(response.get("X_ERROR_DESC"))
    except Exception, e:
        error_code = "01"
        error_desc = str(e)
        result = None
        print e
    finally:
        """create request log"""
        print result
        pass

def set_next_scheduler_date():
    """set the next scheduler_date from the API Defaults"""
    print "in set_next_scheduler_date"
    import datetime

    days = frappe.db.get_value("API Defaults", "API Defaults", "days")
    now = frappe.utils.now_datetime().date()
    next_date = now + datetime.timedelta(days=int(days))
    frappe.db.set_value("API Defaults", "API Defaults", "scheduled_date", next_date)

def get_scheduler_date():
    """get the scheduler date date from API defaults"""
    print "in get_scheduler_date"
    date = frappe.db.get_value("API Defaults", "API Defaults", "scheduled_date")
    if not date:
        frappe.throw("Scheduled Date is not set, Please check API Defaults")
    else:
        return datetime.strptime(date, "%Y-%m-%d").date()

def get_audit_dir_path():
    """get the audit dirctory path from the API Defaults"""
    print "get_audit_dir_path"
    path = frappe.db.get_value("API Defaults", "API Defaults", "audit_file_path")
    if not path:
        frappe.throw("Set the Audit dirctory path first")
    else:
        return path