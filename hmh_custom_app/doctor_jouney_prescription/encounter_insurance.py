import frappe
from frappe import _

@frappe.whitelist()
def update_drug_payment_status(doc, method):
    # Get all Sales Invoices related to the patient and exclude cancelled and drafts
    invoices = frappe.get_all(
        'Pharmacy',
        filters={
            'patient': doc.patient,
            'docstatus': 1  # Only includes submitted documents
        },
        fields=['name', 'outstanding_amount', 'patient_encounter_id']
    )
    
    # Extract custom_patient_ecounter_id from invoices
    encounter_ids = [invoice.patient_encounter_id for invoice in invoices if invoice.patient_encounter_id]
    
    if not encounter_ids:
        return
        # return "No Pharmacy found."

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

        # Access the child table 'drug Prescription'
        for drug in patient_encounter.drug_prescription:
            # Check if the drug is already Send to Pharmacy
            if drug.custom_drug_status != "Send to Pharmacy" and patient_doc.customer_group == "Insurance":
                # Check if any invoice related to this encounter has no outstanding amount
                matching_invoices = [invoice for invoice in invoices if invoice.custom_patient_ecounter_id == encounter.name]
                if all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                    drug.custom_drug_status = "Send to Pharmacy"
                    updated = True
                    investigations.append(drug)
                    
                    # Create a new Pharmacy document
                    create_pharmacy(drug, patient_encounter.patient, 
                                    patient_encounter.name,patient_encounter.encounter_date,
                                    patient_encounter.practitioner)

        if updated:
            patient_encounter.save()
            frappe.db.commit()  # Commit changes to the database
            frappe.msgprint(_("Patient Encount{0} Recieved successfully.").format(patient_encounter.name))

    return investigations

def create_pharmacy(drug, patient, encounter_id,date,practitioner):
    # Fetch the Patient document to get gender 
    patient_doc = frappe.get_doc('Patient', patient)
    patient_reg = frappe.get_doc('Patient Registration Identification', patient.custom_patient_mrno)
    
    # Logging for debugging
    frappe.log_error(f"Creating create_pharmacy for Patient: {patient}, Encounter ID: {encounter_id}", "create_pharmacy Creation")

    # Create a new Pharmacy document 
    pharmacy_doc = frappe.new_doc('Pharmacy')
    pharmacy_doc.patient = patient
    pharmacy_doc.patient_sex = patient_doc.sex
    pharmacy_doc.patient_age = patient_reg.age
    pharmacy_doc.encounter_date = date
    pharmacy_doc.practitioner = practitioner
    pharmacy_doc.patient_encounter_id = encounter_id  
    pharmacy_doc.medical_department = patient_doc.custom_consulting_department  
    # Append item to the Sales Invoice 
    pharmacy_doc.append("drug_prescription", {
        "drug_code": drug.drug_code,
        "dosage": drug.dosage,
        "period": drug.period,
        "qty": drug.custom_rate,
        "dosage_form": drug.dosage_form,
        "strength": drug.strength,
        "strength_uom": drug.strength_uom,

     
    })
    # Logging for debugging
    frappe.log_error(f"Pharmacy Doc Values: {pharmacy_doc.as_dict()}", "Pharmacy Doc Debug")

    pharmacy_doc.insert()
    frappe.db.commit()  # Commit changes to the database
   
