import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def create_sales_invoice(patient_payment):
    try:
        # Get the patient payment document
        patie_payment_doc = frappe.get_doc("Collect Patient Payment", patient_payment)
        patient = patie_payment_doc.patient
        
        # Fetch the patient document linked in the patient payment
        patient_doc = frappe.get_doc("Patient", patient)

        # Check if a Sales Invoice already exists for the patient
        existing_invoice = frappe.db.exists("Sales Invoice", {"custom_collection_payment_id": patie_payment_doc.name})
        if existing_invoice:
            return {
                "message": _(f"A sales invoice already exists for this. {patie_payment_doc.name}.")
            }

        # Create a Sales Invoice
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.patient = patient
        sales_invoice.company = frappe.defaults.get_global_default("company")
        sales_invoice.customer = patient_doc.customer
        sales_invoice.due_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)
        sales_invoice.set_posting_time = 1
        sales_invoice.posting_date = patie_payment_doc.posting_date
        sales_invoice.posting_time = patie_payment_doc.posting_time
        sales_invoice.selling_price_list = patie_payment_doc.price_list
        sales_invoice.custom_collection_payment_id = patie_payment_doc.name
        sales_invoice.cost_center = patie_payment_doc.cost_center
        sales_invoice.additional_discount_account = patie_payment_doc.discount_account
        sales_invoice.discount_amount = patie_payment_doc.discount

        # Add items from patie_payment_doc.items to sales_invoice.items
        for item in patie_payment_doc.items:
            sales_invoice.append("items", {
                "item_code": item.item_code,
                "rate": item.rate,
                "qty": item.qty,
                "cost_center": patie_payment_doc.cost_center,
            })

        # Save the Sales Invoice
        sales_invoice.insert()

        # Optionally, submit the Sales Invoice
        sales_invoice.submit()

        # Check Sales Invoice status and outstanding amount
        sales_invoice.reload()
        if sales_invoice.status == "Paid" and sales_invoice.outstanding_amount == 0:
            patie_payment_doc.bill_status = "CLOSED"
        else:
            patie_payment_doc.bill_status = "OPEN"

        # Save the updated patient payment document
        patie_payment_doc.save()

        return {
            "sales_invoice_name": sales_invoice.name,
            "message": _("Sales Invoice {0} created successfully.").format(sales_invoice.name)
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Sales Invoice Creation Error')
        return {
            "error": str(e)
        }

@frappe.whitelist()
def create_sales_invoice_payments(patient_payment):
    try:
        # Get the patient payment document
        patie_payment_doc = frappe.get_doc("Collect Patient Payment", patient_payment)
        patient = patie_payment_doc.patient

        # Fetch the patient document linked in the patient payment
        patient_doc = frappe.get_doc("Patient", patient)

        # Check if a Sales Invoice already exists for the patient
        existing_invoice = frappe.db.exists("Sales Invoice", {"custom_collection_payment_id": patie_payment_doc.name})
        if existing_invoice:
            return {
                "message": _("A sales invoice already exists for this patient.")
            }

        # Create a Sales Invoice
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.patient = patient
        sales_invoice.company = frappe.defaults.get_global_default("company")
        sales_invoice.customer = patient_doc.customer
        sales_invoice.due_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)
        sales_invoice.set_posting_time = 1
        sales_invoice.posting_date = patie_payment_doc.posting_date
        sales_invoice.posting_time = patie_payment_doc.posting_time
        sales_invoice.selling_price_list = patie_payment_doc.price_list
        sales_invoice.custom_collection_payment_id = patie_payment_doc.name
        sales_invoice.cost_center = patie_payment_doc.cost_center
        sales_invoice.additional_discount_account = patie_payment_doc.discount_account
        sales_invoice.discount_amount = patie_payment_doc.discount

        # Add items from patie_payment_doc.items to sales_invoice.items
        for item in patie_payment_doc.items:
            sales_invoice.append("items", {
                "item_code": item.item_code,
                "rate": item.rate,
                "cost_center": patie_payment_doc.cost_center,
                "qty": item.qty
            })

        # Save the Sales Invoice
        sales_invoice.insert()

        # Optionally, submit the Sales Invoice
        sales_invoice.submit()

        # Fetch the exchange rate (Assuming that payment currency is same as invoice currency)
        target_exchange_rate = frappe.db.get_value("Currency Exchange", 
                                                   {"from_currency": sales_invoice.currency, 
                                                    "to_currency": frappe.defaults.get_global_default("default_currency")},
                                                   "exchange_rate")
        if not target_exchange_rate:
            target_exchange_rate = 1  # Default to 1 if no specific exchange rate is found

        # Create Payment Entries for each mode of payment
        payment_entries = []
        for mode in patie_payment_doc.cash_items:
            # Fetch the default account from the Mode of Payment Account child table
            default_paid_to_account = frappe.db.get_value("Mode of Payment Account", 
                                                          {"parent": mode.mode_of_payment, "company": patie_payment_doc.company}, 
                                                          "default_account")
            if not default_paid_to_account:
                return {
                    "error": _("Default account not found for mode of payment {0} and company {1}").format(mode.mode_of_payment, patie_payment_doc.company)
                }
            
            account_currency = frappe.db.get_value("Account", default_paid_to_account, "account_currency")

            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = patient_doc.customer
            payment_entry.posting_date = frappe.utils.nowdate()
            payment_entry.company = sales_invoice.company
            payment_entry.paid_amount = mode.paid_amount
            payment_entry.received_amount = mode.paid_amount
            payment_entry.reference_no = mode.transaction_id
            payment_entry.custom_colection_payment_id = patie_payment_doc.name
            payment_entry.reference_date = patie_payment_doc.posting_date
            payment_entry.target_exchange_rate = target_exchange_rate
            payment_entry.mode_of_payment = mode.mode_of_payment 
            payment_entry.cost_center = patie_payment_doc.cost_center

            # Set required fields
            payment_entry.paid_to = default_paid_to_account
            payment_entry.paid_to_account_currency = account_currency

            # Link the payment to the Sales Invoice
            payment_entry.append("references", {
                "reference_doctype": "Sales Invoice",
                "reference_name": sales_invoice.name,
                "total_amount": sales_invoice.grand_total,
                "outstanding_amount": sales_invoice.grand_total,
                "allocated_amount": mode.paid_amount
            })

            # Save and submit the Payment Entry
            payment_entry.insert()
            payment_entry.submit()
            payment_entries.append(payment_entry.name)

        # Check Sales Invoice status and outstanding amount
        sales_invoice.reload()
        if sales_invoice.status == "Paid" and sales_invoice.outstanding_amount == 0:
            patie_payment_doc.bill_status = "CLOSED"
        else:
            patie_payment_doc.bill_status = "OPEN"

        # Save the patient payment document with updated bill_status
        patie_payment_doc.save()
  
        return {
            "sales_invoice_name": sales_invoice.name,
            "payment_entry_names": payment_entries,
            "message": _("Sales Invoice {0} and Payment Entries {1} created successfully.").format(sales_invoice.name, ", ".join(payment_entries))
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Sales Invoice and Payment Entry Creation Error')
        return {
            "error": str(e)
        }


@frappe.whitelist()
def get_sales_invoices_with_totals(cost_center=None, posting_date=None, patient=None, customer=None):
    try:
        # Log filter criteria
        frappe.logger().info(f"Fetching sales invoices for cost center: {cost_center}, posting date: {posting_date}, and patient: {patient}")

        # Define filters
        filters = {"docstatus": 1, "outstanding_amount": [">", 0]}
        if cost_center:
            filters["cost_center"] = cost_center
        # if posting_date:
        #     filters["posting_date"] = posting_date
        if patient:
            filters["patient"] = patient
            
        if customer:
            filters["customer"] = customer

        # Fetch sales invoices with specified fields
        sales_invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "posting_date", "outstanding_amount", "cost_center", "posting_date", "patient"]
        )

        # Log fetched sales invoices
        frappe.logger().info(f"Fetched {len(sales_invoices)} sales invoices")

        if not sales_invoices:
            frappe.logger().info("No sales invoices found with the given filters")
            return {
                "Invoices": [],
                "Total Outstanding Amount": 0
            }

        # Calculate the total outstanding amount
        total_outstanding = sum(invoice['outstanding_amount'] for invoice in sales_invoices)

        # Log total outstanding amount
        frappe.logger().info(f"Total outstanding amount: {total_outstanding}")

        # Prepare the response
        result = {
            "Invoices": sales_invoices,
            "Total Outstanding Amount": total_outstanding
        }

        # Log final result
        frappe.logger().info(f"Final result: {result}")
        
        # Return the list of invoices with their outstanding amount and posting date
        return result

    except Exception as e:
        frappe.throw(_("An error occurred while fetching sales invoices: {}").format(str(e)))


