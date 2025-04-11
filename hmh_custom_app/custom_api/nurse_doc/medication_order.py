from frappe.utils import add_days, getdate
import frappe
from frappe import _

@frappe.whitelist()
def populate_administer_drugs(doc_name):
    doc = frappe.get_doc("Nurses Document", doc_name)
    
    # Clear existing entries in the `administer_drugs` table
    doc.administer_drugs = []
    
    # Ensure `encounter_date` is a valid date
    if not doc.encounter_date:
        frappe.throw(_("Encounter Date is required to populate the Administer Drugs table."))
    
    encounter_date = getdate(doc.encounter_date)  # Ensure date format is consistent
    
    # Iterate through `administering_drugs_items`
    for item in doc.administering_drugs_items:
        # Determine the number of days from the `frequency`
        if "week" in item.frequency.lower():
            days = int(item.frequency.split()[0]) * 7
        elif "day" in item.frequency.lower():
            days = int(item.frequency.split()[0])
        elif "month" in item.frequency.lower():  # Handle monthly frequency
            months = int(item.frequency.split()[0])
            days = months * 30  # Approximate number of days in a month
        else:
            frappe.throw(_("Unsupported frequency format: {0}").format(item.frequency))
        
        # Parse the `Dosage` field
        dosage_parts = item.dosage.split("-")
        times_of_day = ["Morning", "Afternoon", "Evening"]

        for day_offset in range(days):  # Loop for the specified number of days
            administration_date = add_days(encounter_date, day_offset)  # Increment the date
            
            for idx, qty in enumerate(dosage_parts):
                if qty and int(qty) > 0:  # Only add rows where qty > 0
                    doc.append("administer_drugs", {
                        "drug_id": item.drug_id,
                        "administration_date": administration_date,
                        "frequency": times_of_day[idx] if idx < len(times_of_day) else "Unspecified",
                        "qty": int(qty)
                    })
    
    # Save and commit changes
    doc.save()
    frappe.db.commit()
