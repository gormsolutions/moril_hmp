import frappe
from frappe import _

@frappe.whitelist()
def create_vital_signs_for_patient(doc_name):
    # Check if a draft Vital Signs document already exists for this patient
    existing_vital_signs = frappe.get_all("Vital Signs", filters={
        "patient": doc_name,
        "custom_patient_status": "Seen The Receptionist",
        "docstatus": 0  # Ensure it's in draft state
    })

    if not existing_vital_signs:
        # Create a new Vital Signs document in draft state
        try:
            vital_signs = frappe.get_doc({
                "doctype": "Vital Signs",
                "patient": doc_name,
                "custom_practionaer": frappe.get_doc("Patient", doc_name).custom_consulting_doctor,
                "custom_patient_status": "Seen The Receptionist",
                "custom_customer_type": frappe.get_doc("Patient", doc_name).customer_group,
                "custom_invoice_no": frappe.get_doc("Patient", doc_name).custom_invoice_no,
            })
            vital_signs.insert(ignore_permissions=True)
            return "Vital Signs created successfully."
        except Exception as e:
            frappe.log_error(f"Failed to create Vital Signs for patient {doc_name}: {str(e)}", "Vital Signs Creation Error")
            return f"Error: {str(e)}"
    else:
        return "Vital Signs document already exists."
    
    
    import frappe



@frappe.whitelist()
def create_patient_encounter(doc_name):
    try:
        # Retrieve the Patient document 
        patient_doc = frappe.get_doc('Patient', doc_name)
        reg_doc = frappe.get_doc('Patient Registration Identification', patient_doc.custom_patient_mrno)
        
        # Get the cost center from the consulting doctor's profile
        cost_center = frappe.get_value('Healthcare Practitioner', patient_doc.custom_consulting_doctor, 'custom_cost_centre')
        
        # Check if a Patient Encounter document already exists for this patient and today's date
        # existing_encounters = frappe.get_all("Patient Encounter", filters={
        #     "patient": doc_name,
        #     "encounter_date": frappe.utils.nowdate()
        # })
        
        # if existing_encounters:
        #     return {
        #         "message": _(f"A Patient Encounter with patient {doc_name} for today already exists.")
        #     }

        # Create a new Patient Encounter document
        patient_encounter = frappe.get_doc({
            "doctype": "Patient Encounter",
            "patient": doc_name,
            "patient_name": patient_doc.patient_name,
            "encounter_date": frappe.utils.nowdate(),
            "custom_cost_center": cost_center,
            "status": "Open",
            "consultation_charge": patient_doc.custom_invoice_no,  # Ensure this field exists
            "practitioner": patient_doc.custom_consulting_doctor,
            "patient_age": reg_doc.age_summary,
            "custom_review_status": "Sent For Reviews"  # Ensure this field exists
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


import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def create_sales_invoice(patient, customer,reason):
    """
    Create a Sales Invoice with the specified details.

    Args:
        patient (str): Name of the Patient.
        customer (str): Customer linked to the Patient.
        time (str): Custom time field.
        reason (float): Review fee amount.

    Returns:
        dict: Details of the created Sales Invoice or an error message.
    """
    try:
        # Create the Sales Invoice document
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "patient":patient,
            "posting_date": frappe.utils.nowdate(),
            "set_posting_time":1,
            "customer": customer,
            "items": [
                {
                    "item_code": "Review Fee",  # Ensure this item exists in your Item master
                    "qty": 1,
                    "rate": reason,  # Use the 'reason' value as the fee
                    "description": f"Review Fee for Patient {patient} "
                }
            ],
            "remarks": f"Sales Invoice for Patient {patient}."
        })

        # Insert and submit the Sales Invoice
        sales_invoice.insert()
        sales_invoice.submit()

        # Return the name of the created Sales Invoice
        return {"message": sales_invoice.name}

    except frappe.ValidationError as e:
        frappe.log_error(frappe.get_traceback(), "Sales Invoice Creation Error")
        return {"message": None, "error": f"Validation Error: {str(e)}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Invoice Creation Error")
        return {"message": None, "error": f"An unexpected error occurred: {str(e)}"}

@frappe.whitelist()
def get_item_price(item_code):
    """
    Fetch the price of the specified item from the Item Price list.

    Args:
        item_code (str): The item code for which to fetch the price.

    Returns:
        float: The price of the item, or 0 if not found.
    """
    try:
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "selling": 1},  # Fetch selling price
            "price_list_rate"
        )
        return price or 0  # Return 0 if price is not found
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching item price")
        return 0
