// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Contractor", {
    setup(frm) {
        frm.set_query("primary_contact", () => {
            if (frm.is_new()) {
                return {
                    filters: {
                        contractor_company: "__invalid__"
                    }
                };
            }

            return {
                filters: {
                    contractor_company: frm.doc.name
                }
            };
        });
    }
});
