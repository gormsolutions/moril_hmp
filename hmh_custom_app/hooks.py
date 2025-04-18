app_name = "hmh_custom_app"
app_title = "Hmh Custom App"
app_publisher = "paul"
app_description = "Hospital Management"
app_email = "mututapaul01@gmail.com"
app_license = "mit"
# from hmh_custom_app.custom_api.later_payments.view_logs import grant_view_permission_to_all_users
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hmh_custom_app/css/hmh_custom_app.css"
app_include_js = "/assets/hmh_custom_app/js/custom_js/material_request.js"
app_include_js = "/assets/hmh_custom_app/js/custom_js/patient_encounter.js"
app_include_js = "/assets/hmh_custom_app/js/custom_js/patient.js"
app_include_js = "/assets/hmh_custom_app/js/custom_js/vitals.js"



# include js, css files in header of web template
# web_include_css = "/assets/hmh_custom_app/css/hmh_custom_app.css"
# web_include_js = "/assets/hmh_custom_app/js/hmh_custom_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hmh_custom_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    # "doctype" : "public/js/doctype.js"
    "Patient Encounter": "/public/js/custom_js/print_format.js",
    
    }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "hmh_custom_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "hmh_custom_app.utils.jinja_methods",
# 	"filters": "hmh_custom_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "hmh_custom_app.install.before_install"
# after_install = "hmh_custom_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "hmh_custom_app.uninstall.before_uninstall"
# after_uninstall = "hmh_custom_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hmh_custom_app.utils.before_app_install"
# after_app_install = "hmh_custom_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "hmh_custom_app.utils.before_app_uninstall"
# after_app_uninstall = "hmh_custom_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hmh_custom_app.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Override the Notification Log class
override_doctype_class = {
    "Notification Log": "hmh_custom_app.custom_api.later_payments.view_logs.CustomNotificationLog"
}


# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Patient": {
        "on_update": [
            "hmh_custom_app.custom_api.patient.create_vital_signs_for_patient",
            # "hmh_custom_app.custom_api.patient.validate_patient"
        ],
        # "validate": "hmh_custom_app.custom_api.patient.validate_patient"
    },
    
    "Pharmacy": {
        "on_submit": [
            "hmh_custom_app.pharmacy_jouney.approved_invoice.on_submit",
            "hmh_custom_app.pharmacy_jouney.approved_invoice.create_nurse_doc",
            # "hmh_custom_app.custom_api.patient.validate_patient"
        ],
        # "validate": "hmh_custom_app.custom_api.patient.validate_patient"
    },
    
    "Nurses Document": {
        "on_update": [
           "hmh_custom_app.pharmacy_jouney.approved_invoice.create_pharmacy_doc",
            # "hmh_custom_app.custom_api.patient.validate_patient"
        ],
        # "validate": "hmh_custom_app.custom_api.patient.validate_patient"
    },


    #  "Notification Requests": {
    #     "after_insert": grant_view_permission_to_all_users
    # },
    
    "Patient Encounter": {
        "on_update": [
            # Lab prescription
            "hmh_custom_app.custom_api.invoice_lab_tests.on_submit",
            "hmh_custom_app.custom_api.encounter_insurance.update_lab_tests_payment_status",
            # Drug prescription
            "hmh_custom_app.doctor_jouney_prescription.invoice_drug_prescription.on_submit",
            # procedures
            "hmh_custom_app.custom_api.procedures.invoice_procedures.on_submit",
            "hmh_custom_app.custom_api.procedures.encounter_insurance.update_procedure_payment_status",
            
            # Radiology
            "hmh_custom_app.custom_api.radiology.invoice_radiology.on_submit",
            "hmh_custom_app.custom_api.radiology.encounter_insurance.update_radiology_payment_status",
        ],
        # "validate": "hmh_custom_app.custom_api.patient.validate_patient"
    },

    "Patient Payment Management": {
        "on_submit": [
            "hmh_custom_app.custom_api.patient.create_vital_signs_for_patient_frompayments",
            "hmh_custom_app.custom_api.self_request.request.create_radiology",
            # apps/hmh_custom_app/hmh_custom_app/custom_api/self_request/request.py
        ]
    },
       "Inpatient Record": {
        "on_update": [
            "hmh_custom_app.custom_api.inpatient_discharge.inpatient_disacharge.create_pharmacy_doc",
        ]
    },
    
    "Sales Invoice": {
        "on_update": "hmh_custom_app.custom_api.update_customer_reg.on_submit_sales_invoice"
    }       

}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"hmh_custom_app.tasks.all"
# 	],
# 	"daily": [
# 		"hmh_custom_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"hmh_custom_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"hmh_custom_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"hmh_custom_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "hmh_custom_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hmh_custom_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "hmh_custom_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["hmh_custom_app.utils.before_request"]
# after_request = ["hmh_custom_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["hmh_custom_app.utils.before_job"]
# after_job = ["hmh_custom_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["module", "=", "HMH CUSTOM APP"]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            ["module", "=", "HMH CUSTOM APP"]
        ]
    },
]


# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"hmh_custom_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

