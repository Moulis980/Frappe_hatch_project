import frappe


def after_install():
    create_default_resources()
    create_default_settings()

    frappe.db.commit()

    frappe.msgprint("Hatch app installed successfully with default data.")


def create_default_resources():
    resources = [
        {
            "resource_name": "Room A",
            "resource_type": "Meeting Room",
            "capacity": 6,
        },
        {
            "resource_name": "Room B",
            "resource_type": "Meeting Room",
            "capacity": 3,
        },
        {
            "resource_name": "Hot Desk Zone",
            "resource_type": "Hot Desk Zone",
            "capacity": 12,
        },
    ]

    for data in resources:
        if not frappe.db.exists("Resource", data["resource_name"]):
            doc = frappe.get_doc({
                "doctype": "Resource",
                **data,
                "is_active": 1,
            })
            doc.insert(ignore_permissions=True)


def create_default_settings():
    if not frappe.db.exists(
        "Hatch Settings",
        "Hatch Settings"
    ):
        frappe.get_doc({
            "doctype": "Hatch Settings",
            "manager_email": "manager@example.com",
            "pending_confirmation_expiry_hours": 2,
            "cancellation_window_hours": 4,
            "waitlist_enabled": 1,
        }).insert(ignore_permissions=True)