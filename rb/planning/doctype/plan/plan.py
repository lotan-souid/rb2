# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Plan(Document):
	pass

@frappe.whitelist()
def update_total_area(plan_name):
    # נוודא שהתוכנית קיימת
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    # חישוב הסכום
    total = frappe.db.get_all(
        "Lot",
        filters={"plan": plan_name},
        fields=["sum(area_sqm) as total"]
    )[0].total or 0

    frappe.db.set_value("Plan", plan_name, "total_area_sqm", total)
    return total

@frappe.whitelist()
def update_total_lots(plan_name):
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    total_lots = frappe.db.count("Lot", filters={"plan": plan_name}) or 0

    frappe.db.set_value("Plan", plan_name, "total_lots", total_lots)
    return total_lots
