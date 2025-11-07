// Copyright (c) 2025, lotan souid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Regional Infrastructure Project", {
	onload(frm) {
		frm.events.calculate_totals(frm);
	},
	refresh(frm) {
		frm.events.calculate_totals(frm);
	},
	regional_infrastructure_development_items_add(frm) {
		frm.events.calculate_totals(frm);
	},
	regional_infrastructure_development_items_remove(frm) {
		frm.events.calculate_totals(frm);
	},
	calculate_totals(frm) {
		const items = frm.doc.regional_infrastructure_development_items || [];
		let totalEstimate = 0;
		let totalActual = 0;
		items.forEach((row) => {
			const planned = frappe.utils.flt(row.planned_cost);
			const actual = frappe.utils.flt(row.actual_cost);
			totalEstimate += planned;
			totalActual += actual;
		});
		frm.set_value("total_estimate_cost", totalEstimate);
		frm.set_value("total_actual_cost", totalActual);
	},
});

frappe.ui.form.on("Regional Infrastructure Development Items", {
	quantity(frm, cdt, cdn) {
		update_row_planned_cost(frm, cdt, cdn);
	},
	unit_cost(frm, cdt, cdn) {
		update_row_planned_cost(frm, cdt, cdn);
	},
	actual_cost(frm) {
		frm.events.calculate_totals(frm);
	},
});

function update_row_planned_cost(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row) {
		return;
	}
	const qty = frappe.utils.flt(row.quantity);
	const unitCost = frappe.utils.flt(row.unit_cost);
	const planned = qty * unitCost;
	frappe.model.set_value(cdt, cdn, "planned_cost", planned || 0);
	frm.events.calculate_totals(frm);
}
