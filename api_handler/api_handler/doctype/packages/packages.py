# -*- coding: utf-8 -*-
# Copyright (c) 2015, New Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Packages(Document):
	def validate(self):
		# validate minimum and maximum number of user
		self.validate_number_of_users()
		self.validate_package_id()

	def validate_number_of_users(self):
		_min = self.minimum_users
		_max = self.maximum_users

		if _min < 1:
			frappe.throw("Minimum number of users should be greater than or equal to 1")
		elif _max < _min:
			frappe.throw("Maximum number of user should be greater than Minimum Number of users")

	def validate_package_id(self):
		if self.package_id == "NA":
			frappe.throw("NA is not a valid package id")

	def on_trash(self):
		# check if package is linked with any site
		if frappe.db.get_values("Sites", {"package_id":self.name}, "name"):
			frappe.throw("Can Not Delete, Package is linked with sites")

def package_as_json(package_id):
	pkg = frappe.get_doc("Packages", package_id)
	if not pkg:
		frappe.throw("Invalid Package ID")
	else:
		pkg_dict = {
			"package_id": pkg.name,
			"minimum_users": pkg.minimum_users,
			"maximum_users": pkg.maximum_users,
			"description": pkg.description,
			"allowed_modules": pkg.allowed_module
		}
		import json
		return json.dumps(pkg_dict)
