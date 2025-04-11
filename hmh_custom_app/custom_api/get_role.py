import frappe
from frappe import _

@frappe.whitelist()
def get_user_roles():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    return {"roles": roles}
