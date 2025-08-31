# Copyright (c) 2025, lotan souid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Lot(Document):
	pass

def on_update(doc, method=None):
    from rb.planning.doctype.plan.plan import update_total_area, update_total_lots
    if doc.plan:
        update_total_area(doc.plan)
        update_total_lots(doc.plan)

def after_delete(doc, method=None):
    from rb.planning.doctype.plan.plan import update_total_area, update_total_lots
    if doc.plan:
        update_total_area(doc.plan)
        update_total_lots(doc.plan)

