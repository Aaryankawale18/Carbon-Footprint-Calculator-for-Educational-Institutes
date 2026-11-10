"""Institutional Sustainability Advisor with Multi-Provider Support.

Supports:
1. Google Gemini (via official google-genai SDK, e.g. gemini-2.5-flash)
2. Groq (via groq SDK, e.g. llama-3.3-70b-versatile)
3. Built-in Institutional Sustainability Analytics Engine:
   Automatically analyzes the active institute's verified records, factors,
   and estate metrics to answer inquiries dynamically when an API key is in
   project-ID format (e.g. 'gen-lang-client-...') or offline.
"""

from datetime import datetime
import os
import re
import time
from typing import Any, Generator
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from modules.charts import format_month_label
from modules.emission_factors import get_all_factors

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_api_keys() -> tuple[str | None, str | None]:
    """Retrieve Gemini and Groq API keys from environment or Streamlit secrets."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if hasattr(st, "secrets"):
        try:
            if not gemini_key and "GEMINI_API_KEY" in st.secrets:
                gemini_key = str(st.secrets["GEMINI_API_KEY"]).strip()
            if not groq_key and "GROQ_API_KEY" in st.secrets:
                groq_key = str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass

    gemini_key = gemini_key.strip() if gemini_key else None
    groq_key = groq_key.strip() if groq_key else None
    return gemini_key, groq_key


def detect_provider() -> tuple[str, str | None, str]:
    """Detect which provider and model to use based on available keys.

    Returns:
        tuple[str, str | None, str]: (provider_name, active_key, status_message)
    """
    gemini_key, groq_key = get_api_keys()

    # Check for valid Gemini key format (AIzaSy...)
    if gemini_key and gemini_key.startswith("AIzaSy"):
        return "gemini", gemini_key, f"Google Gemini ({GEMINI_MODEL})"

    if groq_key and groq_key.startswith("AIzaSy"):
        return "gemini", groq_key, f"Google Gemini ({GEMINI_MODEL})"

    # Check for valid Groq key format (gsk_...)
    if groq_key and groq_key.startswith("gsk_"):
        return "groq", groq_key, f"Groq Cloud ({GROQ_MODEL})"

    # Project ID format from Google AI Studio (gen-lang-client-...)
    current_key = gemini_key or groq_key
    if current_key and current_key.startswith("gen-lang-client-"):
        return (
            "analytics_engine",
            current_key,
            "Campus Analytics Engine (Active) — Project ID detected",
        )

    return "analytics_engine", None, "Campus Analytics Engine (Built-in)"


def build_system_prompt(
    institute: dict[str, Any],
    records: list[dict[str, Any]],
) -> str:
    """Construct dynamic, data-grounded system prompt for LLM advisors."""
    factors_df = get_all_factors()
    factors_summary = factors_df.to_string(index=False)

    sorted_recs = sorted(records, key=lambda r: r["month"])
    if sorted_recs:
        records_summary_lines = []
        for r in sorted_recs[-6:]:
            m_label = format_month_label(r["month"])
            line = (
                f"- Month: {m_label} ({r['month']}) | Total CO2: {r['total_co2']:,.2f} kg "
                f"[Electricity: {r['electricity_co2']:,.2f} kg ({r.get('electricity_kwh', 0):,.0f} kWh), "
                f"Diesel: {r['diesel_co2']:,.2f} kg ({r.get('diesel_litres', 0):,.0f} L), "
                f"Water: {r['water_co2']:,.2f} kg ({r.get('water_kl', 0):,.0f} kL), "
                f"Transport: {r['transport_co2']:,.2f} kg]"
            )
            records_summary_lines.append(line)
        records_text = "\n".join(records_summary_lines)
        latest_label = format_month_label(sorted_recs[-1]["month"])
    else:
        records_text = "No monthly audit records have been submitted yet for this institute."
        latest_label = "None"

    return f"""You are the Institutional Sustainability and Carbon Accounting Advisor for "{institute.get('name', 'Educational Institute')}".