@frappe.whitelist()
def collect_invoices(patient):
    """
    Collect invoices for a given patient. Creates a Sales Invoice if one does not already exist.
    
    Args:
        patient (str): The name of the Patient document.
    
    Returns:
        dict: A message indicating the status of the Sales Invoice creation or an error.
    """
    try:
        # Fetch the patient document linked in the patient payment
        patient_doc = frappe.get_doc("Patient", patient)

        # Check if a Sales Invoice already exists for the patient
        existing_invoice = frappe.db.exists("Sales Invoice", {"custom_payment_id": patient})
        if existing_invoice:
            return {
                "message": _("A sales invoice already exists for this patient.")
            }

        # Create a Sales Invoice
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.patient = patient
        sales_invoice.company = frappe.defaults.get_global_default("company")
        sales_invoice.customer = patient_doc.customer
        sales_invoice.due_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)
        sales_invoice.set_posting_time = 1
        sales_invoice.posting_date = frappe.utils.nowdate()
        sales_invoice.selling_price_list = patient_doc.default_price_list
        sales_invoice.custom_payment_id = patient_doc.name
        sales_invoice.cost_center = patient_doc.custom_consulting_department
   
        # Add items from patient_doc to sales_invoice.items
        sales_invoice.append("items", {
            "item_code": patient_doc.custom_consultation,
            "rate": patient_doc.custom_fee,
            "cost_center": patient_doc.custom_consulting_department,
            "qty": 1
        })

        # Save the Sales Invoice
        sales_invoice.insert()

        # Optionally, submit the Sales Invoice 
        sales_invoice.submit()
        
        
        # Check Sales Invoice status and outstanding amount
        sales_invoice.reload()
        if sales_invoice.outstanding_amount > 0:
            patient_doc.custom_bill_status = "Payments Pending"
        else:
            patient_doc.custom_bill_status = "Approved"
            
        patient_doc.custom_invoice_no = sales_invoice.name
        patient_doc.save()
        frappe.db.commit()

        return {
            "message": _("Sales Invoice created successfully.")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Sales Invoice and Payment Entry Creation Error')
        return {
            "error": str(e)
        }

@frappe.whitelist()
def pay_now(patient):
    try:
        # Fetch the patient document
        patient_doc = frappe.get_doc("Patient", patient)

        # Check if the patient document has a customer linked to it
        if not patient_doc.customer:
            return {
                "message": _("Customer is not linked to the patient.")
            }
        
        # Fetch the company from the customer
        customer_doc = frappe.get_doc("Customer", patient_doc.customer)
        if not customer_doc.default_company:
            return {
                "message": _("Default company is not set for the customer.")
            }

        # Check if a Sales Invoice already exists for the patient
        existing_invoice = frappe.db.exists("Sales Invoice", {"custom_payment_id": patient})
        if existing_invoice:
            return {
                "message": _("A sales invoice already exists for this patient.")
            }
        
        # Check if custom_mode_details table is set
        if not patient_doc.custom_mode_details:
            return {
                "message": _("Please fill in the mode of payments in the Custom Mode Details table.")
            }

        # Create a Sales Invoice
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.patient = patient
        sales_invoice.company = customer_doc.default_company
        sales_invoice.customer = patient_doc.customer
        sales_invoice.due_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)
        sales_invoice.set_posting_time = 1
        sales_invoice.posting_date = frappe.utils.nowdate()
        sales_invoice.selling_price_list = patient_doc.default_price_list
        sales_invoice.custom_payment_id = patient_doc.name
        sales_invoice.cost_center = patient_doc.custom_consulting_department
   
        # Add items to the Sales Invoice
        sales_invoice.append("items", {
            "item_code": patient_doc.custom_consultation,
            "rate": patient_doc.custom_fee,
            "cost_center": patient_doc.custom_consulting_department,
            "qty": 1
        })

        # Save the Sales Invoice
        sales_invoice.insert()
        sales_invoice.submit()

        # Fetch the exchange rate (Assuming that payment currency is the same as invoice currency)
        target_exchange_rate = frappe.db.get_value("Currency Exchange", 
                                                   {"from_currency": sales_invoice.currency, 
                                                    "to_currency": frappe.defaults.get_global_default("default_currency")},
                                                   "exchange_rate")
        if not target_exchange_rate:
            target_exchange_rate = 1  # Default to 1 if no specific exchange rate is found

        # Create Payment Entries for each mode of payment
        payment_entries = []
        remaining_amount = sales_invoice.outstanding_amount

        for mode in patient_doc.custom_mode_details:
            # Fetch the default account from the Mode of Payment Account child table
            default_paid_to_account = frappe.db.get_value("Mode of Payment Account", 
                                                          {"parent": mode.mode_of_payment, "company": customer_doc.default_company}, 
                                                          "default_account")
            if not default_paid_to_account:
                return {
                    "error": _("Default account not found for mode of payment {0} and company {1}").format(mode.mode_of_payment, customer_doc.default_company)
                }
            
            account_currency = frappe.db.get_value("Account", default_paid_to_account, "account_currency")

            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = patient_doc.customer
            payment_entry.posting_date = frappe.utils.nowdate()
            payment_entry.company = sales_invoice.company
            payment_entry.paid_amount = mode.paid_amount
            payment_entry.received_amount = mode.paid_amount
            payment_entry.reference_no = mode.transaction_id
            payment_entry.custom_patient_pay_id = patient_doc.name
            payment_entry.reference_date = frappe.utils.nowdate()
            payment_entry.target_exchange_rate = target_exchange_rate
            payment_entry.mode_of_payment = mode.mode_of_payment 
            payment_entry.cost_center = patient_doc.custom_consulting_department

            # Set required fields
            payment_entry.paid_to = default_paid_to_account
            payment_entry.paid_to_account_currency = account_currency

            # Link the payment to the Sales Invoice
            if remaining_amount > 0:
                allocated = min(remaining_amount, mode.paid_amount)
                payment_entry.append("references", {
                    "reference_doctype": "Sales Invoice",
                    "reference_name": sales_invoice.name,
                    "total_amount": remaining_amount,
                    "outstanding_amount": remaining_amount,
                    "allocated_amount": allocated
                })
                remaining_amount -= allocated

            # Save and submit the Payment Entry
            payment_entry.insert()
            payment_entry.submit()
            payment_entries.append(payment_entry.name)

        # Check Sales Invoice status and outstanding amount
        sales_invoice.reload()
        if sales_invoice.status == "Paid" and sales_invoice.outstanding_amount == 0:
            patient_doc.custom_bill_status = "Approved"
        else:
            patient_doc.custom_bill_status = "Payments Pending"

        # Save the patient payment document with updated bill_status
        patient_doc.custom_invoice_no = sales_invoice.name
        patient_doc.save()
        frappe.db.commit()
        return {
            "message": _("Sales Invoice created and payment recorded successfully.")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Pay Now Error')
        return {
            "error": str(e)
        }


@frappe.whitelist()
def get_sales_invoices_with_drafts(cost_center=None, posting_date=None, patient=None, customer=None):
    try:
        # Log filter criteria
        frappe.logger().info(f"Fetching sales invoices for cost center: {cost_center}, posting date: {posting_date}, and patient: {patient}")

        # Define filters
        filters = {"docstatus": 0, "outstanding_amount": [">", 0]}
        if cost_center:
            filters["cost_center"] = cost_center
        # if posting_date:
        #     filters["posting_date"] = posting_date
        if patient:
            filters["patient"] = patient

        # Fetch sales invoices with specified fields
        sales_invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "posting_date", "outstanding_amount", "cost_center", "posting_date", "patient"]
        )

        # Log fetched sales invoices
        frappe.logger().info(f"Fetched {len(sales_invoices)} sales invoices")

        if not sales_invoices:
            frappe.logger().info("No sales invoices found with the given filters")
            return {
                "Invoices": [],
            }

        # Prepare the response
        result = {
            "Invoices": sales_invoices
        }

        # Log final result
        frappe.logger().info(f"Final result: {result}")
        # Return the list of invoices with their outstanding amount and posting date
        return result

    except Exception as e:
        frappe.throw(_("An error occurred while fetching sales invoices: {}").format(str(e)))

