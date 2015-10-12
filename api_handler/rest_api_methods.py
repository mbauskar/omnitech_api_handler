from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from frappe import _
from api_handler.doctype.request_log.create_log import request_log, get_json
import traceback
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
	        "P_RETURN_CODE":"02",
	        "P_RETURN_DESC":"Success"
	    }
	    request_log('create_customer',json.dumps(response) , data)
	except Exception, e:
		error = "%s\n%s"%(e, traceback.format_exc())
		response = {
		    "P_RETURN_CODE":"01",
		    "P_RETURN_DESC":str(e)
		}
		request_log('create_customer',json.dumps(response) , data, error)

def create_contact(obj, args):
    contact = frappe.new_doc('Contact')
    contact.first_name = obj.customer_name
    contact.email_id = args.get('P_EMAIL')
    contact.phone = args.get('P_CONTACT_NO')
    contact.customer = obj.name
    contact.save(ignore_permissions=True)

def delete_customer(args):
    pass

def create_service(args):
	"""Create New Site"""
	try:
		if isinstance(args, unicode): args = get_json(args)
		if not is_site_already_exists(args.get("P_USER_NAME")):
			create_new_site(args.get("P_USER_NAME"), is_active=True)
			create_sites_doc(args)
			update_customer_package_details(args, is_active=True)
			response = {
			    "P_RETURN_CODE":"02",
			    "P_RETURN_DESC":"Success"
			}
			request_log('create_service',json.dumps(response) , args)
		else:
			frappe.throw("Requested site (%s) already exist"%(args.get("P_USER_NAME")))
	except Exception, e:
		error = "%s\n%s"%(e, traceback.format_exc())
		response = {
		    "P_RETURN_CODE":"01",
		    "P_RETURN_DESC":str(e)
		}
		request_log('create_service',json.dumps(response) , args, error)

def disconnect_service(args):
	try:
		if isinstance(args, unicode): args = get_json(args)
		if is_site_already_exists(args.get("P_USER_NAME")):
			if not frappe.db.get_value("Sites", args.get("P_USER_NAME"),"is_active"):
				configure_site(args.get("P_USER_NAME"), is_disabled=True)
				update_sites_doc(args.get("P_USER_NAME"), is_active=False)
				response = {
				    "P_RETURN_CODE":"02",
				    "P_RETURN_DESC":"Success"
				}
				request_log('disconnect_service',json.dumps(response) , args)
			else:
				frappe.throw("Requested site (%s) is already disconnected"%(args.get("P_USER_NAME")))
		else:
			frappe.throw("Requested site (%s) does not exists"%(args.get("P_USER_NAME")))
	except Exception, e:
		error = "%s\n%s"%(e, traceback.format_exc())
		response = {
		    "P_RETURN_CODE":"01",
		    "P_RETURN_DESC":str(e)
		}
		request_log('disconnect_service',json.dumps(response) , args, error)

def restart_service(args):
	try:
		if isinstance(args, unicode): args = get_json(args)
		if is_site_already_exists(args.get("P_USER_NAME")):
			if frappe.db.get_value("Sites", args.get("P_USER_NAME"),"is_active"):
				configure_site(args.get("P_USER_NAME"), is_disabled=False)
				update_sites_doc(args.get("P_USER_NAME"), is_active=True)
				response = {
				    "P_RETURN_CODE":"02",
				    "P_RETURN_DESC":"Success"
				}
				request_log('disconnect_service',json.dumps(response) , args)
			else:
				frappe.throw("Requested site (%s) is already active"%(args.get("P_USER_NAME")))
		else:
			frappe.throw("Requested site (%s) does not exists"%(args.get("P_USER_NAME")))
	except Exception, e:
		error = "%s\n%s"%(e, traceback.format_exc())
		response = {
		    "P_RETURN_CODE":"01",
		    "P_RETURN_DESC":str(e)
		}
		request_log('disconnect_service',json.dumps(response) , args, error)

def control_action(args):
	args = get_json(args)
	if args.get("P_CREDIT_ACTION") in ["TOS","SUSPEND"]:
		disconnect_service(args);
	else:
		restart_service(args)

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

def is_site_already_exists(domain):
	site = frappe.get_doc("Sites", domain)
	result = True if site else False
	return result

def create_new_site(domain_name, is_active=False):
    # TODO
	# reload nginx and supervisor
	new_site = "bench new-site --mariadb-root-password {0} --admin-password {1} {2}".format(get_mariadb_root_pwd(),
	            get_default_admin_pwd(), domain_name)
	bench_use = "bench use {0}".format(domain_name)
	set_config = "bench set-config is_disabled {0}".format(0 if is_active else 1)
	install_app = "bench install-app erpnext"
	default_site = "bench use {0}".format(get_default_site())
	nginx_setup = "bench setup nginx"
	reload_supervisor = "sudo supervisorctl reload frappe:"
	reload_nginx = "sudo /etc/init.d/nginx reload frappe:"

	for cmd in [new_site, bench_use, set_config, install_app, default_site, nginx_setup, reload_supervisor, reload_nginx]:
	    exec_cmd(cmd, cwd=get_target_banch())

def get_mariadb_root_pwd():
    # return "password"
	db_pwd = frappe.db.get_value("Global Defaults","Global Defaults", "mariadb_password")
	if db_pwd:
		return db_pwd
	else:
		frappe.throw("MariaDB is not configured, Please contact Administrator")

def get_default_site():
	# return "www.test.com"
	default_site = frappe.db.get_value("Global Defaults","Global Defaults", "default_site")
	if default_site:
		return default_site
	else:
		frappe.throw("Default Site is not configured, Please contact Administrator")

def get_default_admin_pwd():
    # return "admin"
	default_pwd = frappe.db.get_value("Global Defaults","Global Defaults", "default_password")
	if default_pwd:
		return default_pwd
	else:
		frappe.throw("Site Details are not Configured, Please Contact Administrator")

def get_target_banch():
	path = frappe.db.get_value("Global Defaults","Global Defaults", "path")
	if path:
		return path
	else:
		frappe.throw("Frappe-bench Path is not configured, Please Contact Administrator")

def update_sites_doc(domain, is_active=True):
    site = frappe.get_doc("Sites", domain)
    if site:
        site.is_active = 1 if is_active else 0
        site.ignore_permissions = True
        site.save();
    else:
        frappe.throw("{0} domain not found in Sites".format(domain))

def configure_site(domain, is_disabled=False):
	bench_use = "bench use {0}".format(domain)
	set_config = "bench set-config is_disabled {0}".format(1 if is_disabled else 0)
	default_site = "bench use {0}".format(get_default_site())
	nginx_setup = "bench setup nginx"
	reload_supervisor = "sudo supervisorctl reload frappe:"
	reload_nginx = "sudo /etc/init.d/nginx reload frappe:"

	for cmd in [bench_use, set_config, default_site,nginx_setup, reload_supervisor, reload_nginx]:
	    exec_cmd(cmd, cwd=get_target_banch())

def exec_cmd(cmd, cwd='.'):
	import subprocess
	_cmd = "echo executing - {0}".format(cmd)
	p = subprocess.Popen(_cmd, cwd=cwd, shell=True, stdout=None, stderr=None)
	return_code = p.wait()
	if return_code > 0:
		raise CommandFailedError(cmd)

def update_customer_package_details(args, is_active=False):
	"""Update the package details in customer doctype"""
	pass
