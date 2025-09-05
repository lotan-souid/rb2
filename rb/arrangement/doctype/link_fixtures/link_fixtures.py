# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe.utils import flt


class LinkFixtures(Document):
	def validate(self):
		# Calculate shared_amount on the server based on share_percentage
		comp_amount = flt(self.compensation_amount or 0)
		share_pct = flt(self.share_percentage or 0)
		self.shared_amount = comp_amount * (share_pct / 100.0)
