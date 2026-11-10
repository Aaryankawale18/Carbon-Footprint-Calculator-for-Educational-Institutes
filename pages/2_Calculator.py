"""Monthly Carbon Emissions Calculator page.

Allows institutional operators to record utility activity metrics (electricity,
diesel generators, water, and fleet transportation), calculate emissions
using standardized factors, and review instant visual dashboards.
"""

from datetime import datetime
import streamlit as st

st.set_page_config(
    page_title="Emissions Calculator | Carbon Footprint Calculator",
    page_icon="🧮",
    layout="wide",
)

from modules.database import (
    get_institute,
    get_monthly_records,
    get_record,
    list_institutes,
    save_monthly_record,
)
from modules.emission_factors import list_subcategories
from modules.results import render_full_results
from modules.ui import (
    inject_custom_css,
    institute_selector,
    render_institute_summary_card,
    render_page_header,
    render_section_title,
)

inject_custom_css()

render_page_header(
    title="Monthly Emissions Calculator",
    subtitle="Input activity data across utilities and transport to compute greenhouse gas emissions.",
    badge="Audit & Accounting",
)

# Institute Selection
active_inst_id = institute_selector(label="Select Institute for Calculation", key="calc_inst_selector")

if not active_inst_id:
    st.stop()

institute = get_institute(active_inst_id)
if not institute:
    st.error("Selected institute could not be found.")
    st.stop()

# Compact read-only institute summary card
render_institute_summary_card(institute)

# Month selector setup
available_vehicle_types = list_subcategories("Transportation")

# Reset calculator view if active institute changed
if "calc_last_institute_id" not in st.session_state or st.session_state["calc_last_institute_id"] != active_inst_id:
    st.session_state["calc_last_institute_id"] = active_inst_id
    st.session_state["calc_active_result"] = None
    st.session_state["calc_transport_rows"] = None

render_section_title("Accounting Period Selection")

col_m1, col_m2 = st.columns([1, 1])

current_year = datetime.now().year
current_month = datetime.now().month

with col_m1:
    year_options = list(range(current_year - 5, current_year + 3))
    # Default to current year if available
    def_year_idx = year_options.index(current_year) if current_year in year_options else len(year_options) - 1
    selected_year = st.selectbox("Select Year", options=year_options, index=def_year_idx, key="calc_sel_year")

with col_m2:
    months_dict = {
        "01": "January (01)",
        "02": "February (02)",
        "03": "March (03)",
        "04": "April (04)",
        "05": "May (05)",
        "06": "June (06)",
        "07": "July (07)",
        "08": "August (08)",
        "09": "September (09)",
        "10": "October (10)",
        "11": "November (11)",
        "12": "December (12)",
    }
    month_keys = list(months_dict.keys())
    def_month_idx = current_month - 1
    selected_month_code = st.selectbox(
        "Select Month",
        options=month_keys,
        format_func=lambda k: months_dict[k],
        index=def_month_idx,
        key="calc_sel_month",
    )

selected_period = f"{selected_year}-{selected_month_code}"

# Check if month record already exists
existing_record = get_record(active_inst_id, selected_period)

if existing_record:
    st.warning(
        f"A verified emission record already exists for **{institute['name']}** in **{selected_period}**. "
        "Submitting the form below will overwrite this month's existing figures."
    )

# Maintain transport fleet rows in session state
session_transport_key = f"transport_rows_{active_inst_id}_{selected_period}"

if session_transport_key not in st.session_state:
    if existing_record and existing_record.get("transport_rows"):
        st.session_state[session_transport_key] = [
            {
                "vehicle_type": r["vehicle_type"],
                "vehicle_count": r["vehicle_count"],
                "distance_km": r["distance_km"],
            }
            for r in existing_record["transport_rows"]
        ]
    else:
        # Initial standard default rows
        st.session_state[session_transport_key] = [
            {"vehicle_type": "Bus", "vehicle_count": 8, "distance_km": 1500.0},
            {"vehicle_type": "Car Petrol", "vehicle_count": 25, "distance_km": 400.0},
            {"vehicle_type": "Two-wheeler", "vehicle_count": 120, "distance_km": 250.0},
        ]

render_section_title("Activity Data Input")

with st.container():
    col_u1, col_u2, col_u3 = st.columns(3)

    default_elec = float(existing_record["electricity_kwh"]) if existing_record else 45000.0
    default_diesel = float(existing_record["diesel_litres"]) if existing_record else 1200.0
    default_water = float(existing_record["water_kl"]) if existing_record else 3200.0

    with col_u1:
        elec_input = st.number_input(
            "Electricity Consumed (kWh) *",
            min_value=0.0,
            max_value=10000000.0,
            value=default_elec,
            step=500.0,
            help="Total utility meter grid electricity consumption in kilowatt-hours (kWh).",
        )
        if elec_input > 1000000.0:
            st.caption("Notice: Value exceeds 1,000,000 kWh. Please verify against utility bills.")

    with col_u2:
        diesel_input = st.number_input(
            "Diesel Fuel for DG Sets (Litres) *",
            min_value=0.0,
            max_value=500000.0,
            value=default_diesel,
            step=100.0,
            help="Volume of diesel fuel consumed for campus backup power generators.",
        )
        if diesel_input > 25000.0:
            st.caption("Notice: High diesel consumption (>25,000 L). Verify logbook hours.")

    with col_u3:
        water_input = st.number_input(
            "Water Consumed (kL) *",
            min_value=0.0,
            max_value=1000000.0,
            value=default_water,
            step=100.0,
            help="Total municipal/groundwater supply volume in kilolitres (1 kL = 1,000 litres).",
        )
        if water_input > 50000.0:
            st.caption("Notice: High water volume (>50,000 kL). Verify flowmeter totals.")

