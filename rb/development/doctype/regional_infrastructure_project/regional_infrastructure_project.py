# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class RegionalInfrastructureProject(Document):
    def validate(self):
        self._ensure_unique_links()
        self._sync_cost_totals()

    def _ensure_unique_links(self):
        seen: set[str] = set()
        duplicates: list[str] = []
        for row in self.get("linked_projects") or []:
            project = getattr(row, "development_project", None)
            if not project:
                continue
            if project in seen:
                duplicates.append(project)
            else:
                seen.add(project)
        if duplicates:
            dup_list = ", ".join(sorted(set(duplicates)))
            frappe.throw(
                _("Development Projects can be linked only once per Regional Infrastructure Project. Duplicates: {0}").format(
                    dup_list
                ),
                frappe.ValidationError,
            )

    def _sync_cost_totals(self):
        planned_total = 0.0
        actual_total = 0.0
        for row in self.get("regional_infrastructure_development_items") or []:
            qty = float(getattr(row, "quantity", 0) or 0)
            unit_cost = float(getattr(row, "unit_cost", 0) or 0)
            planned_cost = float(getattr(row, "planned_cost", 0) or 0)
            if not planned_cost and qty and unit_cost and hasattr(row, "planned_cost"):
                planned_cost = qty * unit_cost
                row.planned_cost = planned_cost
            planned_total += planned_cost
            actual_total += float(getattr(row, "actual_cost", 0) or 0)

        if hasattr(self, "total_estimate_cost"):
            self.total_estimate_cost = planned_total
        if hasattr(self, "total_actual_cost"):
            self.total_actual_cost = actual_total