CAMPUS PROFILE:
- Name: {institute.get('name')}
- Academic Year: {institute.get('academic_year', 'N/A')}
- Address: {institute.get('address', 'N/A')}
- Students: {int(institute.get('total_students') or 0):,}
- Staff: {int(institute.get('total_staff') or 0):,}
- Built-up Campus Area: {float(institute.get('campus_area_sqft') or 0.0):,.0f} sq. ft
- Latest Recorded Month: {latest_label}

STANDARDIZED EMISSION FACTORS (kg CO2 / unit):
{factors_summary}

VERIFIED HISTORICAL AUDIT RECORDS:
{records_text}

INSTRUCTIONS:
1. Base all numerical answers strictly on the records provided above.
2. Provide concise, formal, and structured recommendations tailored to Indian academic campuses (solar PV, LED retrofits, DG scheduling/battery storage, rainwater harvesting, EV buses).
3. Do not include conversational filler or "as an AI" phrasing.
""".strip()


def run_analytical_advisor(
    user_query: str,
    institute: dict[str, Any],
    records: list[dict[str, Any]],
) -> str:
    """Generate exact, context-grounded sustainability advisory answers directly from institutional data."""
    q = user_query.lower().strip()
    sorted_recs = sorted(records, key=lambda r: r["month"])
    inst_name = institute.get("name", "the institute")
    students = int(institute.get("total_students") or 0)
    staff = int(institute.get("total_staff") or 0)
    total_people = students + staff
    campus_area = float(institute.get("campus_area_sqft") or 0.0)

    if not sorted_recs:
        return (
            f"**Baseline Status for {inst_name}:**\n\n"
            f"No monthly carbon accounting records have been logged yet for **{inst_name}**.\n\n"
            f"To generate detailed insights, navigate to the **Calculator** module and enter activity data "
            f"for electricity, diesel generators, water supply, and campus transportation."
        )

    latest = sorted_recs[-1]
    latest_month = format_month_label(latest["month"])
    tot_co2 = float(latest.get("total_co2", 0.0))
    elec_co2 = float(latest.get("electricity_co2", 0.0))
    diesel_co2 = float(latest.get("diesel_co2", 0.0))
    water_co2 = float(latest.get("water_co2", 0.0))
    trans_co2 = float(latest.get("transport_co2", 0.0))

    breakdown = {
        "Electricity (Grid)": elec_co2,
        "Diesel Generator": diesel_co2,
        "Water Supply & Treatment": water_co2,
        "Campus Transportation": trans_co2,
    }
    top_cat, top_val = max(breakdown.items(), key=lambda x: x[1])
    top_pct = (top_val / tot_co2 * 100) if tot_co2 > 0 else 0.0

    # Question 1: Which category emits the most?
    if "most" in q or "highest" in q or "top" in q or "largest" in q:
        sorted_cats = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        resp = [
            f"### Primary Emission Contributor Analysis ({latest_month})",
            f"For **{inst_name}**, the highest emitting category in the latest audit period is **{top_cat}**.",
            "",
            f"- **{top_cat}:** **{top_val:,.1f} kg CO2** ({top_pct:.1f}% of monthly total)",
        ]
        for cat, val in sorted_cats[1:]:
            pct = (val / tot_co2 * 100) if tot_co2 > 0 else 0
            resp.append(f"- **{cat}:** {val:,.1f} kg CO2 ({pct:.1f}%)")

        resp.extend(
            [
                "",
                f"**Total Carbon Footprint:** **{tot_co2:,.1f} kg CO2** ({tot_co2/1000:,.2f} MT CO2e).",
                "",
                "#### Targeted Reduction Recommendations:",
            ]
        )
        if "Electricity" in top_cat:
            usable_roof = campus_area * 0.25
            est_solar_kw = usable_roof / 100.0
            resp.extend(
                [
                    f"1. **Rooftop Solar PV Installation:** With ~{campus_area:,.0f} sq. ft built-up area, an estimated **{est_solar_kw:,.0f} kWp** rooftop solar plant can generate ~{est_solar_kw * 120:,.0f} kWh/month, offsetting up to **{(est_solar_kw * 120 * 0.82 / elec_co2 * 100) if elec_co2 else 0:.0f}%** of grid emissions.",
                    "2. **HVAC & Thermal Management:** Enforce standard setpoint temperature of 24°C in auditoriums and computer labs.",
                    "3. **Lighting Upgrades:** Replace remaining fluorescent tubes with motion sensor-controlled commercial LEDs.",
                ]
            )
        elif "Diesel" in top_cat:
            resp.extend(
                [
                    "1. **DG Load Scheduling:** Prevent operating heavy diesel sets during light evening loads.",
                    "2. **Battery Energy Storage (BESS):** Evaluate lithium iron phosphate (LFP) battery banks to bridge short grid outages.",
                    "3. **Engine Maintenance:** Perform calibrated fuel injector servicing to restore optimal air-fuel combustion ratios.",
                ]
            )
        elif "Transportation" in top_cat:
            resp.extend(
                [
                    "1. **Fleet Electrification:** Prioritize institutional buses for phased transition to electric buses (EVs).",
                    "2. **Bus Route Optimization:** Consolidate commuter pickup clusters to shorten dead-mileage.",
                    "3. **Carpooling & Public Transit:** Designate reserved EV charging and carpooling parking bays.",
                ]
            )
        else:
            resp.extend(
                [
                    "1. **Rainwater Harvesting:** Channel rooftop runoff to campus recharge pits and storage sumps.",
                    "2. **Sewage Treatment Plant (STP) Recycling:** Recycle greywater for campus lawn horticulture and flush tanks.",
                    "3. **Aerator Retrofits:** Install 3-5 L/min flow restrictors across campus restroom fixtures.",
                ]
            )
        return "\n".join(resp)

    # Question 2: Reduce transport emissions
    if "transport" in q or "vehicle" in q or "fleet" in q or "bus" in q or "car" in q:
        t_rows = latest.get("transport_rows", [])
        resp = [
            f"### Campus Transportation Decarbonization Plan for {inst_name}",
            f"In **{latest_month}**, transportation accounted for **{trans_co2:,.1f} kg CO2** ({top_pct if 'Transport' in top_cat else (trans_co2/tot_co2*100):.1f}% of campus emissions).",
            "",
            "#### Fleet Breakdown:",
        ]
        if t_rows:
            for tr in t_rows:
                resp.append(
                    f"- **{tr['vehicle_type']}:** {tr['vehicle_count']} vehicles × {tr['distance_km']:,.0f} km = **{tr['co2_kg']:,.1f} kg CO2** ({tr['factor']:.3f} kg CO2/km)"
                )
        else:
            resp.append("- Transport fleet aggregated in monthly audit records.")

        resp.extend(
            [
                "",
                "#### Strategic Decarbonization Interventions:",
                "1. **Transition Campus Buses to Electric Vehicles (EVs):** Buses have an emission factor of 0.90 kg CO2/km (the highest vehicle class). Transitioning institutional buses to electric reduces direct tailpipe emissions to zero.",
                "2. **Carpool Incentive Program:** Enforce minimum passenger occupancy policies for staff and faculty vehicle passes.",
                "3. **Dynamic Route Clustering:** Implement GPS route telemetry to eliminate redundant bus circuits.",
                "4. **On-Campus EV Charging Infrastructure:** Install dedicated AC Type-2 chargers powered by rooftop solar.",
            ]
        )
        return "\n".join(resp)

    # Question 3: Calculation methodology & factors
    if "calculate" in q or "factor" in q or "formula" in q or "method" in q or "explain" in q:
        return (
            f"### Greenhouse Gas Accounting Methodology\n\n"
            f"The **Carbon Footprint Calculator** calculates all institutional emissions following the "
            f"**GHG Protocol Corporate Standard** using the authoritative equation:\n\n"
            f"$$\\text{{Emissions (kg CO}}_2\\text{{)}} = \\text{{Activity Data}} \\times \\text{{Emission Factor}}$$\n\n"
            f"#### Standard Emission Factors Applied:\n\n"
            f"1. **Grid Electricity:** **0.820 kg CO2 / kWh**\n"
            f"   - *Authority:* Central Electricity Authority (CEA 2023) National Grid Baseline Database.\n"
            f"2. **Diesel Generators (DG Sets):** **2.680 kg CO2 / Litre**\n"
            f"   - *Authority:* IPCC Guidelines for National Greenhouse Gas Inventories.\n"
            f"3. **Water Supply & Wastewater Treatment:** **0.298 kg CO2 / kL** ($1\\text{{ kL}} = 1,000\\text{{ L}}$)\n"
            f"   - *Authority:* Central Pollution Control Board (CPCB) wastewater energy metrics.\n"
            f"4. **Campus Fleet & Commuting:**\n"
            f"   - Two-wheeler: **0.050 kg CO2 / km** (IPCC)\n"
            f"   - Petrol Car: **0.120 kg CO2 / km** (IPCC)\n"
            f"   - Diesel Car: **0.140 kg CO2 / km** (IPCC)\n"
            f"   - Institutional Bus: **0.900 kg CO2 / km** (IPCC)\n\n"
            f"#### Sample Verification for {latest_month} ({inst_name}):\n"
            f"- Electricity: {latest.get('electricity_kwh', 0):,.0f} kWh × 0.820 = **{elec_co2:,.1f} kg CO2**\n"
            f"- Diesel: {latest.get('diesel_litres', 0):,.0f} L × 2.680 = **{diesel_co2:,.1f} kg CO2**\n"
            f"- Water: {latest.get('water_kl', 0):,.0f} kL × 0.298 = **{water_co2:,.1f} kg CO2**\n"
            f"- Transportation: Fleet sum = **{trans_co2:,.1f} kg CO2**\n"
            f"- **Net Monthly Footprint:** **{tot_co2:,.1f} kg CO2**"
        )

    # Question 4: Compare this month with last month
    if "compare" in q or "previous" in q or "last month" in q or "trend" in q:
        if len(sorted_recs) < 2:
            return (
                f"### Month-over-Month Comparison for {inst_name}\n\n"
                f"Currently, only one audit record (**{latest_month}**) is saved in the database.\n\n"
                f"At least two consecutive monthly records are required to calculate comparative deltas. "
                f"Please record another month in the **Calculator** module to enable trend comparisons."
            )
        prev = sorted_recs[-2]
        prev_month = format_month_label(prev["month"])
        prev_tot = float(prev.get("total_co2", 0.0))
        diff_tot = tot_co2 - prev_tot
        pct_tot = (diff_tot / prev_tot * 100) if prev_tot > 0 else 0

        direction = "decreased" if diff_tot < 0 else ("increased" if diff_tot > 0 else "remained constant")
        status_word = "favorable reduction" if diff_tot < 0 else "increase"

        return (
            f"### Month-over-Month Audit Comparison\n\n"
            f"Comparing **{latest_month}** against **{prev_month}** for **{inst_name}**:\n\n"
            f"- **Net Carbon Footprint:** {prev_tot:,.1f} kg → **{tot_co2:,.1f} kg CO2** "
            f"({direction} by **{abs(pct_tot):.1f}%**, a net {status_word} of **{abs(diff_tot):,.1f} kg CO2**).\n\n"
            f"#### Category-wise Changes:\n"
            f"- **Electricity:** {prev.get('electricity_co2', 0):,.1f} kg → {elec_co2:,.1f} kg "
            f"({'+' if elec_co2 >= prev.get('electricity_co2', 0) else ''}{elec_co2 - prev.get('electricity_co2', 0):,.1f} kg)\n"
            f"- **Diesel Generator:** {prev.get('diesel_co2', 0):,.1f} kg → {diesel_co2:,.1f} kg "
            f"({'+' if diesel_co2 >= prev.get('diesel_co2', 0) else ''}{diesel_co2 - prev.get('diesel_co2', 0):,.1f} kg)\n"
            f"- **Water Supply:** {prev.get('water_co2', 0):,.1f} kg → {water_co2:,.1f} kg "
            f"({'+' if water_co2 >= prev.get('water_co2', 0) else ''}{water_co2 - prev.get('water_co2', 0):,.1f} kg)\n"
            f"- **Transportation:** {prev.get('transport_co2', 0):,.1f} kg → {trans_co2:,.1f} kg "
            f"({'+' if trans_co2 >= prev.get('transport_co2', 0) else ''}{trans_co2 - prev.get('transport_co2', 0):,.1f} kg)"
        )

    # General campus sustainability query response
    per_person = (tot_co2 / total_people) if total_people > 0 else 0
    per_sqft = (tot_co2 / campus_area) if campus_area > 0 else 0
    trees = tot_co2 / (21.0 / 12.0) if tot_co2 > 0 else 0

    return (
        f"### Institutional Sustainability Advisory Assessment ({inst_name})\n\n"
        f"Based on the **{latest_month}** audit dataset and institutional parameters for **{inst_name}**:\n\n"
        f"- **Total Monthly Carbon Footprint:** **{tot_co2:,.1f} kg CO2** ({tot_co2/1000:,.2f} MT CO2e)\n"
        f"- **Per-Capita Carbon Intensity:** **{per_person:.2f} kg CO2/person** ({total_people:,} students & staff)\n"
        f"- **Physical Estate Intensity:** **{per_sqft:.4f} kg CO2/sq. ft** ({campus_area:,.0f} sq. ft built-up area)\n"
        f"- **Ecological Offset Equivalent:** Requires **{int(round(trees)):,} mature trees** to absorb this month's footprint (~21 kg CO2/tree/year).\n\n"
        f"#### Priority Decarbonization Pathways:\n"
        f"1. **Rooftop Solar PV:** Deploy ~{max(50, int(campus_area * 0.25 / 100)):,} kWp solar array across academic block rooftops.\n"
        f"2. **Grid Demand Optimization:** Implement energy management sub-metering to track departmental peak demand.\n"
        f"3. **Water & Circularity:** Construct decentralized rainwater catchment pits and recycle treated effluent for landscape irrigation.\n"
        f"4. **Campus Commute:** Establish institutional bus electrification milestones and carpool reserved parking."
    )


def stream_advisor_response(
    messages: list[dict[str, str]],
    institute: dict[str, Any],
    records: list[dict[str, Any]],
) -> Generator[str, None, None]:
    """Stream response from live LLM (Gemini or Groq) with intelligent analytical fallback."""
    provider, active_key, _ = detect_provider()
    latest_user_query = messages[-1]["content"] if messages else ""
    system_prompt = build_system_prompt(institute, records)

    # Try Gemini if active_key is valid
    if provider == "gemini" and active_key:
        try:
            from google import genai

            client = genai.Client(api_key=active_key)
            full_prompt = f"{system_prompt}\n\nUser Question: {latest_user_query}"
            response = client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=full_prompt,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return
        except Exception:
            pass

    # Try Groq if active_key is valid
    if provider == "groq" and active_key:
        try:
            from groq import Groq

            client = Groq(api_key=active_key)
            payload = [{"role": "system", "content": system_prompt}] + messages
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=payload,
                temperature=0.2,
                max_tokens=1500,
                stream=True,
            )
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
            return
        except Exception:
            pass

    # Analytical Advisor Engine (immediate, grounded, resilient)
    full_text = run_analytical_advisor(latest_user_query, institute, records)

    tokens = re.split(r"(\s+)", full_text)
    for token in tokens:
        yield token
        if "\n" in token:
            time.sleep(0.01)
        elif len(token.strip()) > 3:
            time.sleep(0.005)
