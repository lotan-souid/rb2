import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, nowdate


class Agreement(Document):
	def validate(self):
		self.ensure_unique_per_arrangement()
		self.populate_version_metadata()
		self.set_current_version()

	def before_save(self):
		self.unlink_previous_arrangement_when_changed()

	def on_update(self):
		self.link_to_arrangement_file()
		self.update_arrangement_status()

	def on_trash(self):
		self.unlink_from_arrangement_file()

	def ensure_unique_per_arrangement(self):
		"""
		Ensure only a single agreement exists per arrangement file.
		"""
		if not self.arrangement_file:
			return

		filters = {"arrangement_file": self.arrangement_file}
		if self.name:
			filters["name"] = ["!=", self.name]

		duplicate = frappe.db.exists("Agreement", filters)
		if duplicate:
			frappe.throw(
				_("Agreement {0} already exists for Arrangement File {1}.").format(
					duplicate, self.arrangement_file
				)
			)

	def populate_version_metadata(self):
		"""
		Ensure each version row has sequential numbering, creator and creation date.
		"""
		for idx, row in enumerate(self.versions or [], start=1):
			row.version_number = idx
			if not row.creation_date:
				row.creation_date = nowdate()
			if not row.created_by:
				row.created_by = frappe.session.user

	def set_current_version(self):
		"""
		Set the latest version label on the parent document for quick reference.
		"""
		if not self.versions:
			self.current_version = ""
			self.primary_document = ""
			self.legal_owner = ""
			return

		last_version = self.versions[-1]
		version_text = ""
		if last_version.version_number:
			version_text = _("Version {0}").format(last_version.version_number)
		if last_version.creation_date:
			if version_text:
				version_text = f"{version_text} ({formatdate(last_version.creation_date)})"
			else:
				version_text = formatdate(last_version.creation_date)

		self.current_version = version_text
		self.primary_document = last_version.document or ""
		self.legal_owner = last_version.created_by or ""

	def link_to_arrangement_file(self):
		if not self.arrangement_file:
			return

		frappe.db.set_value("Arrangement File", self.arrangement_file, "agreement", self.name)

	def unlink_from_arrangement_file(self):
		if not self.arrangement_file:
			return

		current_link = frappe.db.get_value("Arrangement File", self.arrangement_file, "agreement")
		if current_link == self.name:
			frappe.db.set_value("Arrangement File", self.arrangement_file, "agreement", "")

	def unlink_previous_arrangement_when_changed(self):
		if self.is_new():
			return

		previous_arrangement = self.get_db_value("arrangement_file")
		if previous_arrangement and previous_arrangement != self.arrangement_file:
			current_link = frappe.db.get_value("Arrangement File", previous_arrangement, "agreement")
			if current_link == self.name:
				frappe.db.set_value("Arrangement File", previous_arrangement, "agreement", "")

	def update_arrangement_status(self):
		"""
		Update Arrangement File status when the agreement reaches the signed stage.
		"""
		if not self.arrangement_file or self.agreement_stage != "חתום":
			return

		current_status = frappe.db.get_value("Arrangement File", self.arrangement_file, "arrangement_status")
		if current_status == "נחתם":
			return

		frappe.db.set_value("Arrangement File", self.arrangement_file, "arrangement_status", "נחתם")
		message = _("Arrangement File {0} status updated to Signed (נחתם) based on Agreement {1}.").format(
			self.arrangement_file, self.name
		)
		frappe.msgprint(message, indicator="green", alert=True)
