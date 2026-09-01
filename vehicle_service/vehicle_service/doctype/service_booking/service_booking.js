frappe.ui.form.on("Service Booking", {
	setup(frm) {
		frm.set_query("vehicle", function () {
			return {
				filters: {
					customer: frm.doc.customer,
				},
			};
		});
	},

	refresh(frm) {
		frm.set_df_property("status", "read_only", 1);
	},

	customer(frm) {
		frm.set_value("vehicle", "");

		if (!frm.doc.customer) {
			frm.set_value("discount_amount", 0);
			return;
		}
		calculate_discount(frm);

	},

	service_type(frm) {
		const prices = {
			"General Service": 1500,
			"Full Service": 3000,
			"Repair Service": 2500,
		};

		let price = prices[frm.doc.service_type] ;
		frm.set_value("base_amount", price);

		calculate_discount(frm);
	},

	base_amount(frm) {
		calculate_total(frm);
	},

	discount_amount(frm) {
		calculate_total(frm);
	},

	service_date(frm) {
		if (frm.doc.service_date && frm.doc.service_date < frappe.datetime.get_today()) {
			frappe.msgprint("Service Date cannot be in the past");
			frm.set_value("service_date", "");
			return;
		}

		frm.set_value("service_slot", "");
	},

	service_slot(frm) {
		if (!frm.doc.service_slot) {
			return;
		}
		frappe.db.get_value("Service Slot", frm.doc.service_slot, ["status", "service_date"])
			.then((response) => {
				let slot = response.message;

				if (slot.status === "Full" || slot.status === "Closed") {
					frappe.msgprint("Selected Service Slot is not available");
					frm.set_value("service_slot", "");
					return;
				}

				if (slot.service_date !== frm.doc.service_date) {
					frappe.msgprint("Service Slot date must match Service Date");
					frm.set_value("service_slot", "");
				}
			});
	},
});

frappe.ui.form.on("Service Add-on", {
	add_on(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		const prices = {
			"Engine Oil Change": 800,
			"Car Wash": 500,
			"Interior Cleaning": 1000,
			"Wheel Alignment": 700,
		};

		let rate = prices[row.add_on] ;
		let amount = row.quantity  * rate;

		frappe.model.set_value(cdt, cdn, "rate", rate).then(() => {
			frappe.model.set_value(cdt, cdn, "amount", amount).then(() => {
				calculate_total(frm);
			});
		});
	},

	quantity(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let amount = row.quantity * row.rate ;

		frappe.model.set_value(cdt, cdn, "amount", amount).then(() => {
			calculate_total(frm);
		});
	},

	rate(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let amount = (row.quantity || 0) * (row.rate || 0);

		frappe.model.set_value(cdt, cdn, "amount", amount).then(() => {
			calculate_total(frm);
		});
	},

	add_ons_remove(frm) {
		calculate_total(frm);
	},
});

function calculate_discount(frm) {
	if (!frm.doc.customer) {
		frm.set_value("discount_amount", 0);
		return;
	}

	frappe.db.get_value("Customer", frm.doc.customer, "customer_type").then((response) => {
		let discount = 0;

		if (response.message.customer_type === "Corporate") {
			discount = (frm.doc.base_amount || 0) * 0.15;
		}

		frm.set_value("discount_amount", discount);
	});
}

function calculate_total(frm) {
	let addon_total = 0;

	frm.doc.add_ons.forEach((row) => {
		addon_total += row.amount || 0;
	});

	let total = (frm.doc.base_amount || 0) + addon_total - (frm.doc.discount_amount || 0);

	frm.set_value("total_amount", total);
}
