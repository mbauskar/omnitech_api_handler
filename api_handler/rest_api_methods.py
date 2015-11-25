from __future__ import unicode_literals
import json
import frappe
import traceback
import frappe.utils
from frappe import _
from utils import send_mail
from frappe.utils import cstr, flt, getdate, comma_and, cint
from api_handler.validate_methods import get_full_domain
from api_handler.doctype.request_log.create_log import request_log, get_json
from api_handler.validate_methods import validate_request
from api_handler.validate_methods import validate_create_customer_request
from api_handler.validate_methods import validate_create_service_request
from api_handler.validate_methods import validate_disconnect_service_request
from api_handler.validate_methods import validate_delete_customer_request
from api_handler.validate_methods import validate_control_action_request

class CommandFailedError(Exception):
	pass

def create_customer(data):
	is_completed = False
	try:
	    if isinstance(data, unicode): data = get_json(data)

	    print_msg("Create Customer", data.get("P_USER_NAME"))
	    
	    validate_request["create_customer"](data)	    
	    
	    # Create new customecreate_new_siter document
	    customer = frappe.new_doc('Customer')
	    customer.customer_name = data.get('P_CUST_NAME')
	    customer.customer_type = 'Company'
	    customer.customer_group = 'Commercial'
	    customer.territory = 'All Territories'
	    customer.cpr_cr = data.get("P_CPR_CR")
	    customer.is_active = 0
	    customer.domain_name = data.get("P_USER_NAME")
	    customer.save(ignore_permissions=True)
	    # create new contact
	    create_contact(customer, data)
	    # create new site {deactivated}
	    admin_pwd = create_new_site(data, customer.name)
	    notify_user("create_customer", data)
	    create_request_log("02", "Success", "create_customer", data)
	    is_completed = True
	except Exception, e:
		frappe.db.rollback()
		error = "%s\n%s"%(e, traceback.format_exc())
		print error
		create_request_log("01", str(e), "create_customer", data, error)
	finally:
		if is_completed: frappe.db.commit()
		return is_completed

def create_contact(obj, args):
    contact = frappe.new_doc('Contact')
    contact.first_name = obj.customer_name
    contact.email_id = args.get('P_EMAIL')
    contact.phone = args.get('P_CONTACT_NO')
    contact.customer = obj.name
    contact.save(ignore_permissions=True)

def delete_customer(args):
	is_completed = False
	try:
		if isinstance(args, unicode): args = get_json(args)
		
		print_msg("Delete Customer", args.get("P_USER_NAME"))
		validate_request["delete_customer"](args)
		
		domain_name = args.get("P_USER_NAME")
		site = frappe.get_doc("Sites", domain_name)
		if site.customer:
			if not site.is_active:
				# drop-site
				cmd = {
					"../../bin/bench drop-site --root-password {0} {1}".format(get_mariadb_root_pwd(), domain_name): "Deleting Site - {0}".format(domain_name)
					}
				exec_cmd(cmd, cwd=get_target_banch(), trxn_no=args.get("P_TRXN_NO"))

				notify_user("delete_customer", args)
				# delete customer and site
				frappe.delete_doc("Sites", site.name, ignore_permissions=True)
				frappe.delete_doc("Customer", site.customer, ignore_permissions=True)

				create_request_log("02", "Success", "delete_customer", args)
			else:
				raise Exception("Can not delete the Customer, Please first deactivate the site : %s"%(site.name))
		else:
			raise Exception("Unable to find site customer, Please contact Administrator")
		is_completed = True
	except Exception, e:
		import traceback
		frappe.db.rollback()
		error = "%s\n%s"%(e, traceback.format_exc())
		print error
		create_request_log("01", str(e), "delete_customer", args, error)
	finally:
		if is_completed: frappe.db.commit()
		return is_completed

