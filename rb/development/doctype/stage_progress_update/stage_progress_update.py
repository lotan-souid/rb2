from frappe.model.document import Document
import frappe


class StageProgressUpdate(Document):
    def validate(self):
        if self.progress_percent is not None:
            if self.progress_percent < 0 or self.progress_percent > 100:
                frappe.throw("Progress Percent must be between 0 and 100")
        # Optionally, roll progress up to stage (latest wins)
        if self.development_stage:
            stage = frappe.get_doc("Development Stage", self.development_stage)
            # choose latest by date
            latest = frappe.get_all(
                "Stage Progress Update",
                filters={"development_stage": self.development_stage},
                fields=["name", "update_date", "progress_percent"],
                order_by="update_date desc",
                limit=1,
            )
            if latest:
                stage.progress_percent = latest[0].get("progress_percent") or 0
            stage.save(ignore_permissions=True)

