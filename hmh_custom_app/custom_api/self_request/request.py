import frappe
from frappe import _

def create_radiology(doc, method):
    try:
        # Fetch the Patient Payment Management document and related Patient and Patient Registration Identification
        patient_doc = frappe.get_doc('Patient', doc.patient)
        patient_reg_doc = frappe.get_doc('Patient Registration Identification', patient_doc.custom_patient_mrno)

        # Define item groups to process
        radiology_groups = ['Radiology Services', 'Ultrasound Scan Services', 'X-ray scanning services']
        procedure_groups = ['Minor Procedure', 'Major Procedure', 'Procedures']
        lab_test_groups = ['Laboratory services-Outsourced', 'Laboratory services-In-house', 'Laboratory']
        drug_groups = ['Drugs']

        for item in doc.invoice_detailed_items:
            group = frappe.get_doc('Item', item.item)

            if item.self_request:
                if group.item_group in radiology_groups:
                    # Create Radiology document
                    create_observation(patient_doc, doc, patient_reg_doc,item.item)
                elif group.item_group in procedure_groups:
                    # Create Clinical Procedure document
                    create_clinical_procedure(patient_doc, doc, item.item)
                elif group.item_group in lab_test_groups:
                    # Create Lab Test document
                    create_lab_test(patient_doc, doc, item.item)
                elif group.item_group in drug_groups:
                    # Create Pharmacy document
                    create_pharmacy(patient_doc, doc, patient_reg_doc, item)

        frappe.db.commit()  # Commit changes to the database only after all operations are done

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in creating documents"))
        frappe.throw(_("There was an issue creating the necessary documents. Please check the logs for more details."))

def create_observation(patient_doc, payment_mgt,patient_reg_doc, item):
    try:
        radiology_doc = frappe.new_doc('Observation')
        obseve_name = frappe.get_doc('Observation Template', item)
        radiology_doc.observation_template = obseve_name.name
        radiology_doc.observation_category = obseve_name.observation_category
        # radiology_doc.custom_cost_center = "Radiology - HMH"
        radiology_doc.patient = patient_doc.name
        radiology_doc.invoiced = 1
        radiology_doc.age = patient_reg_doc.full_age
        radiology_doc.posting_date = payment_mgt.posting_date
        radiology_doc.healthcare_practitioner = patient_doc.custom_consulting_doctor
        radiology_doc.custom_sr_payment_id = payment_mgt.name
        # radiology_doc.medical_department = patient_doc.custom_consulting_department

        # Logging for debugging
        # frappe.log_error(f"Observation Doc Values: {radiology_doc.as_dict()}", "Observation Doc Debug")

        radiology_doc.insert()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in creating Observation document"))

def create_clinical_procedure(patient_doc, payment_mgt, item):
    try:
        procedure_doc = frappe.new_doc('Clinical Procedure')
        procedure_doc.procedure_template = item
        procedure_doc.patient = patient_doc.name
        # procedure_doc.custom_cost_center = "Theatre - HMH"
        procedure_doc.invoiced = 1
        procedure_doc.start_date = payment_mgt.posting_date
        procedure_doc.practitioner = patient_doc.custom_consulting_doctor
        procedure_doc.custom_sr_payment_id = payment_mgt.name

        procedure_doc.insert()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in creating Clinical Procedure document"))

def create_lab_test(patient_doc, payment_mgt, item):
    try:
        lab_test_doc = frappe.new_doc('Lab Test')
        lab_test_doc.template = item
        lab_test_doc.patient = patient_doc.name
        lab_test_doc.patient_sex = patient_doc.sex
        lab_test_doc.custom_sr_payment_id = payment_mgt.name
        lab_test_doc.date = payment_mgt.posting_date
        lab_test_doc.practitioner = patient_doc.custom_consulting_doctor
        lab_test_doc.invoiced = 1

        lab_test_doc.save()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in creating Lab Test document"))

def create_pharmacy(patient_doc, payment_mgt, patient_reg_doc, item):
    try:
        pharmacy_doc = frappe.new_doc("Pharmacy")
        pharmacy_doc.update({
            "patient": patient_doc.name,
            "patient_sex": patient_doc.sex,
            "patient_age": patient_reg_doc.full_age,
            "encounter_date": payment_mgt.posting_date,
            "practitioner": patient_doc.custom_consulting_doctor,
            "price_list": patient_doc.default_price_list,
            "custom_sr_payment_id": payment_mgt.name,
            "medical_department": patient_doc.custom_consulting_department,
            "drug_prescription": []
        })
        
        # Append item to the Pharmacy doc
        pharmacy_doc.append("drug_prescription", {
            "drug_code": item.item,
            "qty": 1,
            "amount": item.outstanding_amount,
            "dosage": '1-0-1',
            "dosage_form": 'Cream',
        })

        pharmacy_doc.insert()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in creating Pharmacy document"))
