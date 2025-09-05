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

            if (!frm.doc.price_locked) {
                frm.add_custom_button(__('Lock Price'), () => {
                    frappe.prompt([
                        {
                            fieldname: 'reason',
                            label: __('Reason'),
                            fieldtype: 'Small Text',
                            reqd: 0
                        }
                    ], (values) => {
                        frm.call('lock_price_per_sqm', {reason: values.reason}).then(() => frm.reload_doc());
                    }, __('Lock Price'));
                }, __('Actions'));
            } else {
                frm.add_custom_button(__('Unlock Price'), () => {
                    frappe.prompt([
                        {
                            fieldname: 'reason',
                            label: __('Reason'),
                            fieldtype: 'Small Text',
                            reqd: 0
                        }
                    ], (values) => {
                        frm.call('unlock_price_per_sqm', {reason: values.reason}).then(() => frm.reload_doc());
                    }, __('Unlock Price'));
                }, __('Actions'));
            }
        }
    }
});
