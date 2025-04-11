import frappe
from frappe.model.document import Document

@frappe.whitelist()
def update_customer_in_patient_registration(doc, method):
    # Get the patient and custom_patient_mrno from the Sales Invoice
    patient = doc.patient
    patient_doc = frappe.get_doc('Patient', patient)  # Fetch the Patient document
    custom_patient_mrno = patient_doc.custom_patient_mrno  # Get the custom_patient_mrno from the Patient document
    
    # Search for the Patient Registration Identification where the name matches custom_patient_mrno
    patient_reg = frappe.get_all('Patient Registration Identification', filters={
        'name': custom_patient_mrno  # Ensure the correct field is compared
    }, fields=['name', 'customer'])

    if patient_reg:
        # If matching Patient Registration is found, update the customer field
        patient_reg_name = patient_reg[0].name  # Get the name of the Patient Registration
        customer = doc.customer  # Get the customer from the Sales Invoice

        # Update the customer field in the Patient Registration Identification
        patient_reg_doc = frappe.get_doc('Patient Registration Identification', patient_reg_name)
        if not patient_reg_doc.customer:  # Only update if the customer field is empty
            patient_reg_doc.customer = customer
            patient_reg_doc.save()

            frappe.msgprint(f"Customer field updated in Patient Registration Identification: {patient_reg_name}")

# Trigger the function when the Sales Invoice is submitted
def on_submit_sales_invoice(doc, method):
    update_customer_in_patient_registration(doc, method)