@frappe.whitelist()
def get_sales_invoices_with_drafts_itemgroup(cost_center=None, posting_date=None, patient=None, customer=None):
    try:
        # Log filter criteria
        frappe.logger().info(f"Fetching sales invoices for cost center: {cost_center}, posting date: {posting_date}, and patient: {patient}")

        # Define filters
        filters = {"docstatus": 0, "outstanding_amount": [">", 0]}
        if cost_center:
            filters["cost_center"] = cost_center
        if patient:
            filters["patient"] = patient

        # Fetch sales invoices with specified fields
        sales_invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "posting_date", "outstanding_amount", "cost_center", "patient"]
        )

        # Log fetched sales invoices
        frappe.logger().info(f"Fetched {len(sales_invoices)} sales invoices")

        if not sales_invoices:
            frappe.logger().info("No sales invoices found with the given filters")
            return {
                "Invoices": [],
                "Item Group Totals": []
            }

        # Prepare to group items by item group and calculate totals
        item_group_totals = {}

        # Iterate through the fetched invoices
        for invoice in sales_invoices:
            # Fetch items for each invoice
            invoice_items = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": invoice["name"]},
                fields=["item_code", "amount"]
            )

            # Group items by item group and sum their amounts
            for item in invoice_items:
                item_group = item["item_code"]
                amount = item["amount"]
                if item_group not in item_group_totals:
                    item_group_totals[item_group] = {
                        "total_amount": 0,
                        "invoices": []
                    }
                item_group_totals[item_group]["total_amount"] += amount
                if invoice["name"] not in item_group_totals[item_group]["invoices"]:
                    item_group_totals[item_group]["invoices"].append(invoice["name"])

        # Prepare the response
        result = {
            "Invoices": sales_invoices,
            "Item Group Totals": [
                {
                    "item_code": group,
                    "total_amount": total["total_amount"],
                    "invoice_ids": total["invoices"]
                }
                for group, total in item_group_totals.items()
            ]
        }

        # Log final result
        frappe.logger().info(f"Final result: {result}")
        # Return the list of invoices with their outstanding amount and posting date, and grouped totals
        return result

    except Exception as e:
        frappe.throw(_("An error occurred while fetching sales invoices: {}").format(str(e)))

