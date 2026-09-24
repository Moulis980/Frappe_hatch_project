# Copyright (c) 2026, Moulis and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	filters = filters or {}

	validate_dates(filters)
	bookings = get_bookings(filters)
	data = aggregate_bookings(bookings, filters)

	columns = get_columns()
	#data = get_data()

	chart = get_chart(data)
	report_summary = get_report_summary(data)

	return [columns, data, None, chart,report_summary]



def execute_snapshot_report(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for snapshot report. When 'Synced
	Report' is enabled in report, framework will call this method
	every time the report is refreshed or a filter is updated. It
	accepts the same filters as normal execute. But a utility method -
	get_latest_sync, is also imported.

	"""
	from frappe.database.duckdb.database import get_latest_sync

	columns = get_columns()
	data = get_data()

	#return columns, data

def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
        {
            "label": "Resource",
            "fieldname": "resource",
            "fieldtype": "Link",
            "options": "Resource",
            "width": 180
        },
        {
            "label": "Total Bookings",
            "fieldname": "total_bookings",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": "Total Hours Booked",
            "fieldname": "total_hours_booked",
            "fieldtype": "Float",
            "width": 150
        },
        {
            "label": "Utilization %",
            "fieldname": "utilization",
            "fieldtype": "Percent",
            "width": 130
        },
        {
            "label": "Revenue",
            "fieldname": "revenue",
            "fieldtype": "Currency",
            "width": 130
        }
    ]


def get_data() -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	return [
		["Row 1", 1],
		["Row 2", 2],
	]



def validate_dates(filters):
    if not filters.get("from_date"):
        frappe.throw(_("From Date is required"))
    if not filters.get("to_date"):
        frappe.throw(_("To Date is required"))
    if filters.get("from_date") > filters.get("to_date"):
        frappe.throw("From date can't greater than To date")
        
def get_bookings(filters):
    conditions = {
        "booking_date": [
            "between",
            [
                filters["from_date"],
                filters["to_date"]
            ]
        ]
    }
    if filters.get("resource"):
        conditions["resource"] = filters["resource"]
        
    return frappe.get_list(
        "Booking",
        filters=conditions,
        fields=[
            "name",
            "resource",
            "booking_date",
            "start_time",
            "end_time",
            "headcount",
            "status",
            "total_amount"
        ],
        order_by="booking_date asc, start_time asc",
        page_length=0
    )
    
def aggregate_bookings(bookings,filters):
    grouped = {}
    for booking in bookings:
        resource = booking.resource
        if not resource:
            continue
        if resource not in grouped:
            grouped[resource] ={
                "resource": resource,
                "total_bookings": 0,
                "total_hours_booked": 0,
                "revenue": 0
            }
        grouped[resource]["total_bookings"] += 1
        grouped[resource]["total_hours_booked"] += (calculate_hours(booking.start_time, booking.end_time))
        grouped[resource]["revenue"] += float(booking.total_amount or 0)
    
    period_days = (frappe.utils.getdate(filters["to_date"]) - frappe.utils.getdate(filters["from_date"])).days + 1
    result = []
    for row in grouped.values():
        
        available_hours = period_days * 8
        utilization = 0
        if available_hours:
            utilization = (row["total_hours_booked"] / available_hours) * 100
        result.append({
            "resource": row["resource"],
            "total_bookings": row["total_bookings"],
            "total_hours_booked": round(row["total_hours_booked"],2),
            "utilization": round(utilization,2),
            "revenue": round(row["revenue"],2)
        })
    
    result.sort(key=lambda x: x["total_bookings"], reverse=True)
    return result

def calculate_hours(start_time, end_time):
    if not start_time or not end_time:
        return 0
    return max((end_time.total_seconds() - start_time.total_seconds()) / 3600, 0)
    
def get_chart(data):
    return {
        "data":{"labels":[row["resource"] for row in data],
                "datasets":[{"name":"Bookings","values":[row["total_bookings"] for row in data]}]},
        "type":"bar","height":500}
    
def get_report_summary(data):
    total_bookings = sum(row["total_bookings"] for row in data)
    total_revenue = sum(row["revenue"] for row in data)
    busiest_resource = max(data, key=lambda x: x["total_bookings"])["resource"] if data else None
    
    return [
        {
            "value": total_bookings,
            "label": "Total Bookings",
            "indicator": "green"
        },
        {
            "value": total_revenue,
            "label": "Total Revenue",
            "indicator": "green",
            "datatype": "Currency"
        },
        {
            "value": busiest_resource,
            "label": "Busiest Resource",
            "indicator": "blue"
        }
    ]