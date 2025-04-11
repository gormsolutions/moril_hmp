import frappe
from frappe import _

def on_submit(doc, method):
    if doc.custom_radiology_items:
        try:
            # Fetch the Patient document
            patient_doc = frappe.get_doc('Patient', doc.patient)
            customer = frappe.get_doc('Customer', patient_doc.customer)
            
            # Get the default receivable account from Company
            receivable_account = frappe.get_value('Company', doc.company, 'default_receivable_account')
            
            # If not found, get it from the Customer Group
            if not receivable_account:
                customer_group = frappe.get_doc('Customer Group', customer.customer_group)
                if customer_group.accounts:
                    for default in customer_group.accounts:
                        if default.account:
                            receivable_account = default.account
                            break
            
            if not receivable_account:
                frappe.throw(_("Default Receivable Account is not set for the company {0} or the customer group {1}").format(doc.company, customer.customer_group))
            
            # Check if there is an existing draft Sales Invoice for the same encounter
            existing_invoice = frappe.get_all("Sales Invoice", 
                                              filters={
                                                  "custom_patient_ecounter_id": doc.name,
                                                  "docstatus": 0  # Draft status
                                              }, 
                                              limit=1)
            
            if existing_invoice:
                # Update the existing draft Sales Invoice
                sales_invoice = frappe.get_doc("Sales Invoice", existing_invoice[0].name)
                sales_invoice.set_posting_time = 1
                sales_invoice.cost_center = doc.custom_cost_center
                sales_invoice.posting_date = doc.encounter_date
                
                # Handle None values for due_date
                encounter_date = doc.encounter_date or frappe.utils.nowdate()
                custom_due_date = doc.custom_due_date or encounter_date
                sales_invoice.due_date = max(custom_due_date, encounter_date)
                
            else:
                # Create a new Sales Invoice
                sales_invoice = frappe.new_doc("Sales Invoice")
                sales_invoice.customer = patient_doc.customer
                sales_invoice.patient = doc.patient
                sales_invoice.set_posting_time = 1
                sales_invoice.posting_date = doc.encounter_date
                
                # Handle None values for due_date
                encounter_date = doc.encounter_date or frappe.utils.nowdate()
                custom_due_date = doc.custom_due_date or encounter_date
                sales_invoice.due_date = max(custom_due_date, encounter_date)
                
                sales_invoice.cost_center = doc.custom_cost_center
                sales_invoice.custom_patient_ecounter_id = doc.name
                sales_invoice.debit_to = receivable_account
                sales_invoice.items = []

            # Flag to check if any item should be added
            has_items_to_add = False

            for item in doc.custom_radiology_items:
                # Only add items that are not fully paid and have not been invoiced yet
                if item.radiology_status != "Fully Paid" and item.from_sales_invoice != "Invoice Created":
                    if not item.item_code or not item.amount:
                        frappe.log_error(f"Missing data in custom_items: {item.as_dict()}", "Sales Invoice Creation Error")
                        frappe.throw(_("Missing data for item {0}. Ensure that item code and amount are provided.").format(item.item))
                    
                    # Append item to the Sales Invoice
                    sales_invoice.append("items", {
                        "item_code": item.item_code,
                        "qty": 1,
                        "rate": item.amount,
                        "cost_center": doc.custom_cost_center,
                    })
                    
                    # Set flag to true if at least one item is added
                    has_items_to_add = True

            if not has_items_to_add:
                # If no items are added, show message and proceed
                return
            
            else:
                # Save or update the Sales Invoice as a draft
                sales_invoice.save(ignore_permissions=True)
                frappe.msgprint(_("Please Go to the Reception. A Sales Invoice {0} was created/updated successfully.").format(sales_invoice.name))
                
                # Update `custom_invoice_status` in the Lab Prescription table
                for radiology in doc.custom_radiology_items:
                    if radiology.radiology_status != "Fully Paid" and radiology.from_sales_invoice != "Invoice Created":
                        radiology.from_sales_invoice = "Invoice Created"
                doc.save()
                frappe.db.commit()
                        
                investigations = []
                # Check if the customer group is 'Insurance' and create a Lab Test 
                if customer.customer_group == "Insurance" or customer.custom_bill_status == "Bill Later":
                    for procedure in doc.custom_radiology_items:
                        if procedure.radiology_status != "Fully Paid" or procedure.from_sales_invoice != "Invoice Created":
                            procedure.radiology_status = "Fully Paid"
                            procedure.from_sales_invoice = "Invoice Created"
                            procedure.results_status = "Processing Results"
                            investigations.append(procedure)
                            doc.save()
                            frappe.db.commit()  # Commit changes to the database
                            # Create a new Radiology document
                            procedure_doc = frappe.new_doc('Observation')
                            procedure_doc.observation_template = procedure.radiology_investigation  # Assuming Radiology has a field named lab_test_code
                            procedure_doc.patient = patient_doc
                            procedure_doc.invoiced = 1
                            procedure_doc.posting_date = doc.encounter_date
                            procedure_doc.healthcare_practitioner = doc.practitioner
                            procedure_doc.custom_patient_encounter_id = doc.name  # Use the encounter_id passed to the function
                            
                            procedure_doc.save()
                            frappe.db.commit()  # Commit changes to the database

        except frappe.ValidationError as e:
            frappe.db.rollback()
            frappe.throw(_("There was an error creating the Sales Invoice: {0}").format(str(e)))

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(message=str(e), title="Sales Invoice Creation Error")
            frappe.throw(_("An unexpected error occurred while creating the Sales Invoice. Please try again or contact support. Error details: {0}").format(str(e)))
