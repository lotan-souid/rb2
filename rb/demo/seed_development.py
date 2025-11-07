import frappe
from frappe.utils import nowdate
from frappe.model.workflow import apply_workflow
import random
import re


def _generate_plan_number() -> str:
    """Generate plan number in format ###-####### (e.g., 123-4567890)."""
    left = random.randint(100, 999)
    right = random.randint(1_000_000, 9_999_999)
    return f"{left}-{right}"


def _ensure_plan(plan_number: str | None, plan_name: str | None = None) -> str:
    # normalize/generate plan number to ###-#######
    pat = re.compile(r"^\d{3}-\d{7}$")
    if not plan_number or not pat.match(plan_number):
        plan_number = _generate_plan_number()
    existing = frappe.get_all("Plan", filters={"plan_number": plan_number}, fields=["name"], limit=1)
    if existing:
        return existing[0]["name"]
    # default Hebrew names if not provided
    plan_name = plan_name or random.choice([
        "הרחבת שכונה ה",
        "רובע צפון",
        "קריית הדרום",
        "שכונת הגנים",
        "מרכז העסקים החדש",
    ])
    plan = frappe.get_doc({
        "doctype": "Plan",
        "plan_number": plan_number,
        "plan_name": plan_name,
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


def _ensure_dev_project(plan: str, name: str, allocatable_total_cost: float, project_lots: list[str] | None = None) -> str:
    existing = frappe.get_all(
        "Development Project",
        filters={"plan": plan, "development_project_name": name},
        fields=["name"],
        limit=1,
    )
    if existing:
        dp_name = existing[0]["name"]
        if project_lots:
            dp = frappe.get_doc("Development Project", dp_name)
            _sync_project_lots(dp, project_lots)
        return dp_name
    dp = frappe.get_doc({
        "doctype": "Development Project",
        "plan": plan,
        "development_project_name": name,
        "development_project_type": "Single Plan",
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
    if project_lots:
        _sync_project_lots(dp, project_lots)
    dp.save(ignore_permissions=True)
    return dp.name


def _sync_project_lots(dp, project_lots: list[str]):
    project_lots = [lot for lot in project_lots if lot]
    if not project_lots:
        return
    existing = {row.get("lot") for row in (dp.get("development_project_lots") or []) if row.get("lot")}
    changed = False
    for lot in project_lots:
        if lot in existing:
            continue
        dp.append("development_project_lots", {"lot": lot})
        changed = True
    if changed:
        dp.save(ignore_permissions=True)


def _add_committee_review(dp_name: str, approved_allocatable_cost: float) -> str:
    # Create in Pending, then transition via workflow to Approved
    cr = frappe.get_doc({
        "doctype": "Development Committee Review",
        "development_project": dp_name,
        "committee_status": "Pending",
        "review_date": nowdate(),
        "approved_allocatable_cost": approved_allocatable_cost,
        "decisions": "Approved budget for allocation.",
    })
    cr.insert(ignore_permissions=True)
    try:
        apply_workflow(cr, "Approve")
    except Exception:
        # Fallback: set field directly if workflow action unavailable
        frappe.db.set_value("Development Committee Review", cr.name, "committee_status", "Approved")
    return cr.name


def _recalculate_allocations(dp_name: str):
    dp = frappe.get_doc("Development Project", dp_name)
    try:
        # Method checks permissions; Administrator should pass in bench context
        dp.recalculate_cost_allocation()
    except Exception:
        # Fallback inline allocation if permission check blocks
        project_lots = [
            row.get("lot")
            for row in (dp.get("development_project_lots") or [])
            if row.get("lot")
        ]
        if project_lots:
            lots = frappe.get_all(
                "Lot",
                filters={
                    "name": ["in", project_lots],
                    "chargeable": 1,
                },
                fields=["name", "area_sqm"],
            )
        else:
            lots = []
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


def run(
    plan_number: str | None = None,
    plan_name: str | None = None,
    project_name: str | None = None,
    allocatable_total_cost: float = 5_000_000,
    num_lots: int = 3,
    lot_area_min: int = 500,
    lot_area_max: int = 1500,
) -> dict:
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
    # ensure framework reloads disabled scripts
    frappe.clear_cache()

    try:
        # 1) Plan (plan_number auto-generated to ###-####### if not provided)
        plan_docname = _ensure_plan(plan_number, plan_name=plan_name)

        # 2) Lots (numeric lot_number; area in [min,max])
        created_lots = []
        # start lot numbers from 101, 102, ...
        base_no = random.randint(100, 199)
        for i in range(num_lots):
            lot_no = str(base_no + i)
            area = float(random.randint(int(lot_area_min), int(lot_area_max)))
            name = _ensure_lot(plan_docname, lot_no, area)
            created_lots.append({"name": name, "lot_number": lot_no, "area_sqm": area})

        # 3) Development Project with items
        effective_project_name = project_name or f"פרויקט פיתוח {plan_docname}"
        project_lot_names = [lot["name"] for lot in created_lots if lot.get("name")]
        dp_name = _ensure_dev_project(plan_docname, effective_project_name, allocatable_total_cost, project_lot_names)

        # 4) Committee Review (Approved)
        _add_committee_review(dp_name, approved_allocatable_cost=allocatable_total_cost)

        # 5) Recalculate cost allocations and reflect on Lot
        _recalculate_allocations(dp_name)

        return {
            "plan": plan_docname,
            "project": dp_name,
            "lots": created_lots,
            "price_per_sqm": frappe.db.get_value("Development Project", dp_name, "dev_price_per_sqm"),
        }
    finally:
        # Re-enable scripts we disabled
        for name in reenable:
            frappe.db.set_value("Server Script", name, "disabled", 0)
        frappe.clear_cache()


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


def apply_actuals_for_project(
    project_name: str,
    stage_a_items: tuple[str, ...] = ("Earthworks", "Access Roads"),
    stage_b_items: tuple[str, ...] = ("Water Network", "Sewer Network"),
) -> dict:
    """Populate actual_cost and stage assignment for an existing Development Project.

    - Assigns items by name to StageA/StageB
    - Sets actual_cost = planned_cost and item_status = Completed for those
    - Recomputes stage totals and keeps stage statuses

    Usage:
      bench --site <site> execute rb.demo.seed_development.apply_actuals_for_project --kwargs '{"project_name":"<DP_NAME>"}'
    """
    # Disable interfering server scripts
    reenable = []
    for s in frappe.get_all(
        "Server Script",
        filters={"reference_doctype": ["in", ["Development Task", "Development Project"]]},
        fields=["name", "disabled"],
    ):
        if not s.get("disabled"):
            reenable.append(s["name"])
            frappe.db.set_value("Server Script", s["name"], "disabled", 1)
    frappe.clear_cache()

    try:
        dp = frappe.get_doc("Development Project", project_name)
        # Fetch Stage docnames
        stages = {
            s.get("stage_name"): s.get("name")
            for s in frappe.get_all(
                "Development Stage",
                filters={"development_project": dp.name},
                fields=["name", "stage_name"],
            )
        }
        stage_a = stages.get("StageA")
        stage_b = stages.get("StageB")

        changed = 0
        for row in (dp.get("table_dtxh") or []):
            name = (getattr(row, "item_name", "") or "").strip()
            if name in stage_a_items and stage_a:
                row.stage = stage_a
                row.actual_cost = row.planned_cost or 0
                row.item_status = "Completed"
                changed += 1
            elif name in stage_b_items and stage_b:
                row.stage = stage_b
                row.actual_cost = row.planned_cost or 0
                row.item_status = "Completed"
                changed += 1

        if changed:
            dp.save(ignore_permissions=True)

        # Recompute stage totals explicitly
        for key in ("StageA", "StageB", "Final"):
            if key in stages:
                st = frappe.get_doc("Development Stage", stages[key])
                st.update_totals_from_items()
                st.save(ignore_permissions=True)

        return {"project": dp.name, "items_updated": changed}
    finally:
        for name in reenable:
            frappe.db.set_value("Server Script", name, "disabled", 0)
        frappe.clear_cache()


def seed_stage_b_completed(
    plan_number: str | None = None,
    plan_name: str | None = None,
    project_name: str | None = None,
    allocatable_total_cost: float = 6_000_000,
    num_lots: int = 4,
    lot_area_min: int = 500,
    lot_area_max: int = 1500,
) -> dict:
    """Seed a Development Project for a new Plan where development started and Stage B is completed.

    - Project status set to "שלב ב" (in progress at stage B)
    - Stage A: Completed, Stage B: Completed, Final: NotStarted

    Usage:
      bench --site <site> execute rb.demo.seed_development.seed_stage_b_completed
    """
    # Disable interfering server scripts
    reenable = []
    for s in frappe.get_all(
        "Server Script", filters={"reference_doctype": ["in", ["Development Task", "Development Project"]]}, fields=["name", "disabled"]
    ):
        if not s.get("disabled"):
            reenable.append(s["name"])
            frappe.db.set_value("Server Script", s["name"], "disabled", 1)
    frappe.clear_cache()

    try:
        # Create base data via run()
        base = run(
            plan_number=plan_number,
            plan_name=plan_name,
            project_name=project_name,
            allocatable_total_cost=allocatable_total_cost,
            num_lots=num_lots,
            lot_area_min=lot_area_min,
            lot_area_max=lot_area_max,
        )

        dp_name = base["project"]

        # Update stages
        stages = frappe.get_all(
            "Development Stage",
            filters={"development_project": dp_name},
            fields=["name", "stage_name", "stage_status"],
        )
        status_map = {"StageA": "Completed", "StageB": "Completed", "Final": "NotStarted"}
        for st in stages:
            new_status = status_map.get(st.get("stage_name"))
            if new_status and new_status != st.get("stage_status"):
                frappe.db.set_value("Development Stage", st.get("name"), {
                    "stage_status": new_status,
                    "start_date": nowdate() if new_status != "NotStarted" else None,
                    "end_date": nowdate() if new_status == "Completed" else None,
                })

        # Set project status to "שלב ב" and reflect committee_status Approved on the project
        frappe.db.set_value("Development Project", dp_name, {
            "status": "שלב ב",
            "status_change": nowdate(),
            "committee_status": "Approved",
        })

        # Return summary
        updated = frappe.get_all(
            "Development Stage",
            filters={"development_project": dp_name},
            fields=["stage_name", "stage_status", "start_date", "end_date"],
            order_by="stage_name asc",
        )
        return {"plan": base["plan"], "project": dp_name, "stages": updated}
    finally:
        for name in reenable:
            frappe.db.set_value("Server Script", name, "disabled", 0)
        frappe.clear_cache()
