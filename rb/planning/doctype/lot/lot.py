# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Lot(Document):
	def validate(self):
		# If Lot ID exists and no geometry yet, try to fetch quietly
		try:
			if getattr(self, "lot_id", None) and not getattr(self, "location", None):
				from rb.gis_integration.api import fetch_lot_geometry
				fetch_lot_geometry(self.name)
		except Exception as e:
			frappe.msgprint(f"Could not fetch geometry automatically: {e}", indicator="orange")

		# Housing units allowed only on residential lots
		if getattr(self, "housing_units", None) and getattr(self, "main_land_designation", None) != "מגורים":
			frappe.throw(_("Housing Units can be set only for lots with main land designation 'מגורים'."))

		# Calculate lot price from area and development price per sqm
		if hasattr(self, "lot_price"):
			area = flt(getattr(self, "area_sqm", 0))
			price_per_sqm = flt(getattr(self, "dev_price_per_sqm", 0))
			self.lot_price = area * price_per_sqm


def on_update(doc, method=None):
	from rb.planning.doctype.plan.plan import (
		update_residential_lots,
		update_total_area,
		update_total_chargeable_area,
		update_total_housing_units,
		update_total_lots,
		update_total_residential_area,
	)
	if doc.plan:
		update_total_area(doc.plan)
		update_total_residential_area(doc.plan)
		update_total_chargeable_area(doc.plan)
		update_total_lots(doc.plan)
		update_residential_lots(doc.plan)
		update_total_housing_units(doc.plan)

	# GIS sync: if Lot ID changed, enqueue geometry fetch
	try:
		if hasattr(doc, "lot_id") and doc.has_value_changed("lot_id") and doc.lot_id:
			frappe.enqueue(
				"rb.gis_integration.api.fetch_lot_geometry",
				lot_name=doc.name,
				queue="short",
				timeout=30,
			)
	except Exception as e:
		frappe.log_error(f"GIS enqueue error for Lot {doc.name}: {e}", "GIS Lot on_update")


def after_delete(doc, method=None):
	from rb.planning.doctype.plan.plan import (
		update_residential_lots,
		update_total_area,
		update_total_chargeable_area,
		update_total_housing_units,
		update_total_lots,
		update_total_residential_area,
	)
	if doc.plan:
		update_total_area(doc.plan)
		update_total_residential_area(doc.plan)
		update_total_chargeable_area(doc.plan)
		update_total_lots(doc.plan)
		update_residential_lots(doc.plan)
		update_total_housing_units(doc.plan)
