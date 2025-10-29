# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt

class Plan(Document):
    def validate(self):
        try:
            if getattr(self, "plan_number", None) and not getattr(self, "location", None) and not self.is_new():
                from rb.gis_integration.api import fetch_plan_geometry
                fetch_plan_geometry(self.name)
        except Exception as e:
            frappe.msgprint(f"Could not fetch plan geometry automatically: {e}", indicator="orange")

    def after_insert(self):
        self._enqueue_geometry_fetch()

    def on_update(self):
        if getattr(self.flags, "in_insert", False):
            return
        try:
            if self.has_value_changed("plan_number") or (self.plan_number and not self.location):
                self._enqueue_geometry_fetch()
        except Exception as e:
            frappe.log_error(f"GIS enqueue error for Plan {self.name}: {e}", "GIS Plan on_update")

    def _enqueue_geometry_fetch(self):
        try:
            if not getattr(self, "plan_number", None):
                return
            frappe.enqueue(
                "rb.gis_integration.api.fetch_plan_geometry",
                plan_name=self.name,
                queue="short",
                timeout=30,
            )
        except Exception as e:
            frappe.log_error(f"GIS enqueue scheduling failed for Plan {self.name}: {e}", "GIS Plan enqueue")

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

    total_area = flt(total)

    frappe.db.set_value("Plan", plan_name, "total_area_sqm", total_area)
    return total_area

@frappe.whitelist()
def update_total_lots(plan_name):
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    total_lots = frappe.db.count("Lot", filters={"plan": plan_name}) or 0

    frappe.db.set_value("Plan", plan_name, "total_lots", total_lots)
    return total_lots

@frappe.whitelist()
def update_total_housing_units(plan_name):
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    total = frappe.db.get_all(
        "Lot",
        filters={"plan": plan_name},
        fields=["sum(housing_units) as total"]
    )[0].total

    total_units = cint(total) if total is not None else 0

    frappe.db.set_value("Plan", plan_name, "housing_units", total_units)
    return total_units

@frappe.whitelist()
def update_total_residential_area(plan_name):
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    total = frappe.db.get_all(
        "Lot",
        filters={
            "plan": plan_name,
            "main_land_designation": "מגורים",
        },
        fields=["sum(area_sqm) as total"],
    )[0].total or 0

    total_area = flt(total)

    frappe.db.set_value("Plan", plan_name, "total_residential_area_sqm", total_area)
    return total_area

@frappe.whitelist()
def update_total_chargeable_area(plan_name):
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    total = frappe.db.get_all(
        "Lot",
        filters={
            "plan": plan_name,
            "chargeable": 1,
        },
        fields=["sum(area_sqm) as total"],
    )[0].total or 0

    total_area = flt(total)

    frappe.db.set_value("Plan", plan_name, "total_chargeable_area_sqm", total_area)
    return total_area

@frappe.whitelist()
def update_residential_lots(plan_name):
    if not frappe.db.exists("Plan", plan_name):
        frappe.throw(f"Plan not found: {plan_name}")

    total = frappe.db.count(
        "Lot",
        filters={
            "plan": plan_name,
            "main_land_designation": "מגורים",
        },
    ) or 0

    frappe.db.set_value("Plan", plan_name, "residential_lots", total)
    return total
