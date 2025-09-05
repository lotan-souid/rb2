import frappe
from frappe.utils import nowdate


def _ensure_plan(plan_number: str, plan_name: str | None = None) -> str:
    existing = frappe.get_all("Plan", filters={"plan_number": plan_number}, fields=["name"], limit=1)
    if existing:
        return existing[0]["name"]
    plan = frappe.get_doc({
        "doctype": "Plan",
        "plan_number": plan_number,
        "plan_name": plan_name or plan_number,
    })
    plan.insert(ignore_permissions=True)
    return plan.name


def _ensure_lot(plan: str, lot_number: str, area_sqm: float) -> str:
    existing = frappe.get_all(
        "Lot", filters={"plan": plan, "lot_number": lot_number}, fields=["name"], limit=1
    )
    if existing:
        return existing[0]["name"]
    lot = frappe.get_doc({
        "doctype": "Lot",
        "plan": plan,
        "lot_number": lot_number,
        "area_sqm": area_sqm,
        # chargeable defaults to 1 in DocType; set explicitly for clarity
        "chargeable": 1,
    })
    lot.insert(ignore_permissions=True)
    return lot.name


def _ensure_dev_project(plan: str, name: str, allocatable_total_cost: float) -> str:
    existing = frappe.get_all(
        "Development Project",
        filters={"plan": plan, "development_project_name": name},
        fields=["name"],
        limit=1,
    )
    if existing:
        return existing[0]["name"]
    dp = frappe.get_doc({
        "doctype": "Development Project",
        "plan": plan,
        "development_project_name": name,
        "calculation_source": "Approved",
        "allocatable_total_cost": allocatable_total_cost,
    })
    # Add sample items (auto-compute planned_cost)
    for row in (
        {"item_name": "Earthworks", "category": "Earthworks", "quantity": 1, "unit": "lot", "unit_cost": 1_000_000},
        {"item_name": "Water Network", "category": "Water", "quantity": 1, "unit": "lot", "unit_cost": 800_000},
        {"item_name": "Sewer Network", "category": "Sewer", "quantity": 1, "unit": "lot", "unit_cost": 900_000},
        {"item_name": "Access Roads", "category": "Roads", "quantity": 1, "unit": "lot", "unit_cost": 1_200_000},
    ):
        dp.append("table_dtxh", row)
    dp.insert(ignore_permissions=True)
    dp.save(ignore_permissions=True)
    return dp.name


def _add_committee_review(dp_name: str, approved_allocatable_cost: float) -> str:
    cr = frappe.get_doc({
        "doctype": "Development Committee Review",
        "development_project": dp_name,
        "committee_status": "Approved",
        "review_date": nowdate(),
        "approved_allocatable_cost": approved_allocatable_cost,
        "decisions": "Approved budget for allocation.",
    })
    cr.insert(ignore_permissions=True)
    return cr.name


def _recalculate_allocations(dp_name: str):
    dp = frappe.get_doc("Development Project", dp_name)
    try:
        # Method checks permissions; Administrator should pass in bench context
        dp.recalculate_cost_allocation()
    except Exception:
        # Fallback inline allocation if permission check blocks
        lots = frappe.get_all("Lot", filters={"plan": dp.plan, "chargeable": 1}, fields=["name", "area_sqm"])
        price = dp.dev_price_per_sqm or 0
        for lot in lots:
            area = lot.get("area_sqm") or 0
            allocated = area * price
            existing = frappe.get_all(
                "Development Cost Allocation",
                filters={"development_project": dp.name, "lot": lot["name"]},
                fields=["name", "locked"],
                limit=1,
            )
            if existing and existing[0].get("locked"):
                continue
            if existing:
                alloc = frappe.get_doc("Development Cost Allocation", existing[0].get("name"))
                alloc.chargeable_area_sqm = area
                alloc.price_per_sqm = price
                alloc.allocated_cost = allocated
                alloc.calculation_date = nowdate()
                alloc.save(ignore_permissions=True)
            else:
                alloc = frappe.get_doc({
                    "doctype": "Development Cost Allocation",
                    "development_project": dp.name,
                    "lot": lot["name"],
                    "calculation_source": getattr(dp, "calculation_source", "Approved"),
                    "calculation_date": nowdate(),
                    "chargeable_area_sqm": area,
                    "price_per_sqm": price,
                    "allocated_cost": allocated,
                })
                alloc.insert(ignore_permissions=True)
            frappe.db.set_value("Lot", lot["name"], {
                "related_project": dp.name,
                "dev_price_per_sqm": price,
                "allocated_dev_cost": allocated,
                "lot_development_status": "InProgress",
            })


def run(plan_number: str = "RB-100", project_name: str = "RB-100 Dev", allocatable_total_cost: float = 5_000_000):
    """Seed demo data for Development workflow.

    Usage:
      bench --site <site> execute rb.demo.seed_development.run
    """
    frappe.flags.in_test = True  # reduce side-effects

    # Temporarily disable Server Scripts that depend on Development Task
    reenable = []
    for s in frappe.get_all("Server Script", filters={"reference_doctype": ["in", ["Development Task", "Development Project"]]}, fields=["name", "disabled", "reference_doctype"]):
        if not s.get("disabled"):
            reenable.append(s["name"])
            frappe.db.set_value("Server Script", s["name"], "disabled", 1)

    try:
        # 1) Plan
        plan_name = _ensure_plan(plan_number, plan_name=f"Plan {plan_number}")

        # 2) Lots
        for lot_no, area in (("L-01", 500.0), ("L-02", 750.0), ("L-03", 1250.0)):
            _ensure_lot(plan_name, lot_no, area)

        # 3) Development Project with items
        dp_name = _ensure_dev_project(plan_name, project_name, allocatable_total_cost)

        # 4) Committee Review (Approved)
        _add_committee_review(dp_name, approved_allocatable_cost=allocatable_total_cost)

        # 5) Recalculate cost allocations and reflect on Lot
        _recalculate_allocations(dp_name)

        return {
            "plan": plan_name,
            "project": dp_name,
            "lots": frappe.get_all("Lot", filters={"plan": plan_name}, fields=["name", "area_sqm"], order_by="name asc"),
            "price_per_sqm": frappe.db.get_value("Development Project", dp_name, "dev_price_per_sqm"),
        }
    finally:
        # Re-enable scripts we disabled
        for name in reenable:
            frappe.db.set_value("Server Script", name, "disabled", 0)


def toggle_dev_task_scripts(disabled: int = 1):
    """Enable/disable server scripts that reference Development Task/Project to avoid seed-time errors.

    Usage:
      bench --site <site> execute rb.demo.seed_development.toggle_dev_task_scripts --kwargs '{"disabled": 1}'
    """
    names = frappe.get_all(
        "Server Script",
        filters={"reference_doctype": ["in", ["Development Task", "Development Project"]]},
        pluck="name",
    )
    for n in names:
        frappe.db.set_value("Server Script", n, "disabled", 1 if int(disabled) else 0)
    return {"updated": names, "disabled": int(disabled)}
