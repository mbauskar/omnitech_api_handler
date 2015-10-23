import frappe
from datetime import datetime

def reconsile_transactions(path):
	error_code = "02"
	error_desc = "Success"
	result = None
	try:
		erp_tx = get_customer_transaction_details()
		crm_tx = get_crm_transaction_details(path)
		result = compair_csv_details(erp_tx, crm_tx)
		save_result_to_csv(path, "erp", erp_tx)
		save_result_to_csv(path, "result", result)
	except Exception, e:
		error_code = "01"
		error_desc = str(e)
	finally:
		return {
			"X_ERRPR_CODE": error_code,
			"X_ERROR_DESC": error_desc,
		}

def get_customer_transaction_details():
	"""
	get customer transaction details in format
	{
		package_id:package_transction_details_doc
	}
	"""
	erp_crm = {}
	query = """ SELECT 
					cust.domain_name AS domain,
					cust.name AS customer_name,
					cust.current_package AS package_id,
					cust.cpr_cr AS cpr_cr,
					cust.is_active,
					cont.email_id AS email,
					cont.phone AS contact,
					ptd.description AS package_desc

				FROM
				    `tabPackage Transaction Details` AS ptd,
				    `tabCustomer` AS cust,
				    `tabContact` AS cont
				WHERE
				    ptd.parent=cust.name
				AND cust.current_package=ptd.package_id
				AND cont.customer=cust.name"""
	result = frappe.db.sql(query, as_dict=True)
	[erp_crm.update({ cust.get("domain"): cust }) for cust in result]
	return erp_crm

def get_crm_transaction_details(path):
	"""
	read csv and create the dict of following format
	{
		domain: {csv_row_details}
	}
	"""
	from os.path import join, isfile
	
	now = frappe.utils.now_datetime()
	file_name = "CRM_SAAS_%s.csv"%(now.strftime("%d%m%Y"))
	file_path = join(path, "esb", file_name)
	if isfile(file_path):
		crm_tx = {}
		result = read_csv(file_path)
		[crm_tx.update({r[0]:list_to_dict(r)}) for r in result]
		return crm_tx
	else:
		print "error"
		raise Exception("can not find %s in %s path"%(file_name, path))

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
	import copy

	result = {}
	erp_rec = copy.deepcopy(erp_tx)
	crm_rec = copy.deepcopy(crm_tx)
	crm_keys = crm_rec.keys()

	for key, val in crm_rec.iteritems():
		new_val = {}
		new_val = copy.deepcopy(val)
		# records missing from ERP but present in ESB
		if not erp_rec.get(key):
			msg = "%s's Record is either missing or disconnected from ERPNext System"%(val.get("domain"))
		else:
			# compare values
			msg = ""
			invalid_fields = []
			
			rec = erp_rec.get(key)
			if rec.get("customer_name") != val.get("customer_name"): invalid_fields.append("Customer")
			if rec.get("cpr_cr") != val.get("cpr_cr"): invalid_fields.append("CPR CR")
			if rec.get("contact") != val.get("contact"): invalid_fields.append("Contact")
			if rec.get("email") != val.get("email"): invalid_fields.append("EMAIL")
			if rec.get("package_id") != val.get("package_id"): invalid_fields.append("PACAKGE ID")

			if not invalid_fields:
				msg = "Matched and %s"%("Active" if rec.get("is_active") else "Disconnected")
			else:
				msg = "%s fields value does not match"%(",".join(invalid_fields))
			erp_rec.pop(key)

		new_val.update({"carriage_return":msg})
		result.update({key:new_val})

	# records missing in ESB but present in ERP
	for key, val in erp_rec.iteritems():
		val.update({"carriage_return": "Active but record is missing from ESB %s-%s"%(key, val)})
		result.update({key:val})
	return result

def read_csv(csv_path):
	"""Read the csv file from path and return list of dict"""
	from frappe.utils.csvutils import read_csv_content
	with open(csv_path, "r") as csv_file:
		csv_content = csv_file.read()
	result = read_csv_content(csv_content)
	return result[1:]

def list_to_dict(row):
	result = {}
	result.update({
		"domain": row[0],
		"cpr_cr": row[1],
		"customer_name": row[2],
		"contact": row[3],
		"email": row[4],
		"package_id": row[5],
		"package_desc": row[6],
		"carriage_return": row[7]
	})
	return result

def save_result_to_csv(path, directory, content):
	"""write the result in respective csv file"""
	import csv
	from os.path import join

	now = frappe.utils.now_datetime()
	file_name = "CRM_SAAS_%s.csv"%(now.strftime("%d%m%Y"))
	file_path = join(path, directory, file_name)

	with open(file_path, 'wb') as f:
	    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
	    writer.writerows(get_rows(content))

def get_rows(content):
	rows = []
	header = [
		"Domain","CR_CPR","CUSTOMER NAME",
		"CONTACT","EMAIL","Package ID",
		"Package Description","Package Details",
		"Carriage Return"
	]
	rows.append(header)

	for key, val in content.iteritems():
		res = []
		res.append(val.get("domain"))
		res.append(val.get("cpr_cr"))
		res.append(val.get("customer_name"))
		res.append(val.get("contact"))
		res.append(val.get("contact"))
		res.append(val.get("email"))
		res.append(val.get("package_id"))
		res.append(val.get("package_desc"))
		res.append(val.get("carriage_return"))
		rows.append(res)
	return rows
