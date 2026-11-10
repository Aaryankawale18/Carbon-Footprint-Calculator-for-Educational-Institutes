"""Institute profile management page.

Allows campus administrators to create, update, review, and delete educational
institute profiles, with automatic validation of academic year, enrollment,
and physical estate parameters.
"""

import re
import streamlit as st

st.set_page_config(
    page_title="Institute Details | Carbon Footprint Calculator",
    page_icon="🏛️",
    layout="wide",
)

from modules.database import (
    delete_institute,
    get_institute,
    list_institutes,
    save_institute,
)
from modules.ui import (
    inject_custom_css,
    render_institute_summary_card,
    render_page_header,
    render_section_title,
)

inject_custom_css()

render_page_header(
    title="Institute Profile & Estate Configuration",
    subtitle="Configure campus demographic and physical parameters for standardized carbon accounting.",
    badge="Configuration Module",
)

# Initialize editing state if not present
if "edit_institute_id" not in st.session_state:
    st.session_state["edit_institute_id"] = None


def validate_academic_year(ay_str: str) -> tuple[bool, str]:
    """Validate academic year format YYYY-YYYY and check consecutive years."""
    match = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", ay_str)
    if not match:
        return False, "Academic Year must follow the format 'YYYY-YYYY' (e.g., 2026-2027)."
    y1, y2 = int(match.group(1)), int(match.group(2))
    if y2 != y1 + 1:
        return False, f"Academic Year ending year ({y2}) must be exactly one year after start year ({y1})."
    return True, f"{y1}-{y2}"


# Load institute to edit if requested
editing_id = st.session_state.get("edit_institute_id")
institute_to_edit = get_institute(editing_id) if editing_id else None

# Current Active Institute Profile Banner
active_id = st.session_state.get("active_institute_id")
if active_id:
    active_inst = get_institute(active_id)
    if active_inst:
        render_section_title("Currently Selected Institute")
        render_institute_summary_card(active_inst)

# 2-column layout: Form on Left, List on Right
col_form, col_list = st.columns([1.1, 1], gap="large")

