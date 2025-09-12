# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Cluster(Document):
	def validate(self):
		# If Cluster ID exists and no geometry yet, try to fetch quietly
		try:
			if getattr(self, "cluster_name", None) and not getattr(self, "location", None):
				from rb.gis_integration.api import fetch_cluster_geometry
				fetch_cluster_geometry(self.name)
		except Exception as e:
			frappe.msgprint(f"Could not fetch geometry automatically: {e}", indicator="orange")

	def on_update(self):
		# GIS sync: if Cluster Name changed, enqueue geometry fetch
		try:
			if hasattr(self, "cluster_name") and self.has_value_changed("cluster_name") and self.cluster_name:
				frappe.enqueue(
					"rb.gis_integration.api.fetch_cluster_geometry",
					cluster_name=self.name,
					queue="short",
					timeout=30,
				)
		except Exception as e:
			frappe.log_error(f"GIS enqueue error for Cluster {self.name}: {e}", "GIS Cluster on_update")
