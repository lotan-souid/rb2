// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

frappe.ui.form.on('Arrangement File', {
    refresh: function(frm) {
        // חישוב סכום בהתחלה כשפותחים טופס
        update_total_fixture_compensation(frm);

        // הוספת כפתור למחיקת Fixture Compensation (השורה הראשונה כדוגמה)
        if (frm.doc.link_fixtures && frm.doc.link_fixtures.length > 0) {
            frm.add_custom_button(__('Delete Fixture Compensation'), function() {
                let row = frm.doc.link_fixtures[0]; 
                if (!row.link_fixture) {
                    frappe.msgprint(__('No linked Fixture Compensation found.'));
                    return;
                }

                // ווידוא כפול
                frappe.confirm(
                    __('Are you sure you want to delete Fixture Compensation {0}?', [row.link_fixture]),
                    function() {
                        frappe.confirm(
                            __('This action is irreversible. Delete {0}?', [row.link_fixture]),
                            function() {
                                frappe.call({
                                    method: "frappe.client.delete",
                                    args: {
                                        doctype: "Fixture Compensation",
                                        name: row.link_fixture
                                    },
                                    callback: function(r) {
                                        if (!r.exc) {
                                            frappe.msgprint(__('Fixture Compensation {0} deleted.', [row.link_fixture]));
                                            frm.reload_doc();
                                        }
                                    }
                                });
                            }
                        );
                    }
                );
            }, __("Actions"));
        }
    }
});

// מאזינים לשינויים בטבלת Link Fixtures
frappe.ui.form.on('Link Fixtures', {
    compensation_amount: function(frm, cdt, cdn) {
        update_total_fixture_compensation(frm);
    },
    link_fixture: function(frm, cdt, cdn) {
        update_total_fixture_compensation(frm);
    }
});

// פונקציה לחישוב הסכום הכולל
function update_total_fixture_compensation(frm) {
    let total = 0.0;
    (frm.doc.link_fixtures || []).forEach(row => {
        total += flt(row.compensation_amount) || 0;
    });
    frm.set_value('total_fixture_compensation', total);
}
