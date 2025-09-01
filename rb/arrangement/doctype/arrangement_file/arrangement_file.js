// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Arrangement File", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Arrangement File', {
    refresh: function(frm) {
        // מחשבים סכום בהתחלה (כשפותחים טופס)
        update_total_fixture_compensation(frm);
    }
});

// מאזינים לשינויים בשורות של Link Fixtures
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