with col_form:
    form_title = "Edit Institute Profile" if institute_to_edit else "Register New Institute"
    render_section_title(form_title)

    default_name = institute_to_edit["name"] if institute_to_edit else ""
    default_address = institute_to_edit["address"] if institute_to_edit else ""
    default_ay = institute_to_edit["academic_year"] if institute_to_edit else "2026-2027"
    default_students = int(institute_to_edit["total_students"]) if institute_to_edit else 5000
    default_staff = int(institute_to_edit["total_staff"]) if institute_to_edit else 450
    default_area = float(institute_to_edit["campus_area_sqft"]) if institute_to_edit else 350000.0

    with st.form("institute_form", clear_on_submit=False):
        inst_name = st.text_input(
            "Institute Name *",
            value=default_name,
            placeholder="e.g. National Institute of Technology, Campus North",
            help="Official institutional name (unique).",
        )

        inst_address = st.text_area(
            "Campus Address",
            value=default_address,
            placeholder="Street address, city, state, postal code",
            help="Physical campus location.",
            height=85,
        )

        inst_ay = st.text_input(
            "Academic Year (YYYY-YYYY) *",
            value=default_ay,
            placeholder="2026-2027",
            help="Current academic tracking cycle (must be consecutive years).",
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            total_students = st.number_input(
                "Total Students",
                min_value=0,
                max_value=200000,
                value=default_students,
                step=100,
                help="Full-time enrolled student population.",
            )
        with col_s2:
            total_staff = st.number_input(
                "Total Staff (Faculty & Support)",
                min_value=0,
                max_value=25000,
                value=default_staff,
                step=10,
                help="Total academic, administrative, and facility employees.",
            )

        campus_area = st.number_input(
            "Total Built-up Campus Area (sq. ft) *",
            min_value=100.0,
            max_value=100000000.0,
            value=default_area,
            step=5000.0,
            format="%.0f",
            help="Gross indoor built-up footprint in square feet.",
        )

        submit_label = "Update Institute Profile" if institute_to_edit else "Save Institute"
        btn_submit = st.form_submit_button(submit_label, type="primary", use_container_width=True)

        if btn_submit:
            # Validate input fields
            errors = []
            if not inst_name.strip():
                errors.append("Institute Name is required.")

            ay_valid, ay_formatted_or_err = validate_academic_year(inst_ay)
            if not ay_valid:
                errors.append(ay_formatted_or_err)

            if campus_area <= 0:
                errors.append("Campus Area must be a positive value greater than zero.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                try:
                    target_id = institute_to_edit["id"] if institute_to_edit else None
                    saved_id = save_institute(
                        name=inst_name,
                        address=inst_address,
                        academic_year=ay_formatted_or_err,
                        total_students=int(total_students),
                        total_staff=int(total_staff),
                        campus_area_sqft=float(campus_area),
                        institute_id=target_id,
                    )
                    st.session_state["active_institute_id"] = saved_id
                    st.session_state["edit_institute_id"] = None
                    st.success(f"Institute profile for '{inst_name.strip()}' saved successfully.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error saving institute: {ex}")

    if institute_to_edit:
        if st.button("Cancel Editing (Switch to New Registration)", use_container_width=True):
            st.session_state["edit_institute_id"] = None
            st.rerun()

with col_list:
    render_section_title("Saved Institutes")

    institutes = list_institutes()
    if not institutes:
        st.info("No institutes registered yet. Use the form on the left to add your first campus profile.")
    else:
        st.write(f"Total Registered: **{len(institutes)}**")

        for inst in institutes:
            is_active = (inst["id"] == active_id)
            is_editing = (inst["id"] == editing_id)

            badge_text = "Active" if is_active else ""
            border_color = "#2E7D32" if is_active else "#E0EBE2"
            bg_color = "#F3F8F4" if is_active else "#FFFFFF"

            st.markdown(
                f"""
                <div class="inst-card" style="background-color: {bg_color}; border: 1.5px solid {border_color}; margin-bottom: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin: 0 0 0.25rem 0; color: #1B2A1F; font-size: 1.1rem;">{inst['name']}</h4>
                            <p style="margin: 0; font-size: 0.83rem; color: #4B6351;">AY: {inst['academic_year']} | {inst.get('address') or 'No address'}</p>
                            <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem; color: #4B6351;">
                                Enrollment: <b>{inst['total_students']:,}</b> | Staff: <b>{inst['total_staff']:,}</b> | Area: <b>{inst['campus_area_sqft']:,.0f} sq.ft</b>
                            </p>
                        </div>
                        <div>
                            {'<span class="inst-pill">Active</span>' if is_active else ''}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1.2])

            with btn_col1:
                if not is_active:
                    if st.button("Select Active", key=f"btn_activate_{inst['id']}", use_container_width=True):
                        st.session_state["active_institute_id"] = inst["id"]
                        st.rerun()
                else:
                    st.button("Active Selected", key=f"btn_active_label_{inst['id']}", disabled=True, use_container_width=True)

            with btn_col2:
                if st.button("Edit Profile", key=f"btn_edit_{inst['id']}", use_container_width=True):
                    st.session_state["edit_institute_id"] = inst["id"]
                    st.rerun()

            with btn_col3:
                # Deletion with safety confirmation
                with st.popover("Delete Institute", use_container_width=True):
                    st.warning(f"Delete **{inst['name']}**?")
                    st.caption("Warning: All historical monthly records and transport data for this institute will be permanently deleted.")
                    if st.button("Confirm Delete", key=f"btn_confirm_del_{inst['id']}", type="primary", use_container_width=True):
                        delete_institute(inst["id"])
                        if st.session_state.get("active_institute_id") == inst["id"]:
                            st.session_state["active_institute_id"] = None
                        if st.session_state.get("edit_institute_id") == inst["id"]:
                            st.session_state["edit_institute_id"] = None
                        st.success(f"Institute '{inst['name']}' deleted.")
                        st.rerun()
