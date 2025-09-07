import frappe


def execute(filters=None):
    columns = [
        {"label": "Fixture Type", "fieldname": "fixture_type", "fieldtype": "Data", "width": 160},
        {"label": "Approval Status", "fieldname": "approval_status", "fieldtype": "Data", "width": 160},
        {"label": "Count", "fieldname": "cnt", "fieldtype": "Int", "width": 90},
        {"label": "Total Compensation", "fieldname": "total_amount", "fieldtype": "Currency", "width": 160},
        {"label": "Shared Between Files", "fieldname": "shared_between_files", "fieldtype": "Data", "width": 160},
    ]

    rows = frappe.db.sql(
        """
        SELECT
            fixture_type,
            approval_status,
            CASE WHEN shared_between_files = 1 THEN 'Yes' ELSE 'No' END AS shared_between_files,
            COUNT(*) AS cnt,
            SUM(COALESCE(compensation_amount, 0)) AS total_amount
        FROM `tabFixture Compensation`
        GROUP BY fixture_type, approval_status, shared_between_files
        ORDER BY fixture_type, approval_status
        """,
        as_dict=True,
    )

    return columns, rows

