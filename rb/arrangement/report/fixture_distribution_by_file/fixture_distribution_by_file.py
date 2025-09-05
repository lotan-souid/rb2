import frappe


def execute(filters=None):
    columns = [
        {"label": "Arrangement File", "fieldname": "arrangement_file", "fieldtype": "Link", "options": "Arrangement File", "width": 190},
        {"label": "Fixture", "fieldname": "link_fixture", "fieldtype": "Link", "options": "Fixture Compensation", "width": 180},
        {"label": "Approval Status", "fieldname": "approval_status", "fieldtype": "Data", "width": 140},
        {"label": "Compensation Amount", "fieldname": "compensation_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Share %", "fieldname": "share_percentage", "fieldtype": "Float", "width": 90},
        {"label": "Shared Amount", "fieldname": "shared_amount", "fieldtype": "Currency", "width": 150},
    ]

    rows = frappe.db.sql(
        """
        SELECT
            lf.parent AS arrangement_file,
            lf.link_fixture,
            fc.approval_status,
            lf.compensation_amount,
            lf.share_percentage,
            lf.shared_amount
        FROM `tabLink Fixtures` lf
        LEFT JOIN `tabFixture Compensation` fc ON fc.name = lf.link_fixture
        WHERE lf.parenttype = 'Arrangement File'
        ORDER BY lf.parent, lf.modified DESC
        """,
        as_dict=True,
    )

    return columns, rows

