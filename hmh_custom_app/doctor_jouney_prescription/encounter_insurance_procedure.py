import frappe
from frappe import _

@frappe.whitelist()
def update_procedure_payment_status(doc, method):
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
        for procedure in patient_encounter.procedure_prescription:
            # Check if the lab test is already Fully Paid
            if procedure.custom_procedure_status != "Fully Paid" and patient_doc.customer_group == "Insurance":
                # Check if any invoice related to this encounter has no outstanding amount
                matching_invoices = [invoice for invoice in invoices if invoice.custom_patient_ecounter_id == encounter.name]
                if all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                    procedure.custom_procedure_status = "Fully Paid"
                    updated = True
                    investigations.append(procedure)
                    
                    # Create a new Lab Test document
                    create_procedure(procedure, patient_encounter.patient, 
                                    patient_encounter.name,patient_encounter.encounter_date,
                                    patient_encounter.practitioner)

        if updated:
            patient_encounter.save()
            frappe.db.commit()  # Commit changes to the database
            frappe.msgprint(_("Patient Encount{0} Recieved successfully.").format(patient_encounter.name))

    return investigations

def create_procedure(procedure, patient, encounter_id,date,practitioner):
    # Fetch the Patient document to get gender 
    patient_doc = frappe.get_doc('Patient', patient)
    
    # Logging for debugging
    frappe.log_error(f"Creating Lab Test for Patient: {patient}, Encounter ID: {encounter_id}", "Lab Test Creation")

    # Create a new Lab Test document
    procedure_doc = frappe.new_doc('Clinical Procedure')
    procedure_doc.procedure_template = procedure.procedure  # Assuming lab_test has a field named lab_test_code
    procedure_doc.patient = patient
    procedure_doc.custom_cost_center = patient_doc.custom_consulting_department
    procedure_doc.invoiced = 1
    procedure_doc.start_date = date
    procedure_doc.practitioner = practitioner
    procedure_doc.custom_patient_encount_id = encounter_id  # Use the encounter_id passed to the function
    
    # Logging for debugging
    frappe.log_error(f"Lab Test Doc Values: {procedure_doc.as_dict()}", "Lab Test Doc Debug")

    procedure_doc.insert()
    frappe.db.commit()  # Commit changes to the database
   
