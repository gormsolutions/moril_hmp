import frappe

@frappe.whitelist()
def update_admission_status_for_all_patients():
    # Get all Patient docs where admission_status is "Admitted"
    patients = frappe.get_all("Patient", filters={"inpatient_record": "Admitted"}, fields=["name", "inpatient_record", "custom_patient_mrno"])

    for patient in patients:
        # Get the Patient Registration Identification doc matching custom_patient_mrno
        pri_doc = frappe.get_doc("Patient Registration Identification", {"name": patient.custom_patient_mrno})
        if pri_doc:
            # Update the admission_status field in Patient Registration Identification
            pri_doc.admission_status = patient.inpatient_record
            pri_doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.msgprint(f"Updated admission_status for Patient Registration Identification: {patient.custom_patient_mrno}")
        else:
            frappe.msgprint(f"No matching Patient Registration Identification found for Patient: {patient.custom_patient_mrno}")

    return "Admission statuses updated for all matching Patient Registration Identifications."

