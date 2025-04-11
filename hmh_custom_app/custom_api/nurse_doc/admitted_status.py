import frappe

@frappe.whitelist()
def update_inpatient_status():
    # Fetch records from Pharmacy where inpatient_status is empty
    patients = frappe.get_all(
        "Pharmacy",
        filters={"inpatient_status": ""},
        fields=["name", "patient"]  # Ensure 'patient' field is included
    )
    
    updated_count = 0  # To track the number of updated Pharmacy records
    debug_info = []    # To collect debug information

    for patient in patients:
        # Fetch the status from the Inpatient Record doctype for this specific patient
        inpatient_status = frappe.db.get_value(
            "Inpatient Record", 
            {"patient": patient["patient"]},  # Use dynamic patient assignment
            "status"
        )
        
        # Log data for debugging
        debug_info.append({
            "pharmacy_name": patient["name"],
            "patient_id": patient["patient"],
            "inpatient_status_found": inpatient_status
        })
        
        if inpatient_status:
            # Update the inpatient_status field for the Pharmacy
            frappe.db.set_value("Pharmacy", patient["name"], "inpatient_status", inpatient_status)
            updated_count += 1

    # Return both debug info and count for better insights
    return {
        "updated_count": updated_count,
        "debug_info": debug_info
    }


@frappe.whitelist()
def update_inpatient_nurse():
    # Fetch records from Pharmacy where inpatient_status is empty
    patients = frappe.get_all(
        "Nurses Document",
        filters={"inpatient_status": ""},
        fields=["name", "patient"]  # Ensure 'patient' field is included
    )
    
    updated_count = 0  # To track the number of updated Pharmacy records
    debug_info = []    # To collect debug information

    for patient in patients:
        # Fetch the status from the Inpatient Record doctype for this specific patient
        inpatient_status = frappe.db.get_value(
            "Inpatient Record", 
            {"patient": patient["patient"]},  # Use dynamic patient assignment
            "status"
        )
        
        # Log data for debugging
        debug_info.append({
            "pharmacy_name": patient["name"],
            "patient_id": patient["patient"],
            "inpatient_status_found": inpatient_status
        })
        
        if inpatient_status:
            # Update the inpatient_status field for the Pharmacy
            frappe.db.set_value("Nurses Document", patient["name"], "inpatient_status", inpatient_status)
            updated_count += 1

    # Return both debug info and count for better insights
    return {
        "updated_count": updated_count,
        "debug_info": debug_info
    }
