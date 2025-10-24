# Copyright (c) 2024, RB and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class EnforcementOrder(Document):
    """Arrangement enforcement order mapped to GIS Enforcement Order layer."""

    def validate(self):
        if not self.order_id:
            frappe.throw(_("Order ID is required"))
