import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime


class Booking(Document):
    
    def before_print(self,settings=None):
        self.print_summary = f"{self.member} - {self.resource} on {self.booking_date}"

    def validate(self):
        self.validate_time()
        self.calculate_amounts()
        self.validate_capacity()


    def validate_time(self):
        start_time = get_datetime(
            f"{self.booking_date} {self.start_time}"
        )
        end_time = get_datetime(
            f"{self.booking_date} {self.end_time}"
        )

        if end_time <= start_time:
            frappe.throw("End Time must be greater than Start Time")


    def calculate_amounts(self):
        start_time = get_datetime(
            f"{self.booking_date} {self.start_time}"
        )
        end_time = get_datetime(
            f"{self.booking_date} {self.end_time}"
        )

        duration_hours = (
            end_time - start_time
        ).total_seconds() / 3600

        hourly_rate = frappe.db.get_value(
            "Resource",
            self.resource,
            "hourly_rate"
        )

        if hourly_rate is None:
            frappe.throw("Hourly rate not found for selected Resource")

        self.base_amount = flt(hourly_rate) * duration_hours

        addons_total = 0

        for row in self.addons or []:
            row.amount = flt(row.rate) * flt(row.quantity)
            addons_total += row.amount

        self.addons_total = addons_total
        self.total_amount = self.base_amount + self.addons_total


    def validate_capacity(self):
        resource = frappe.db.get_value(
            "Resource",
            self.resource,
            ["capacity", "resource_name"],
            as_dict=True
        )

        if not resource:
            frappe.throw("Selected Resource does not exist")

        existing_headcount = frappe.db.sql(
            """
            SELECT COALESCE(SUM(headcount), 0)
            FROM `tabBooking`
            WHERE name != %(name)s
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
                "name": self.name,
                "resource": self.resource,
                "booking_date": self.booking_date,
                "start_time": self.start_time,
                "end_time": self.end_time,
            }
        )[0][0]

        existing_headcount = flt(existing_headcount)
        requested_headcount = flt(self.headcount)

        free_capacity = flt(resource.capacity) - existing_headcount

        if existing_headcount + requested_headcount > flt(resource.capacity):
            frappe.throw(
                f"Only {free_capacity:g} seat(s) are available in "
                f"{resource.resource_name} for the selected time. "
                f"You requested {requested_headcount:g} seat(s)."
            )


    def before_submit(self):
        if self.status not in ["Pending Confirmation", "Confirmed"]:
            frappe.throw(
                "Only bookings with status 'Pending Confirmation' or 'Confirmed'"
                "can be submitted."
            )


    def on_submit(self):
        self.status = "Confirmed"

        frappe.enqueue(
            method=send_booking_confirmation,
            queue="default",
            enqueue_after_commit=True,
            booking_name=self.name
        )
        
        frappe.enqueue(
            method="hatch.api.send_webhook",
            queue="short",
            enqueue_after_commit=True,
            booking_name=self.name
        )
        
    def on_cancel(self):
        self.status = "Cancelled"


    def on_trash(self):
        if self.status not in ("Cancelled", "Draft"):
            frappe.throw(
                "Only Draft or Cancelled Bookings can be deleted."
            )


def send_booking_confirmation(booking_name):
    
    booking = frappe.get_doc("Booking", booking_name)
    
    email = frappe.db.get_value("Member",booking.member,"email")
    
    if not email:
        frappe.throw(f"Member {booking.member} does not have an email address.")

    frappe.sendmail(
        recipients=[email],
        subject=f"Booking Confirmation - {booking.name}",
        message=f"Your booking {booking.name} has been confirmed."
    )