import frappe
from frappe import _

def on_submit(doc, method):
    if doc.lab_test_prescription:
        try:
            # Fetch the Patient document
            patient_doc = frappe.get_doc('Patient', doc.patient)
            customer = frappe.get_doc('Customer', patient_doc.customer)
            
            # Get the default receivable account from Company
            receivable_account = frappe.get_value('Company', doc.company, 'default_receivable_account')
            
            # If not found, get it from the Customer Group
            if not receivable_account:
                customer_group = frappe.get_doc('Customer Group', customer.customer_group)
                receivable_account = next(
                    (account.account for account in customer_group.accounts if account.account), 
                    None
                )
            
            if not receivable_account:
                frappe.throw(_("Default Receivable Account is not set for the company {0} or the customer group {1}").format(doc.company, customer.customer_group))
            
            # Check if there is an existing draft Sales Invoice for the same encounter
            existing_invoice = frappe.get_all(
                "Sales Invoice", 
                filters={
                    "custom_patient_ecounter_id": doc.name,
                    "docstatus": 0  # Draft status
                }, 
                limit=1
            )
            
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
                
                # sales_invoice.items = []
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

            for item in doc.lab_test_prescription:
                if item.custom_lab_status == "Fully Paid" or item.custom_invoice_status == "Invoice Created":
                    # Skip items that are already paid or invoiced
                    continue
                
                if not item.custom_item_code or not item.custom_amount:
                    frappe.log_error(f"Missing data in lab_test_prescription: {item.as_dict()}", "Sales Invoice Creation Error")
                    frappe.throw(_("Missing data for item {0}. Ensure that item code and amount are provided.").format(item.item))
                
                # Append item to the Sales Invoice
                sales_invoice.append("items", {
                    "item_code": item.custom_item_code,
                    "qty": 1,
                    "rate": item.custom_amount,
                    "cost_center": doc.custom_cost_center,
                })
                
                # Set flag to true if at least one item is added
                has_items_to_add = True

            if has_items_to_add:
                # Save or update the Sales Invoice as a draft
                sales_invoice.save(ignore_permissions=True)
                frappe.msgprint(_("Sales Invoice {0} created/updated successfully.").format(sales_invoice.name))
                
                # Update the `custom_invoice_status` in the Lab Test Prescription table
                for lab_test in doc.lab_test_prescription:
                    if lab_test.custom_lab_status != "Fully Paid" and lab_test.custom_invoice_status != "Invoice Created":
                        lab_test.custom_invoice_status = "Invoice Created"
                
                doc.save()
                frappe.db.commit()
            
                # Check if the customer group is 'Insurance' and create a Lab Test 
                if customer.customer_group == "Insurance" or customer.custom_bill_status == "Bill Later":
                    for lab_test in doc.lab_test_prescription:
                        if lab_test.custom_lab_status != "Fully Paid" or lab_test.custom_invoice_status != "Invoice Created":
                            lab_test.custom_lab_status = "Fully Paid"
                            lab_test.custom_invoice_status = "Invoice Created"
                            lab_test.custom_results_status = "Processing Results"
                            lab_test.invoiced = 1
                       
                            # Create a new Lab Test document
                            lab_test_doc = frappe.new_doc('Lab Test')
                            lab_test_doc.template = lab_test.lab_test_code
                            lab_test_doc.patient = patient_doc.name
                            lab_test_doc.patient_sex = patient_doc.sex
                            lab_test_doc.custom_encounter_id = doc.name
                            lab_test_doc.date = doc.encounter_date
                            lab_test_doc.practitioner = doc.practitioner
                            lab_test_doc.invoiced = 1
                            lab_test_doc.save()
                            frappe.db.commit()  # Commit changes to the database
            # else:
                # If no items are added, show a message
                # frappe.msgprint(_("No items were added to the Sales Invoice."))

        except frappe.ValidationError as e:
            frappe.db.rollback()
            frappe.throw(_("There was an error creating the Sales Invoice: {0}").format(str(e)))

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(message=str(e), title="Sales Invoice Creation Error")
            frappe.throw(_("An unexpected error occurred while creating the Sales Invoice. Please try again or contact support. Error details: {0}").format(str(e)))

