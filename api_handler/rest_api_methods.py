from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from frappe import _
from api_handler.doctype.request_log.create_log import request_log, get_json
import json

def create_customer(data):
    data = get_json(data)
    customer = frappe.new_doc('Customer')
    customer.customer_name = data.get('P_CUST_NAME')
    customer.customer_type = 'Company'
    customer.customer_group = 'Commercial'
    customer.territory = 'All Territories'
    customer.save(ignore_permissions=True)
    create_contact(customer, data)
    request_log('create_customer', customer.name, data)

def create_contact(obj, args):
    contact = frappe.new_doc('Contact')
    contact.first_name = obj.customer_name
    contact.email_id = args.get('P_USER_NAME')
    contact.phone = args.get('P_CONTACT_NO')
    contact.customer = obj.name
    contact.save(ignore_permissions=True)

def delete_customer(obj, args):
    pass

def create_service(obj, args):
    pass

def disconnect_service(obj, args):
    pass

def control_action(obj, args):
    pass
