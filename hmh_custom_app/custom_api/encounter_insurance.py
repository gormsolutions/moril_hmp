import frappe
from frappe import _

@frappe.whitelist()
def update_lab_tests_payment_status(doc, method):
    # Get all Sales Invoices related to the patient and exclude cancelled and drafts
    invoices = frappe.get_all(
        'Sales Invoice',
        filters={
            'patient': doc.patient,
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
        fields=['name', 'patient']
    )

    investigations = []
    
    for encounter in encounters:
        patient_encounter = frappe.get_doc('Patient Encounter', encounter.name)
        patient_doc = frappe.get_doc('Patient', patient_encounter.patient)
        updated = False

        # Access the child table 'Lab Prescription'
        for lab_test in patient_encounter.lab_test_prescription:
            # Check if the lab test is already Fully Paid
            if lab_test.custom_lab_status != "Fully Paid" and patient_doc.customer_group == "Insurance":
                # Check if any invoice related to this encounter has no outstanding amount
                matching_invoices = [invoice for invoice in invoices if invoice.custom_patient_ecounter_id == encounter.name]
                if all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                    lab_test.custom_lab_status = "Fully Paid"
                    updated = True
                    investigations.append(lab_test)
                    
                    # Create a new Lab Test document
                    create_lab_test(lab_test, patient_encounter.patient, 
                                    patient_encounter.name,patient_encounter.encounter_date,
                                    patient_encounter.practitioner)

        if updated:
            patient_encounter.save()
            frappe.db.commit()  # Commit changes to the database
            frappe.msgprint(_("Patient Encount{0} Recieved successfully.").format(patient_encounter.name))

    return investigations

def create_lab_test(lab_test, patient, encounter_id,date,practitioner):
    # Fetch the Patient document to get gender 
    patient_doc = frappe.get_doc('Patient', patient)
    
    # Logging for debugging
    frappe.log_error(f"Creating Lab Test for Patient: {patient}, Encounter ID: {encounter_id}", "Lab Test Creation")

    # Create a new Lab Test document
    lab_test_doc = frappe.new_doc('Lab Test')
    lab_test_doc.template = lab_test.lab_test_code  # Assuming lab_test has a field named lab_test_code
    lab_test_doc.patient = patient
    lab_test_doc.patient_sex = patient_doc.sex
    lab_test_doc.invoiced = 1
    lab_test_doc.date = date
    lab_test_doc.practitioner = practitioner
    lab_test_doc.custom_encounter_id = encounter_id  # Use the encounter_id passed to the function
    
    # Logging for debugging
    frappe.log_error(f"Lab Test Doc Values: {lab_test_doc.as_dict()}", "Lab Test Doc Debug")

    lab_test_doc.insert()
    frappe.db.commit()  # Commit changes to the database
   
