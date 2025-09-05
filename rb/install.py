import frappe


def ensure_workflow_state(name: str, icon: str = "question-sign", style: str = "Info"):
    if not frappe.db.exists("Workflow State", name):
        doc = frappe.get_doc({
            "doctype": "Workflow State",
            "workflow_state_name": name,
            "name": name,
            "icon": icon,
            "style": style,
        })
        doc.insert(ignore_permissions=True)


def after_migrate():
    # Make sure required states used by workflows exist
    # Especially for: Development Committee Review Workflow
    try:
        ensure_workflow_state("Pending", icon="question-sign", style="Info")
        ensure_workflow_state("RevisionsRequired", icon="edit", style="Warning")
    except Exception:
        # Do not block migrate; admin can import fixtures as fallback
        pass

