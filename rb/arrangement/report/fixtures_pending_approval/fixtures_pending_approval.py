import frappe


def execute(filters=None):
    columns = [
        {"label": "Name", "fieldname": "name", "fieldtype": "Link", "options": "Fixture Compensation", "width": 160},
        {"label": "Fixture Type", "fieldname": "fixture_type", "fieldtype": "Data", "width": 140},
        {"label": "Compensation Amount", "fieldname": "compensation_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Approval Status", "fieldname": "approval_status", "fieldtype": "Data", "width": 150},
        {"label": "Approved by Mapping", "fieldname": "approved_by_mapping", "fieldtype": "Check", "width": 150},
        {"label": "Approved by Finance", "fieldname": "approved_by_finance", "fieldtype": "Check", "width": 150},
        {"label": "Shared Between Files", "fieldname": "shared_between_files", "fieldtype": "Check", "width": 180},
    ]

    data = frappe.get_all(
        "Fixture Compensation",
        filters={"approval_status": ["in", ["Pending Mapping", "Pending Finance"]]},
        fields=[
            "name",
            "fixture_type",
            "compensation_amount",
            "approval_status",
            "approved_by_mapping",
            "approved_by_finance",
            "shared_between_files",
        ],
        order_by="modified desc",
    )

    return columns, data

