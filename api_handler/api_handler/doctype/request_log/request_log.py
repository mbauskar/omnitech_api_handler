# -*- coding: utf-8 -*-
# Copyright (c) 2015, New Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json

class RequestLog(Document):
	def validate(self):
		self.pass_request_to_client_esb()

	def pass_request_to_client_esb(self):
		# Request and response data
		logged_request = json.loads(self.request_parameters)
		logged_response = json.loads(self.response)

		P_CRM_ID = logged_request.get("P_TRXN_NO")
		P_CIRCUIT_NO = "17XXXXXX"
		P_SERVICE_TYPE = "SaaS"
		P_ACTION_TYPE = "00"
		P_RETURN_CODE = logged_response.get("P_RETURN_CODE")
		P_RETURN_MESG = logged_response.get("P_RETURN_MESG")
		P_ATTRIBUTE1 = logged_request.get("P_ATTRIBUTE1") or None
		P_ATTRIBUTE2 = logged_request.get("P_ATTRIBUTE2") or None
		P_ATTRIBUTE3 = logged_request.get("P_ATTRIBUTE3") or None

		try:
			from suds.client import Client

			#TODO check the URL for wsdl
			url = "%s/assets/erpnext/CRM_ACCEPTANCE_MSGService.wsdl"%(frappe.utils.get_url())
			# url = "http://localhost:9777/assets/erpnext/CRM_ACCEPTANCE_MSGService.wsdl"
			print frappe.utils.get_url(), "URL", url
			# url = "http://84.255.152.200:9777/assets/erpnext/CRM_ACCEPTANCE_MSGService.wsdl"
			client = Client(url, cache=None)

			response = client.service.AcceptRequest(P_CRM_ID=P_CRM_ID,P_SERVICE_TYPE=P_SERVICE_TYPE,
				                                    P_CIRCUIT_NO=P_CIRCUIT_NO,P_ACTION_TYPE=P_ACTION_TYPE,
				                                    P_RETURN_CODE=P_RETURN_CODE,P_RETURN_MESG=P_RETURN_MESG,
				                                    P_ATTRIBUTE1=P_ATTRIBUTE1,P_ATTRIBUTE2=P_ATTRIBUTE2,
				                                    P_ATTRIBUTE3=P_ATTRIBUTE3)
			self.esb_request = client.last_sent().str()
			self.esb_response = str(response)
			self.status = "Completed" if response.X_ERROR_CODE == "S" else "Not Completed"
			print "Completed", str(response)
		except Exception, e:
			import traceback
			# print traceback.format_exc()
			self.status = "Not Completed"
			self.error = str(traceback.format_exc())
			self.esb_request = "<xmp>%s</xmp>"%client.last_sent().str()
		finally:
			return True
