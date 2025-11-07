# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate
from typing import Any


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

        if not getattr(self, "development_project_type", None):
            if self.get("participating_plans"):
                self.development_project_type = "Multiple Plans"
            else:
                self.development_project_type = "Single Plan"

        project_type = self.development_project_type or "Single Plan"
        if project_type == "Single Plan":
            if not getattr(self, "plan", None):
                frappe.throw(
                    _("Plan is required when Development Project Type is Single Plan."),
                    frappe.ValidationError,
                )
            if self.get("participating_plans"):
                frappe.throw(
                    _("Participating Plans must be empty when Development Project Type is Single Plan."),
                    frappe.ValidationError,
                )
        elif project_type == "Multiple Plans":
            if not self.get("participating_plans"):
                frappe.throw(
                    _("Add at least one Participating Plan when Development Project Type is Multiple Plans."),
                    frappe.ValidationError,
                )
            if getattr(self, "plan", None):
                frappe.throw(
                    _("Plan must be empty when Development Project Type is Multiple Plans."),
                    frappe.ValidationError,
                )

        project_plans = self._get_project_plan_names()
        lot_details = self._get_project_lot_details()
        self._validate_project_lots(project_plans, lot_details)
        self._update_plan_aggregates(project_plans)

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
            self._compute_price_per_sqm(allocatable, lot_details=lot_details)

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

    def _get_project_plan_names(self) -> list[str]:
        plan_names: list[str] = []
        primary = getattr(self, "plan", None)
        if primary:
            plan_names.append(primary)
        for row in (self.get("participating_plans") or []):
            plan_name = getattr(row, "plan", None)
            if plan_name and plan_name not in plan_names:
                plan_names.append(plan_name)
        return plan_names

    def _update_plan_aggregates(self, plan_names: list[str]):
        total_residential = 0
        total_housing_units = 0
        first_location = None

        if plan_names:
            try:
                plan_rows = frappe.get_all(
                    "Plan",
                    filters=[["Plan", "name", "in", plan_names]],
                    fields=["name", "residential_lots", "housing_units", "location"],
                )
            except Exception:
                plan_rows = []
            for row in plan_rows:
                total_residential += int(row.get("residential_lots") or 0)
                total_housing_units += int(row.get("housing_units") or 0)
                if not first_location and row.get("location"):
                    first_location = row.get("location")

        if hasattr(self, "residential_lots"):
            self.residential_lots = total_residential
        if hasattr(self, "housing_units"):
            self.housing_units = total_housing_units
        if hasattr(self, "location"):
            if first_location:
                self.location = first_location
            else:
                self.location = None

    def _compute_price_per_sqm(self, allocatable_total_cost: float, lot_details: list[dict[str, Any]] | None = None):
        lot_details = lot_details or self._get_project_lot_details()
        if not lot_details:
            return
        total_area = sum((lot.get("area_sqm") or 0) for lot in lot_details if int(lot.get("chargeable") or 0))
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
        """Create or update Development Cost Allocation for all linked project lots and update Lot fields."""
        self.check_permission("write")
        lot_details = self._get_project_lot_details()
        chargeable_lots = [lot for lot in lot_details if int(lot.get("chargeable") or 0)]
        if not chargeable_lots:
            raise frappe.ValidationError("Add at least one chargeable Lot under Development Project Lots before recalculation.")
        price_per_sqm = getattr(self, "dev_price_per_sqm", None)
        if not price_per_sqm:
            raise frappe.ValidationError("Dev Price per sqm is not set. Save the document first.")
        existing_allocs = {
            row.get("lot"): row
            for row in frappe.get_all(
                "Development Cost Allocation",
                filters={"development_project": self.name},
                fields=["name", "lot", "locked"],
                limit_page_length=1000,
            )
        }
        current_lot_names = {lot.get("name") for lot in chargeable_lots}
        self._sync_lot_assignments(list(current_lot_names))

        for lot in chargeable_lots:
            area = lot.get("area_sqm") or 0
            allocated = (area or 0) * price_per_sqm
            existing = existing_allocs.get(lot["name"])
            if existing and existing.get("locked"):
                continue
            if existing:
                alloc = frappe.get_doc("Development Cost Allocation", existing.get("name"))
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
                "lot_price": allocated,
                "lot_development_status": lot_status,
            })
        # Remove stale allocations for lots that are no longer linked (unless locked)
        for lot_name, alloc in existing_allocs.items():
            if lot_name in current_lot_names or alloc.get("locked"):
                continue
            try:
                frappe.delete_doc("Development Cost Allocation", alloc.get("name"), ignore_permissions=True)
            except Exception:
                pass
        return {
            "updated_lots": len(chargeable_lots),
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
        self._sync_lot_assignments()

    def on_update(self):
        # Keep stage totals in sync on updates
        self._update_stage_totals()
        self._sync_lot_assignments()

    def on_trash(self):
        self._sync_lot_assignments(clear_all=True)

    def _get_project_lot_names(self) -> list[str]:
        lot_names: list[str] = []
        for row in (self.get("development_project_lots") or []):
            lot_name = getattr(row, "lot", None)
            if lot_name and lot_name not in lot_names:
                lot_names.append(lot_name)
        return lot_names

    def _get_project_lot_details(self) -> list[dict[str, Any]]:
        lot_names = self._get_project_lot_names()
        if not lot_names:
            return []
        lots = frappe.get_all(
            "Lot",
            filters={"name": ["in", lot_names]},
            fields=["name", "plan", "area_sqm", "chargeable"],
            limit_page_length=1000,
        )
        # Preserve child table order
        by_name = {lot["name"]: lot for lot in lots}
        ordered = [by_name[name] for name in lot_names if name in by_name]
        return ordered

    def _validate_project_lots(self, allowed_plans: list[str], lot_details: list[dict[str, Any]]):
        if not (self.get("development_project_lots") or []):
            return
        seen: set[str] = set()
        for row in self.get("development_project_lots") or []:
            lot = getattr(row, "lot", None)
            if not lot:
                continue
            if lot in seen:
                frappe.throw(
                    _("Lot {0} cannot be added more than once to the same Development Project.").format(frappe.bold(lot)),
                    frappe.ValidationError,
                )
            seen.add(lot)
        allowed = set(allowed_plans or [])
        lookup = {lot["name"]: lot for lot in lot_details}
        if not allowed and lot_details:
            frappe.throw(
                _("Set the Plan/Participating Plans before linking lots to the Development Project."),
                frappe.ValidationError,
            )
        for lot in lot_details:
            plan_name = lot.get("plan")
            if allowed and plan_name not in allowed:
                frappe.throw(
                    _("Lot {0} belongs to Plan {1}, which is not part of this Development Project.").format(
                        frappe.bold(lot.get("name")), frappe.bold(plan_name or "-")
                    ),
                    frappe.ValidationError,
                )
            if not int(lot.get("chargeable") or 0):
                frappe.throw(
                    _("Lot {0} is not marked as Chargeable and cannot participate in cost allocation.").format(
                        frappe.bold(lot.get("name"))
                    ),
                    frappe.ValidationError,
                )
        other_refs = frappe.get_all(
            "Development Project Lot",
            filters={
                "lot": ["in", list(lookup.keys())],
                "parenttype": "Development Project",
                "parent": ["!=", self.name],
            },
            fields=["lot", "parent"],
            limit_page_length=1000,
        )
        if other_refs:
            blocked = ", ".join(sorted({ref.get("lot") for ref in other_refs if ref.get("lot")}))
            frappe.throw(
                _("Each Lot can belong to a single Development Project. Already linked lots: {0}").format(blocked),
                frappe.ValidationError,
            )

    def _sync_lot_assignments(self, lot_names: list[str] | None = None, clear_all: bool = False):
        if not self.name:
            return
        target = set(lot_names or self._get_project_lot_names())
        existing = set(frappe.get_all("Lot", filters={"related_project": self.name}, pluck="name") or [])
        to_clear = existing if clear_all else existing - target
        to_set = set() if clear_all else target - existing
        if to_clear:
            for lot in to_clear:
                frappe.db.set_value(
                    "Lot",
                    lot,
                    {
                        "related_project": None,
                        "dev_price_per_sqm": 0,
                        "allocated_dev_cost": 0,
                        "lot_price": 0,
                        "lot_development_status": None,
                    },
                )
        for lot in to_set:
            frappe.db.set_value("Lot", lot, {"related_project": self.name})


def refresh_development_project_plan_totals(plan_name: str):
    """Update aggregated plan-driven totals on every Development Project referencing the given Plan."""
    if not plan_name:
        return

    processed = frappe.flags.setdefault("_dp_plan_refresh", set())
    if plan_name in processed:
        return
    processed.add(plan_name)

    try:
        linked_projects = set(
            frappe.get_all("Development Project", filters={"plan": plan_name}, pluck="name") or []
        )
        participating_projects = frappe.get_all(
            "Development Project Plan",
            filters={
                "plan": plan_name,
                "parenttype": "Development Project",
            },
            fields=["parent"],
        )
        for row in participating_projects:
            if row.get("parent"):
                linked_projects.add(row.get("parent"))

        if not linked_projects:
            return

        for project_name in linked_projects:
            try:
                project = frappe.get_doc("Development Project", project_name)
                plan_names = project._get_project_plan_names()
                project._update_plan_aggregates(plan_names)
                frappe.db.set_value(
                    "Development Project",
                    project_name,
                    {
                        "residential_lots": getattr(project, "residential_lots", 0),
                        "housing_units": getattr(project, "housing_units", 0),
                        "location": getattr(project, "location", None),
                    },
                )
            except Exception as err:
                frappe.log_error(
                    f"Could not refresh Development Project aggregates for {project_name}: {err}",
                    "Development Project Aggregate Sync",
                )
    except Exception as outer_err:
        frappe.log_error(
            f"Failed gathering Development Projects for plan {plan_name}: {outer_err}",
            "Development Project Aggregate Sync",
        )
