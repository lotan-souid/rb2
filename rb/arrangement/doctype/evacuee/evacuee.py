# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils.data import getdate, today


class Evacuee(Document):
	@property
	def age(self) -> int | None:
		"""Return evacuee age in whole years based on date_of_birth."""
		if not self.date_of_birth:
			return None

		try:
			birth_date = getdate(self.date_of_birth)
			current_date = getdate(today())
		except Exception:
			return None

		years = current_date.year - birth_date.year
		if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
			years -= 1

		return max(years, 0)
