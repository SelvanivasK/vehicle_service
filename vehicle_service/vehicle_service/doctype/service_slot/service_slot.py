# Copyright (c) 2026, nivas and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ServiceSlot(Document):
	def validate(self):
		self.slot_title = f" {self.service_date} "
