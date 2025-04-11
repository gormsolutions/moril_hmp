// frappe.ui.form.on("Patient Encounter", {
//     refresh: function(frm) {
//         // Check if the document is submitted
//         if (frm.doc.docstatus == 0 || frm.doc.docstatus == 1) {
//             frm.add_custom_button(
//                 __("Print PDF"),
//                 function() {
//                     // Define the print format name
//                     var print_format = "Patient Medical Report";

//                     // Generate the URL to download the PDF file using the base URL
//                     var base_url = "/printview";
//                     var url = 
//                         `${base_url}?doctype=${encodeURIComponent(frm.doc.doctype)}` +
//                         `&name=${encodeURIComponent(frm.doc.name)}` +
//                         `&format=${encodeURIComponent(print_format)}` +
//                         `&no_letterhead=1` + // Set to 1 to disable letterhead; change to 0 to include it
//                         `&letterhead=No%20Letterhead` +
//                         `&settings={}` +
//                         `&_lang=en`;

//                     // Log the URL for debugging
//                     console.log(url);

//                     // Open the PDF file in a new tab
//                     window.open(url, '_blank');
//                 },
//                 __("PDF")
//             );
//         }
//     }
// });

