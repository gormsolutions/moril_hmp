import frappe
from frappe import _

@frappe.whitelist()
def create_notification_request(patient, customer, time, reason):
    """Create a Notification Requests document."""
    # Temporarily set user to Administrator or a user with necessary permissions
    original_user = frappe.session.user
    frappe.set_user('Administrator')  # Change this to a user with permissions

    try:
        notification_request = frappe.get_doc({
            'doctype': 'Notification Requests',
            'patient': patient,
            'customer': customer,
            'time': time,
            'reason': reason,
            'docstatus': 0  # Ensure it's created as a draft
        })

        # Save the document and return the name
        notification_request.insert()
        return notification_request.name
    finally:
        # Reset the user back to the original user
        frappe.set_user(original_user)

@frappe.whitelist()
def create_notification_log(subject, document_type, document_name):
    """Create a Notification Log entry."""
    # Temporarily set user to Administrator or a user with necessary permissions
    original_user = frappe.session.user
    frappe.set_user('Administrator')  # Change this to a user with permissions

    try:
        notification_log = frappe.get_doc({
            'doctype': 'Notification Log',
            'subject': subject,
            'document_type': document_type,
            'document_name': document_name,
            'for_user': frappe.session.user,
            'type': 'Alert'
        })

        # Save the document
        notification_log.insert()
    finally:
        # Reset the user back to the original user
        frappe.set_user(original_user)



import frappe
from frappe import _

@frappe.whitelist()
def before_submit(docname):
    """Delete draft notifications related to the Notification Requests document before submission."""
    # Fetch the Notification Requests document
    doc = frappe.get_doc('Notification Requests', docname)

    # Validate the required fields
    if not doc.name or not doc.patient:
        frappe.throw(_('Document name or patient is missing.'))

    patient_id = doc.patient

    # Create the subject pattern to look for in the Notification Log
    notification_subject = f'Draft Notification Requests for {patient_id}'

    # Find related Notification Logs
    notification_logs = frappe.get_all('Notification Log', 
                                        filters={'subject': notification_subject,
                                                  'for_user': frappe.session.user},
                                        fields=['name'])

    if notification_logs:
        # Using Query Builder to delete each matching Notification Log
        table = frappe.qb.DocType("Notification Log")
        for log in notification_logs:
            frappe.db.delete(table, filters=(table.name == log.name))  # Delete by name
            frappe.msgprint(_('Draft notification removed as the document is now submitted.'))
    else:
        frappe.msgprint(_('No draft notification found for this patient.'))

    # Update custom bill status for the linked customer, if available
    if doc.customer:
        # Fetch the Customer document
        customer_doc = frappe.get_doc('Customer', doc.customer)

        # Check if the custom_bill_status field exists
        if hasattr(customer_doc, 'custom_bill_status'):
            # Update the custom bill status
            customer_doc.custom_bill_status = doc.bill_status
            # Save the customer document
            customer_doc.save()
            frappe.msgprint(_('Customer Bill Status updated successfully.'))
        else:
            frappe.msgprint(_('Custom bill status field does not exist in the Customer document.'))
    else:
        frappe.msgprint(_('No customer linked to update Bill Status.'))
