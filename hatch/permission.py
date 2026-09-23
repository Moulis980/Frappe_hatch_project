import frappe


def booking_query(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)

    if (
        "Front Desk Staff" in roles
        or "Space Manager" in roles
        or user == "Administrator"
    ):
        return ""

    if "Hatch Member" in roles:
        return """
            EXISTS (
                SELECT 1
                FROM `tabMember` AS m
                WHERE m.name = `tabBooking`.member
                AND m.user = {user}
            )
        """.format(
            user=frappe.db.escape(user)
        )

    return "1 = 0"