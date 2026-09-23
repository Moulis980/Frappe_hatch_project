import frappe

def rename_member(old_name,new_name):
    return frappe.rename_doc(
        "Member",
        old_name,
        new_name,
        merge=False
    )