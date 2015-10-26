from __future__ import unicode_literals
import json
import frappe
import frappe.utils
from frappe import _
from frappe.utils import cstr, flt, getdate, comma_and, cint
from api_handler.api_handler.doctype.request_log.create_log import get_json
from api_handler.utils import xml_to_json
from api_handler.conf import services_fields, mandatory_fields, fields_and_types, fields_and_length

def validate_and_get_json_request():
    if validate_request_method():
        validate_url()
        xml_req = "<root>%s</root>"%(frappe.local.form_dict.data)
        req_params = xml_to_json(xml_req)
        frappe.local.form_dict.data = req_params
        validate_mandatory_field(req_params)
        validate_fields_length(req_params)
        validate_authentication_token(req_params)
        validate_request_parameters(req_params)

def validate_request_method():
    if frappe.request.method == "POST":
        return True
    else:
        raise Exception("Invalid Request Method, Please use 'POST' method for request")

def validate_url():
	path = frappe.request.path[1:].split("/",2)
    # path[1] in services_fields.keys() <= check if url is correct
	if len(path) == 2 and path[1] in services_fields.keys():
		frappe.local.form_dict.cmd = path[1]
	else:
		frappe.throw(_("Invalid URL"))

def validate_mandatory_field(req_params):
    data = req_params
    # check missing or extra fields
    missing_fields = [field for field in mandatory_fields.get(frappe.local.form_dict.cmd) if field not in data.keys()]
    extra_fields = [field for field in data.keys() if field not in services_fields.get(frappe.local.form_dict.cmd)]

    if extra_fields:
        frappe.throw(_("XML Request contains following extra field(s): {0}".format(",".join(extra_fields))))
    if missing_fields:
        frappe.throw(_("XML Request is missing following field(s): {0}".format(",".join(missing_fields))))
    # check mandatory fields
    for key in mandatory_fields.get(frappe.local.form_dict.cmd):
        if not data.get(key):
            frappe.throw(_("{0} field is mandatory").format(key))
        elif key == "P_CREDIT_ACTION" and data.get(key) not in ["TOS","ROS","SUSPEND"]:
            frappe.throw(_("Invalid P_CREDIT_ACTION value"))

        is_valid_datatype(key, data.get(key))

def validate_fields_length(params):
    invalid_fields = []

    for key, val in params.iteritems():
        allowed_len = fields_and_length.get(key)
        if allowed_len and allowed_len < len(val):
            invalid_fields.append(key)

    if invalid_fields:
        msg = "Character limit exceeded for following field(s) : %s"%(",".join(invalid_fields))
        raise Exception(msg)

def is_valid_datatype(field, val):
    # TODO type checking
    # error = Exception("Invalid data type for {0} parameter".format(field))
    # if fields_and_types.get(field) == "int":
    #     if not isinstance(val, int):
    #         raise error
    # else:
    #     if not isinstance(val, unicode):
    #         raise error
    pass

def validate_authentication_token(req_params):
    data = req_params
    auth_token = frappe.db.get_value('API Defaults', "API Defaults",'token')

    if auth_token:
    	if auth_token != data.get('P_AUTHENTICATE'):
    		frappe.throw(_('Invalid authentication token'))
    else:
    	frappe.throw(_('Authentication token has not been set, contact to support team'))

def validate_request_parameters(req_params):
    params = req_params
    cmd = frappe.local.form_dict.cmd

    if is_request_already_exists(cmd, params):
		err_msg = "Ignoring Request as the similer request is already exists in scheduler queue"
		raise Exception(err_msg)
    else:
        validate_request[cmd](params)

def validate_create_customer_request(params):
    """validate create customer request parameters"""
    domain = get_full_domain(params.get("P_USER_NAME"))
    params.update({"P_USER_NAME":domain})
    is_cpr_cr_already_assigned(params.get("P_CPR_CR"), domain, params.get("P_CUST_NAME"))
    validate_email(params.get("P_EMAIL"))
    validate_contact_number("P_CONTACT_NO")
    if is_domain_name_already_exsits(domain):
        frappe.throw(_("{0} Domain already exist".format(domain)))
    else:
        is_customer_already_exsits(params)
        is_valid_email(params.get("P_EMAIL"))

def validate_delete_customer_request(params):
    """validate delete customer request parameters"""
    domain = get_full_domain(params.get("P_USER_NAME"))
    params.update({"P_USER_NAME":domain})
    if not is_domain_name_already_exsits(domain):
        raise Exception(_("Requested Domain({0}) does not exist, Please check domain name in request".format(domain)))
    # check if site is active or not ?
    elif frappe.db.get_value("Sites",domain, "is_active") == 1:
        raise Exception("Can not delete customer, Customer has a Active ERPNext Instance")
    else:
        customer = frappe.db.get_value("Sites", domain, "customer")
        if not frappe.db.get_value("Customer", customer, "name"):
            raise Exception("Can not link any customer with given domain, Please contact Administrator")

    is_valid_cpr_cr(params.get("P_CPR_CR"), domain)

def validate_create_service_request(params):
    """validate create service request parameters"""
    # domain = params.get("P_USER_NAME")
    domain = get_full_domain(params.get("P_USER_NAME"))
    is_valid_cpr_cr(params.get("P_CPR_CR"), domain)
    is_valid_package_id(params.get("P_PACKAGE_ID"), domain)
    params.update({"P_USER_NAME":domain})
    
    if not is_domain_name_already_exsits(domain):
        raise Exception(_("Requested Domain does not exist, Please check domain name in request".format(domain)))

