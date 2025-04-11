# ..............imports to EFRIS.................
from frappe.model.document import Document
import frappe
from frappe import _, throw, msgprint
from frappe.utils import nowdate

@frappe.whitelist()
def encounter_doc(docname):
    doc = frappe.get_doc("Patient Encounter", docname)
    return doc
