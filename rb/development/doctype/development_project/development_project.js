// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

const get_allowed_plans = (frm) => {
    const plans = [];
    if (frm.doc.plan) {
        plans.push(frm.doc.plan);
    }
    (frm.doc.participating_plans || []).forEach((row) => {
        if (row.plan && !plans.includes(row.plan)) {
            plans.push(row.plan);
        }
    });
    return plans;
};

const apply_project_type_rules = (frm) => {
    const project_type = frm.doc.development_project_type || "Single Plan";
    const is_single_plan = project_type === "Single Plan";

    if (!is_single_plan && frm.doc.plan) {
        frm.set_value("plan", null);
    }

    if (is_single_plan && Array.isArray(frm.doc.participating_plans) && frm.doc.participating_plans.length) {
        frm.clear_table("participating_plans");
        frm.refresh_field("participating_plans");
    }

    frm.toggle_display("plan", is_single_plan);
    frm.toggle_reqd("plan", is_single_plan);

    frm.toggle_display("participating_plans", !is_single_plan);
    frm.toggle_reqd("participating_plans", !is_single_plan);

    if (frm.fields_dict && frm.fields_dict.participating_plans && frm.fields_dict.participating_plans.grid) {
        frm.fields_dict.participating_plans.grid.set_read_only(is_single_plan ? 1 : 0);
    }
};

const ensure_project_type = (frm) => {
    if (!frm.doc.development_project_type) {
        const default_type = Array.isArray(frm.doc.participating_plans) && frm.doc.participating_plans.length
            ? "Multiple Plans"
            : "Single Plan";
        frm.set_value("development_project_type", default_type);
        return;
    }

    apply_project_type_rules(frm);
};

frappe.ui.form.on("Development Project", {
    setup(frm) {
        frm.set_query("contractor_contact", () => {
            if (!frm.doc.contractor) {
                return {};
            }

            return {
                filters: {
                    contractor_company: frm.doc.contractor
                }
            };
        });

        if (frm.fields_dict.development_project_lots && frm.fields_dict.development_project_lots.grid) {
            frm.fields_dict.development_project_lots.grid.get_field("lot").get_query = function () {
                const filters = {
                    chargeable: 1
                };
                const allowedPlans = get_allowed_plans(frm);
                if (allowedPlans.length) {
                    filters.plan = ["in", allowedPlans];
                }
                return {
                    filters
                };
            };
        }
    },
    onload(frm) {
        ensure_project_type(frm);
    },
    development_project_type(frm) {
        apply_project_type_rules(frm);
    },
    contractor(frm) {
        if (!frm.doc.contractor_contact) {
            return;
        }

        frm.set_value("contractor_contact", null);
    },
    refresh(frm) {
        ensure_project_type(frm);

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
