# Copyright (c) 2025, rb
from frappe.model.document import Document
import frappe


class DevelopmentCommitteeReview(Document):
    def validate(self):
        # If approved, ensure approved_allocatable_cost is set
        if self.committee_status == "Approved" and not self.approved_allocatable_cost:
            frappe.throw("Approved Allocatable Cost is required when status is Approved")

    def after_save(self):
        # Update linked Development Project status hints if needed
        if self.development_project:
            try:
                project = frappe.get_doc("Development Project", self.development_project)
                # Reflect latest committee status on project (stored in a field we'll add)
                if hasattr(project, "committee_status"):
                    project.db_set("committee_status", self.committee_status)
                if self.committee_status == "Approved" and hasattr(project, "allocatable_total_cost") and self.approved_allocatable_cost:
                    project.db_set("allocatable_total_cost", self.approved_allocatable_cost)
            except Exception:
                pass

