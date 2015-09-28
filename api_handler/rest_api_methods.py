from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from frappe import _
from api_handler.doctype.request_log.create_log import request_log, get_json
import json

class CommandFailedError(Exception):
	pass

def create_customer(data):
    try:
        data = get_json(data)
        customer = frappe.new_doc('Customer')
        customer.customer_name = data.get('P_CUST_NAME')
        customer.customer_type = 'Company'
        customer.customer_group = 'Commercial'
        customer.territory = 'All Territories'
        customer.save(ignore_permissions=True)
        create_contact(customer, data)
        response = {
            "P_RETURN_CODE":"S",
            "P_RETURN_MESG":"Success"
        }
        request_log('create_customer',json.dumps(response) , data)
    except Exception, e:
        response = {
            "P_RETURN_CODE":"E",
            "P_RETURN_MESG":str(e)
        }
        request_log('create_customer',json.dumps(response) , data)

def create_contact(obj, args):
    contact = frappe.new_doc('Contact')
    contact.first_name = obj.customer_name
    contact.email_id = args.get('P_USER_NAME')
    contact.phone = args.get('P_CONTACT_NO')
    contact.customer = obj.name
    contact.save(ignore_permissions=True)

def delete_customer(req_params):
    pass

def create_service(req_params):
    # create new doc of type Sites
	try:
	    args = get_json(req_params)
	    create_sites_doc(args)
	    create_new_site(args.get("P_USER_NAME"), is_active=True)
		response = {
            "P_RETURN_CODE":"S",
            "P_RETURN_MESG":"Success"
        }
        request_log('create_service',json.dumps(response) , data)
	except Exception, e:
		response = {
            "P_RETURN_CODE":"E",
            "P_RETURN_MESG":str(e)
        }
        request_log('create_service',json.dumps(response) , data)

def disconnect_service(req_params):
	try:
	    args = get_json(req_params)
	    update_sites_doc(args.get("P_USER_NAME"), is_active=0)
	    disable_site(args.get("P_USER_NAME"))
		response = {
            "P_RETURN_CODE":"S",
            "P_RETURN_MESG":"Success"
        }
        request_log('disconnect_service',json.dumps(response) , data)
	except Exception, e:
		response = {
            "P_RETURN_CODE":"E",
            "P_RETURN_MESG":str(e)
        }
        request_log('disconnect_service',json.dumps(response) , data)

def control_action(req_params):
    pass

def create_sites_doc(args):
    doc = {
        "doctype":"Sites",
        "transaction_number": args.get("P_TRXN_NO"),
        "domain": args.get("P_USER_NAME"),
        "is_active":1,
        "cpr_cr": args.get("P_CPR_CR"),
        "package_id": args.get("P_PACKAGE_ID"),
        "order_number":args.get("P_ORDER_NO")
    }
    site = frappe.get_doc(doc)
    site.ignore_permissions = True
    site.save()

def create_new_site(domain_name, is_active=False):
    # TODO
    # 1 Create new site instance
    # 2 If is_active is false add is_disabled param in site.config
    # 3 Run bench setup nginx to add nginx settings
	new_site = "bench new-site --mariadb-root-password {0} --admin-password {1} {2}".format(get_mariadb_root_pwd(),
	            get_default_admin_pwd(), "domain_name")
	bench_use = "bench use {0}".format(domain_name)
	set_config = "bench set-config is_disabled {0}".format(0 if is_active else 1)
	nginx_setup = "bench setup nginx"

	for cmd in [new_site, bench_use, set_config, nginx_setup]:
	    exec_cmd(cmd, cwd=get_target_banch())

def get_mariadb_root_pwd():
    # return "password"
	db_pwd = frappe.db.get_value("Global Defaults","Global Defaults", "mariadb_password")
	if db_pwd:
		return db_pwd
	else:
		frappe.throw("Please set the MariaDB Password in Global Defaults")

def get_default_admin_pwd():
    # return "admin"
	default_pwd = frappe.db.get_value("Global Defaults","Global Defaults", "default_password")
	if default_pwd:
		return default_pwd
	else:
		frappe.throw("Please set the Default Password in Global Defaults")

def get_target_banch():
	path = frappe.db.get_value("Global Defaults","Global Defaults", "path")
	if path:
		return path
	else:
		frappe.throw("Please set the frappe-bench path in Global Defaults")

def update_sites_doc(domain, is_active=True):
    site = frappe.get_doc("Sites", domain)
    if site:
        site.is_active = 1 if is_active else 0
        site.ignore_permissions = True
        site.save();
    else:
        frappe.throw("{0} domain not found in Sites".format(domain))

def disable_site(domain):
	bench_use = "bench use {0}".format(domain)
	set_config = "bench set-config is_disabled 1"
	nginx_setup = "bench setup nginx"

	for cmd in [bench_use, set_config, nginx_setup]:
	    exec_cmd(cmd, cwd=get_target_banch())

def exec_cmd(cmd, cwd='.'):
	import subprocess
	_cmd = "echo executing command - {0};{1}".format(cmd, cmd)
	p = subprocess.Popen(_cmd, cwd=cwd, shell=True, stdout=None, stderr=None)
	return_code = p.wait()
	if return_code > 0:
		raise CommandFailedError(cmd)
