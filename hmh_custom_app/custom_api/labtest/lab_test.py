import frappe
from frappe import _

@frappe.whitelist()
def lab_status(docname):
    """
    Update the status of lab test prescriptions in related Patient Encounter documents.
    
    Args:
        docname (str): The name of the Lab Test document to update status for.
        
    Returns:
        dict: A dictionary containing the status and message of the operation.
    """
    try:
        # Fetch the Lab Test document
        lab_test = frappe.get_doc('Lab Test', docname)
        
        # Get related Patient Encounter documents
        encounters = frappe.get_all(
            'Patient Encounter',
            filters={
                'name': lab_test.custom_encounter_id,
                'docstatus': 0  # Ensuring that only submitted documents are included
            },
            fields=['name']
        )
        
        for encounter in encounters:
            # Load the Patient Encounter document
            encounter_doc = frappe.get_doc('Patient Encounter', encounter['name'])
            
            # Update custom_results_status with plain text indicating readiness
            for prescription in encounter_doc.lab_test_prescription:
                if (prescription.custom_results_status == "Processing Results" and 
                    prescription.lab_test_code == lab_test.template):
                    # Update the custom_results_status and custom_labtest_id
                    prescription.custom_results_status = "Results Ready"
                    prescription.custom_labtest_id = docname
                    # Exit the loop after updating the relevant prescription
                    break
            
            # Save the changes to the Patient Encounter document
            encounter_doc.save()
        
        return {"status": "success", "message": "Updated successfully"}

    except frappe.DoesNotExistError:
        # Handle case where Lab Test or Patient Encounter does not exist
        return {"status": "error", "message": "Lab Test or Patient Encounter does not exist"}

    except frappe.ValidationError as e:
        # Handle validation errors from saving the document
        return {"status": "error", "message": str(e)}

    except Exception as e:
        # Handle any other exceptions
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