def create_service(args):
	"""Activate newly created service"""
	# update customer master - is_active and CPR CR, current package id
	is_completed = False
	try:
		if isinstance(args, unicode): args = get_json(args)
		
		print_msg("Create Service", args.get("P_USER_NAME"))
		validate_request["create_service"](args)
		
		if is_site_already_exists(args.get("P_USER_NAME")):
			result = {}
			if frappe.db.get_value("Sites", args.get("P_USER_NAME"),"is_active"):
				result = update_client_instance_package_details(args, is_active=True)
			else:
				configure_site(args.get("P_USER_NAME"), is_disabled=False, trxn_no=args.get("P_TRXN_NO"))
				update_sites_doc(args.get("P_USER_NAME"), is_active=True)
				# Allowing the supervisor and nginx to reload
				import time
				time.sleep(10)
				result = update_client_instance_package_details(args, is_active=True)

			if result.get("X_ERROR_CODE") == "02":
				update_customer_package_details(args)
				notify_user("create_service", args, password=get_admin_pwd(args.get("P_USER_NAME")))
				create_request_log("02", "Success", "create_service", args)
			else:
				configure_site(args.get("P_USER_NAME"), is_disabled=True)
				update_sites_doc(args.get("P_USER_NAME"), is_active=False)
				raise Exception("Error : ", result.get("X_ERROR_DESC"))
		else:
			raise Exception("Requested site (%s) does not exist"%(args.get("P_USER_NAME")))
		is_completed = True
	except Exception, e:
		frappe.db.rollback()
		print e
		error = "%s\n%s"%(e, traceback.format_exc())
		print error
		create_request_log("01", str(e), "create_service", args, error)
	finally:
		if is_completed: frappe.db.commit()
		return is_completed

def disconnect_service(args, parent_service=None):
	# update customer master, is_active
	is_completed = False
	try:
		if isinstance(args, unicode): args = get_json(args)
		
		cmd = "disconnect_service" if not parent_service else parent_service
		print_msg(cmd.upper(), args.get("P_USER_NAME"))
		
		validate_request[cmd](args)
		
		if is_site_already_exists(args.get("P_USER_NAME")):
			if frappe.db.get_value("Sites", args.get("P_USER_NAME"),"is_active"):
				configure_site(args.get("P_USER_NAME"), is_disabled=True, trxn_no=args.get("P_TRXN_NO"))
				update_sites_doc(args.get("P_USER_NAME"), is_active=False)
				update_customer_domain_details(args.get("P_USER_NAME"), is_active=False)
				# check if any site is linked with package if not then update is_assigned value of package
				if not frappe.db.get_value("Sites",{"package_id":args.get("P_PACKAGE_ID")},"name"):
					frappe.db.set_value("Packages", args.get("P_PACKAGE_ID"), "is_assigned", 0)
				notify_user("disconnect_service", args)
				create_request_log("02", "Success", "disconnect_service", args)
			else:
				frappe.throw("Requested site (%s) is already disconnected"%(args.get("P_USER_NAME")))
		else:
			frappe.throw("Requested site (%s) does not exists"%(args.get("P_USER_NAME")))
		is_completed = True
	except Exception, e:
		frappe.db.rollback()
		error = "%s\n%s"%(e, traceback.format_exc())
		print error
		create_request_log("01", str(e), "disconnect_service", args, error)
	finally:
		if is_completed: frappe.db.commit()
		return is_completed

def restart_service(args, parent_service=None):
	# update customer master, is_active
	is_completed = False
	domain = args.get("P_USER_NAME")
	try:
		if isinstance(args, unicode): args = get_json(args)
		
		cmd = "restart_service" if not parent_service else parent_service
		print_msg(cmd.upper(), args.get("P_USER_NAME"))
		validate_request[cmd](args)
		
		if is_site_already_exists(domain):
			if not frappe.db.get_value("Sites", domain, "is_active"):
				configure_site(domain, is_disabled=False, trxn_no=args.get("P_TRXN_NO"))
				update_sites_doc(domain, is_active=True)
				update_customer_domain_details(domain, is_active=True)
				notify_user("restart_service", args)
				create_request_log("02", "Success", "restart_service", args)
			else:
				frappe.throw("Requested site (%s) is already active"%(domain))
		else:
			frappe.throw("Requested site (%s) does not exists"%(domain))
		is_completed = True
	except Exception, e:
		frappe.db.rollback()
		error = "%s\n%s"%(e, traceback.format_exc())
		print error
		create_request_log("01", str(e), "restart_service", args, error)
	finally:
		if is_completed: frappe.db.commit()
		return is_completed

def control_action(args):
	args = get_json(args)
	if args.get("P_CREDIT_ACTION") in ["TOS","SUSPEND"]:
		return disconnect_service(args, parent_service="control_action");
	else:
		return restart_service(args, parent_service="control_action")

def create_new_site(args, customer):
	"""Create new site, create site doc"""
	if isinstance(args, unicode): args = get_json(args)
	if not is_site_already_exists(args.get("P_USER_NAME")):
		pwd = generate_random_password()
		create_site(args.get("P_USER_NAME"), args.get("P_AUTHENTICATE"), pwd, args.get("P_TRXN_NO"), is_active=False)
		create_sites_doc(args, customer, pwd)
		return pwd
	else:
		raise Exception("Requested site (%s) already exist"%(args.get("P_USER_NAME")))

