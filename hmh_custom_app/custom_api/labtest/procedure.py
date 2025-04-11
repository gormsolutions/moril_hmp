import frappe
from frappe import _

@frappe.whitelist()
def procedure_status(docname):
    """
    Update the status of lab test prescriptions in related Patient Encounter documents
    only if the procedure test status is 'Completed'.
    
    Args:
        docname (str): The name of the Lab Test document to update status for.
        
    Returns:
        dict: A dictionary containing the status and message of the operation.
    """
    try:
        # Fetch the procedure Test document
        procedure_test = frappe.get_doc('Clinical Procedure', docname)
        
        # Check if the procedure status is 'Completed'
        if procedure_test.status != 'Completed':
            msg = "Procedure Results not sent to Doctor Because status is not 'Completed',. Please Start >> Complete  and >> Send Results To Doctor"
            # frappe.msgprint(msg, alert=True)
            # return {"status": "info", "message": msg}
            return frappe.msgprint(msg)
        
        # Get related Patient Encounter documents
        encounters = frappe.get_all(
            'Patient Encounter',
            filters={
                'name': procedure_test.custom_patient_encount_id,
                'docstatus': 0  # Ensuring that only submitted documents are included
            },
            fields=['name']
        )
        
        for encounter in encounters:
            # Load the Patient Encounter document
            encounter_doc = frappe.get_doc('Patient Encounter', encounter['name'])
            
            # Update custom_results_status with plain text indicating readiness
            for prescription in encounter_doc.procedure_prescription:
                if (prescription.custom_proceding_status == "Processing Results" and 
                    prescription.procedure == procedure_test.procedure_template):
                    # Update the custom_results_status and custom_labtest_id
                    prescription.custom_proceding_status = "Results Ready"
                    prescription.custom_procedure_id = docname
                    # Exit the loop after updating the relevant prescription
                    break
            
            # Save the changes to the Patient Encounter document
            encounter_doc.save()
        
        return {"status": "success", "message": "Results successfully Sent"}

    except frappe.DoesNotExistError:
        # Handle case where Lab Test or Patient Encounter does not exist
        return {"status": "error", "message": "Lab Test or Patient Encounter does not exist"}

    except frappe.ValidationError as e:
        # Handle validation errors from saving the document
        return {"status": "error", "message": str(e)}

    except Exception as e:
        # Handle any other exceptions
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
