# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FixtureCompensation(Document):
	def validate(self):
		# If managing shares at the fixture level, compute shared_amount per row
		if getattr(self, "fixture_shares", None):
			for row in self.fixture_shares:
				pct = flt(getattr(row, "share_percentage", 0))
				row.shared_amount = flt(self.compensation_amount or 0) * (pct / 100.0)
