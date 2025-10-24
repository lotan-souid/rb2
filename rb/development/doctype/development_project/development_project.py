# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _
from frappe.model.document import Document
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
        if allocatable is not None and not getattr(self, "price_locked", 0):
            self._compute_price_per_sqm(allocatable)

        # Ensure selected contractor contact matches contractor
        if getattr(self, "contractor_contact", None):
            if not getattr(self, "contractor", None):
                frappe.throw(
                    _("Select a contractor before choosing a contractor contact."),
                    frappe.ValidationError,
                )
            contact_company = frappe.db.get_value(
                "Contractor Contact",
                self.contractor_contact,
                "contractor_company",
            )
            if contact_company and contact_company != self.contractor:
                frappe.throw(
                    _("Contractor Contact must belong to the selected contractor."),
                    frappe.ValidationError,
                )

        # Ensure default stages exist (StageA, StageB, Final)
        # moved to after_insert to avoid link validation before project exists
        pass

        # Update stage totals will run after insert/update

        # Sync committee status from related Committee Reviews (latest decision wins)
        self._sync_committee_status()

    def _ensure_default_stages(self):
        if not self.name or not frappe.db.exists("Development Project", self.name):
            return
        existing = frappe.get_all("Development Stage", filters={"development_project": self.name}, fields=["name", "stage_name"])
        if existing:
            return
        for s in ("StageA", "StageB", "Final"):
            stage = frappe.get_doc({
                "doctype": "Development Stage",
                "development_project": self.name,
                "stage_name": s,
            })
            stage.insert(ignore_permissions=True)

    def _update_stage_totals(self):
        stages = frappe.get_all("Development Stage", filters={"development_project": self.name}, fields=["name"]) 
        for st in stages:
            try:
                stage = frappe.get_doc("Development Stage", st.get("name"))
                stage.update_totals_from_items()
                stage.save(ignore_permissions=True)
            except Exception:
                pass

    def _compute_price_per_sqm(self, allocatable_total_cost: float):
        # Sum chargeable areas from all lots in this plan
        if not self.plan:
            return
        lots = frappe.get_all("Lot", filters={"plan": self.plan, "chargeable": 1}, fields=["name", "area_sqm"])
        total_area = sum((lot.get("area_sqm") or 0) for lot in lots)
        if total_area and hasattr(self, "dev_price_per_sqm"):
            self.dev_price_per_sqm = allocatable_total_cost / total_area

    def _append_price_history_if_changed(self, prev_price):
        cur_price = getattr(self, "dev_price_per_sqm", None)
        if cur_price is None:
            return
        if prev_price is None or float(prev_price) != float(cur_price):
            row = {
                "change_date": nowdate(),
                "price_per_sqm": cur_price,
                "calculation_source": getattr(self, "calculation_source", None),
                "locked": getattr(self, "price_locked", 0),
                "note": "Auto entry on save",
            }
            try:
                self.append("price_history", row)
            except Exception:
                pass

    def _sync_committee_status(self):
        try:
            if not hasattr(self, "committee_status") or not self.name:
                return
            latest = frappe.get_all(
                "Development Committee Review",
                filters={"development_project": self.name},
                fields=["committee_status", "modified"],
                order_by="modified desc",
                limit=1,
            )
            if latest:
                self.committee_status = latest[0].get("committee_status") or self.committee_status
        except Exception:
            # Fail-safe: don't block save if Committee Review doctype is missing or query fails
            pass

    @frappe.whitelist()
    def lock_price_per_sqm(self, reason: str | None = None):
        self.check_permission("write")
        if not getattr(self, "dev_price_per_sqm", None):
            raise frappe.ValidationError("Cannot lock. Price per sqm is empty.")
        self.price_locked = 1
        self.price_lock_date = nowdate()
        if reason:
            self.price_lock_reason = reason
        # Add history
        self.append("price_history", {
            "change_date": nowdate(),
            "price_per_sqm": self.dev_price_per_sqm,
            "calculation_source": getattr(self, "calculation_source", None),
            "locked": 1,
            "note": reason or "Locked",
        })
        self.save()
        return {"locked": True, "price": self.dev_price_per_sqm}

    @frappe.whitelist()
    def unlock_price_per_sqm(self, reason: str | None = None):
        self.check_permission("write")
        self.price_locked = 0
        # Log history
        self.append("price_history", {
            "change_date": nowdate(),
            "price_per_sqm": self.dev_price_per_sqm,
            "calculation_source": getattr(self, "calculation_source", None),
            "locked": 0,
            "note": reason or "Unlocked",
        })
        self.save()
        return {"locked": False}

    @frappe.whitelist()
    def recalculate_cost_allocation(self):
        """Create or update Development Cost Allocation for all lots in the plan and update Lot fields."""
        self.check_permission("write")
        if not self.plan:
            raise frappe.ValidationError("Plan is required on Development Project")
        price_per_sqm = getattr(self, "dev_price_per_sqm", None)
        if not price_per_sqm:
            raise frappe.ValidationError("Dev Price per sqm is not set. Save the document first.")
        lots = frappe.get_all("Lot", filters={"plan": self.plan, "chargeable": 1}, fields=["name", "area_sqm"])
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

    def before_save(self):
        # If price is locked, avoid recomputing it (keep as is)
        prev_price = None
        if not self.is_new():
            prev_price = frappe.db.get_value("Development Project", self.name, "dev_price_per_sqm")
        if getattr(self, "price_locked", 0):
            # Skip recompute of price, but still update totals
            pass
        else:
            # Allow validate() to compute dev_price_per_sqm; nothing to do here
            pass
        # Append to history if changed
        self._append_price_history_if_changed(prev_price)

    def after_insert(self):
        # Create default stages only after the project exists in DB
        self._ensure_default_stages()
        self._update_stage_totals()

    def on_update(self):
        # Keep stage totals in sync on updates
        self._update_stage_totals()
