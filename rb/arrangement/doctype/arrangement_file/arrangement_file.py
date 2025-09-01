# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class ArrangementFile(Document):
	def validate(self):
		"""
		בכל שמירה של Arrangement File:
		- מסכמים את כל compensation_amount מהטבלה link_fixtures
		- שומרים את התוצאה בשדה total_fixture_compensation
		"""
		self.update_total_fixture_compensation_from_child_rows()

	def update_total_fixture_compensation_from_child_rows(self):
		total = 0.0
		for row in (self.link_fixtures or []):
			total += flt(getattr(row, "compensation_amount", 0))
		self.total_fixture_compensation = total



# אופציונלי: פונקציה לשימוש ידני אם תרצה לעדכן לפי שם הרשומה (למשל מתוך Console)
@frappe.whitelist()
def recompute_total_fixture_compensation(name: str) -> float:
	"""
	טען Arrangement File מה־DB, חשב מחדש את הסכום מתוך שורות הילד,
	ועדכן את השדה במסד (ללא מעבר בכל תהליך validate/save).
	"""
	if not frappe.db.exists("Arrangement File", name):
		frappe.throw(f"Arrangement File not found: {name}")

	# סכימה ישירות מה־DB על ערך הילד (כפי שמוצג בטבלה)
	total = frappe.db.sql("""
		SELECT COALESCE(SUM(compensation_amount), 0)
		FROM `tabLink Fixtures`
		WHERE parent = %s AND parenttype = 'Arrangement File'
	""", (name,))[0][0] or 0

	frappe.db.set_value("Arrangement File", name, "total_fixture_compensation", total)
	return float(total)
