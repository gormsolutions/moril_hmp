import frappe
from frappe import _

@frappe.whitelist()
def update_radiology_payment_status(doc, method):
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
        for procedure in patient_encounter.custom_radiology_items:
            # Check if the Radiology is already Fully Paid
            if procedure.radiology_status != "Fully Paid" and patient_doc.customer_group == "Insurance":
                # Check if any invoice related to this encounter has no outstanding amount
                matching_invoices = [invoice for invoice in invoices if invoice.custom_patient_ecounter_id == encounter.name]
                if all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                    procedure.radiology_status = "Fully Paid"
                    updated = True
                    investigations.append(procedure)
                    
                    # Create a new Lab Test document
                    create_radiology(procedure, patient_encounter.patient, 
                                    patient_encounter.name,patient_encounter.encounter_date,
                                    patient_encounter.practitioner,patient_encounter.medical_department)

        if updated:
            patient_encounter.save()
            frappe.db.commit()  # Commit changes to the database
            frappe.msgprint(_("Patient Encount{0} Recieved successfully.").format(patient_encounter.name))

    return investigations

def create_radiology(procedure, patient, encounter_id,date,practitioner,medical_department):
    # Fetch the Patient document to get gender 
    patient_doc = frappe.get_doc('Patient', patient)
    
    # Logging for debugging
    frappe.log_error(f"Creating Procedure for Patient: {patient}, Encounter ID: {encounter_id}", "Procedure Creation")

    # Create a new Radiology document
    procedure_doc = frappe.new_doc('Observation')
    procedure_doc.observation_template = procedure.radiology_investigation  # Assuming Radiology has a field named lab_test_code
    procedure_doc.patient = patient
    procedure_doc.custom_cost_center = "General Ward Cost Centre - MORIL"
    procedure_doc.invoiced = 1
    procedure_doc.posting_date = date
    procedure_doc.healthcare_practitioner = practitioner
    procedure_doc.custom_patient_encounter_id = encounter_id  # Use the encounter_id passed to the function
    procedure_doc.medical_department = medical_department
    # Logging for debugging
    frappe.log_error(f"Procedure Doc Values: {procedure_doc.as_dict()}", "LProcedure Doc Debug")

    procedure_doc.insert()
    frappe.db.commit()  # Commit changes to the database
   
