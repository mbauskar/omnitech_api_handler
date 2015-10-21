import frappe
from datetime import datetime

def reconsile_transactions(path):
	print "in reconsile_transactions"
	error_code = "02"
	error_desc = "Success"
	result = None
	try:
		erp_tx = get_customer_transaction_details()
		crm_tx = get_crm_transaction_details(path)
		result = compair_csv_details(erp_tx, crm_tx)
		save_result_csv(path, result)
	except Exception, e:
		error_code = "01"
		error_desc = str(e)
		result = None
	finally:
		return {
			"X_ERRPR_CODE": error_code,
			"X_ERROR_DESC": error_desc,
			"X_CMP_RESULT": result
		}

def get_customer_transaction_details():
	"""
	get customer transaction details in format
	{
		package_id:package_transction_details_doc
	}
	"""
	erp_crm = {}
	query = """SELECT *	FROM
			    `tabPackage Transaction Details` AS ptd,
			    `tabCustomer` AS cust
			WHERE
			    ptd.parent=cust.name
			AND cust.is_active=1
			AND cust.current_package=ptd.package_id"""
	result = frappe.db.sql(query, as_dict=True)
	[erp_crm.update({ cust.get("package_id"): cust }) for cust in result]
	return erp_crm

def get_crm_transaction_details(path):
	"""
	read csv and create the dict of following format
	{
		package_id: {csv_row_details}
	}
	"""
	file_name = "audit.csv"
	pass

def save_result_csv(path):
	"""write the result in respective csv file"""
	# file name format CRM_SAAS_DDMMYYYYHH24MI.csv
	now = frappe.utils.now_datetime()
	file_name = "CRM_SAAS_%s"%()
	pass

def compair_csv_details(erp_tx, crm_tx):
	"""
		compair two csv and append the status
		result structure
		result = {
			"domain_name": {
				"domain":val,
				"customer_name":val,
				"cpr_cr":val,
				"contact":val,
				"email":val,
				"package_id":val,
				"package_desc":val,
				"carriage_return":val
			}
		}
	"""
	result = {}

	pass

def validate_customer_details(params):
	"""
	validate the customer details name, cpr_cr, contact, email, package_id, domain
	in case of invalid details uppend status to params
	"""
	pass