# Transportation Section with Dynamic Rows
render_section_title("Transportation & Commute Fleet")

transport_list = st.session_state[session_transport_key]

# Display each vehicle row
rows_to_remove = []
for idx, row_item in enumerate(transport_list):
    col_v1, col_v2, col_v3, col_v4 = st.columns([1.5, 1.2, 1.2, 0.6])

    with col_v1:
        curr_vtype = row_item.get("vehicle_type", available_vehicle_types[0])
        v_idx = available_vehicle_types.index(curr_vtype) if curr_vtype in available_vehicle_types else 0
        new_vtype = st.selectbox(
            f"Vehicle Class #{idx+1}",
            options=available_vehicle_types,
            index=v_idx,
            key=f"v_type_{idx}_{session_transport_key}",
        )
        row_item["vehicle_type"] = new_vtype

    with col_v2:
        new_count = st.number_input(
            f"No. of Vehicles #{idx+1}",
            min_value=1,
            max_value=10000,
            value=int(row_item.get("vehicle_count", 1)),
            step=1,
            key=f"v_count_{idx}_{session_transport_key}",
        )
        row_item["vehicle_count"] = new_count

    with col_v3:
        new_dist = st.number_input(
            f"Distance / Vehicle (km) #{idx+1}",
            min_value=0.0,
            max_value=100000.0,
            value=float(row_item.get("distance_km", 100.0)),
            step=50.0,
            key=f"v_dist_{idx}_{session_transport_key}",
        )
        row_item["distance_km"] = new_dist

    with col_v4:
        st.write("")
        st.write("")
        if st.button("Remove", key=f"btn_remove_{idx}_{session_transport_key}", use_container_width=True):
            rows_to_remove.append(idx)

# Remove requested rows if any
if rows_to_remove:
    for idx in sorted(rows_to_remove, reverse=True):
        if len(transport_list) > 1:
            transport_list.pop(idx)
        else:
            st.warning("At least one vehicle category row must be maintained.")
    st.session_state[session_transport_key] = transport_list
    st.rerun()

# Button to Add Another Vehicle Type
if st.button("Add Another Vehicle Type", key=f"btn_add_v_{session_transport_key}"):
    # Pick a vehicle type not yet chosen if available
    used_types = {r["vehicle_type"] for r in transport_list}
    unused = [t for t in available_vehicle_types if t not in used_types]
    next_type = unused[0] if unused else available_vehicle_types[0]
    transport_list.append({"vehicle_type": next_type, "vehicle_count": 5, "distance_km": 300.0})
    st.session_state[session_transport_key] = transport_list
    st.rerun()

st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

# Calculation Submission
btn_calculate = st.button("Calculate and Save", type="primary", use_container_width=True)

if btn_calculate:
    # Merge duplicate vehicle types if any exist
    consolidated_transport: dict[str, dict] = {}
    for item in transport_list:
        v_t = item["vehicle_type"]
        cnt = item["vehicle_count"]
        dst = item["distance_km"]
        if v_t in consolidated_transport:
            # Weighted average distance or combined vehicle-km
            prev = consolidated_transport[v_t]
            total_km = (prev["vehicle_count"] * prev["distance_km"]) + (cnt * dst)
            new_cnt = prev["vehicle_count"] + cnt
            consolidated_transport[v_t] = {
                "vehicle_type": v_t,
                "vehicle_count": new_cnt,
                "distance_km": round(total_km / new_cnt, 2) if new_cnt > 0 else 0.0,
            }
        else:
            consolidated_transport[v_t] = {
                "vehicle_type": v_t,
                "vehicle_count": cnt,
                "distance_km": dst,
            }

    final_transport_list = list(consolidated_transport.values())

    try:
        # Save to SQLite database
        record_id = save_monthly_record(
            institute_id=active_inst_id,
            month=selected_period,
            electricity_kwh=float(elec_input),
            water_kl=float(water_input),
            diesel_litres=float(diesel_input),
            transport_rows_data=final_transport_list,
        )

        st.success(f"Emissions calculated and saved successfully for {institute['name']} ({selected_period}).")

        # Load fresh record and all records to display
        fresh_record = get_record(active_inst_id, selected_period)
        all_inst_records = get_monthly_records(active_inst_id, order_desc=False)

        st.session_state["calc_active_result"] = {
            "record": fresh_record,
            "all_records": all_inst_records,
            "institute": institute,
            "period": selected_period,
        }
    except Exception as ex:
        st.error(f"Error executing calculation: {ex}")

# Persistent rendering of calculation results below the button
active_result = st.session_state.get("calc_active_result")

if active_result and active_result.get("record"):
    # Ensure active result matches currently selected institute
    if active_result["institute"]["id"] == active_inst_id:
        render_full_results(
            record=active_result["record"],
            all_records=active_result["all_records"],
            institute=active_result["institute"],
        )
