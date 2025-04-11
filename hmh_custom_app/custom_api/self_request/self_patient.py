import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def create_pharmacy(patient_doc):
    try:
        # Fetch the Patient Payment Management document and related Patient and Patient Registration Identification
        patient_doc = frappe.get_doc('Patient', patient_doc)
        patient_reg_doc = frappe.get_doc('Patient Registration Identification', patient_doc.custom_patient_mrno)
        pharmacy_doc = frappe.new_doc("Pharmacy")
        pharmacy_doc.update({
            "patient": patient_doc.name,
            "patient_sex": patient_doc.sex,
            "patient_age": patient_reg_doc.full_age,
            "encounter_date": patient_doc.date,
            "practitioner": patient_doc.custom_consulting_doctor,
            "price_list": patient_doc.default_price_list,
            "medical_department": patient_doc.custom_consulting_department,
            "drug_prescription": []
        })
        
        # Append item to the Pharmacy doc
        pharmacy_doc.append("drug_prescription", {
            "drug_code": item.item,
            "qty": 1,
            "amount": item.outstanding_amount,
            "dosage": '1-0-1',
            "dosage_form": 'Cream',
        })

        pharmacy_doc.insert()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in creating Pharmacy document"))
