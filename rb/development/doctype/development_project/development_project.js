// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Development Project", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Recalculate Allocation'), () => {
                frm.call('recalculate_cost_allocation').then(r => {
                    frappe.show_alert({
                        message: __('Allocation updated. Price/m²: {0}', [frm.doc.dev_price_per_sqm || '-']),
                        indicator: 'green'
                    });
                });
            }, __('Actions'));
        }
    }
});
