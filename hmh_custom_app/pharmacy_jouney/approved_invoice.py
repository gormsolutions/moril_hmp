import frappe
from frappe import _

def on_submit(doc, method):
    # Check if payment_status is already set; if so, exit the function
    if doc.payment_status:
        return
    
    if doc.patient:
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
                                                  "custom_pharmacy_id": doc.name,
                                                  "docstatus": 0  # Draft status
                                              }, 
                                              limit=1)
            
            if existing_invoice:
                # Update the existing draft Sales Invoice
                sales_invoice = frappe.get_doc("Sales Invoice", existing_invoice[0].name)
                sales_invoice.set_posting_time = 1
                sales_invoice.cost_center = doc.medical_department
                sales_invoice.posting_date = doc.encounter_date
                
                # Handle None values for due_date
                encounter_date = doc.encounter_date or frappe.utils.nowdate()
                sales_invoice.due_date = encounter_date
                
                sales_invoice.items = []
            else:
                # Create a new Sales Invoice
                sales_invoice = frappe.new_doc("Sales Invoice")
                sales_invoice.customer = patient_doc.customer
                sales_invoice.patient = doc.patient
                sales_invoice.set_posting_time = 1
                sales_invoice.posting_date = doc.encounter_date
                
                # Handle None values for due_date
                encounter_date = doc.encounter_date or frappe.utils.nowdate()
                sales_invoice.due_date = encounter_date
                
                sales_invoice.cost_center = doc.medical_department
                sales_invoice.custom_pharmacy_id = doc.name
                sales_invoice.debit_to = receivable_account
                sales_invoice.items = []

            for item in doc.drug_prescription:
                # Append item to the Sales Invoice
                sales_invoice.append("items", {
                        "item_code": item.drug_code,
                        "qty": item.qty,
                        "rate": item.rate,
                        "cost_center": doc.medical_department,
                })
            
            # Save or update the Sales Invoice as a draft
            sales_invoice.save(ignore_permissions=True)
            sales_invoice.submit()
            
            # Update the following fields before committing to the database
            doc.sales_invoice_id = sales_invoice.name
            doc.payment_status = "Payment Pending"
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            frappe.msgprint(_("Sales Invoice {0} created/updated successfully.").format(sales_invoice.name))
             
        except frappe.ValidationError as e:
            frappe.db.rollback()
            frappe.throw(_("There was an error creating the Sales Invoice: {0}").format(str(e)))

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(message=str(e), title="Sales Invoice Creation Error")
            frappe.throw(_("An unexpected error occurred while creating the Sales Invoice. Please try again or contact support. Error details: {0}").format(str(e)))

