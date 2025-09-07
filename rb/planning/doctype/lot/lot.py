# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Lot(Document):
	def validate(self):
		# If Lot ID exists and no geometry yet, try to fetch quietly
		try:
			if getattr(self, "lot_id", None) and not getattr(self, "location", None):
				from rb.gis_integration.api import fetch_lot_geometry
				fetch_lot_geometry(self.name)
		except Exception as e:
			frappe.msgprint(f"Could not fetch geometry automatically: {e}", indicator="orange")

def on_update(doc, method=None):
    from rb.planning.doctype.plan.plan import update_total_area, update_total_lots
    if doc.plan:
        update_total_area(doc.plan)
        update_total_lots(doc.plan)

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
    from rb.planning.doctype.plan.plan import update_total_area, update_total_lots
    if doc.plan:
        update_total_area(doc.plan)
        update_total_lots(doc.plan)
