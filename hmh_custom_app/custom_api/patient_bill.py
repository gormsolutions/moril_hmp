import frappe
from frappe import _

def on_submit(doc, method):
    if doc.custom_items:
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
                sales_invoice.due_date = max(doc.custom_due_date, doc.encounter_date) 
                sales_invoice.items = []  # Clear existing items
            else:
                # Create a new Sales Invoice
                sales_invoice = frappe.new_doc("Sales Invoice")
                sales_invoice.customer = patient_doc.customer
                sales_invoice.patient = doc.patient  # Assuming patient is linked to customer
                sales_invoice.set_posting_time = 1
                sales_invoice.posting_date = doc.encounter_date
                sales_invoice.due_date = max(doc.custom_due_date, doc.encounter_date)  # Ensure due date is not before posting date
                sales_invoice.cost_center = doc.custom_cost_center
                sales_invoice.custom_patient_ecounter_id = doc.name
                sales_invoice.debit_to = receivable_account
                sales_invoice.items = []
            
            for item in doc.custom_items:
                if not item.item or not item.qty or not item.rate:
                    frappe.log_error(f"Missing data in custom_items: {item.as_dict()}", "Sales Invoice Creation Error")
                    frappe.throw(_("Missing data for item {0}. Ensure that item code, quantity, and rate are provided.").format(item.item))
                
                sales_invoice.append("items", {
                    "item_code": item.item,  # Assuming item.item is the correct field
                    "qty": item.qty,
                    "rate": item.rate,
                    "cost_center": doc.custom_cost_center,
                })
                
            # Save or update the Sales Invoice as a draft
            sales_invoice.save(ignore_permissions=True)
            
            # Notify user
            frappe.msgprint(_("Sales Invoice {0} created/updated successfully.").format(sales_invoice.name))
        
        except frappe.ValidationError as e:
            frappe.db.rollback()
            frappe.throw(_("There was an error creating the Sales Invoice: {0}").format(str(e)))

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(message=str(e), title="Sales Invoice Creation Error")
            frappe.throw(_("An unexpected error occurred while creating the Sales Invoice. Please try again or contact support. Error details: {0}").format(str(e)))
