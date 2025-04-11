import frappe
from frappe.model.document import Document

@frappe.whitelist()
def create_stock_entry(docname, warehouse, posting_date, posting_time, patient, cost_center):
    # Check if Stock Entry already exists
    stock_entry_list = frappe.get_list('Stock Entry', filters={'custom_pharmacy_id': docname, 'docstatus': 1}, fields=['name'])
    
    if stock_entry_list:
        return {'status': 'exists', 'message': 'Items already Issued Please'}
    
    # Fetch the Pharmacy document
    pharmacy = frappe.get_doc('Pharmacy', docname)
    
    if not pharmacy:
        return {'status': 'error', 'message': 'Pharmacy document not found'}
    
    # Create new Stock Entry
    se = frappe.new_doc('Stock Entry')
    se.stock_entry_type = 'Material Issue'
    se.remarks = f"{patient} - {docname}"
    se.posting_date = posting_date
    se.posting_time = posting_time
    se.custom_patient_id = patient
    se.custom_pharmacy_id = docname
    
    # Check if negative stock is allowed
    allow_negative_stock = frappe.db.get_single_value('Stock Settings', 'allow_negative_stock')
    
    # Add Stock Entry details based on Medication Entry items
    for item in pharmacy.drug_prescription:
        item_code = item.drug_code
        item_doc = frappe.get_doc('Item', item_code)

        # Ensure the item is a stock item before proceeding
        if not item_doc.is_stock_item:
            continue  # Skip non-stock items

        uom = item_doc.stock_uom  # Retrieve the UOM from the Item document
        
        # Check if the item has batch tracking enabled
        has_batch = frappe.get_value('Item', item_code, 'has_batch_no')
        
        batch_no = None  # Default to None

        if has_batch:
            # Fetch batches with positive stock in the specified warehouse
            batch_info = frappe.db.sql("""
                SELECT b.name AS batch_id, sle.actual_qty
                FROM `tabBatch` b
                JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
                WHERE b.item = %s
                AND b.docstatus = 1  -- Ensure batch is active
                AND b.disabled = 0   -- Ensure batch is not disabled
                AND sle.warehouse = %s
                AND sle.actual_qty > 0  -- Ensure batch has positive stock in the warehouse
                ORDER BY sle.actual_qty DESC  -- Prioritize batches with highest stock
                LIMIT 1
            """, (item_code, warehouse), as_dict=True)

            if batch_info:
                batch_no = batch_info[0]['batch_id']

        # Append item to Stock Entry
        se.append('items', {
            'item_code': item_code,
            'qty': item.qty,
            'uom': uom,
            's_warehouse': warehouse,
            'transfer_qty': item.qty,
            'cost_center': cost_center,
            'use_serial_batch_fields': 1,
            'batch_no': batch_no  # Assign batch if found
        })
    
    if allow_negative_stock:
        frappe.db.set_value('Stock Entry', se.name, 'allow_negative_stock', 1)  # Ensure negative stock is allowed for this Stock Entry

    se.insert()
    se.submit()
    
    return {'status': 'created', 'name': se.name}
