"""
Page: Browse Questions
Filter, preview, and delete questions from the database.
"""

import streamlit as st
from shared.ui import inject_css, page_header, add_navigation
from shared.constants import TOPICS, AGE_GROUPS, DIFFICULTY_LEVELS, QUESTION_TYPES, ACTIVITY_ICONS
from shared import database as db

st.set_page_config(page_title="Browse Questions", page_icon="📋", layout="wide")
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────
add_navigation()

page_header("📋 Browse Questions", "Filter and review all saved activities.")

# ── Filters ──────────────────────────────────────────────────────
with st.expander("🔍 Filters", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1: f_topics = st.multiselect("Topic",      TOPICS)
    with c2: f_types  = st.multiselect("Type",       list(QUESTION_TYPES.keys()),
                                        format_func=lambda k: QUESTION_TYPES[k])
    with c3: f_age    = st.selectbox("Age group",    ["All"] + AGE_GROUPS)
    with c4: f_diff   = st.selectbox("Difficulty",   ["All"] + DIFFICULTY_LEVELS)

# ── Load data ────────────────────────────────────────────────────
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

    st.markdown(f"**{len(questions)} question(s) found**")
    st.markdown("---")

    if not questions:
        st.info("No questions match the selected filters.")
    else:
        for q in questions:
            icon  = ACTIVITY_ICONS.get(q["activity_type_key"], "❓")
            label = QUESTION_TYPES.get(q["activity_type_key"], q["activity_type_key"])
            topic_name = (
                q["topics"]["name"]
                if q.get("topics") else q["topic_id"]
            )
            header = f"{icon} **{topic_name}** — {label} · {q['age_group']} · {q['difficulty']}"
            with st.expander(header):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**ID:** `{q['id']}`")
                    st.markdown(f"**Created:** {q['created_at'][:19].replace('T', ' ')}")
                    st.json(q["content"])
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{q['id']}"):
                        db.delete_question(q["id"])
                        st.success("Deleted.")
                        st.rerun()

except Exception as e:
    st.error(f"Could not load questions: {e}")