@frappe.whitelist()
def get_sales_invoices_with_totals_itemgroup(cost_center=None, posting_date=None, patient=None, customer=None):
    try:
        # Log filter criteria
        frappe.logger().info(f"Fetching sales invoices for cost center: {cost_center}, posting date: {posting_date}, and patient: {patient}")

        # Define filters
        filters = {"docstatus": 1, "outstanding_amount": [">", 0]}
        if cost_center:
            filters["cost_center"] = cost_center
        if patient:
            filters["patient"] = patient

        # Fetch sales invoices with specified fields
        sales_invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "posting_date", "outstanding_amount", "cost_center", "patient"]
        )

        # Log fetched sales invoices
        frappe.logger().info(f"Fetched {len(sales_invoices)} sales invoices")

        if not sales_invoices:
            frappe.logger().info("No sales invoices found with the given filters")
            return {
                "Invoices": [],
                "Total Outstanding Amount": 0,
                "Item Group Totals": []
            }

        # Calculate the total outstanding amount
        total_outstanding = sum(invoice['outstanding_amount'] for invoice in sales_invoices)

        # Prepare to group items by item group and calculate totals
        item_group_totals = []

        # Iterate through the fetched invoices
        for invoice in sales_invoices:
            # Fetch items for each invoice
            invoice_items = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": invoice["name"]},
                fields=["item_code", "amount","custom_self_request"]
            )

            # Group items by item group and sum their amounts
            for item in invoice_items:
                item_group = item["item_code"]
                amount = item["amount"]
                self_request = item["custom_self_request"]

                # Check if the item group already exists in the totals list
                existing_group = next((group for group in item_group_totals if group["item_code"] == item_group and group["invoice_name"] == invoice["name"]), None)

                if existing_group:
                    existing_group["total_amount"] += amount
                else:
                    item_group_totals.append({
                        "invoice_name": invoice["name"],
                        "item_code": item_group,
                        "self_request": self_request,
                        "total_amount": amount
                    })

        # Log total outstanding amount
        frappe.logger().info(f"Total outstanding amount: {total_outstanding}")

        # Prepare the response
        result = {
            "Invoices": sales_invoices,
            "Total Outstanding Amount": total_outstanding,
            "Item Group Totals": item_group_totals
        }

        # Log final result
        frappe.logger().info(f"Final result: {result}")
        
        # Return the list of invoices with their outstanding amount and posting date, and grouped totals
        return result

    except Exception as e:
        frappe.throw(_("An error occurred while fetching sales invoices: {}").format(str(e)))
