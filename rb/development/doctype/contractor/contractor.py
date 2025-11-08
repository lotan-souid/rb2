# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

MANAGING_COMPANY_TYPE = "חברה מנהלת"


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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_managing_company_query(doctype, txt, searchfield, start, page_len, filters=None):
	"""Return contractors tagged as managing companies."""
	managing_type = (filters or {}).get("managing_type") or MANAGING_COMPANY_TYPE
	return frappe.db.sql(
		"""
		SELECT
			name,
			company_name
		FROM `tabContractor`
		WHERE docstatus < 2
			AND (name LIKE %(txt)s OR company_name LIKE %(txt)s)
			AND EXISTS (
				SELECT 1
				FROM `tabContractor Type Item` cti
				WHERE cti.parent = `tabContractor`.name
					AND cti.contractor_type = %(managing_type)s
			)
		ORDER BY
			IF(LOCATE(%(txt)s, name), LOCATE(%(txt)s, name), 99999),
			name
		LIMIT %(start)s, %(page_len)s
		""",
		{
			"txt": f"%{txt}%",
			"start": start,
			"page_len": page_len,
			"managing_type": managing_type,
		},
	)
