import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def on_submit(patient_encounter, dosage, period,selected_drug_code =None,):
    try:
        # Retrieve the encounter document
        encounter = frappe.get_doc('Patient Encounter', patient_encounter)
        
        # Get the rate of the selected drug
        rate = frappe.get_value('Item Price', {'item_code': selected_drug_code, 'price_list': encounter.custom_price_list}, 'price_list_rate') or 0
        
        # Process dosage
        if '-' in dosage:
            dosage_total = sum(map(int, dosage.split('-')))
        else:
            dosage_total = 1
        
        # Process period
        period_days = 0
        period_split = period.split(' ')
        
        if len(period_split) == 2:
            try:
                number = int(period_split[0])
                unit = period_split[1].lower()
                
                if unit in ['day', 'days']:
                    period_days = number
                elif unit in ['week', 'weeks']:
                    period_days = number * 7
                else:
                    raise ValueError("Invalid period unit. Expected 'Day' or 'Week'.")
            except ValueError:
                raise ValueError("Invalid period format. Expected format is 'X Day(s)' or 'X Week(s)'.")
        else:
            raise ValueError("Invalid period format. Expected format is 'X Day(s)' or 'X Week(s)'.")
        
        # Calculate quantity and amount
        qty = dosage_total * period_days
        selected_item_amount = flt(qty) * flt(rate)
        
        return {
            'selected_item_amount': selected_item_amount,
            'qty': qty,
            'rate': flt(rate),
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in updating custom items table')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def pharmacy_calculate(pharmacy, selected_drug_code, dosage, period):
    try:
        # Retrieve the encounter document
        encounter = frappe.get_doc('Pharmacy', pharmacy)
        
        # Get the rate of the selected drug
        rate = frappe.get_value('Item Price', {'item_code': selected_drug_code, 'price_list': encounter.price_list}, 'price_list_rate') or 0
        
        # Process dosage
        if '-' in dosage:
            dosage_total = sum(map(int, dosage.split('-')))
        else:
            dosage_total = 1
        
        # Process period
        period_days = 0
        period_split = period.split(' ')
        
        if len(period_split) == 2:
            try:
                number = int(period_split[0])
                unit = period_split[1].lower()
                
                if unit in ['day', 'days']:
                    period_days = number
                elif unit in ['week', 'weeks']:
                    period_days = number * 7
                else:
                    raise ValueError("Invalid period unit. Expected 'Day' or 'Week'.")
            except ValueError:
                raise ValueError("Invalid period format. Expected format is 'X Day(s)' or 'X Week(s)'.")
        else:
            raise ValueError("Invalid period format. Expected format is 'X Day(s)' or 'X Week(s)'.")
        
        # Calculate quantity and amount
        qty = dosage_total * period_days
        selected_item_amount = flt(qty) * flt(rate)
        
        return {
            'selected_item_amount': selected_item_amount,
            'qty': qty,
            'rate': flt(rate),
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in updating custom items table')
        return {'status': 'error', 'message': str(e)}
