# Copyright (c) 2026, nivas and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class ServiceBooking(Document):
		

	def before_submit(self):
		self.validate_required_fields()
		self.validate_customer_vehicle()
		self.validate_service_date()
		self.validate_service_slot()
		self.validate_duplicate_booking()
		self.calculate_pricing()
		self.status = "Confirmed"

	def on_submit(self):
		slot = frappe.get_doc("Service Slot",self.service_slot)
		slot.booked_vehicles = (slot.booked_vehicles or 0) + 1
		if slot.booked_vehicles >= slot.maximum_vehicles:
			slot.status = "Full"
		else:
			slot.status = "Available"	
		slot.save()

	def before_cancel(self):
		self.status = "Cancelled"
   

	def on_cancel(self):
		self.update_slot_on_cancel()

	def validate_required_fields(self):
		if not self.customer:
			frappe.throw("Customer is required")
		if not self.vehicle:
			frappe.throw("Vehicle is required")
		if not self.service_date:
			frappe.throw("Service Date is required")
		if not self.service_slot:
			frappe.throw("Service Slot is required")
		if not self.service_type:
			frappe.throw("Service Type is required")

	def validate_customer_vehicle(self):
		vehicle_customer = frappe.db.get_value(
			"Vehicle",
			self.vehicle,
			"customer"
		)

		if vehicle_customer != self.customer:
			frappe.throw("Selected Vehicle does not belong to this Customer")

	def validate_service_date(self):
		if getdate(self.service_date) < getdate():
			frappe.throw("Service Date cannot be in the past")

	def validate_service_slot(self):
		slot = frappe.db.get_value(
			"Service Slot",
			self.service_slot,
			["service_date", "status", "booked_vehicles", "maximum_vehicles"],
			as_dict=True
		)

		if not slot:
			frappe.throw("Service Slot does not exist")
		if getdate(slot.service_date) != getdate(self.service_date):
			frappe.throw("Service Slot date must match Service Date")
		if slot.status in ["Full", "Closed"]:
			frappe.throw("Selected Service Slot is not available")
		if (slot.booked_vehicles or 0) >= (slot.maximum_vehicles or 0):
			frappe.throw("Service Slot is full")

	def validate_duplicate_booking(self):
		duplicate = frappe.db.exists(
			"Service Booking",
			{
				"vehicle": self.vehicle,
				"service_date": self.service_date,
				"service_slot": self.service_slot,
				"status": ["!=", "Cancelled"],
				"name": ["!=", self.name]
			}
		)

		if duplicate:
			frappe.throw("Duplicate booking is not allowed")

	def calculate_pricing(self):
		service_prices = {
			"General Service": 1500,
			"Full Service": 3000,
			"Repair Service": 2500
		}

		base_amount = service_prices.get(self.service_type)
		self.base_amount = base_amount

		addon_prices = {
			"Engine Oil Change": 800,
			"Car Wash": 500,
			"Interior Cleaning": 1000,
			"Wheel Alignment": 700
		}

		addon_total = 0

		for row in self.add_ons:
			rate = addon_prices.get(row.add_on)
			if rate is None:
				frappe.throw("Invalid Add-on: " + str(row.add_on))
			if not row.quantity or row.quantity <= 0:
				frappe.throw("Add-on quantity must be greater than zero")

			row.rate = rate
			row.amount = row.quantity * rate
			addon_total += row.amount

		customer_type = frappe.db.get_value("Customer",self.customer,"customer_type")

		self.discount_amount = 0
		if customer_type == "Corporate":
			self.discount_amount = self.base_amount * 0.15
		self.total_amount = self.base_amount+ addon_total - self.discount_amount
  
	def update_slot_on_cancel(self):
		slot = frappe.get_doc("Service Slot",self.service_slot)
		if (slot.booked_vehicles or 0) > 0:
			slot.booked_vehicles -= 1
		if slot.status != "Closed":
			slot.status = "Available"
		slot.save()
        