"""
Page: Export
Build a filtered export, preview the JSON, download it, and/or send via email.
"""

import json
import streamlit as st
from datetime import datetime
from shared.ui import inject_css, page_header, json_preview, add_navigation
from shared.constants import TOPICS, AGE_GROUPS, DIFFICULTY_LEVELS, QUESTION_TYPES
from shared import database as db

st.set_page_config(page_title="Export JSON", page_icon="📤", layout="wide")
inject_css()

add_navigation()

page_header("📤 Export JSON", "Filter, preview, and send content to Unity.")

# ── Filters ──────────────────────────────────────────────────────
st.markdown("### 🔍 Filter Export")
c1, c2, c3, c4 = st.columns(4)
with c1: f_topics = st.multiselect("Topics (empty = all)",     TOPICS,                  key="ex_topics")
with c2: f_types  = st.multiselect("Types (empty = all)",      list(QUESTION_TYPES.keys()),
                                    format_func=lambda k: QUESTION_TYPES[k],            key="ex_types")
with c3: f_age    = st.selectbox("Age group",                  ["All"] + AGE_GROUPS,    key="ex_age")
with c4: f_diff   = st.selectbox("Difficulty",                 ["All"] + DIFFICULTY_LEVELS, key="ex_diff")

if st.button("🔄 Build Export", type="primary"):
    try:
        topic_ids = None
        if f_topics:
            all_topics = db.get_topics()
            topic_ids  = [t["id"] for t in all_topics if t["name"] in f_topics]

        questions = db.get_questions(
            topic_ids  = topic_ids or None,
            type_keys  = f_types or None,
            age_group  = None if f_age  == "All" else f_age,
            difficulty = None if f_diff == "All" else f_diff,
        )

        payload  = db.export_questions_as_payload(questions)
        json_str = json.dumps(payload, ensure_ascii=False, indent=2)
        filename = f"islamic_education_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

        st.session_state["export_json"]     = json_str
        st.session_state["export_filename"] = filename
        st.session_state["export_count"]    = len(questions)

    except Exception as e:
        st.error(f"Export failed: {e}")

# ── Preview & actions ────────────────────────────────────────────
if "export_json" in st.session_state:
    count = st.session_state["export_count"]
    st.markdown(f"**{count} question(s) ready for export.**")

    with st.expander("📄 JSON Preview"):
        json_preview(st.session_state["export_json"])


    st.download_button(
        label    = f"⬇️ Download JSON ({count} questions)",
        data     = st.session_state["export_json"].encode("utf-8"),
        file_name = st.session_state["export_filename"],
        mime     = "application/json",
    )
