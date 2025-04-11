import frappe

def create_anaesthetic_record_child_table(doc,method):
    # Check if the Child Table already exists
    if frappe.db.exists("DocType", "Anaesthetic Record Details"):
        print("Child Table 'Anaesthetic Record Details' already exists!")
        return

    # Define fields for the Child Table
    fields = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "reqd": 1},
        {"label": "Procedure", "fieldname": "procedure", "fieldtype": "Data", "reqd": 1},
        {"label": "Anaesthetist", "fieldname": "anaesthetist", "fieldtype": "Link", "options": "Doctor"},
        {"label": "Surgeon", "fieldname": "surgeon", "fieldtype": "Link", "options": "Doctor"},
        {
            "label": "Monitoring Parameters",
            "fieldname": "monitoring_parameters",
            "fieldtype": "Table",
            "options": "Monitoring Parameters Table"
        },
        {"label": "Crystalloids", "fieldname": "crystalloids", "fieldtype": "MultiSelect"},
        {"label": "Colloids", "fieldname": "colloids", "fieldtype": "MultiSelect"},
        {"label": "Blood Loss (ml)", "fieldname": "blood_loss", "fieldtype": "Float"},
        {"label": "Anaesthetic Technique", "fieldname": "anaesthetic_technique", "fieldtype": "Select"},
        {"label": "Ventilation", "fieldname": "ventilation", "fieldtype": "Select"},
        {"label": "Special Techniques", "fieldname": "special_techniques", "fieldtype": "Table"},
        {"label": "Pre-induction Checklist", "fieldname": "pre_induction_checklist", "fieldtype": "Table"}
    ]

    # Create the Child Table
    child_table = frappe.get_doc({
        "doctype": "DocType",
        "name": "Anaesthetic Record Details",
        "module": "Healthcare",
        "istable": 1,  # Marks it as a child table
        "custom": 1,
        "fields": fields
    })
    child_table.insert()
    print("Child Table 'Anaesthetic Record Details' created successfully!")

def add_child_table_to_post_anaesthesia_care_unit():
    # Add the child table to the Post Anaesthesia Care Unit Doctype
    pacu_doctype = frappe.get_doc("DocType", "Post Anaesthesia Care Unit")

    # Check if the field already exists
    if any(field.fieldname == "anaesthetic_record_details" for field in pacu_doctype.fields):
        print("Field 'Anaesthetic Record Details' already exists in 'Post Anaesthesia Care Unit'!")
        return

    # Add the child table field
    pacu_doctype.append("fields", {
        "fieldname": "anaesthetic_record_details",
        "fieldtype": "Table",
        "label": "Anaesthetic Record",
        "options": "Anaesthetic Record Details",
        "reqd": 0
    })
    pacu_doctype.save()
    print("Field 'Anaesthetic Record Details' added to 'Post Anaesthesia Care Unit' successfully!")

# Run the functions
create_anaesthetic_record_child_table()
add_child_table_to_post_anaesthesia_care_unit()
