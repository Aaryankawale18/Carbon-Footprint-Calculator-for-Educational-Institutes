"""Institutional Historical Emission Data and Audited Records Repository.

Provides a persistent archive of all verified monthly carbon accounting records.
Includes record filtering, CSV export, record deletion, and the standardized
full results view for any selected period.
"""

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Data Records | Carbon Footprint Calculator",
    page_icon="📁",
    layout="wide",
)

from modules.charts import format_month_label
from modules.database import (
    delete_month,
    export_dataframe,
    get_institute,
    get_monthly_records,
    get_record,
    list_institutes,
)
from modules.results import render_full_results
from modules.ui import (
    inject_custom_css,
    institute_selector,
    render_institute_summary_card,
    render_metric_card,
    render_page_header,
    render_section_title,
)

inject_custom_css()

render_page_header(
    title="Institutional Emission Records Repository",
    subtitle="Audit-ready historical records, category trends, and verified data exports.",
    badge="Data Archive",
)

# Institute Selector
active_inst_id = institute_selector(label="Select Institute", key="data_page_inst_selector")

if not active_inst_id:
    st.stop()

institute = get_institute(active_inst_id)
if not institute:
    st.error("Selected institute could not be found.")
    st.stop()

# Institute Profile Summary
render_institute_summary_card(institute)

# Fetch monthly records
all_records_asc = get_monthly_records(active_inst_id, order_desc=False)

if not all_records_asc:
    st.info(f"No monthly carbon records have been saved for **{institute['name']}** yet.")
    if st.button("Open Calculator to Input Data", type="primary"):
        st.switch_page("pages/2_Calculator.py")
    st.stop()

# Summary row
total_records_count = len(all_records_asc)
first_month_label = format_month_label(all_records_asc[0]["month"])
last_month_label = format_month_label(all_records_asc[-1]["month"])
lifetime_co2 = sum(r["total_co2"] for r in all_records_asc)

render_section_title("Longitudinal Audit Summary")
sum_col1, sum_col2, sum_col3 = st.columns(3)

with sum_col1:
    render_metric_card(
        label="Audited Periods",
        value=f"{total_records_count} Month{'s' if total_records_count != 1 else ''}",
        subvalue=f"From {first_month_label} to {last_month_label}",
    )
with sum_col2:
    render_metric_card(
        label="Cumulative Footprint",
        value=f"{lifetime_co2:,.1f} kg CO2",
        subvalue=f"{(lifetime_co2 / 1000.0):,.2f} Metric Tonnes CO2e",
    )
with sum_col3:
    avg_monthly = lifetime_co2 / total_records_count if total_records_count > 0 else 0
    render_metric_card(
        label="Average Monthly Footprint",
        value=f"{avg_monthly:,.1f} kg CO2",
        subvalue="Mean institutional baseline",
    )

# Filterable Monthly Records Table
render_section_title("Monthly Records")

# Extract distinct years for filtering
years_available = sorted(list({r["month"].split("-")[0] for r in all_records_asc}), reverse=True)
filter_col1, filter_col2 = st.columns([1, 2])

with filter_col1:
    filter_year = st.selectbox(
        "Filter by Year",
        options=["All Recorded Years"] + years_available,
        key="data_filter_year",
    )

filtered_records_desc = sorted(
    [r for r in all_records_asc if filter_year == "All Recorded Years" or r["month"].startswith(filter_year)],
    key=lambda r: r["month"],
    reverse=True,
)

# Build tabular representation
table_rows = []
for r in filtered_records_desc:
    table_rows.append(
        {
            "Month": format_month_label(r["month"]),
            "Electricity (kWh)": f"{r.get('electricity_kwh', 0):,.0f}",
            "Elec CO2 (kg)": f"{r.get('electricity_co2', 0):,.1f}",
            "Diesel (L)": f"{r.get('diesel_litres', 0):,.0f}",
            "Diesel CO2 (kg)": f"{r.get('diesel_co2', 0):,.1f}",
            "Water (kL)": f"{r.get('water_kl', 0):,.0f}",
            "Water CO2 (kg)": f"{r.get('water_co2', 0):,.1f}",
            "Transport CO2 (kg)": f"{r.get('transport_co2', 0):,.1f}",
            "Total CO2 (kg)": f"{r.get('total_co2', 0):,.1f}",
        }
    )

st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

# Export & Deletion Action Bar
act_col1, act_col2 = st.columns([1.5, 1.5])

with act_col1:
    export_df = export_dataframe(active_inst_id)
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Full Records as CSV",
        data=csv_bytes,
        file_name=f"{institute['name'].replace(' ', '_').lower()}_carbon_records.csv",
        mime="text/csv",
        use_container_width=True,
    )

with act_col2:
    months_for_del = [r["month"] for r in filtered_records_desc]
    with st.popover("Delete a Specific Monthly Record", use_container_width=True):
        st.warning("Permanent Record Deletion")
        del_target = st.selectbox(
            "Select Month to Delete",
            options=months_for_del,
            format_func=format_month_label,
            key="del_target_select",
        )
        if st.button("Confirm Record Deletion", type="primary", use_container_width=True):
            delete_month(active_inst_id, del_target)
            st.success(f"Record for {format_month_label(del_target)} deleted.")
            st.rerun()

# Selected Month Detailed Audit View
render_section_title("Detailed Monthly Audit View")

# Selectbox populated from saved months (latest month default)
all_months_desc = [r["month"] for r in sorted(all_records_asc, key=lambda x: x["month"], reverse=True)]
selected_view_month = st.selectbox(
    "Select Target Accounting Period for Detailed Analysis",
    options=all_months_desc,
    format_func=format_month_label,
    index=0,
    key="data_detail_month_selector",
)

selected_detailed_record = get_record(active_inst_id, selected_view_month)

if selected_detailed_record:
    # Call the exact shared results renderer
    render_full_results(
        record=selected_detailed_record,
        all_records=all_records_asc,
        institute=institute,
    )
