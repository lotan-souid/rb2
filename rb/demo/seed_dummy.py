import frappe
from frappe import _
from typing import Optional, Dict, Any, Sequence


def _doctype_exists(doctype: str) -> bool:
    return frappe.db.exists("DocType", doctype) is not None


def _by_field(doctype: str, field: str, value: Any) -> Optional[str]:
    rows = frappe.get_all(doctype, filters={field: value}, fields=["name"], limit=1)
    return rows[0].name if rows else None


def _ensure(doctype: str, values: Dict[str, Any], name: Optional[str] = None) -> Optional[str]:
    """Create a document if it doesn't exist. Tries by explicit name, else by first string field.
    Returns the docname or None if doctype is missing.
    """
    if not _doctype_exists(doctype):
        return None
    # If explicit name requested, try get by name
    if name and frappe.db.exists(doctype, name):
        return name
    # Try to find by common title field candidates
    candidates: Sequence[str] = (
        "plan_number",
        "development_project_name",
        "employee_name",
        "department_name",
        "designation_name",
        "sector_name",
        "region_name",
        "committee_name",
        "planning_zone_name",
        "tribe_name",
        "cluster_name",
        "lot_number",
        "full_name",
        "title",
        "name",
    )
    existing_name = None
    for f in candidates:
        if f in values and values.get(f) is not None:
            existing_name = _by_field(doctype, f, values[f])
            if existing_name:
                break
    if existing_name:
        return existing_name
    # Create
    doc = frappe.get_doc({"doctype": doctype, **values})
    if name:
        doc.name = name
    doc.insert(ignore_permissions=True)
    return doc.name


def _map_by_field(doctype: str, key_field: str) -> Dict[Any, str]:
    if not _doctype_exists(doctype):
        return {}
    rows = frappe.get_all(doctype, fields=["name", key_field])
    return {r.get(key_field): r.get("name") for r in rows}


