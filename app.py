"""Carbon Footprint Calculator for Educational Institutes.

Main entry point and overview landing page for institutional sustainability monitoring.
"""

import streamlit as st

st.set_page_config(
    page_title="Carbon Footprint Calculator",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

from modules.charts import format_month_label
from modules.database import get_institute, get_monthly_records, list_institutes
from modules.ui import (
    inject_custom_css,
    institute_selector,
    render_metric_card,
    render_section_title,
)

# Apply global institutional styling
inject_custom_css()

# Sidebar navigation & active institute context
st.sidebar.markdown(
    """
    <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #E0EBE2; margin-bottom: 1rem;">
        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #4B6351; font-weight: 700;">Institutional Platform</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #2E7D32;">Sustainability Office</div>
    </div>
    """,
    unsafe_allow_html=True,
)

active_id = institute_selector(label="Select Active Institute", key="home_sidebar_selector", sidebar=True)

# Hero Banner
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">Carbon Footprint Calculator</div>
        <div class="hero-subtitle">Tracking sustainability for educational institutes</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main 2-column layout
col_left, col_right = st.columns([1.6, 1.2], gap="large")

with col_left:
    render_section_title("Campus Carbon Accounting Platform")
    st.markdown(
        """
        The **Carbon Footprint Calculator** provides academic administrators, campus planners,
        and sustainability committees with a standardized, audit-ready framework to measure, monitor,
        and decarbonize campus operations.

        Greenhouse gas emissions are quantified using authoritative national and international emission factors:
        - **Electricity Consumption:** Grid power emissions measured using Central Electricity Authority (CEA 2023) grid baseline factors.
        - **Diesel Generators:** Backup power combustion measured using Intergovernmental Panel on Climate Change (IPCC) emission indices.
        - **Water Supply & Treatment:** Pumping and effluent treatment footprint quantified according to Central Pollution Control Board (CPCB) standards.
        - **Transportation Fleet:** Campus commuter and institutional fleet emissions segmented by vehicle class (two-wheelers, petrol cars, diesel cars, and institutional buses).

        All calculation equations strictly adhere to the international activity-data standard:
        $$\\text{Total Emission (kg } \\text{CO}_2\\text{)} = \\sum (\\text{Activity Units} \\times \\text{Emission Factor})$$
        """
    )

with col_right:
    render_section_title("Operational Scope")

    subcol1, subcol2 = st.columns(2)
    with subcol1:
        render_metric_card(
            label="Emission Scopes",
            value="4 Categories",
            subvalue="Grid, DG, Water, Fleet",
        )
    with subcol2:
        render_metric_card(
            label="Audit Cadence",
            value="Monthly",
            subvalue="Continuous tracking",
        )

    # Active institute telemetry if available
    if active_id:
        active_inst = get_institute(active_id)
        if active_inst:
            records = get_monthly_records(active_id, order_desc=True)
            num_months = len(records)
            latest_month_str = format_month_label(records[0]["month"]) if records else "No data yet"
            latest_co2 = f"{records[0]['total_co2']:,.1f} kg" if records else "0.0 kg"

            st.markdown(
                f"""
                <div class="inst-card" style="background-color: #F8FAF8; border-color: #C8E6C9; margin-top: 0.5rem;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; color: #4B6351; font-weight: 700;">Active Campus Status</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #1B2A1F; margin: 0.2rem 0;">{active_inst['name']}</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.75rem;">
                        <div>
                            <span style="font-size: 0.75rem; color: #4B6351;">Records Stored</span>
                            <div style="font-weight: 600; color: #2E7D32;">{num_months} month{'s' if num_months != 1 else ''}</div>
                        </div>
                        <div>
                            <span style="font-size: 0.75rem; color: #4B6351;">Latest Month</span>
                            <div style="font-weight: 600; color: #1B2A1F;">{latest_month_str}</div>
                        </div>
                        <div>
                            <span style="font-size: 0.75rem; color: #4B6351;">Latest Total CO2</span>
                            <div style="font-weight: 600; color: #1B2A1F;">{latest_co2}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# How It Works Workflow Section
render_section_title("System Workflow")

w_col1, w_col2, w_col3, w_col4 = st.columns(4)

with w_col1:
    st.markdown(
        """
        <div class="inst-card" style="height: 100%;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #2E7D32; text-transform: uppercase; margin-bottom: 0.4rem;">Step 1</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.05rem; color: #1B2A1F;">Institute Profile</h4>
            <p style="font-size: 0.85rem; color: #4B6351; line-height: 1.4; margin: 0;">
                Register institutional parameters including student enrollment, faculty count, academic year, and campus area in square feet.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w_col2:
    st.markdown(
        """
        <div class="inst-card" style="height: 100%;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #2E7D32; text-transform: uppercase; margin-bottom: 0.4rem;">Step 2</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.05rem; color: #1B2A1F;">Calculator</h4>
            <p style="font-size: 0.85rem; color: #4B6351; line-height: 1.4; margin: 0;">
                Input monthly utility receipts for electricity, diesel, water, and fleet transit. Computes and visualizes emissions instantly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w_col3:
    st.markdown(
        """
        <div class="inst-card" style="height: 100%;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #2E7D32; text-transform: uppercase; margin-bottom: 0.4rem;">Step 3</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.05rem; color: #1B2A1F;">Data Records</h4>
            <p style="font-size: 0.85rem; color: #4B6351; line-height: 1.4; margin: 0;">
                Explore longitudinal historical audit data, review past months, analyze multi-month trends, and export verified records to CSV.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w_col4:
    st.markdown(
        """
        <div class="inst-card" style="height: 100%;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #2E7D32; text-transform: uppercase; margin-bottom: 0.4rem;">Step 4</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.05rem; color: #1B2A1F;">Advisor</h4>
            <p style="font-size: 0.85rem; color: #4B6351; line-height: 1.4; margin: 0;">
                Consult the AI sustainability advisor for data-grounded insights, reduction interventions, and solar/efficiency recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Quick navigation action row
st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    if st.button("Manage Institutes", use_container_width=True):
        st.switch_page("pages/1_Institute_Details.py")
with nav_col2:
    if st.button("Open Calculator", use_container_width=True):
        st.switch_page("pages/2_Calculator.py")
with nav_col3:
    if st.button("View Stored Data", use_container_width=True):
        st.switch_page("pages/3_Data.py")
with nav_col4:
    if st.button("Sustainability Advisor", use_container_width=True):
        st.switch_page("pages/4_Chatbot.py")
