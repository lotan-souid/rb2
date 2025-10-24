# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Contractor(Document):
	def validate(self):
		if not self.primary_contact:
			return

		linked_company = frappe.db.get_value(
			"Contractor Contact",
			self.primary_contact,
			"contractor_company",
		)

		if linked_company and linked_company != self.name:
			frappe.throw(
				_("Primary Contact must belong to this contractor."),
				frappe.ValidationError,
			)
