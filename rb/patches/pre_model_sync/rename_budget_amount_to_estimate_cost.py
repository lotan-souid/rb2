import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
    if frappe.db.has_column("Regional Infrastructure Project", "budget_amount"):
        rename_field("Regional Infrastructure Project", "budget_amount", "estimate_cost")
