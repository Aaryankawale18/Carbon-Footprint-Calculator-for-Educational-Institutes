"""Standardized results visualization and reporting components.

Shared across Calculator and Data pages to guarantee consistent
presentation of emission metrics, Plotly charts, transport details,
per-capita benchmarks, and actionable insights.
"""

from typing import Any
import pandas as pd
import streamlit as st

from modules.charts import (
    create_breakdown_donut,
    create_category_bar,
    create_monthly_trend_chart,
    create_stacked_monthly_bar,
    format_month_label,
)
from modules.ui import render_metric_card, render_section_title


def render_overview(record: dict[str, Any], previous_record: dict[str, Any] | None = None) -> None:
    """Render 5 primary emission metrics with delta comparison against the previous recorded month."""
    render_section_title("Emissions Overview")

    cols = st.columns(5)

    def calc_delta(curr: float, prev: float | None) -> tuple[float | None, str | None]:
        if prev is None or prev == 0:
            return None, None
        diff = curr - prev
        pct = (diff / prev) * 100
        return diff, f"{abs(pct):.1f}% vs prev month ({'+' if diff > 0 else ''}{diff:,.1f} kg)"

    # Electricity
    e_curr = float(record.get("electricity_co2", 0.0))
    e_prev = float(previous_record.get("electricity_co2", 0.0)) if previous_record else None
    d_val, d_txt = calc_delta(e_curr, e_prev)
    with cols[0]:
        render_metric_card(
            label="Electricity",
            value=f"{e_curr:,.1f} kg",
            subvalue=f"{record.get('electricity_kwh', 0.0):,.0f} kWh",
            delta=d_val,
            delta_text=d_txt,
        )

    # Diesel
    d_curr = float(record.get("diesel_co2", 0.0))
    d_prev = float(previous_record.get("diesel_co2", 0.0)) if previous_record else None
    d_val, d_txt = calc_delta(d_curr, d_prev)
    with cols[1]:
        render_metric_card(
            label="Diesel Generator",
            value=f"{d_curr:,.1f} kg",
            subvalue=f"{record.get('diesel_litres', 0.0):,.0f} Litres",
            delta=d_val,
            delta_text=d_txt,
        )

    # Water
    w_curr = float(record.get("water_co2", 0.0))
    w_prev = float(previous_record.get("water_co2", 0.0)) if previous_record else None
    d_val, d_txt = calc_delta(w_curr, w_prev)
    with cols[2]:
        render_metric_card(
            label="Water Supply",
            value=f"{w_curr:,.1f} kg",
            subvalue=f"{record.get('water_kl', 0.0):,.0f} kL",
            delta=d_val,
            delta_text=d_txt,
        )

    # Transportation
    t_curr = float(record.get("transport_co2", 0.0))
    t_prev = float(previous_record.get("transport_co2", 0.0)) if previous_record else None
    d_val, d_txt = calc_delta(t_curr, t_prev)
    with cols[3]:
        render_metric_card(
            label="Transportation",
            value=f"{t_curr:,.1f} kg",
            subvalue="Campus Fleet & Commute",
            delta=d_val,
            delta_text=d_txt,
        )

    # Total CO2
    tot_curr = float(record.get("total_co2", 0.0))
    tot_prev = float(previous_record.get("total_co2", 0.0)) if previous_record else None
    d_val, d_txt = calc_delta(tot_curr, tot_prev)
    with cols[4]:
        render_metric_card(
            label="Total Emissions",
            value=f"{tot_curr:,.1f} kg",
            subvalue="Net Monthly Footprint",
            delta=d_val,
            delta_text=d_txt,
        )


def render_charts(record: dict[str, Any], all_records: list[dict[str, Any]]) -> None:
    """Render the breakdown donut, category comparison, monthly trend, and stacked bar charts."""
    render_section_title("Emissions Analysis and Breakdown")

    breakdown = {
        "Electricity": float(record.get("electricity_co2", 0.0)),
        "Diesel Generator": float(record.get("diesel_co2", 0.0)),
        "Water": float(record.get("water_co2", 0.0)),
        "Transportation": float(record.get("transport_co2", 0.0)),
    }

    col1, col2 = st.columns(2)
    with col1:
        fig_donut = create_breakdown_donut(breakdown)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        fig_bar = create_category_bar(breakdown)
        st.plotly_chart(fig_bar, use_container_width=True)

    if all_records and len(all_records) > 1:
        render_section_title("Historical Trends")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_trend = create_monthly_trend_chart(all_records)
            st.plotly_chart(fig_trend, use_container_width=True)
        with col_t2:
            fig_stacked = create_stacked_monthly_bar(all_records)
            st.plotly_chart(fig_stacked, use_container_width=True)


