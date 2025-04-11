import frappe

@frappe.whitelist()
def create_missing_items_from_lab_test_template():
    """
    Fetch all Lab Test Template documents and create a new Item for each template if an Item
    with the same 'item' (as item_code) does not already exist. Existing Items are skipped.
    The new Item will be created with the 'item_group' set to 'Laboratory'.
    """
    # Fetch all Lab Test Template documents (retrieve name and item fields)
    lab_templates = frappe.get_all("Lab Test Template", fields=["name", "item"])

    messages = []  # To collect status messages

    if not lab_templates:
        frappe.msgprint("No Lab Test Template records found.")
        return

    # Collect all non-empty item codes from the templates
    item_codes = [template.item for template in lab_templates if template.item]

    if not item_codes:
        frappe.msgprint("No item codes found in any Lab Test Template.")
        return

    # Bulk fetch existing Items whose item_code is in the collected list
    existing_items = frappe.db.get_all(
        "Item",
        filters={"item_code": ["in", item_codes]},
        fields=["item_code"]
    )
    # Build a set of existing item codes for quick lookup
    existing_item_codes = {item.item_code for item in existing_items}

    # Loop through each Lab Test Template and process the item
    for template in lab_templates:
        itemb = template.name
        itema = template.item
        if not itemb:
            continue  # Skip if there is no item

        if itemb in existing_item_codes:
            messages.append(f"Item '{itemb}' already exists, skipping.")
        else:
            try:
                # Create a new Item with the 'Laboratory' group
                new_item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": itema,
                    "item_name": itemb,
                    "item_group": "Laboratory",
                    "is_stock_item": 0,  # Change to 1 if the item is a stock item
                })
                new_item.insert(ignore_permissions=True)
                messages.append(f"Created new Item '{itemb}' under 'Laboratory' group.")
                # Update the lookup set to include the newly created item
                existing_item_codes.add(itemb)
            except Exception as e:
                # Log error and add a message for this template
                frappe.log_error(message=str(e), title=f"Error creating Item for {itemb}")
                messages.append(f"Failed to create Item '{itemb}': {e}")

    # Display a summary of the operations
    frappe.msgprint("<br>".join(messages))
    return messages
