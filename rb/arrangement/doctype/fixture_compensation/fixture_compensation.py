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

		# Auto-load GIS geometry when available (skip for brand-new docs until persisted)
		if not self.is_new() and not getattr(self, "location", None):
			self._ensure_geolocation()

	def after_insert(self):
		# Newly created records get their geometry right after insert, once the name exists
		self._ensure_geolocation(force=True)

	def _ensure_geolocation(self, force: bool = False):
		try:
			if force or not getattr(self, "location", None):
				from rb.gis_integration.api import fetch_fixture_compensation_geometry
				fetch_fixture_compensation_geometry(self.name)
		except Exception as e:
			frappe.msgprint(f"Could not fetch fixture geometry automatically: {e}", indicator="orange")
