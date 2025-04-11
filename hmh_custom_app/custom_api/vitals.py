import frappe
from frappe import _

@frappe.whitelist()
def create_patient_encounter(patient, encounter_date, vital_signs, practitioner, patient_name):
    try:
        # Retrieve the Patient document 
        patient_doc = frappe.get_doc('Patient', patient)
        doc_vitals = frappe.get_doc('Vital Signs', vital_signs)
        reg_doc = frappe.get_doc('Patient Registration Identification', patient_doc.custom_patient_mrno)
        
        # Get the cost center from the consulting doctor's profile
        cost_center = frappe.get_value('Healthcare Practitioner', patient_doc.custom_consulting_doctor, 'custom_cost_centre')
        
        # Check if a Patient Encounter document already exists for this patient with the given vital signs
        existing_encounters = frappe.get_all("Patient Encounter", filters={
            "custom_vitals_id": vital_signs,
        })
        
        if existing_encounters:
            return {
                "message": _(f"A Patient Encounter with Vital Signs {vital_signs} already exists.")
            }
         
        # Check if doc_vitals.custom_encounter_id is set
        if doc_vitals.custom_encounter_id:
            existing_draft_encounter = frappe.get_all("Patient Encounter", filters={
                "name": doc_vitals.custom_encounter_id,
                "docstatus": 0  # Check for draft documents only
            }, limit=1)

            if existing_draft_encounter:
                # Get the draft Patient Encounter
                patient_encounter = frappe.get_doc("Patient Encounter", existing_draft_encounter[0].name)
                
                # Add items from doc_vitals to custom_vital_items in the existing draft Patient Encounter
                patient_encounter.append("custom_vital_items", {
                        "blood_pressure": doc_vitals.bp,
                        "spo2": doc_vitals.custom_spo2_,
                        "pulse": doc_vitals.pulse,
                        "weight_in_kilogram": doc_vitals.weight,
                        "body_temperature": doc_vitals.temperature
                })
                
                # Save the updated draft Patient Encounter
                patient_encounter.save(ignore_permissions=True)
                
                return {
                    "message": _("Vital Signs updated successfully in the existing draft Patient Encounter."),
                    "patient_encounter_name": patient_encounter.name
                }

        # Create a new Patient Encounter document if no draft encounter exists or if doc_vitals.custom_encounter_id is not set
        patient_encounter = frappe.get_doc({
            "doctype": "Patient Encounter",
            "patient": patient,
            "patient_name": patient_name,
            "encounter_date": encounter_date,
            "custom_cost_center": cost_center,
            "status": "Open",
            "consultation_charge": patient_doc.custom_invoice_no,  # Ensure this field exists in Patient doctype
            "practitioner": practitioner,
            "patient_age":reg_doc.age_summary,
            "custom_vitals_id": vital_signs  # Ensure this field exists in Patient Encounter doctype
        })
        
        # Add items from doc_vitals to custom_vital_items in the new Patient Encounter
        patient_encounter.append("custom_vital_items", {
            "blood_pressure": doc_vitals.bp,
            "spo2": doc_vitals.custom_spo2_,
            "pulse": doc_vitals.pulse,
            "weight_in_kilogram": doc_vitals.weight,
            "body_temperature": doc_vitals.temperature
        })

        # Insert the new Patient Encounter document
        patient_encounter.insert(ignore_permissions=True)
        
        return {
            "message": _("Direct the Patient to go and See the Doctor. Vital Signs updated successfully."),
            "patient_encounter_name": patient_encounter.name
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Patient Encounter Creation Error')
        return {"error": str(e)}
