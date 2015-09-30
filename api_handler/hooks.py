# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "api_handler"
app_title = "Api Handler"
app_publisher = "New Indictrans"
app_description = "APIs Handler "
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "contact@indictranstech.com"
app_version = "0.0.1"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/api_handler/css/api_handler.css"
# app_include_js = "/assets/api_handler/js/api_handler.js"

# include js, css files in header of web template
# web_include_css = "/assets/api_handler/css/api_handler.css"
# web_include_js = "/assets/api_handler/js/api_handler.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"
api_name = "omni_api"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "api_handler.install.before_install"
# after_install = "api_handler.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "api_handler.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# "Request Log": {
	# 	"on_update": "api_handler.api_handler.doctype.request_log.create_log.pass_request_to_client_esb",
	# },
	"Global Defaults": {
		"on_update": "api_handler.api_handler.validate_methods.validate_bench_path",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"api_handler.custom_scheduler_methods.execute_scheduler_methods"
	]
	# "daily": [
	# 	"api_handler.tasks.daily"
	# ],
	# "hourly": [
	# 	"api_handler.tasks.hourly"
	# ],
	# "weekly": [
	# 	"api_handler.tasks.weekly"
	# ]
	# "monthly": [
	# 	"api_handler.tasks.monthly"
	# ]
}

fixtures = ["Custom Field"]

# Testing
# -------

# before_tests = "api_handler.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "api_handler.event.get_events"
# }
