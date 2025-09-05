# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class FixtureShares(Document):
    def validate(self):
        # Calculate shared_amount based on parent compensation_amount and share_percentage if parent present
        pct = flt(self.share_percentage or 0)
        # Parent will be Fixture Compensation when used as child table
        try:
            parent_comp = flt(getattr(self, "compensation_amount", 0))
        except Exception:
            parent_comp = 0.0
        # If the framework doesn't inject parent's field on child, just leave shared_amount as-is; it will be
        # set by parent DocType validate where compensation_amount is available.
        if parent_comp:
            self.shared_amount = parent_comp * (pct / 100.0)

