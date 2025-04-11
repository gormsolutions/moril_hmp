import frappe
@frappe.whitelist()
def create_or_validate_custom_batch(custom_batch, item, manufacturing_date=None, expiry_date=None):
    # Check if the batch already exists
    existing_batch = frappe.get_all('Custom Batch', filters={'batch_no': custom_batch}, fields=['name'])
    if not existing_batch:
        # Create a new batch
        new_batch = frappe.get_doc({
            'doctype': 'Custom Batch',
            'batch_no': custom_batch,
            'item': item,
            'manufacturing_date': manufacturing_date,
            'expiry_date': expiry_date
        })
        new_batch.insert()
        frappe.db.commit()
        return new_batch.name
    else:
        # Return the existing batch
        return existing_batch[0].name
