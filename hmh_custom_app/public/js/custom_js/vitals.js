frappe.ui.form.on('Vital Signs', {
    on_submit: function (frm) {
        frappe.call({
            method: 'hmh_custom_app.custom_api.vitals.create_patient_encounter',
            args: {
                patient: frm.doc.patient,
                encounter_date: frm.doc.signs_date,
                vital_signs: frm.doc.name,
                patient_name: frm.doc.patient_name,
                practitioner: frm.doc.custom_practionaer // Ensure the field name is correct
            },
            callback: function (response) {
                
                if (response.message && !response.error) {
                    frappe.msgprint(__('Direct the Patient to go and See the Doctor. Patient Encounter created successfully.'));
                    
                    // Set the returned patient encounter name to the custom_encounter_id field
                    frm.set_value('custom_encounter_id', response.message.patient_encounter_name);
                    
                    // Save the form after setting the custom_encounter_id
                    frm.save_or_update().then(() => {
                        frappe.msgprint(__('Patient Encounter saved successfully.'));
                    }).catch((error) => {
                        frappe.msgprint(__('Error saving the form: ' + error.message));
                    });
                } else {
                    frappe.msgprint(__('Error creating Patient Encounter: ' + response.error));
                }
            },
            error: function (error) {
                frappe.msgprint(__('An error occurred: ' + error.message));
            }
        });
    }
});
