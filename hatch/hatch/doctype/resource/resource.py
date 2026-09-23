# Copyright (c) 2026, Moulis and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Resource(Document):
    
    def on_update(self):
        doc = frappe.get_value("Hatch Settings",None,"pending_confirmation_expiry_hours")

        frappe.msgprint(
            f"Pending Confirmation Expiry Hours: {doc}"
        )