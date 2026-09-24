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
    
@frappe.whitelist()
def unsafe_get_bookings():
    return frappe.get_all(
        "Booking",
        fields=["*"]
    )


@frappe.whitelist()
def safe_get_bookings():
    bookings = frappe.get_list(
        "Booking",
        fields=[
            "name",
            "member",
            "start_time",
            "end_time",
            "status"
        ]
    )

    is_staff = (
        frappe.get_roles("Front Desk Staff")
        or frappe.get_roles("Space Manager")
        or frappe.session.user == "Administrator"
    )

    if is_staff:
        for booking in bookings:
            contact = frappe.db.get_value(
                "Member",
                booking.member,
                ["email", "phone"],
                as_dict=True  
            )

            booking["member_email"] = contact.email if contact else None
            booking["member_phone"] = contact.phone if contact else None

    return bookings

from frappe.utils import flt, get_datetime


@frappe.whitelist()
def get_live_availability(
    resource,
    booking_date,
    start_time,
    end_time,
    booking_name=None
):
    start = get_datetime(f"{booking_date} {start_time}")
    end = get_datetime(f"{booking_date} {end_time}")

    if end <= start:
        frappe.throw("End Time must be greater than Start Time")

    capacity = frappe.db.get_value(
        "Resource",
        resource,
        "capacity"
    )

    if capacity is None:
        frappe.throw("Resource not found")

    existing_headcount = frappe.db.sql(
        """
        SELECT COALESCE(SUM(headcount), 0)
        FROM `tabBooking`
        WHERE name != %(booking_name)s
          AND resource = %(resource)s
          AND booking_date = %(booking_date)s
          AND status IN (
              'Pending Confirmation',
              'Confirmed',
              'Checked-In'
          )
          AND start_time < %(end_time)s
          AND end_time > %(start_time)s
        """,
        {
            "booking_name": booking_name or "",
            "resource": resource,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time
        }
    )[0][0]

    existing_headcount = flt(existing_headcount)
    free_seats = flt(capacity) - existing_headcount

    return {
        "capacity": flt(capacity),
        "occupied_seats": existing_headcount,
        "free_seats": max(free_seats, 0)
    }
    
@frappe.whitelist()
def cancel_booking(booking_name, cancellation_reason):
    booking = frappe.get_doc("Booking", booking_name)
    
    if booking.status == "Cancelled":
        frappe.throw("Booking is already cancelled")
        
    booking.cancel()
    
    return  {
        "status": "Success",
        "message": f"Booking {booking_name} has been cancelled for reason {cancellation_reason}"
    }
    
@frappe.whitelist()
def reassign_booking(booking_name, new_member):
    booking = frappe.get_doc("Booking", booking_name)
    
    booking.member = new_member
    booking.save()
    
    return {
        "status": "Success",
        "message": f"Booking has been reassigned to new member {new_member}"
    }