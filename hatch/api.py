import frappe


@frappe.whitelist()
def share_booking(booking_name, user_email):
    if not frappe.db.exists("Booking", booking_name):
        frappe.throw(f"Booking {booking_name} does not exist")

    if not frappe.db.exists("User", user_email):
        frappe.throw(f"User {user_email} does not exist")

    frappe.share.add(
        "Booking",
        str(booking_name),
        user_email,
        read=1,
        write=0,
        submit=0,
        share=0,
        everyone=0
    )

    return {
        "status": "success",
        "message": f"Booking {booking_name} shared with {user_email}",
    }