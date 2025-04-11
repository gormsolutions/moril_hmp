import frappe
from frappe import _

@frappe.whitelist()
def radiology_status(docname):
    """
    Update the status of observation test prescriptions in related Patient Encounter documents.
    
    Args:
        docname (str): The name of the Observation Test document to update status for.
        
    Returns:
        dict: A dictionary containing the status and message of the operation.
    """
    try:
        # Fetch the Lab Test document
        observe_test = frappe.get_doc('Observation', docname)
        
        # Get related Patient Encounter documents
        encounters = frappe.get_all(
            'Patient Encounter',
            filters={
                'name': observe_test.custom_patient_encounter_id,
                'docstatus': 0  # Ensuring that only submitted documents are included
            },
            fields=['name']
        )
        
        for encounter in encounters:
            # Load the Patient Encounter document
            encounter_doc = frappe.get_doc('Patient Encounter', encounter['name'])
            
            # Update custom_results_status with plain text indicating readiness
            for prescription in encounter_doc.custom_radiology_items:
                if (prescription.results_status == "Processing Results" and 
                    prescription.radiology_investigation == observe_test.observation_template):
                    # Update the custom_results_status and custom_labtest_id
                    prescription.results_status = "Results Ready"
                    prescription.observe_id = docname
                    # Exit the loop after updating the relevant prescription
                    break
            
            # Save the changes to the Patient Encounter document
            encounter_doc.save()
        
        return {"status": "success", "message": "Results Sent Back to the Doctor successfully"}

    except frappe.DoesNotExistError:
        # Handle case where Lab Test or Patient Encounter does not exist
        return {"status": "error", "message": "Lab Test or Patient Encounter does not exist"}

    except frappe.ValidationError as e:
        # Handle validation errors from saving the document
        return {"status": "error", "message": str(e)}

    except Exception as e:
        # Handle any other exceptions
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