def create_sites_doc(args, customer, pwd):
	site = frappe.new_doc("Sites")
	site.transaction_number = args.get("P_TRXN_NO")
	site.domain = args.get("P_USER_NAME")
	site.is_active = 0
	site.cpr_cr = args.get("P_CPR_CR") or "NA"
	site.package_id = args.get("P_PACKAGE_ID") or "NA"
	site.order_number = args.get("P_ORDER_NO") or "NA"
	site.customer = customer
	site.admin_password = pwd
	site.save(ignore_permissions=True)

def is_site_already_exists(domain):
	if frappe.db.get_value("Sites", domain, "domain"):
		return True
	else:
		return False

def create_site(domain_name, auth_token, pwd, trxn_no, is_active=False):
  	cmds = [
		{
			"../../bin/bench new-site --mariadb-root-password {0} --admin-password {1} {2}".format(
					get_mariadb_root_pwd(), pwd, domain_name
				): "Creating New Site : {0}".format(domain_name)
		},
		{
			"../../bin/bench use {0}".format(domain_name): "Using {0}".format(domain_name)
		},
		{
			"../../bin/bench set-config is_disabled {0}".format(0 if is_active else 1): "Disabling {0}".format(domain_name)
		},
		{
			"../../bin/bench set-config auth_token {0}".format(get_encrypted_token(auth_token)): "Setting up authentication token to site"
		},
		{ "../../bin/bench install-app omnitechapp":"Installing Omnitech App" },
		{ "../../bin/bench install-app erpnext": "Installing ERPNext App" },
		{ "../../bin/bench use {0}".format(get_default_site()): "Setting up the default site" },
	]

	for cmd in cmds:
		exec_cmd(cmd, cwd=get_target_banch(), trxn_no=trxn_no)

def get_mariadb_root_pwd():
	db_pwd = frappe.db.get_value("API Defaults","API Defaults", "mariadb_password")
	if db_pwd:
		return db_pwd
	else:
		frappe.throw("MariaDB is not configured, Please contact Administrator")

def get_default_site():
	default_site = frappe.db.get_value("API Defaults","API Defaults", "default_site")
	if default_site:
		return default_site
	else:
		frappe.throw("Default Site is not configured, Please contact Administrator")

def get_admin_pwd(domain):
	pwd = frappe.db.get_value("Sites",domain, "admin_password")
	if pwd:
		return pwd
	else:
		return None

def get_target_banch():
	path = frappe.db.get_value("API Defaults","API Defaults", "path")
	if path:
		return path
	else:
		frappe.throw("Frappe-bench Path is not configured, Please Contact Administrator")

def update_sites_doc(domain, is_active=True):
    site = frappe.get_doc("Sites", domain)
    if site:
        site.is_active = 1 if is_active else 0
        site.ignore_permissions = True
        site.save(ignore_permissions=True);
    else:
        frappe.throw("{0} domain not found in Sites".format(domain))

def configure_site(domain, is_disabled=False, trxn_no=None):
	cmds = [
		{"../../bin/bench use {0}".format(domain): "Using {0}".format(domain) },
		{
			"../../bin/bench set-config is_disabled {0}".format(1 if is_disabled else 0): "Disabling {0}".format(domain)
		},
		{ "../../bin/bench use {0}".format(get_default_site()): "Setting up Default Site" },
		{"../../bin/bench setup nginx": "Deactivating {0}".format(domain) if is_disabled else "Deploying {0}".format(domain) },
		# { "sudo supervisorctl reload": None },
		{ "sudo service nginx reload": "Reloading nginx" }
	]

	for cmd in cmds:
	    exec_cmd(cmd, cwd=get_target_banch(), trxn_no=trxn_no)

def exec_cmd(cmd_dict, cwd='.', trxn_no=None):
	import subprocess

	key = cmd_dict.keys()[0]
	val = cmd_dict[key]
	cmd = "echo {desc} && {cmd}".format(desc=val, cmd=key) if val else key

	p = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=None, stderr=None)
	return_code = p.wait()
	if return_code > 0:
		raise CommandFailedError("Error while executing commend : %s, Transaction ID : %s"%(val, trxn_no))

def get_encrypted_token(auth_token=None):
	"""get encrypted P_AUTHENTICATE"""
	import hashlib

	encrypted_token = None
	if not auth_token:
		auth_token = frappe.db.get_value("API Defaults", "API Defaults", "token")
	encrypted_token = hashlib.sha1(auth_token).hexdigest()[:10]
	return encrypted_token

