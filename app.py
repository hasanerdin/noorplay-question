"""
Islamic Education – Content Editor
Entry point. Streamlit multi-page apps load pages/ automatically.
This file sets global config and renders the home / dashboard page.
"""

import streamlit as st
from shared.ui import inject_css, page_header, add_navigation
from shared.constants import APP_TITLE, APP_ICON
from shared import database as db

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────
add_navigation()

# ── Dashboard ────────────────────────────────────────────────────
page_header("🏠 Dashboard", "Overview of your content library")

try:
    questions = db.get_questions()
    topics    = db.get_topics()

    total  = len(questions)
    t_count = len(topics)

    from shared.constants import QUESTION_TYPES
    type_counts = {k: 0 for k in QUESTION_TYPES}
    for q in questions:
        key = q.get("activity_type_key", "")
        if key in type_counts:
            type_counts[key] += 1

    # ── Stats row ────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Questions", total)
    c2.metric("Topics",          t_count)
    c3.metric("Multiple Choice", type_counts["multiple_choice"])
    c4.metric("Image Matching",  type_counts["image_matching"])
    c5.metric("Drag & Drop",     type_counts["drag_drop_sorting"])

    st.markdown("---")

    # ── Recent questions ─────────────────────────────────────────
    st.markdown("### Recent Questions")
    recent = questions[:8]
    if not recent:
        st.info("No questions yet. Go to **Add Activity** to create your first one.")
    else:
        from shared.constants import ACTIVITY_ICONS
        for q in recent:
            icon  = ACTIVITY_ICONS.get(q["activity_type_key"], "❓")
            topic = q.get("topics", {}).get("name", q["topic_id"]) if q.get("topics") else q["topic_id"]
            st.markdown(
                f'<div class="info-card"><h4>{icon} {topic}</h4>'
                f'<p>{q["activity_type_key"].replace("_"," ").title()} · '
                f'{q["age_group"]} · {q["difficulty"]} · '
                f'<code>{q["id"]}</code></p></div>',
                unsafe_allow_html=True,
            )

except Exception as e:
    st.warning(f"Could not load data from Supabase: {e}")
    st.info("Make sure your Supabase credentials are set in **.streamlit/secrets.toml**")