def render_transport_table(transport_rows: list[dict[str, Any]]) -> None:
    """Render tabular breakdown of transportation emissions by vehicle type."""
    render_section_title("Transportation Fleet Breakdown")

    if not transport_rows:
        st.info("No transportation rows recorded for this month.")
        return

    data = []
    total_co2 = 0.0
    total_vehicles = 0

    for r in transport_rows:
        v_type = r["vehicle_type"]
        v_count = int(r["vehicle_count"])
        v_dist = float(r["distance_km"])
        factor = float(r["factor"])
        co2 = float(r["co2_kg"])
        total_co2 += co2
        total_vehicles += v_count

        data.append(
            {
                "Vehicle Type": v_type,
                "No. of Vehicles": f"{v_count:,}",
                "Distance (km)": f"{v_dist:,.1f}",
                "Emission Factor (kg CO2/km)": f"{factor:.3f}",
                "Emissions (kg CO2)": f"{co2:,.2f}",
            }
        )

    # Append summary total row
    data.append(
        {
            "Vehicle Type": "Total",
            "No. of Vehicles": f"{total_vehicles:,}",
            "Distance (km)": "-",
            "Emission Factor (kg CO2/km)": "-",
            "Emissions (kg CO2)": f"{total_co2:,.2f}",
        }
    )

    df = pd.DataFrame(data)
    st.table(df)


def render_extra_metrics(record: dict[str, Any], institute: dict[str, Any]) -> None:
    """Render per-capita intensity, area intensity, and offset equivalency metrics."""
    render_section_title("Institutional Intensity & Offsets")

    total_co2 = float(record.get("total_co2", 0.0))
    students = int(institute.get("total_students") or 0)
    staff = int(institute.get("total_staff") or 0)
    total_population = students + staff
    campus_area = float(institute.get("campus_area_sqft") or 0.0)

    per_person = (total_co2 / total_population) if total_population > 0 else 0.0
    per_sqft = (total_co2 / campus_area) if campus_area > 0 else 0.0

    # Tree equivalent: ~21 kg CO2 absorbed per mature tree per year (~1.75 kg/month)
    # Standard methodology: annual absorption of 1 mature tree is ~21 kg CO2.
    # Therefore, monthly trees required to offset this month's emissions = total_co2 / (21 / 12) = total_co2 / 1.75
    trees_needed = (total_co2 / (21.0 / 12.0)) if total_co2 > 0 else 0.0

    cols = st.columns(3)
    with cols[0]:
        render_metric_card(
            label="Emissions per Person",
            value=f"{per_person:,.2f} kg CO2",
            subvalue=f"Across {total_population:,} students & staff",
        )

    with cols[1]:
        render_metric_card(
            label="Emissions per Sq. Ft",
            value=f"{per_sqft:.4f} kg CO2",
            subvalue=f"Across {campus_area:,.0f} sq. ft campus area",
        )

    with cols[2]:
        render_metric_card(
            label="Trees Required to Offset",
            value=f"{int(round(trees_needed)):,} trees",
            subvalue="Assumes ~21 kg CO2 absorbed per mature tree/year (~1.75 kg/month)",
        )


