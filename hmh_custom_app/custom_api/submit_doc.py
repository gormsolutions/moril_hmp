import frappe

@frappe.whitelist()
def submit_unique_invoices(parent_docname):
    try:
        # Fetch the parent document which contains the child table 'invoice_awaiting'
        parent_doc = frappe.get_doc('Patient Payment Management', parent_docname)
        
        # Get the unique invoice IDs from the child table
        invoice_ids = set()
        for child in parent_doc.invoice_awaiting:
            invoice_ids.add(child.invoice)
        
        # Convert set to list for processing
        invoice_ids = list(invoice_ids)
        
        # Process each unique invoice ID
        submitted_invoices = []
        failed_invoices = []
        for invoice_id in invoice_ids:
            try:
                invoice = frappe.get_doc('Sales Invoice', invoice_id)
                if invoice.docstatus != 1:  # Check if already submitted
                    invoice.submit()
                    submitted_invoices.append(invoice_id)
                else:
                    failed_invoices.append(f"{invoice_id} (already submitted)")
            except frappe.DoesNotExistError:
                failed_invoices.append(f"{invoice_id} (does not exist)")
            except Exception as e:
                failed_invoices.append(f"{invoice_id} (error: {str(e)})")
        
        # Return results
        return {
            "status": "success",
            "submitted_invoices": submitted_invoices,
            "failed_invoices": failed_invoices
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
