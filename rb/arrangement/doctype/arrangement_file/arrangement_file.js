// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

frappe.ui.form.on('Arrangement File', {
    refresh: function(frm) {
        // חישוב סכום בהתחלה כשפותחים טופס
        update_total_fixture_compensation(frm);

        // סינון בחירת מגרש לפי סטטוס התב"ע: רק מגרשים שבתוכנית הסטטוס שלה "אישור ומתן תוקף"
        frm.set_query('assigned_lot', function() {
            return {
                filters: {
                    plan_status: 'אישור ומתן תוקף'
                }
            };
        });

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
    },
    assigned_lot: function(frm) {
        const lot = frm.doc.assigned_lot;
        if (!lot) {
            return;
        }

        frappe.call({
            method: 'rb.arrangement.doctype.arrangement_file.arrangement_file.check_assigned_lot_conflicts',
            args: {
                assigned_lot: lot,
                docname: frm.is_new() ? null : frm.doc.name
            },
            callback: function({ message }) {
                const data = message || {};
                if (data.conflict) {
                    const conflictDoc = data.conflict;
                    frm.set_value('assigned_lot', null);
                    frappe.msgprint({
                        message: __('Lot {0} is already assigned to Arrangement File {1}.', [lot, conflictDoc]),
                        indicator: 'red'
                    });
                    return;
                }

                const cancelled = Array.isArray(data.cancelled) ? data.cancelled : [];
                if (cancelled.length) {
                    frappe.msgprint({
                        message: __('Lot {0} was previously assigned to cancelled Arrangement File(s): {1}.', [lot, cancelled.join(', ')]),
                        indicator: 'orange'
                    });
                }
            }
        });
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
