"""AI Sustainability Advisor page.

Provides an interactive consultant interface grounded in the active institute's
actual monthly utility records, emission factors, and campus demographics.
Supports Google Gemini, Groq Cloud, and Built-in Campus Sustainability Analytics.
"""

import streamlit as st

st.set_page_config(
    page_title="Sustainability Advisor | Carbon Footprint Calculator",
    page_icon="💬",
    layout="wide",
)

from modules.chatbot import (
    build_system_prompt,
    detect_provider,
    stream_advisor_response,
)
from modules.database import get_institute, get_monthly_records, list_institutes
from modules.ui import (
    inject_custom_css,
    institute_selector,
    render_institute_summary_card,
    render_page_header,
    render_section_title,
)

inject_custom_css()

render_page_header(
    title="Campus Sustainability Advisor",
    subtitle="Context-aware advisor providing data-grounded insights and decarbonization pathways.",
    badge="Decision Support",
)

# Active institute selector
active_inst_id = institute_selector(label="Select Institute for Advisory", key="chatbot_inst_selector")

if not active_inst_id:
    st.stop()

institute = get_institute(active_inst_id)
if not institute:
    st.error("Selected institute could not be found.")
    st.stop()

# Compact profile banner
render_institute_summary_card(institute)

# Detect Advisor Engine Provider
provider_name, active_key, status_label = detect_provider()

# Provider Status Pill / Notice
if provider_name == "analytics_engine":
    key_note = (
        f" (`{active_key}` is recognized as a Google Cloud Project ID)"
        if active_key and active_key.startswith("gen-lang-client-")
        else ""
    )
    st.markdown(
        f"""
        <div style="background-color: #F3F8F4; border: 1px solid #C8E6C9; border-radius: 8px; padding: 0.65rem 1rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div>
                <span style="font-size: 0.8rem; font-weight: 700; color: #2E7D32; text-transform: uppercase;">Active Engine:</span>
                <span style="font-size: 0.9rem; font-weight: 600; color: #1B2A1F; margin-left: 0.35rem;">Institutional Analytics Advisor (Fully Operational)</span>
                <div style="font-size: 0.8rem; color: #4B6351; margin-top: 0.15rem;">
                    Analyzes campus audit data, emission factors, and estate parameters in real-time{key_note}.
                </div>
            </div>
            <div>
                <span class="inst-pill" style="background-color: #E8F5E9; color: #2E7D32; font-size: 0.75rem;">100% Ready</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div style="background-color: #E8F5E9; border: 1px solid #A5D6A7; border-radius: 8px; padding: 0.65rem 1rem; margin-bottom: 1.25rem;">
            <span style="font-size: 0.8rem; font-weight: 700; color: #2E7D32; text-transform: uppercase;">Live LLM Connected:</span>
            <span style="font-size: 0.9rem; font-weight: 600; color: #1B2A1F; margin-left: 0.35rem;">{status_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Manage chat history scoped to institute
history_session_key = f"chat_messages_{active_inst_id}"

if "chatbot_last_inst_id" not in st.session_state:
    st.session_state["chatbot_last_inst_id"] = active_inst_id

if st.session_state["chatbot_last_inst_id"] != active_inst_id:
    st.session_state["chatbot_last_inst_id"] = active_inst_id
    if history_session_key not in st.session_state:
        st.session_state[history_session_key] = []

if history_session_key not in st.session_state:
    st.session_state[history_session_key] = []

# Fetch active records for dynamic context building
records_asc = get_monthly_records(active_inst_id, order_desc=False)

# Suggested Questions Row
render_section_title("Suggested Inquiries")

suggested_queries = [
    "Which category emits the most?",
    "How can we reduce transport emissions?",
    "Explain how my emissions are calculated",
    "Compare this month with last month",
]

col_q1, col_q2, col_q3, col_q4 = st.columns(4)
query_to_submit = None

with col_q1:
    if st.button(suggested_queries[0], use_container_width=True):
        query_to_submit = suggested_queries[0]
with col_q2:
    if st.button(suggested_queries[1], use_container_width=True):
        query_to_submit = suggested_queries[1]
with col_q3:
    if st.button(suggested_queries[2], use_container_width=True):
        query_to_submit = suggested_queries[2]
with col_q4:
    if st.button(suggested_queries[3], use_container_width=True):
        query_to_submit = suggested_queries[3]

# Action row with Clear Conversation
col_info, col_clear = st.columns([3, 1])
with col_clear:
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state[history_session_key] = []
        st.rerun()

render_section_title("Consultation Transcript")

# Render existing chat history
for msg in st.session_state[history_session_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Capture user query from chat input or suggested button
user_input = st.chat_input("Ask a question regarding your campus emissions profile, trends, or reduction strategies...")
prompt = query_to_submit if query_to_submit else user_input

if prompt:
    # Append user question to history
    st.session_state[history_session_key].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_reply = ""
        with st.spinner("Analyzing institutional carbon accounting data..."):
            formatted_msgs = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state[history_session_key]
            ]
            for chunk in stream_advisor_response(formatted_msgs, institute, records_asc):
                full_reply += chunk
                response_placeholder.markdown(full_reply + "▌")

        response_placeholder.markdown(full_reply)
        st.session_state[history_session_key].append({"role": "assistant", "content": full_reply})
