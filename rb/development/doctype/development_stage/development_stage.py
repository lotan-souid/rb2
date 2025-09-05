from frappe.model.document import Document
import frappe


class DevelopmentStage(Document):
    def update_totals_from_items(self):
        if not self.development_project:
            return
        # Sum planned/actual from project child items linked to this stage
        project = frappe.get_doc("Development Project", self.development_project)
        planned = 0
        actual = 0
        total_items = 0
        completed_items = 0
        for row in (project.get("table_dtxh") or []):
            if getattr(row, "stage", None) == self.name:
                planned += (getattr(row, "planned_cost", 0) or 0)
                actual += (getattr(row, "actual_cost", 0) or 0)
                total_items += 1
                if getattr(row, "item_status", "") == "Completed":
                    completed_items += 1
        self.planned_cost = planned
        self.actual_cost = actual
        if total_items:
            # If no explicit progress updates, fall back to items completion ratio
            self.progress_percent = round(100.0 * completed_items / total_items, 2)
        # Auto stage status when all items complete
        if total_items and completed_items == total_items:
            self.stage_status = "Completed"

    def validate(self):
        # Derive totals before save
        self.update_totals_from_items()

