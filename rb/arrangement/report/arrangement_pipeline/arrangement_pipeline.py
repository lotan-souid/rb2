import frappe


def execute(filters=None):
    columns = [
        {"label": "Stage", "fieldname": "arrangement_stage", "fieldtype": "Data", "width": 160},
        {"label": "Status", "fieldname": "arrangement_status", "fieldtype": "Data", "width": 140},
        {"label": "Count", "fieldname": "cnt", "fieldtype": "Int", "width": 90},
        {"label": "Avg Age (days)", "fieldname": "avg_age_days", "fieldtype": "Float", "width": 130},
    ]

    rows = frappe.db.sql(
        """
        SELECT
            arrangement_stage,
            arrangement_status,
            COUNT(*) AS cnt,
            AVG(DATEDIFF(NOW(), creation)) AS avg_age_days
        FROM `tabArrangement File`
        GROUP BY arrangement_stage, arrangement_status
        ORDER BY arrangement_stage, arrangement_status
        """,
        as_dict=True,
    )

    return columns, rows