@frappe.whitelist()
def pharmacy_status(custom_payment_id):
    # Get all Sales Invoices where custom_payment_id matches and exclude canceled and drafts
    invoices = frappe.get_all(
        'Sales Invoice',
        filters={
            'patient': custom_payment_id,
            'docstatus': 1  # Only includes submitted documents
        },
        fields=['name', 'outstanding_amount', 'custom_pharmacy_id']
    )
    
    # Extract custom_pharmacy_id from invoices
    pharmacy_ids = [invoice.custom_pharmacy_id for invoice in invoices if invoice.custom_pharmacy_id]
    
    if not pharmacy_ids:
        return "No Pharmacy doc found."

    # Find the corresponding Pharmacy documents
    pharmacies = frappe.get_all(
        'Pharmacy',
        filters={'name': ['in', pharmacy_ids]},
        fields=['name', 'approval_status', 'payment_status', 'patient']
    )

    investigations = []
    
    for pharmacy in pharmacies:
        # Fetch the Pharmacy document
        patient_pharmacy = frappe.get_doc('Pharmacy', pharmacy.name)
        updated = False
        
        # Fetch related Patient and Customer documents
        patient_id = frappe.get_doc('Patient', patient_pharmacy.patient)
        customer_id = frappe.get_doc('Customer', patient_id.customer)
        
        # Filter invoices matching the current pharmacy
        matching_invoices = [invoice for invoice in invoices if invoice.custom_pharmacy_id == pharmacy.name]
        
        # Check the criteria for updating payment status and creating the Stock Entry
        if (patient_pharmacy.approval_status != 'Approved To Be Issued' and (
            customer_id.customer_group == 'Insurance' or 
            customer_id.custom_bill_status == 'Bill Later' or
            all(invoice.outstanding_amount <= 0 for invoice in matching_invoices))):
            
            # Update payment and approval statuses
            if customer_id.customer_group == 'Insurance' or customer_id.custom_bill_status == 'Bill Later':
                patient_pharmacy.payment_status = "Pending Payment"
            elif all(invoice.outstanding_amount <= 0 for invoice in matching_invoices):
                patient_pharmacy.payment_status = "Fully Paid"
            
            patient_pharmacy.approval_status = 'Approved To Be Issued'
            updated = True
            
            # Create new Stock Entry after updating the payment status
            se = frappe.new_doc('Stock Entry')
            se.stock_entry_type = 'Material Issue'
            se.from_warehouse = patient_pharmacy.store
            se.remarks = f"{patient_pharmacy.patient} - {patient_pharmacy.name}"
            se.posting_date = patient_pharmacy.encounter_date
            se.posting_time = patient_pharmacy.encounter_time
            se.custom_patient_id = patient_pharmacy.patient
            se.custom_pharmacy_id = patient_pharmacy.name

            # Add Stock Entry details based on Medication Entry items
            for item in patient_pharmacy.drug_prescription:
                item_code = item.drug_code
                item_doc = frappe.get_doc('Item', item_code)
                uom = item_doc.stock_uom  # Retrieve the UOM from the Item document
                
                se.append('items', {
                    'item_code': item_code,
                    'qty': item.qty,
                    'uom': uom,
                    'transfer_qty': item.qty,
                    'cost_center': patient_pharmacy.custom_cost_center
                })

            se.insert()
            se.submit()
        
        elif (patient_pharmacy.approval_status != 'Approved To Be Issued' and
              any(invoice.outstanding_amount > 0 for invoice in matching_invoices)):
            patient_pharmacy.payment_status = "Partially Paid"
            updated = True
        
        if updated:
            patient_pharmacy.save(ignore_permissions=True)
            investigations.append({
                'pharmacy': patient_pharmacy.name,
                'status': patient_pharmacy.payment_status
            })

    if investigations:
        frappe.db.commit()  # Commit changes to the database

    return investigations or "No updates were made to Pharmacy documents."

@frappe.whitelist()
def create_nurse_doc(doc, method=None):
    """
    Creates or updates a Nurses Document based on the provided pharmacy document.
    
    Args:
        doc: The pharmacy document triggering this function.
        method: The Frappe method triggering this function (usually 'on_submit' or 'on_update').
    """
    pharmacy_doc = frappe.get_doc("Pharmacy", doc)
    if doc.nurse_doc_id:
        return

    try:
        # Check if a draft Nurses Document already exists for the pharmacy document
        existing_nurse_doc = frappe.get_all(
            "Nurses Document",
            filters={
                "pharmacy_id": doc.name,
                "docstatus": 0  # Draft status
            },
            limit=1
        )

        if existing_nurse_doc:
            # Load the existing draft Nurses Document
            nurse_doc = frappe.get_doc("Nurses Document", existing_nurse_doc[0].name)
            # Update encounter details
            nurse_doc.encounter_date = doc.encounter_date
            nurse_doc.encounter_time = doc.encounter_time
            # Clear existing drug items
            nurse_doc.administering_drugs_items = []
        else:
            # Create a new Nurses Document
            nurse_doc = frappe.new_doc("Nurses Document")
            nurse_doc.patient = doc.patient
            nurse_doc.patient_encounter_id = doc.patient_encounter_id
            nurse_doc.healthcare_practitioner = doc.practitioner
            nurse_doc.gender = doc.patient_sex
            nurse_doc.age = doc.patient_age
            nurse_doc.patient_type = "IPD"
            nurse_doc.encounter_date = doc.encounter_date
            nurse_doc.encounter_time = doc.encounter_time
            nurse_doc.pharmacy_id = doc.name
            nurse_doc.administering_drugs_items = []

        # Add drug prescriptions to the Nurses Document
        for item in doc.drug_prescription:
            nurse_doc.append("administering_drugs_items", {
                "drug_id": item.drug_code,
                "dosage": item.dosage,
                "frequency": item.period,
                "status": "Pending"
            })

        # Save the Nurses Document as a draft
        nurse_doc.save(ignore_permissions=True)

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

