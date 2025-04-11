import frappe
from frappe import _

@frappe.whitelist()
def create_nurse_doc(doc, method=None):
    """
    Creates or updates a Nurses Document based on the provided pharmacy document.
    
    Args:
        doc: The pharmacy document triggering this function.
        method: The Frappe method triggering this function (usually 'on_submit' or 'on_update').
    """
    try:
        # Ensure that doc is a Frappe document object
        pharmacy_doc = frappe.get_doc("Pharmacy", doc) if isinstance(doc, str) else doc

        # If nurse_doc_id exists, no need to proceed
        if pharmacy_doc.nurse_doc_id:
            return  frappe.msgprint(
            _("Nurses Document {0} already Created.").format(pharmacy_doc.nurse_doc_id)
        )

        # Check if a draft Nurses Document already exists for the pharmacy document
        existing_nurse_doc = frappe.get_all(
            "Nurses Document",
            filters={
                "pharmacy_id": pharmacy_doc.name,
                "docstatus": 0  # Draft status
            },
            limit=1
        )

        if existing_nurse_doc:
            # Load the existing draft Nurses Document
            nurse_doc = frappe.get_doc("Nurses Document", existing_nurse_doc[0].name)
            # Update encounter details
            nurse_doc.encounter_date = pharmacy_doc.encounter_date
            nurse_doc.encounter_time = pharmacy_doc.encounter_time
            # Clear existing drug items
            nurse_doc.administering_drugs_items = []
        else:
            # Create a new Nurses Document
            nurse_doc = frappe.new_doc("Nurses Document")
            nurse_doc.patient = pharmacy_doc.patient
            nurse_doc.patient_encounter_id = pharmacy_doc.patient_encounter_id
            nurse_doc.healthcare_practitioner = pharmacy_doc.practitioner
            nurse_doc.gender = pharmacy_doc.patient_sex
            nurse_doc.age = pharmacy_doc.patient_age
            nurse_doc.patient_type = "IPD"
            nurse_doc.encounter_date = pharmacy_doc.encounter_date
            nurse_doc.encounter_time = pharmacy_doc.encounter_time
            nurse_doc.pharmacy_id = pharmacy_doc.name
            nurse_doc.administering_drugs_items = []

        # Add drug prescriptions to the Nurses Document
        for item in pharmacy_doc.drug_prescription:
            nurse_doc.append("administering_drugs_items", {
                "drug_id": item.drug_code,
                "dosage": item.dosage,
                "frequency": item.period,
                "status": "Pending"
            })

        # Save the Nurses Document as a draft
        nurse_doc.save(ignore_permissions=True)

        # Update the pharmacy_doc.nurse_doc_id field with the newly created nurse_doc
        pharmacy_doc.nurse_doc_id = nurse_doc.name
        pharmacy_doc.save(ignore_permissions=True)

        # Notify the user of successful creation/update
        frappe.msgprint(
            _("Nurses Document {0} created/updated successfully.").format(nurse_doc.name)
        )

    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.throw(
            _("There was an error creating the Nurses Document: {0}").format(str(e))
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(message=str(e), title="Nurses Document Creation Error")
        frappe.throw(
            _("An unexpected error occurred while creating the Nurses Document. Please try again or contact support. Error details: {0}").format(str(e))
        )
