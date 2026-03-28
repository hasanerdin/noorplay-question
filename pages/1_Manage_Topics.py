"""
Page: Manage Topics
Create, view, and delete topics. Topics are stored in Supabase.
"""

import uuid
import streamlit as st
from shared.ui import inject_css, page_header, tip, success_banner, add_navigation
from shared import database as db

st.set_page_config(page_title="Manage Topics", page_icon="🏷️", layout="wide")
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────
add_navigation()

# ── Main ─────────────────────────────────────────────────────────
page_header("🏷️ Manage Topics", "Add new topics or remove unused ones.")

# ── Add new topic ────────────────────────────────────────────────
st.markdown("### Add New Topic")
tip("Topic names should be in English. They are used as category labels across all activities.")

col1, col2 = st.columns([3, 1])
with col1:
    new_topic_name = st.text_input(
        "Topic name",
        placeholder="e.g. Five Pillars of Islam",
        label_visibility="collapsed",
    )
with col2:
    add_clicked = st.button("➕ Add Topic", type="primary", use_container_width=True)

if add_clicked:
    if not new_topic_name.strip():
        st.warning("Please enter a topic name.")
    else:
        try:
            # Check for duplicate
            existing = db.get_topics()
            names = [t["name"].lower() for t in existing]
            if new_topic_name.strip().lower() in names:
                st.warning(f'Topic "{new_topic_name.strip()}" already exists.')
            else:
                topic_id = f"topic_{uuid.uuid4().hex[:8]}"
                result   = db.upsert_topic(topic_id, new_topic_name.strip())
                if result:
                    success_banner(f'✅ Topic "{new_topic_name.strip()}" added successfully.')
                    st.rerun()
                else:
                    st.error("Failed to save. Check Supabase connection.")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")

# ── Topic list ───────────────────────────────────────────────────
st.markdown("### Existing Topics")

try:
    topics = db.get_topics()

    if not topics:
        st.info("No topics yet. Add your first topic above.")
    else:
        st.caption(f"{len(topics)} topic(s) in the database.")
        st.markdown("")

        for topic in topics:
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{topic['name']}**")
            with col2:
                st.caption(f"`{topic['id']}`")
            with col3:
                # Warn if topic has questions attached
                if st.button("🗑️ Delete", key=f"del_topic_{topic['id']}", use_container_width=True):
                    st.session_state[f"confirm_{topic['id']}"] = True

            # Confirmation step before deleting
            if st.session_state.get(f"confirm_{topic['id']}"):
                questions = db.get_questions(topic_ids=[topic["id"]])
                q_count   = len(questions)

                if q_count > 0:
                    st.warning(
                        f'⚠️ "{topic["name"]}" has **{q_count} question(s)** linked to it. '
                        f'Deleting the topic will NOT delete the questions, '
                        f'but they will have a broken topic reference.'
                    )

                col_yes, col_no, _ = st.columns([1, 1, 4])
                with col_yes:
                    if st.button("Yes, delete", key=f"yes_{topic['id']}", type="primary"):
                        try:
                            db.get_client().table("topics").delete().eq("id", topic["id"]).execute()
                            st.session_state.pop(f"confirm_{topic['id']}", None)
                            st.success(f'"{topic["name"]}" deleted.')
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
                with col_no:
                    if st.button("Cancel", key=f"no_{topic['id']}"):
                        st.session_state.pop(f"confirm_{topic['id']}", None)
                        st.rerun()

            st.divider()

except Exception as e:
    st.error(f"Could not load topics: {e}")