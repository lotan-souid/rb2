import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
    if frappe.db.has_column("Regional Infrastructure Project", "estimate_cost"):
        rename_field("Regional Infrastructure Project", "estimate_cost", "total_estimate_cost")
    if frappe.db.has_column("Regional Infrastructure Project", "actual_cost"):
        rename_field("Regional Infrastructure Project", "actual_cost", "total_actual_cost")
