import frappe
from frappe import _
from frappe.utils import nowdate, nowtime

def create_pharmacy_doc(doc, method):
    if not doc.custom_inpatient_discharge_drugs:
        return

    try:
        # Check for existing draft Pharmacy linked to the inpatient encounter
        existing_pharmacy = frappe.get_all(
            "Pharmacy",
            filters={
                "inpatient_id": doc.name,
                "docstatus": 0  # Draft status
            },
            limit=1
        )

        if existing_pharmacy:
            # Update the existing draft Pharmacy
            pharmacy_doc = frappe.get_doc("Pharmacy", existing_pharmacy[0].name)
        else:
            # Create a new Pharmacy document
            pharmacy_doc = frappe.new_doc("Pharmacy")

        # Populate common fields
        pharmacy_doc.update({
            "patient": doc.patient,
            "practitioner": doc.secondary_practitioner,
            "patient_sex": doc.gender,
            "encounter_date": nowdate(),
            "encounter_time": nowtime(),
            "inpatient_id": doc.name,
        })

        # Flag to check if any items should be added
        has_items_to_add = False

        for item in doc.custom_inpatient_discharge_drugs:
            if item.drug_status == "Sent to Pharmacy":
                # Skip items already sent to Pharmacy
                continue

            # Fetch the item document to validate existence
            item_code_doc = frappe.get_doc("Item", item.discharge_drugs)

            if not item_code_doc:
                frappe.throw(
                    _("Item {0} not found. Ensure that the item code is valid.").format(item.discharge_drugs)
                )

            # Append item to the drug_prescription table in Pharmacy
            pharmacy_doc.append("drug_prescription", {
                "drug_code": item.discharge_drugs,
                "qty": 1,
                "comment": item.comment,
                "dosage": "0-0-1",
                "dosage_form": "Tablet"
            })

            # Mark that we have items to add
            has_items_to_add = True

        if not has_items_to_add:
            # Exit if no valid items are added
            frappe.msgprint(_("No valid discharge drugs to send to Pharmacy."))
            return

        # Save or update the Pharmacy document
        pharmacy_doc.save(ignore_permissions=True)

        # Notify the user
        frappe.msgprint(_("Pharmacy {0} created/updated successfully.").format(pharmacy_doc.name))

        # Update `pharmacy_status` in the consumables table
        for dischard_drugs in doc.custom_inpatient_discharge_drugs:
            if dischard_drugs.drug_status != "Sent to Pharmacy":
                dischard_drugs.drug_status = "Sent to Pharmacy"

        # Save the parent document to persist updates
        doc.save(ignore_permissions=True)

    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.throw(_("Validation error while creating the Pharmacy: {0}").format(str(e)))

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(message=str(e), title="Pharmacy Creation Error")
        frappe.throw(
            _("An unexpected error occurred while creating the Pharmacy. Please contact support. Error details: {0}")
            .format(str(e))
        )
