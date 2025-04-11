import frappe
from frappe import _

@frappe.whitelist()
def update_procedure_payment_status(custom_payment_id):
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
    
    # Ensure that encounter_ids is a string
    # frappe.msgprint(_("Encounter IDs: {0}").format(", ".join(encounter_ids)))
    
    # Return the encounter_ids as a JSON-compatible list
    # return encounter_ids

    if not encounter_ids:
        return "No encounters found."

    # Find the corresponding Patient Encounter documents
    encounters = frappe.get_all(
        'Patient Encounter',
        filters={'name': ['in', encounter_ids]},
        fields=['name']
    )
    # return encounters
    investigations = []
    
    for encounter in encounters:
        patient_encounter = frappe.get_doc('Patient Encounter', encounter)
        updated = False

        # Access the child table 'Lab Prescription'
        for lab_test in patient_encounter.procedure_prescription:
            # Check if the lab test is already Fully Paid
            if lab_test.custom_procedure_status != "Fully Paid":
                # Check if any invoice related to this encounter has no outstanding amount
                matching_invoices = [invoice for invoice in invoices if invoice.custom_patient_ecounter_id == encounter.name]
                if all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                    lab_test.custom_procedure_status = "Fully Paid"
                    lab_test.custom_proceding_status = "Processing Results"
                    lab_test.invoiced = 1
                    updated = True
                    investigations.append(lab_test)
                    
                    # Create a new Lab Test document
                    create_lab_test(lab_test, patient_encounter.patient,
                                    patient_encounter.name,
                                    patient_encounter.encounter_date,
                                    patient_encounter.practitioner,patient_encounter.medical_department)

        if updated:
            patient_encounter.save()
            frappe.db.commit()  # Commit changes to the database

    return investigations

def create_lab_test(lab_test, patient,patient_encounter,date,practitioner,medical_department):
    # Fetch the Patient document to get gender 
    patient_doc = frappe.get_doc('Patient', patient)
    procedure_doc = frappe.new_doc('Clinical Procedure')
    procedure_doc.procedure_template = lab_test.procedure
    procedure_doc.patient = patient
    procedure_doc.custom_cost_center = patient_doc.custom_consulting_department
    procedure_doc.invoiced = 1
    procedure_doc.start_date = date
    procedure_doc.practitioner = practitioner
    procedure_doc.medical_department = medical_department
    procedure_doc.custom_patient_encount_id = patient_encounter
    procedure_doc.save()
    frappe.db.commit()  # Commit changes to the database
