import frappe
from frappe import _

@frappe.whitelist()
def update_lab_tests_payment_status(custom_payment_id):
    # Get all Sales Invoices where custom_payment_id matches and exclude cancelled and drafts
    invoices = frappe.get_all(
        'Sales Invoice',
        filters={
            'patient': custom_payment_id,
            'docstatus': 1  # Only includes submitted documents
        },
        fields=['name', 'outstanding_amount', 'custom_patient_ecounter_id']
    )
    
    # Extract custom_patient_ecounter_id from invoices
    encounter_ids = [invoice.custom_patient_ecounter_id for invoice in invoices if invoice.custom_patient_ecounter_id]
    
    if not encounter_ids:
        return "No encounters found."

    # Find the corresponding Patient Encounter documents
    encounters = frappe.get_all(
        'Patient Encounter',
        filters={'name': ['in', encounter_ids]},
        fields=['name']
    )

    investigations = []
    
    for encounter in encounters:
        patient_encounter = frappe.get_doc('Patient Encounter', encounter.name)
        updated = False

        # Access the child table 'Lab Prescription'
        for lab_test in patient_encounter.lab_test_prescription:
            # Check if the lab test is already Fully Paid
            if lab_test.custom_lab_status != "Fully Paid":
                # Check if any invoice related to this encounter has no outstanding amount
                matching_invoices = [invoice for invoice in invoices if invoice.custom_patient_ecounter_id == encounter.name]
                if all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                    lab_test.custom_lab_status = "Fully Paid"
                    lab_test.custom_results_status = "Processing Results"
                    lab_test.invoiced = 1
                    updated = True
                    investigations.append(lab_test)
                    
                    # Create a new Lab Test document
                    create_lab_test(lab_test, patient_encounter.patient,
                                    patient_encounter.name,
                                    patient_encounter.encounter_date,
                                    patient_encounter.practitioner)

        if updated:
            patient_encounter.save()
            frappe.db.commit()  # Commit changes to the database

    return investigations

def create_lab_test(lab_test, patient,patient_encounter,date,practitioner):
    # Fetch the Patient document to get gender 
    patient_doc = frappe.get_doc('Patient', patient)
    # Create a new Lab Test document
    lab_test_doc = frappe.new_doc('Lab Test')
    lab_test_doc.template = lab_test.lab_test_code  # Assuming lab_test has a field named test_template
    lab_test_doc.patient = patient
    lab_test_doc.patient_sex = patient_doc.sex
    lab_test_doc.custom_encounter_id = patient_encounter
    lab_test_doc.date = date
    lab_test_doc.practitioner = practitioner
    lab_test_doc.invoiced = 1
    lab_test_doc.save()
    frappe.db.commit()  # Commit changes to the database