def render_insight(record: dict[str, Any], previous_record: dict[str, Any] | None = None) -> None:
    """Generate dynamic textual analysis highlighting top contributor, MoM trajectory, and actionable recommendations."""
    render_section_title("Key Sustainability Insight")

    breakdown = {
        "Electricity": float(record.get("electricity_co2", 0.0)),
        "Diesel Generator": float(record.get("diesel_co2", 0.0)),
        "Water Supply": float(record.get("water_co2", 0.0)),
        "Transportation": float(record.get("transport_co2", 0.0)),
    }

    total_co2 = sum(breakdown.values())
    if total_co2 <= 0:
        st.markdown(
            """
            <div class="insight-card">
                <b>Emissions Profile:</b> No emissions recorded for this calculation period.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Identify primary contributor
    top_category, top_val = max(breakdown.items(), key=lambda x: x[1])
    top_share = (top_val / total_co2) * 100

    # Sector specific reduction suggestion
    suggestions = {
        "Electricity": "Conduct energy audits, optimize HVAC thermostats to 24°C, replace legacy lighting with sensor-based LEDs, and evaluate rooftop solar PV installations under institutional net-metering schemes.",
        "Diesel Generator": "Reduce peak demand reliance by scheduling heavy machinery, perform regular DG servicing to maintain combustion efficiency, and install battery energy storage systems (BESS) for brief grid interruptions.",
        "Water Supply": "Implement campus-wide rainwater harvesting, repair fixture leaks, install low-flow aerators, and treat greywater for campus landscaping and irrigation.",
        "Transportation": "Consolidate bus routing schedules, incentivize carpooling and public transit among staff and students, and phase in electric campus shuttles or EV buses.",
    }
    actionable_tip = suggestions.get(top_category, "Implement automated continuous monitoring across utility meters.")

    # Month over month trend narrative
    mom_text = "This is the initial baseline record for this institute."
    if previous_record:
        prev_total = float(previous_record.get("total_co2", 0.0))
        diff = total_co2 - prev_total
        if prev_total > 0:
            pct = (diff / prev_total) * 100
            if diff > 0:
                mom_text = f"Emissions increased by <b>{pct:.1f}%</b> (+{diff:,.1f} kg CO2) compared to the previous recorded period ({format_month_label(previous_record['month'])})."
            elif diff < 0:
                mom_text = f"Emissions decreased by <b>{abs(pct):.1f}%</b> (-{abs(diff):,.1f} kg CO2) compared to the previous recorded period ({format_month_label(previous_record['month'])}), demonstrating positive progress."
            else:
                mom_text = f"Emissions remained stable compared to {format_month_label(previous_record['month'])}."

    st.markdown(
        f"""
        <div class="insight-card">
            <p style="margin: 0 0 0.5rem 0; font-size: 0.95rem;">
                <b>Primary Emission Contributor:</b> <b>{top_category}</b> accounts for <b>{top_share:.1f}%</b> ({top_val:,.1f} kg CO2) of the total monthly carbon footprint.
            </p>
            <p style="margin: 0 0 0.5rem 0; font-size: 0.92rem; color: #1B2A1F;">
                <b>Month-over-Month Assessment:</b> {mom_text}
            </p>
            <p style="margin: 0; font-size: 0.92rem; color: #2E7D32;">
                <b>Recommended Intervention:</b> {actionable_tip}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_full_results(
    record: dict[str, Any],
    all_records: list[dict[str, Any]],
    institute: dict[str, Any],
) -> None:
    """Orchestrate the complete, identical results section used across Calculator and Data pages.

    1. Header: <Institute name> - <Month label> (<Academic year>)
    2. Emissions Overview (5 metrics with deltas)
    3. Category-wise Breakdown donut and Comparison bar chart
    4. Monthly Trend line & Stacked bar chart (if multiple months exist)
    5. Transport Breakdown table
    6. Additional metrics (per person, per sq. ft, trees equivalent)
    7. Key Insight box
    """
    month_label = format_month_label(record["month"])
    acad_year = institute.get("academic_year", "")
    acad_suffix = f" ({acad_year})" if acad_year else ""

    st.markdown(
        f"""
        <div style="background-color: #F3F8F4; border: 1px solid #C8E6C9; border-radius: 10px; padding: 1rem 1.25rem; margin: 1.25rem 0 1rem 0;">
            <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #4B6351; font-weight: 600;">Monthly Carbon Audit Result</div>
            <h2 style="color: #2E7D32; margin: 0.2rem 0 0 0; font-size: 1.5rem; font-weight: 700;">
                {institute['name']} — {month_label}{acad_suffix}
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Find previous record from all_records (chronological order)
    sorted_all = sorted(all_records, key=lambda r: r["month"])
    prev_record = None
    for idx, r in enumerate(sorted_all):
        if r["month"] == record["month"]:
            if idx > 0:
                prev_record = sorted_all[idx - 1]
            break

    # 1. Overview metrics
    render_overview(record, prev_record)

    # 2. Charts
    render_charts(record, sorted_all)

    # 3. Transport Table
    render_transport_table(record.get("transport_rows", []))

    # 4. Extra Metrics (per capita, per area, tree offset)
    render_extra_metrics(record, institute)

    # 5. Key Insight
    render_insight(record, prev_record)