@frappe.whitelist()
def seed_all():
    """Seed a minimal but complete dataset for demo purposes.
    Safe to run multiple times (idempotent best-effort).
    """
    # 1) Base dictionaries
    # Departments
    for d in ("אגף פיתוח", "אגף הסדרה", "אגף תכנון", "אגף הנהלה", "אגף כספים"):
        _ensure("Department", {"department_name": d})

    # Designations
    for d in ("רכז משא ומתן", "מנהל מרחב", "איש GIS", "מנהל אגף", "איש לוגיסטיקה", "איש אגף תכנון", "איש אגף פיתוח"):
        _ensure("Designation", {"designation_name": d})

    # Employees
    employees = [
        {"employee_name": "עומר אדם", "designation": "מנהל מרחב", "department": "אגף הסדרה", "mobile_no": "052-700-1111", "email_id": "omer.adam@example.com"},
        {"employee_name": "אייל גולן", "designation": "מנהל אגף", "department": "אגף הנהלה", "mobile_no": "052-700-2222"},
        {"employee_name": "שירי מימון", "designation": "איש אגף פיתוח", "department": "אגף פיתוח", "mobile_no": "052-700-3333"},
        {"employee_name": "שלמה ארצי", "designation": "איש GIS", "department": "אגף תכנון", "mobile_no": "052-700-4444"},
        {"employee_name": "נינט טייב", "designation": "רכז משא ומתן", "department": "אגף הסדרה", "mobile_no": "052-700-5555"},
        {"employee_name": "מרגלית צנעני", "designation": "איש אגף תכנון", "department": "אגף תכנון", "mobile_no": "052-700-6666"},
        {"employee_name": "רביד פלוטניק", "designation": "איש לוגיסטיקה", "department": "אגף כספים", "mobile_no": "052-700-7777"},
        {"employee_name": "נועה קירל", "designation": "רכז משא ומתן", "department": "אגף הסדרה", "mobile_no": "052-700-8888"},
    ]
    for e in employees:
        _ensure("Employee", e)

    emp_map = _map_by_field("Employee", "employee_name")

    # Tribe
    for t in ("שמעון", "לוי", "נפתלי", "יהודה", "יששכר", "זבולון", "דן", "גד", "אשר", "ראובן", "בנימין", "יוסף"):
        _ensure("Tribe", {"tribe_name": t})

    # Regions
    regions = [
        {"region_name": "מרחב צפון", "region_manager": emp_map.get("עומר אדם")},
        {"region_name": "מרחב מרכז", "region_manager": emp_map.get("שירי מימון")},
        {"region_name": "מרחב דרום", "region_manager": emp_map.get("אייל גולן")},
    ]
    for r in regions:
        _ensure("Region", r)

    reg_map = _map_by_field("Region", "region_name")

    # Sectors
    sectors = [
        {"sector_name": "גליל עליון", "region": reg_map.get("מרחב צפון"), "coordinator": emp_map.get("נינט טייב")},
        {"sector_name": "שרון דרומי", "region": reg_map.get("מרחב מרכז"), "coordinator": emp_map.get("נועה קירל")},
        {"sector_name": "עמק יזרעאל", "region": reg_map.get("מרחב צפון"), "coordinator": emp_map.get("נינט טייב")},
        {"sector_name": "שפלת יהודה", "region": reg_map.get("מרחב מרכז"), "coordinator": emp_map.get("נועה קירל")},
        {"sector_name": "נגב מערבי", "region": reg_map.get("מרחב דרום"), "coordinator": emp_map.get("נינט טייב")},
        {"sector_name": "ערבה תיכונה", "region": reg_map.get("מרחב דרום"), "coordinator": emp_map.get("נועה קירל")},
    ]
    for s in sectors:
        _ensure("Sector", s)

    sec_map = _map_by_field("Sector", "sector_name")
    tribe_map = _map_by_field("Tribe", "tribe_name")

    # Clusters
    clusters = [
        {"cluster_name": "כהן", "tribe": tribe_map.get("לוי"), "sector": sec_map.get("גליל עליון"), "established_date": "1984-06-12"},
        {"cluster_name": "לוי", "tribe": tribe_map.get("יהודה"), "sector": sec_map.get("שרון דרומי"), "established_date": "1992-03-01"},
        {"cluster_name": "מזרחי", "tribe": tribe_map.get("נפתלי"), "sector": sec_map.get("נגב מערבי"), "established_date": "1979-11-22"},
        {"cluster_name": "חדד", "tribe": tribe_map.get("בנימין"), "sector": sec_map.get("עמק יזרעאל"), "established_date": "2001-07-15"},
        {"cluster_name": "פרץ", "tribe": tribe_map.get("דן"), "sector": sec_map.get("שפלת יהודה"), "established_date": "1995-02-10"},
    ]
    for c in clusters:
        _ensure("Cluster", c)

    # Evacuees
    evacuees = [
        {"full_name": "בראד פיט", "id_number": "123456782", "phone": "052-123-4567", "email": "brad.pit@example.com"},
        {"full_name": "אנג'לינה ג'ולי", "id_number": "234567891", "phone": "054-222-3344"},
        {"full_name": "טום קרוז", "id_number": "345678912", "phone": "050-987-6543", "email": "tom.cruise@example.com"},
        {"full_name": "סנדרה בולוק", "id_number": "456789123", "phone": "053-111-2222"},
        {"full_name": "ג'ניפר לורנס", "id_number": "567891234", "phone": "055-876-5432", "email": "j.law@example.com"},
        {"full_name": "קיאנו ריבס", "id_number": "678912345", "phone": "052-765-4321"},
        {"full_name": "מריל סטריפ", "id_number": "789123456", "phone": "058-333-2211", "email": "meryl@example.com"},
        {"full_name": "דנזל וושינגטון", "id_number": "891234567", "phone": "052-444-7788"},
        {"full_name": "רוברט דאוני ג'וניור", "id_number": "912345678", "phone": "050-555-6677"},
        {"full_name": "נטלי פורטמן", "id_number": "135792468", "phone": "054-999-8888", "email": "n.portman@example.com"},
    ]
    for e in evacuees:
        _ensure("Evacuee", e)

    # Planning master data
    for pc in ("ועדת תכנון מרחבית הגליל", "ועדת תכנון נגב", "ועדת תכנון מרכז"):
        _ensure("Planning Committee", {"committee_name": pc})
    for pz in ("אזור תכנון בקעת הירדן", "אזור תכנון שרון", "אזור תכנון גולן", "אזור תכנון שומרון"):
        _ensure("Planning Zone", {"planning_zone_name": pz})

    # Plans (use plan_number as name for easier linking)
    plans = [
        {"name": "101-000123", "plan_number": "101-000123", "plan_name": "תב\"ע הרחבת כביש 90 - צפון", "planning_committee": "ועדת תכנון מרחבית הגליל", "planning_zone": "אזור תכנון גולן", "approval_date": "2023-05-12"},
        {"name": "204-012345", "plan_number": "204-012345", "plan_name": "תב\"ע שכונת מגורים נווה צוף",   "planning_committee": "ועדת תכנון מרכז",       "planning_zone": "אזור תכנון שרון", "approval_date": "2022-11-02"},
        {"name": "315-100200", "plan_number": "315-100200", "plan_name": "תב\"ע פארק תעשייה נגב צפון",     "planning_committee": "ועדת תכנון נגב",         "planning_zone": "אזור תכנון שומרון", "approval_date": "2021-03-27"},
    ]
    for p in plans:
        name = p.pop("name")
        _ensure("Plan", p, name=name)

    # Lots (linked by plan name)
    lots = [
        {"plan": "101-000123", "lot_number": "1",  "area_sqm": 450,  "chargeable": 1},
        {"plan": "101-000123", "lot_number": "2",  "area_sqm": 600,  "chargeable": 1},
        {"plan": "204-012345", "lot_number": "12", "area_sqm": 320,  "chargeable": 1},
        {"plan": "204-012345", "lot_number": "13", "area_sqm": 510,  "chargeable": 1},
        {"plan": "315-100200", "lot_number": "A1", "area_sqm": 1200, "chargeable": 1},
    ]
    for l in lots:
        _ensure("Lot", l)

    # Development Projects (auto-name). Keep a map by human title
    projects_def = [
        {"plan": "101-000123", "development_project_name": "פיתוח כביש 90 צפון", "calculation_source": "Approved", "allocatable_total_cost": 3_500_000, "committee_status": "Pending"},
        {"plan": "204-012345", "development_project_name": "תשתיות שכונת נווה צוף", "calculation_source": "Planned",  "committee_status": "Pending"},
    ]
    proj_name_map: Dict[str, str] = {}
    for pr in projects_def:
        dp_name = _ensure("Development Project", pr)
        if dp_name:
            # map by title field for later linking
            proj_name_map[pr["development_project_name"]] = dp_name

    # Ensure default stages exist (controller creates them after insert)
    # Add Development Items and compute totals
    for human_title, dp_name in proj_name_map.items():
        try:
            project = frappe.get_doc("Development Project", dp_name)
        except Exception:
            continue
        # Refresh stages and build map: stage_name -> stage_docname
        stages = frappe.get_all("Development Stage", filters={"development_project": dp_name}, fields=["name", "stage_name"]) or []
        stage_by_name = {s.get("stage_name"): s.get("name") for s in stages}
        # Seed a few items if table empty
        if not (project.get("table_dtxh") or []):
            items = [
                {"item_name": "עבודות עפר",   "stage": stage_by_name.get("StageA"), "category": "Earthworks", "quantity": 1000, "unit": "m3",   "unit_cost": 50,  "item_status": "InTender"},
                {"item_name": "קו מים ראשי",  "stage": stage_by_name.get("StageA"), "category": "Water",      "quantity": 800,  "unit": "m",    "unit_cost": 120, "item_status": "Planned"},
                {"item_name": "כביש גישה",     "stage": stage_by_name.get("StageB"), "category": "Roads",      "quantity": 500,  "unit": "m",    "unit_cost": 300, "item_status": "Planned"},
                {"item_name": "תאורה היקפית", "stage": stage_by_name.get("Final"),  "category": "Lighting",   "quantity": 80,   "unit": "unit", "unit_cost": 900, "item_status": "Planned"},
            ]
            for it in items:
                project.append("table_dtxh", it)
            project.save(ignore_permissions=True)

        # If Approved allocatable is set and price is not locked, compute price
        try:
            project.reload()
            project.save(ignore_permissions=True)
        except Exception:
            pass

    # Committee Reviews
    reviews = [
        {"development_project": proj_name_map.get("פיתוח כביש 90 צפון"),   "committee_status": "Approved",          "review_date": "2025-09-01", "approved_allocatable_cost": 3_600_000, "summary": "אישור תקציב לביצוע שלב א' וב'"},
        {"development_project": proj_name_map.get("תשתיות שכונת נווה צוף"), "committee_status": "RevisionsRequired", "review_date": "2025-09-03", "summary": "נדרשים עדכוני פירוט לכמויות"},
    ]
    for r in reviews:
        if not r.get("development_project"):
            continue
        _ensure("Development Committee Review", r)

    # Recalculate cost allocation for each project (if controller method exists)
    for dp in proj_name_map.values():
        try:
            project = frappe.get_doc("Development Project", dp)
            if hasattr(project, "recalculate_cost_allocation"):
                project.recalculate_cost_allocation()
        except Exception:
            pass

    # Stage progress updates (optional showcase)
    for dp in proj_name_map.values():
        stages = frappe.get_all("Development Stage", filters={"development_project": dp}, fields=["name", "stage_name"]) or []
        for s in stages:
            if s.get("stage_name") == "StageA":
                _ensure("Stage Progress Update", {"development_stage": s["name"], "update_date": "2025-09-10", "progress_percent": 35, "notes": "סיום חפירה 30%"})
            if s.get("stage_name") == "StageB":
                _ensure("Stage Progress Update", {"development_stage": s["name"], "update_date": "2025-09-18", "progress_percent": 10})

    return {"ok": True}