def update_customer_package_details(args):
	"""add/update entry in customer package transaction details"""
	# TODO check append row
	def append_row(doc, transaction_number, package_id):
		"""Append New Child Table Row"""
		ch = doc.append('package_transction', {})
		ch.transaction_number = transaction_number
		ch.package_id = package_id
		ch.description = frappe.db.get_value("Packages", package_id, "description") or "NA"
		doc.save(ignore_permissions=True)

	transaction_number = args.get("P_TRXN_NO")
	package_id = args.get("P_PACKAGE_ID")
	desc = args.get("P_DESC") or "NA"

	customer = frappe.db.get_value("Sites", args.get("P_USER_NAME"), "customer")
	doc = frappe.get_doc("Customer", customer)

	# check if customer has a child table entry if not create new
	if not doc:
		raise Exception("Customer Not Found, Please contact Administrator")

	if not doc.package_transction:
		append_row(doc, transaction_number, package_id)
	else:
		# check if package number from the child table and in request are same or not
		if doc.current_package != package_id:
			append_row(doc, transaction_number, package_id)

	# set package id in site
	frappe.db.set_value("Sites", args.get("P_USER_NAME"), "package_id", package_id)
	frappe.db.set_value("Packages", args.get("P_PACKAGE_ID"), "is_assigned", 1)
	update_customer_domain_details(args.get("P_USER_NAME"), is_active=True, package_id=package_id)

def update_customer_domain_details(domain, is_active=False, package_id=None, cpr_cr=None):
	customer = frappe.db.get_value("Sites", domain, "customer")
	doc = frappe.get_doc("Customer", customer)
	doc.is_active = 1 if is_active else 0

	if package_id: doc.current_package = package_id
	if cpr_cr: doc.cpr_cr = cpr_cr

	doc.save(ignore_permissions=True)

def update_client_instance_package_details(args, is_active=False):
	"""Update the package details in customer doctype"""
	import requests
	from api_handler.doctype.packages.packages import package_as_json

	try:
		token = get_encrypted_token(args.get("P_AUTHENTICATE"))
		pkg = json.loads(package_as_json(args.get("P_PACKAGE_ID")))
		url = "http://{0}/omniClient/setUserPackage".format(args.get("P_USER_NAME"))
		headers = { "content-type":"application/x-www-form-urlencoded" }
		params = {
			"P_AUTHENTICATE":token,
			"P_MIN_USERS":pkg.get("minimum_users"),
			"P_MAX_USERS":pkg.get("maximum_users"),
			"P_DESC":pkg.get("description"),
			"P_MODULES":pkg.get("allowed_modules"),
			"P_PACKAGE_ID":pkg.get("package_id")
		}
		req = { "data": json.dumps(params) }
		response = requests.get(url, data=req, headers=headers)
		return response.json()
	except Exception, e:
		import traceback
		print traceback.format_exc()
		return {
			"X_ERROR_CODE": "01",
			"X_ERROR_DESC": str(e)
		}

def create_request_log(error_code, error_desc, method, request, traceback=None):
	response = {
		"P_RETURN_CODE": error_code,
		"P_RETURN_DESC": error_desc
	}
	request_log(method, json.dumps(response, indent=4), request, traceback)

def generate_random_password(len=8):
	import random, string
	return "".join(random.choice(string.lowercase) for i in range(len))

subj = {
	"create_customer": "New Instance Of OmniTech ERPNext is Created",
	"delete_customer": "OmniTech ERPNext Instance is deleted",
	"create_service": "New Instance Of Omnitech ERPNext is Activated",
	"disconnect_service": "Omnitech ERPNext Instance has been Deactivated",
	"restart_service": "Omnitech ERPNext Instance has been re-activated"
}

def notify_user(action, params, password=None):
	args = {}
	customer_name = frappe.db.get_value("Sites", params.get("P_USER_NAME"), "customer")
	if customer_name:
		customer = frappe.get_doc("Customer", customer_name)
		email = frappe.db.get_value("Contact", {"customer":customer_name, "is_primary_contact":1 }, "email_id")
		args.update({
			"full_name": customer.customer_name or "User",
			"email": email,
			"action": action,
			"user": "Administrator",
			"password": password or None,
			"link": params.get("P_USER_NAME"),
		})

		return send_mail(args, subj.get(action), "templates/email/email_template.html")


def print_msg(method, user_name):
	print method, ">>", user_name

def customer_autoname(doc, method):
	doc.name = doc.domain_name