"""Shared UI layout helpers, design system CSS, and component builders.

Implements an institutional, publication-grade light theme with deep green
accents (#2E7D32), soft tinted panels (#F3F8F4, #E8F5E9), clear metric cards,
and synchronized institute selection across pages.
"""

from typing import Any
import streamlit as st
from modules.database import get_institute, list_institutes


def inject_custom_css() -> None:
    """Inject custom institutional CSS styling into the Streamlit application."""
    st.markdown(
        """
        <style>
        /* Base typography & colors */
        :root {
            --primary: #2E7D32;
            --primary-light: #E8F5E9;
            --primary-border: #C8E6C9;
            --bg-secondary: #F3F8F4;
            --text-main: #1B2A1F;
            --text-muted: #4B6351;
            --card-border: #E0EBE2;
            --danger-bg: #FFEBEE;
            --danger-text: #C62828;
            --success-bg: #E8F5E9;
            --success-text: #2E7D32;
        }

        /* Hide Streamlit default branding elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {background: transparent;}

        /* App general background and font */
        .stApp {
            background-color: #FFFFFF;
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Section Headings with Green Left Accent Bar */
        .section-header {
            display: flex;
            align-items: center;
            margin-top: 1.6rem;
            margin-bottom: 0.9rem;
            padding-left: 0.75rem;
            border-left: 4px solid var(--primary);
        }
        .section-header h2, .section-header h3, .section-header h4 {
            margin: 0;
            padding: 0;
            color: var(--text-main);
            font-weight: 600;
            font-size: 1.25rem;
            letter-spacing: -0.01em;
        }

        /* Institutional Metric Cards */
        .inst-card {
            background-color: #FFFFFF;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 1px 3px rgba(27, 42, 31, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            margin-bottom: 0.75rem;
        }
        .inst-card:hover {
            box-shadow: 0 4px 12px rgba(46, 125, 50, 0.08);
            transform: translateY(-2px);
        }

        .metric-title {
            font-size: 0.825rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text-main);
            line-height: 1.2;
            margin-bottom: 0.25rem;
        }
        .metric-sub {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .metric-delta {
            display: inline-flex;
            align-items: center;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            margin-top: 0.35rem;
        }
        .delta-down {
            background-color: var(--success-bg);
            color: var(--success-text);
        }
        .delta-up {
            background-color: var(--danger-bg);
            color: var(--danger-text);
        }

        /* Pill Badges */
        .inst-pill {
            display: inline-block;
            background-color: var(--primary-light);
            color: var(--primary);
            border: 1px solid var(--primary-border);
            border-radius: 9999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #E8F5E9 0%, #F1F8E9 50%, #FFFFFF 100%);
            border: 1px solid var(--primary-border);
            border-radius: 14px;
            padding: 2.25rem 2rem;
            margin-bottom: 1.75rem;
            text-align: center;
        }
        .hero-title {
            color: var(--primary);
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            color: var(--text-muted);
            font-size: 1.05rem;
            font-weight: 400;
            margin-bottom: 0;
        }

        /* Key Insight Callout */
        .insight-card {
            background-color: #F8FAF8;
            border-left: 4px solid var(--primary);
            border-radius: 0 8px 8px 0;
            padding: 1rem 1.25rem;
            margin: 1rem 0;
            color: var(--text-main);
        }

        /* Styled Tables */
        .dataframe {
            border-collapse: collapse;
            width: 100%;
            font-size: 0.9rem;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--card-border);
        }
        .dataframe th {
            background-color: var(--bg-secondary);
            color: var(--text-main);
            font-weight: 600;
            text-align: left;
            padding: 0.65rem 0.85rem;
            border-bottom: 1px solid var(--card-border);
        }
        .dataframe td {
            padding: 0.6rem 0.85rem;
            border-bottom: 1px solid #EEF2F0;
        }
        .dataframe tr:nth-child(even) {
            background-color: #FAFCFA;
        }

        /* Streamlit button fine-tuning (clean, professional) */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 500;
            padding: 0.45rem 1.25rem;
            transition: all 0.15s ease-in-out;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, badge: str | None = None) -> None:
    """Render a standardized page title banner with clean typography."""
    badge_html = f'<div style="margin-bottom: 0.4rem;"><span class="inst-pill">{badge}</span></div>' if badge else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--card-border, #E0EBE2);">
            {badge_html}
            <h1 style="color: #2E7D32; font-size: 1.85rem; font-weight: 700; margin: 0 0 0.25rem 0; letter-spacing: -0.02em;">{title}</h1>
            <p style="color: #4B6351; font-size: 0.95rem; margin: 0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str) -> None:
    """Render a section header with an institutional left accent bar."""
    st.markdown(
        f"""
        <div class="section-header">
            <h3>{title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def institute_selector(
    label: str = "Active Institute",
    key: str = "shared_institute_selector",
    sidebar: bool = False,
) -> int | None:
    """Synchronized institute selector component.

    Reads registered institutes from database and maintains
    st.session_state['active_institute_id'].

    Returns:
        int | None: The active institute ID, or None if none exist.
    """
    institutes = list_institutes()
    container = st.sidebar if sidebar else st

    if not institutes:
        container.warning("No institutes registered yet. Please create an institute profile first.")
        if container.button("Register New Institute", key=f"{key}_btn_goto_profile"):
            st.switch_page("pages/1_Institute_Details.py")
        return None

    # Institute name to ID map
    inst_options = {inst["name"]: inst["id"] for inst in institutes}
    inst_names = list(inst_options.keys())

    # Determine default index based on session state
    current_active_id = st.session_state.get("active_institute_id")
    default_idx = 0
    if current_active_id:
        for i, inst in enumerate(institutes):
            if inst["id"] == current_active_id:
                default_idx = i
                break
    else:
        st.session_state["active_institute_id"] = institutes[0]["id"]
        default_idx = 0

    selected_name = container.selectbox(
        label,
        options=inst_names,
        index=default_idx,
        key=key,
        help="Calculations, trends, and chatbot interactions will be scoped to this institute.",
    )

    chosen_id = inst_options[selected_name]
    st.session_state["active_institute_id"] = chosen_id
    return chosen_id


def render_institute_summary_card(institute: dict[str, Any]) -> None:
    """Render a compact read-only institutional profile card."""
    st.markdown(
        f"""
        <div class="inst-card" style="background-color: #F8FAF8; border: 1px solid #D7E7D9; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <span class="inst-pill" style="margin-bottom: 0.35rem;">Selected Institute</span>
                    <h3 style="margin: 0.25rem 0 0.15rem 0; color: #1B2A1F; font-size: 1.25rem; font-weight: 700;">{institute['name']}</h3>
                    <p style="margin: 0; color: #4B6351; font-size: 0.85rem;">{institute.get('address') or 'Address not specified'}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.75rem; text-transform: uppercase; color: #4B6351; font-weight: 600;">Academic Year</span>
                    <div style="font-size: 1rem; font-weight: 700; color: #2E7D32;">{institute.get('academic_year', 'N/A')}</div>
                </div>
            </div>
            <hr style="border: 0; border-top: 1px solid #E2EBE2; margin: 0.75rem 0;">
            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.75rem; color: #4B6351; text-transform: uppercase;">Students</span>
                    <div style="font-weight: 600; color: #1B2A1F;">{int(institute.get('total_students') or 0):,}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #4B6351; text-transform: uppercase;">Staff</span>
                    <div style="font-weight: 600; color: #1B2A1F;">{int(institute.get('total_staff') or 0):,}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #4B6351; text-transform: uppercase;">Campus Area</span>
                    <div style="font-weight: 600; color: #1B2A1F;">{float(institute.get('campus_area_sqft') or 0.0):,.0f} sq. ft</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: str,
    subvalue: str | None = None,
    delta: float | None = None,
    delta_text: str | None = None,
    higher_is_better: bool = False,
) -> None:
    """Render a clean institutional metric card with optional delta indicator."""
    delta_html = ""
    if delta is not None and delta_text:
        # In carbon accounting, a reduction (delta < 0) is favorable (green)
        is_favorable = (delta < 0) if not higher_is_better else (delta > 0)
        delta_class = "delta-down" if is_favorable else "delta-up"
        delta_sign = "+" if delta > 0 else ""
        delta_html = f'<div class="metric-delta {delta_class}">{delta_sign}{delta_text}</div>'

    sub_html = f'<div class="metric-sub">{subvalue}</div>' if subvalue else ""

    st.markdown(
        f"""
        <div class="inst-card">
            <div class="metric-title">{label}</div>
            <div class="metric-value">{value}</div>
            {sub_html}
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
