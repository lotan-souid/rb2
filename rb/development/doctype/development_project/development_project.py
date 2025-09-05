# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import nowdate


class DevelopmentProject(Document):
	def validate(self):
		# Compute planned cost from child items if present (quantity * unit_cost)
		planned_total = 0
		actual_total = 0
		for row in (self.get("table_dtxh") or []):
			# Backward compatibility: if child row has planned_cost, trust it; otherwise compute
			qty = (getattr(row, "quantity", None) or 0) if hasattr(row, "quantity") else 0
			unit_cost = (getattr(row, "unit_cost", None) or 0) if hasattr(row, "unit_cost") else 0
			if hasattr(row, "planned_cost"):
				if not row.planned_cost and qty and unit_cost:
					row.planned_cost = qty * unit_cost
				planned_total += (row.planned_cost or 0)
			else:
				planned_total += 0
			actual_total += (getattr(row, "actual_cost", 0) or 0)

		# Mirror totals into existing fields
		if hasattr(self, "estimate_cost"):
			self.estimate_cost = planned_total
		if hasattr(self, "actual_cost"):
			self.actual_cost = actual_total

		# Derive allocatable cost and dev price per sqm when possible
		alloc_source = (self.calculation_source or "Approved") if hasattr(self, "calculation_source") else "Approved"
		allocatable = None
		if alloc_source == "Approved" and getattr(self, "allocatable_total_cost", None):
			allocatable = self.allocatable_total_cost
		elif alloc_source == "Planned":
			allocatable = planned_total
		elif alloc_source == "Actual":
			allocatable = actual_total
		# ManualAdjustment leaves value as-is
		if allocatable is not None:
			self._compute_price_per_sqm(allocatable)

	def _compute_price_per_sqm(self, allocatable_total_cost: float):
		# Sum chargeable areas from all lots in this plan
		if not self.plan:
			return
		lots = frappe.get_all("Lot", filters={"plan": self.plan}, fields=["name", "area_sqm"])
		total_area = sum((lot.get("area_sqm") or 0) for lot in lots)
		if total_area and hasattr(self, "dev_price_per_sqm"):
			self.dev_price_per_sqm = allocatable_total_cost / total_area

	@frappe.whitelist()
	def recalculate_cost_allocation(self):
		"""Create or update Development Cost Allocation for all lots in the plan and update Lot fields."""
		self.check_permission("write")
		if not self.plan:
			raise frappe.ValidationError("Plan is required on Development Project")
		price_per_sqm = getattr(self, "dev_price_per_sqm", None)
		if not price_per_sqm:
			raise frappe.ValidationError("Dev Price per sqm is not set. Save the document first.")
		lots = frappe.get_all("Lot", filters={"plan": self.plan}, fields=["name", "area_sqm"])
		for lot in lots:
			area = lot.get("area_sqm") or 0
			allocated = (area or 0) * price_per_sqm
			# Upsert allocation row
			existing = frappe.get_all(
				"Development Cost Allocation",
				filters={"development_project": self.name, "lot": lot["name"]},
				fields=["name", "locked"],
				limit=1,
			)
			if existing and existing[0].get("locked"):
				continue
			if existing:
				alloc = frappe.get_doc("Development Cost Allocation", existing[0].get("name"))
				alloc.chargeable_area_sqm = area
				alloc.price_per_sqm = price_per_sqm
				alloc.allocated_cost = allocated
				alloc.calculation_date = nowdate()
				alloc.save(ignore_permissions=True)
			else:
				alloc = frappe.get_doc({
					"doctype": "Development Cost Allocation",
					"development_project": self.name,
					"lot": lot["name"],
					"calculation_source": getattr(self, "calculation_source", "Approved"),
					"calculation_date": nowdate(),
					"chargeable_area_sqm": area,
					"price_per_sqm": price_per_sqm,
					"allocated_cost": allocated,
				})
				alloc.insert(ignore_permissions=True)
			# Reflect on Lot fields
			# Map project status to lot development status
			proj_status = getattr(self, "status", "") or ""
			lot_status = "NotStarted"
			if proj_status in ("שלב א", "שלב ב", "שלב גמר", "אישור ועדה"):
				lot_status = "InProgress"
			if proj_status in ("מסירה",):
				lot_status = "Completed"
			frappe.db.set_value("Lot", lot["name"], {
				"related_project": self.name,
				"dev_price_per_sqm": price_per_sqm,
				"allocated_dev_cost": allocated,
				"lot_development_status": lot_status,
			})
		return {
			"updated_lots": len(lots),
			"price_per_sqm": price_per_sqm,
		}