def create_pharmacy_doc(doc, method):
    if doc.consumables:
        try:

            # Check if there is an existing draft Pharmacy for the same encounter
            existing_pharmacy = frappe.get_all("Pharmacy", 
                                              filters={
                                                  "nurse_doc_id": doc.name,
                                                  "docstatus": 0  # Draft status
                                              }, 
                                              limit=1)
            
            if existing_pharmacy:
                # Update the existing draft Pharmacy
                pharmacy_doc = frappe.get_doc("Pharmacy", existing_pharmacy[0].name)
                pharmacy_doc.patient = doc.patient
                pharmacy_doc.practitioner = doc.healthcare_practitioner
                pharmacy_doc.patient_sex = doc.gender
                pharmacy_doc.patient_age = doc.age
                pharmacy_doc.encounter_date = doc.encounter_date
                pharmacy_doc.encounter_time = doc.encounter_time
                pharmacy_doc.nurse_doc_id = doc.name
            else:
                # Create a new Pharmacy
                pharmacy_doc = frappe.new_doc("Pharmacy")
                pharmacy_doc.patient = doc.patient
                pharmacy_doc.patient_encounter_id = doc.patient_encounter_id
                pharmacy_doc.practitioner = doc.healthcare_practitioner
                pharmacy_doc.patient_sex = doc.gender
                pharmacy_doc.patient_age = doc.age
                pharmacy_doc.encounter_date = doc.encounter_date
                pharmacy_doc.encounter_time = doc.encounter_time
                pharmacy_doc.nurse_doc_id = doc.name
                pharmacy_doc.drug_prescription = []

            # Flag to check if any item should be added
            has_items_to_add = False

            for item in doc.consumables:
                if item.pharmacy_status == "Sent to Pharmacy":
                    # Skip items that are already paid
                    continue
                
                # Fetch the item document using the item code
                item_code_doc = frappe.get_doc('Item', item.item)
                
                if not item_code_doc or not item.amount:
                    frappe.log_error(f"Missing data in custom_items: {item.as_dict()}", "Sales Invoice Creation Error")
                    frappe.throw(_("Missing data for item {0}. Ensure that item code and amount are provided.").format(item.item))
                
                # Append item to the Pharmacy
                pharmacy_doc.append("drug_prescription", {
                    "drug_code": item.item,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                    "dosage":item.dosage,
                    "dosage_form":item.dosage_form
              })
                
                # Set flag to true if at least one item is added
                has_items_to_add = True

            if not has_items_to_add:
                # If no items are added, show message and proceed
                return
                # frappe.msgprint(_("No valid Lab Tests Investigations found to create an Invoice"), raise_exception=False)
            else:
                # Save or update the Pharmacy as a draft
                pharmacy_doc.save(ignore_permissions=True)
                # sales_invoice.submit()
                frappe.msgprint(_("Pharmacy {0} created/updated successfully.").format(pharmacy_doc.name))
                
                # Update `pharmacy_status` in the Lab Prescription table
                for procede in doc.consumables:
                    if item.pharmacy_status != "Sent to Pharmacy":
                        procede.pharmacy_status = "Sent to Pharmacy"
                doc.save()
                frappe.db.commit()
                  
         
        except frappe.ValidationError as e:
            frappe.db.rollback()
            frappe.throw(_("There was an error creating the Pharmacy: {0}").format(str(e)))

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(message=str(e), title="Pharmacy Creation Error")
            frappe.throw(_("An unexpected error occurred while creating the Pharmacy. Please try again or contact support. Error details: {0}").format(str(e)))

