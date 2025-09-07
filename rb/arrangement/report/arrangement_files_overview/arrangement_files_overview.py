import frappe


def execute(filters=None):
    columns = [
        {"label": "Arrangement File", "fieldname": "name", "fieldtype": "Link", "options": "Arrangement File", "width": 180},
        {"label": "Stage", "fieldname": "arrangement_stage", "fieldtype": "Data", "width": 120},
        {"label": "Status", "fieldname": "arrangement_status", "fieldtype": "Data", "width": 120},
        {"label": "Evacuee A", "fieldname": "evacuee_a", "fieldtype": "Link", "options": "Evacuee", "width": 140},
        {"label": "Evacuee B", "fieldname": "evacuee_b", "fieldtype": "Link", "options": "Evacuee", "width": 140},
        {"label": "Assigned Lot", "fieldname": "assigned_lot", "fieldtype": "Link", "options": "Lot", "width": 140},
        {"label": "Total Compensation", "fieldname": "total_fixture_compensation", "fieldtype": "Currency", "width": 150},
        {"label": "Approved", "fieldname": "total_fixture_comp_approved", "fieldtype": "Currency", "width": 140},
        {"label": "Pending", "fieldname": "total_fixture_comp_pending", "fieldtype": "Currency", "width": 140},
        {"label": "Created", "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
        {"label": "Last Modified", "fieldname": "modified", "fieldtype": "Datetime", "width": 160},
    ]

    data = frappe.get_all(
        "Arrangement File",
        fields=[
            "name",
            "arrangement_stage",
            "arrangement_status",
            "evacuee_a",
            "evacuee_b",
            "assigned_lot",
            "total_fixture_compensation",
            "total_fixture_comp_approved",
            "total_fixture_comp_pending",
            "creation",
            "modified",
        ],
        order_by="modified desc",
    )

    return columns, data

