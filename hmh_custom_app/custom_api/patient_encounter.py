# import frappe
# from frappe import _
# from frappe.utils import flt

# def fetch_item_rate(item_code, price_list):
#     item_price = frappe.get_value('Item Price', {'item_code': item_code, 'price_list': price_list}, 'price_list_rate')
#     return item_price if item_price else 0

# def calculate_qty(dosage, period):
#     if not dosage or not period:
#         return 0
#     dosage_parts = dosage.split('-')
#     dosage_total = sum([int(d) for d in dosage_parts if d.isdigit()])
#     period_days = int(period.split(' ')[0]) * (7 if 'Week' in period else 1)
#     return dosage_total * period_days

# def process_drug_prescriptions(encounter):
#     drug_sum = 0
#     for drug in encounter.drug_prescription:
#         qty = calculate_qty(drug.dosage, drug.period)
#         rate = fetch_item_rate(drug.drug_code, encounter.custom_price_list)
#         amount = qty * rate
#         drug_sum += amount
#         if not any(item.item == drug.drug_code for item in encounter.custom_items):
#             encounter.append('custom_items', {
#                 'item': drug.drug_code,
#                 'qty': qty,
#                 'rate': rate,
#                 'amount': amount
#             })
#     return drug_sum

# def process_lab_test_prescriptions(encounter):
#     lab_test_sum = 0
#     for lab_test in encounter.lab_test_prescription:
#         rate = fetch_item_rate(lab_test.lab_test_code, encounter.custom_price_list)
#         lab_test_sum += rate
#         if not any(item.item == lab_test.lab_test_code for item in encounter.custom_items):
#             encounter.append('custom_items', {
#                 'item': lab_test.lab_test_code,
#                 'qty': 1,
#                 'rate': rate,
#                 'amount': rate
#             })
#     return lab_test_sum

# def process_procedure_prescriptions(encounter):
#     procedure_sum = 0
#     for procedure in encounter.procedure_prescription:
#         rate = fetch_item_rate(procedure.procedure, encounter.custom_price_list)
#         procedure_sum += rate
#         if not any(item.item == procedure.procedure for item in encounter.custom_items):
#             encounter.append('custom_items', {
#                 'item': procedure.procedure,
#                 'qty': 1,
#                 'rate': rate,
#                 'amount': rate
#             })
#     return procedure_sum

# def process_therapy_plans(encounter):
#     therapy_sum = 0
#     for therapy in encounter.therapies:
#         rate = fetch_item_rate(therapy.therapy_type, encounter.custom_price_list)
#         therapy_sum += rate
#         if not any(item.item == therapy.therapy_type for item in encounter.custom_items):
#             encounter.append('custom_items', {
#                 'item': therapy.therapy_type,
#                 'qty': 1,
#                 'rate': rate,
#                 'amount': rate
#             })
#     return therapy_sum

# def process_service_requests(encounter):
#     service_sum = 0
#     service_requests = frappe.get_all('Service Request', filters={'order_group': encounter.name, 'order_date': encounter.encounter_date}, fields=['template_dn'])

#     for service in service_requests:
#         rate = fetch_item_rate(service['template_dn'], encounter.custom_price_list)
#         service_sum += rate
#         if not any(item.item == service['template_dn'] for item in encounter.custom_items):
#             encounter.append('custom_items', {
#                 'item': service['template_dn'],
#                 'qty': 1,
#                 'rate': rate,
#                 'amount': rate
#             })
#     return service_sum

# def process_encounter(encounter):
#     drug_sum = process_drug_prescriptions(encounter)
#     lab_test_sum = process_lab_test_prescriptions(encounter)
#     procedure_sum = process_procedure_prescriptions(encounter)
#     therapy_sum = process_therapy_plans(encounter)
#     service_sum = process_service_requests(encounter)

#     total_qty = sum([item.qty for item in encounter.custom_items])
#     grand_total = sum([item.amount for item in encounter.custom_items])
    
#     encounter.custom_total_qty = total_qty
#     encounter.custom_grand_totals = grand_total
    
#     encounter.save()
#     frappe.db.commit()  # Ensure changes are committed to the database
    
#     return {
#         'drug_sum': drug_sum,
#         'lab_test_sum': lab_test_sum,
#         'procedure_sum': procedure_sum,
#         'therapy_sum': therapy_sum,
#         'service_sum': service_sum,
#         'total_sum': drug_sum + lab_test_sum + procedure_sum + therapy_sum + service_sum
#     }

# @frappe.whitelist()
# def on_submit(patient_encounter):
#     try:
#         encounter = frappe.get_doc('Patient Encounter', patient_encounter)
#         sums = process_encounter(encounter)
#         return {'status': 'success', 'message': 'Custom items table updated successfully.', 'sums': sums}
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), 'Error in updating custom items table')
#         return {'status': 'error', 'message': str(e)}
