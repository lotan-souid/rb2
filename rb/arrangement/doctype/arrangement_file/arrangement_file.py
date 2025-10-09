# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ArrangementFile(Document):
	def validate(self):
		"""
		בכל שמירה של Arrangement File:
		- מחשבים לכל שורת Link Fixtures את shared_amount = compensation_amount * (share_percentage/100)
		- מסכמים את כל ה-shared_amount לשדה total_fixture_compensation
		- מסכמים לפי סטטוס אישור של ה-Fixture: Approved ו-Pending (Mapping/Finance)
		"""
		self.validate_assigned_lot_uniqueness()
		self.update_totals_with_shares_and_approval()

	def validate_assigned_lot_uniqueness(self):
		assigned_lot = getattr(self, "assigned_lot", None)
		if not assigned_lot:
			return

		conflicts = get_assigned_lot_conflicts(assigned_lot, self.name)
		conflict = conflicts.get("conflict")
		if conflict:
			frappe.throw(
				_("Lot {0} is already assigned to Arrangement File {1}.").format(assigned_lot, conflict),
				frappe.ValidationError,
			)

		cancelled = conflicts.get("cancelled") or []
		if cancelled:
			frappe.msgprint(
				_("Lot {0} was previously assigned to cancelled Arrangement File(s): {1}.").format(
					assigned_lot, ", ".join(cancelled)
				),
				indicator="orange",
				alert=True,
			)

	def update_totals_with_shares_and_approval(self):
		total_all = 0.0
		total_approved = 0.0
		total_pending = 0.0

		for row in self.link_fixtures or []:
			comp = flt(getattr(row, "compensation_amount", 0))
			pct = flt(getattr(row, "share_percentage", 0))
			shared = comp * (pct / 100.0)
			# Ensure child field reflects the computed value
			row.shared_amount = shared
			total_all += shared

			# Lookup approval_status from linked Fixture Compensation
			if getattr(row, "link_fixture", None):
				status = frappe.db.get_value("Fixture Compensation", row.link_fixture, "approval_status")
				if status == "Approved":
					total_approved += shared
				elif status in ("Pending Mapping", "Pending Finance"):
					total_pending += shared

		self.total_fixture_compensation = total_all
		self.total_fixture_comp_approved = total_approved
		self.total_fixture_comp_pending = total_pending


# אופציונלי: פונקציה לשימוש ידני אם תרצה לעדכן לפי שם הרשומה (למשל מתוך Console)
@frappe.whitelist()
def recompute_total_fixture_compensation(name: str) -> float:
	"""
	טען Arrangement File מה־DB, חשב מחדש את הסכום מתוך שורות הילד,
	ועדכן את השדה במסד (ללא מעבר בכל תהליך validate/save).
	"""
	if not frappe.db.exists("Arrangement File", name):
		frappe.throw(f"Arrangement File not found: {name}")

	# סכימה ישירות מה־DB לפי shared_amount (שמחושב בצד השרת)
	totals = frappe.db.sql(
		"""
		SELECT
			COALESCE(SUM(lf.shared_amount), 0) AS total_all,
			COALESCE(SUM(CASE WHEN fc.approval_status = 'Approved' THEN lf.shared_amount ELSE 0 END), 0) AS total_approved,
			COALESCE(SUM(CASE WHEN fc.approval_status IN ('Pending Mapping','Pending Finance') THEN lf.shared_amount ELSE 0 END), 0) AS total_pending
		FROM `tabLink Fixtures` lf
		LEFT JOIN `tabFixture Compensation` fc ON fc.name = lf.link_fixture
		WHERE lf.parent = %s AND lf.parenttype = 'Arrangement File'
		""",
		(name,),
	)[0]

	total_all = float(totals[0] or 0)
	total_approved = float(totals[1] or 0)
	total_pending = float(totals[2] or 0)

	frappe.db.set_value(
		"Arrangement File",
		name,
		{
			"total_fixture_compensation": total_all,
			"total_fixture_comp_approved": total_approved,
			"total_fixture_comp_pending": total_pending,
		},
	)
	return total_all


def get_assigned_lot_conflicts(assigned_lot, current_name=None):
	if not assigned_lot:
		return {"conflict": None, "cancelled": []}

	conflict_filters = {
		"assigned_lot": assigned_lot,
		"docstatus": ["!=", 2],
	}
	if current_name:
		conflict_filters["name"] = ["!=", current_name]

	conflict = frappe.db.get_value("Arrangement File", conflict_filters, "name")

	cancelled_filters = {
		"assigned_lot": assigned_lot,
		"docstatus": 2,
	}
	if current_name:
		cancelled_filters["name"] = ["!=", current_name]

	cancelled = frappe.get_all("Arrangement File", filters=cancelled_filters, pluck="name")
	return {"conflict": conflict, "cancelled": cancelled}


@frappe.whitelist()
def check_assigned_lot_conflicts(assigned_lot=None, docname=None):
	if not docname or (isinstance(docname, str) and docname.lower() == "null"):
		docname = None
	return get_assigned_lot_conflicts(assigned_lot, docname)