def validate_disconnect_service_request(params):
    """validate disconnected service request parameters"""
    # domain = params.get("P_USER_NAME")
    domain = get_full_domain(params.get("P_USER_NAME"))
    is_valid_cpr_cr(params.get("P_CPR_CR"), domain)
    is_valid_package_id(params.get("P_PACKAGE_ID"), domain)
    params.update({"P_USER_NAME":domain})

    if not is_domain_name_already_exsits(domain):
        raise Exception(_("Requested Domain does not exist, Please check domain name in request".format(params.get(domain))))
    elif not frappe.db.get_value("Sites", domain, "is_active"):
        raise Exception(_("Request Domain is already disconnected"))

def validate_control_action_request(params):
    """validate control action request parameters"""
    # domain = params.get("P_USER_NAME")
    domain = get_full_domain(params.get("P_USER_NAME"))
    is_valid_cpr_cr(params.get("P_CPR_CR"), domain)
    params.update({"P_USER_NAME":domain})
    
    if not is_domain_name_already_exsits(domain):
        raise Exception(_("Requested Domain does not exist, Please check domain name in request".format(params.get(domain))))
    elif not frappe.db.get_value("Sites", domain, "is_active") and params.get("P_CREDIT_ACTION") in ["TOS", "SUSPEND"]:
        raise Exception(_("Request Domain is already disconnected"))
    elif frappe.db.get_value("Sites", domain, "is_active") and params.get("P_CREDIT_ACTION") == "ROS":
        raise Exception(_("Request Domain is already active"))

def is_customer_already_exsits(req_params):
    if frappe.db.get_value('Selling Settings', None, 'cust_master_name') == 'Customer Name':
        if frappe.db.get_value('Customer', req_params.get('P_CUST_NAME'), 'name'):
            raise Exception(_("Customer {0} is already exist").format(req_params.get('P_CUST_NAME')))

def is_domain_name_already_exsits(domain_name):
    if frappe.db.get_value("Sites",domain_name, 'name'):
        return True
    else:
        return False

def validate_domain_name(domain_name):
    # validate the domain name
    # ^[w]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$
    # ^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$
    import re
    # pattern = "^[w]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"
    pattern = "^[a-zA-Z0-9]+$"
    if not re.match(pattern, domain_name) or domain_name == "www":
        frappe.throw("Invalid Domain Name")

def is_request_already_exists(service, req_params):
    req = {}
    
    query = """ SELECT request_data FROM `tabScheduler Task` WHERE method_name='%s' AND
                task_status<>'Completed'"""%(service)
    results = frappe.db.sql(query, as_list=True, debug=True)

    req.update(req_params)
    if req.get("P_USER_NAME"):
        req.update({"P_USER_NAME": get_full_domain(req.get("P_USER_NAME"))})

    # requests = [res[0] for res in results if json.loads(res[0]) == req_params]
    requests = [res[0] for res in results if json.loads(res[0]) == req]
    flag = False if not requests  else True
    return flag

def is_valid_email(email):
    """validate email id"""
    import re
    pattern = "[^@]+@[^@]+\.[^@]+"
    if not re.match(pattern, email):
        raise Exception("Invalid Email ID")

def is_valid_cpr_cr(cpr_cr, domain, action=None, customer=None):
    """validate CPR_CR for requested customer"""
    customer = frappe.db.get_value("Sites", domain, "customer")

    if customer:
        if frappe.db.get_value("Customer",customer, "cpr_cr") != cpr_cr:
            raise Exception("Invalid CPR_CR value")
    else:
        raise Exception("Requested Domain does not exist, Please check domain name in request".format(domain))

def is_cpr_cr_already_assigned(cpr_cr, domain, customer):
    customers = frappe.db.get_values("Customer", {"cpr_cr":cpr_cr}, "name")
    names = [cust[0] for cust in customers]
    if names:
        linked_with = ", ".join(names)
        raise Exception("CPR CR is already linked with {0} customer(s)".format(linked_with))


def is_valid_package_id(package_id, domain):
    """validate package id"""
    if package_id == "NA":
        raise Exception("NA is not a valid package id")
    if not frappe.db.get_value("Packages",package_id, 'name'):
        raise Exception(_("Invalid Package ID"))
    else:
        customer = frappe.db.get_value("Sites", domain, "customer")
        if customer:
            current_package = frappe.db.get_value("Customer",customer, "current_package")
            if current_package != "NA":
                if frappe.db.get_value("Customer",customer, "current_package") != package_id:
                    raise Exception("Package ID does not match")

def get_full_domain(domain):
    default_domain = frappe.db.get_value("API Defaults", "API Defaults", "default_domain")
    if not default_domain:
        raise Exception("Domain Name is not set, Please Contact Administrator")
    else:
        # domain should be subdomain.default_domain.com
        validate_domain_name(domain)
        return "{0}.{1}".format(domain, default_domain)

validate_request = {
    "create_service": validate_create_service_request,
    "create_customer": validate_create_customer_request,
    "disconnect_service": validate_disconnect_service_request,
    "delete_customer": validate_delete_customer_request,
    "control_action": validate_control_action_request
}

def validate_email(email):
    if frappe.db.get_value("Contact",{"email_id":email},"name"):
        raise Exception("Email ID is already in use ...")

def validate_contact_number(contact):
    if frappe.db.get_value("Contact", {"phone":contact}, "name"):
        raise Exception("Contact Number already in use ...")