def wipe_custom_drug_status(doc):
    """
    Wipes the `custom_drug_status` field for each item in the drug prescription.
    
    :param doc: The document object containing the drug prescription with items.
    """
    # Loop through each item in the drug prescription
    for item in doc.drug_prescription:
        # Set the `custom_drug_status` field to an empty value (or None, if that is the desired default)
        item.custom_drug_status = None  # or '' if you want to set it to an empty string
    
    # Optionally, save the document if changes need to be persisted
    doc.save()