def create_vital_signs_doc(doc, method):
    if doc.vital_sign_items:
        try:

            # Check if there is an existing draft Pharmacy for the same encounter
            existing_pharmacy = frappe.get_all("Pharmacy", 
                                              filters={
                                                  "nurse_doc_id": doc.name,
                                                  "docstatus": 0  # Draft status
                                              }, 
                                              limit=1)
            
            if existing_pharmacy:
                # Update the existing draft Pharmacy
                pharmacy_doc = frappe.get_doc("Pharmacy", existing_pharmacy[0].name)
                pharmacy_doc.patient = doc.patient
                pharmacy_doc.practitioner = doc.healthcare_practitioner
                pharmacy_doc.patient_sex = doc.gender
                pharmacy_doc.patient_age = doc.age
                pharmacy_doc.encounter_date = doc.encounter_date
                pharmacy_doc.encounter_time = doc.encounter_time
                pharmacy_doc.nurse_doc_id = doc.name
            else:
                # Create a new Pharmacy
                pharmacy_doc = frappe.new_doc("Pharmacy")
                pharmacy_doc.patient = doc.patient
                pharmacy_doc.patient_encounter_id = doc.patient_encounter_id
                pharmacy_doc.practitioner = doc.healthcare_practitioner
                pharmacy_doc.patient_sex = doc.gender
                pharmacy_doc.patient_age = doc.age
                pharmacy_doc.encounter_date = doc.encounter_date
                pharmacy_doc.encounter_time = doc.encounter_time
                pharmacy_doc.nurse_doc_id = doc.name
                pharmacy_doc.drug_prescription = []

            # Flag to check if any item should be added
            has_items_to_add = False

            for item in doc.consumables:
                if item.pharmacy_status == "Sent to Pharmacy":
                    # Skip items that are already paid
                    continue
                
                # Fetch the item document using the item code
                item_code_doc = frappe.get_doc('Item', item.item)
                
                if not item_code_doc or not item.amount:
                    frappe.log_error(f"Missing data in custom_items: {item.as_dict()}", "Sales Invoice Creation Error")
                    frappe.throw(_("Missing data for item {0}. Ensure that item code and amount are provided.").format(item.item))
                
                # Append item to the Pharmacy
                pharmacy_doc.append("drug_prescription", {
                    "drug_code": item.item,
                    "qty": item.qty,
                    "rate": item.amount,
                    "dosage":item.dosage,
                    "dosage_form":item.dosage_form
              })
                
                # Set flag to true if at least one item is added
                has_items_to_add = True

            if not has_items_to_add:
                # If no items are added, show message and proceed
                return
                # frappe.msgprint(_("No valid Lab Tests Investigations found to create an Invoice"), raise_exception=False)
            else:
                # Save or update the Pharmacy as a draft
                pharmacy_doc.save(ignore_permissions=True)
                # sales_invoice.submit()
                frappe.msgprint(_("Pharmacy {0} created/updated successfully.").format(pharmacy_doc.name))
                
                # Update `pharmacy_status` in the Lab Prescription table
                for procede in doc.consumables:
                    if item.pharmacy_status != "Sent to Pharmacy":
                        procede.pharmacy_status = "Sent to Pharmacy"
                doc.save()
                frappe.db.commit()
                  
         
        except frappe.ValidationError as e:
            frappe.db.rollback()
            frappe.throw(_("There was an error creating the Pharmacy: {0}").format(str(e)))

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(message=str(e), title="Pharmacy Creation Error")
            frappe.throw(_("An unexpected error occurred while creating the Pharmacy. Please try again or contact support. Error details: {0}").format(str(e)))
