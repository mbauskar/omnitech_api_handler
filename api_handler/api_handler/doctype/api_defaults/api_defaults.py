# -*- coding: utf-8 -*-
# Copyright (c) 2015, New Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class APIDefaults(Document):
	pass
	def validate(self):
		validate_token(self.token)
		validate_bench_path(self.path)
		validate_default_domain(self.default_domain)
		validate_default_domain(self.default_domain, is_default_domain=False)
		self.scheduled_date = validate_days_and_get_scheduled_date(self.days)

def validate_bench_path(path):
	import os
	if not os.path.exists(path):
		frappe.throw("<b>{0}</b><br>Directory does not exists, Please check the directory Path".format(path))

def validate_token(token):
	import re
	pattern = "^\d+$"
	if re.match(pattern, token):
		frappe.throw("Invalid Token, Please use alpha-numeric value as token")

def validate_default_domain(domain, is_default_domain=True):
	"""Validate domain name"""
	import re
	# ([A-Za-z0-9]+[.{1}][A-Za-z0-9]+){1}
	# [A-Za-z0-9]+.{1}[A-Za-z0-9]+
	if is_default_domain:
		pattern = "^([a-z0-9\-]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"
	else:
		pattern = "^([a-z0-9\-]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"
		if not re.match(pattern, domain):
			msg = "Invalid %s name"%("Default Domain" if is_default_domain else "Default Site")
			frappe.throw(msg)

def validate_days_and_get_scheduled_date(days):
	if days <= 0:
		frappe.throw("Invalid Days value")
	else:
		import datetime
		now = frappe.utils.now_datetime()
		return now.date() + datetime.timedelta(days=days)