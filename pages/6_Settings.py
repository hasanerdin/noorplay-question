"""
Page: Settings
Manage users, view Supabase connection status, and check app info.
"""

import streamlit as st
from shared.ui import inject_css, page_header, tip, success_banner, add_navigation
from shared.constants import APP_VERSION, APP_TITLE
from shared import database as db

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
inject_css()

add_navigation()

page_header("⚙️ Settings", "Supabase connection, users, and app info.")

tab_conn, tab_users, tab_info = st.tabs(["🔌 Connection", "👥 Users", "ℹ️ App Info"])

# ── Connection tab ───────────────────────────────────────────────
with tab_conn:
    st.markdown("### Supabase Connection Test")
    if st.button("Test connection"):
        try:
            topics = db.get_topics()
            questions = db.get_questions()
            st.success(f"✅ Connected! Found {len(topics)} topics and {len(questions)} questions.")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")

    st.markdown("---")
    st.markdown("### Secrets Required")
    tip("Add these to <code>.streamlit/secrets.toml</code> locally, or via the Streamlit Cloud Secrets UI.")
    st.code("""
    SUPABASE_URL   = "https://YOUR_PROJECT.supabase.co"
    SUPABASE_KEY   = "YOUR_SERVICE_ROLE_KEY"
    OPENAI_API_KEY = "sk-..."
    """, language="toml")

# ── Users tab ────────────────────────────────────────────────────
with tab_users:
    st.markdown("### Registered Users")
    try:
        users = db.get_all_users()
        if not users:
            st.info("No users yet.")
        else:
            for u in users:
                st.markdown(
                    f'<div class="info-card"><h4>{u["display_name"]}</h4>'
                    f'<p>{u["email"]} · {u["role"]} · last seen: {u.get("last_seen","–")[:10]}</p></div>',
                    unsafe_allow_html=True,
                )
    except Exception as e:
        st.error(f"Could not load users: {e}")

    st.markdown("---")
    st.markdown("### Add / Update User")
    import uuid
    c1, c2 = st.columns(2)
    with c1:
        new_name  = st.text_input("Display name", placeholder="Fatima")
        new_email = st.text_input("Email",         placeholder="fatima@example.com")
    with c2:
        new_role  = st.selectbox("Role", ["teacher", "admin", "viewer"])
    if st.button("💾 Save User", type="primary"):
        if new_name and new_email:
            uid    = f"user_{uuid.uuid4().hex[:8]}"
            result = db.upsert_user(uid, new_email, new_name, new_role)
            if result:
                success_banner(f"✅ User '{new_name}' saved.")
                st.rerun()
            else:
                st.error("Save failed.")
        else:
            st.warning("Name and email are required.")

# ── Info tab ─────────────────────────────────────────────────────
with tab_info:
    st.markdown(f"### {APP_TITLE}")
    st.markdown(f"**Version:** {APP_VERSION}")
    st.markdown("""
    **Project structure:**
    ```
    islam_editor/
    ├── app.py                     ← Dashboard (entry point)
    ├── requirements.txt
    ├── .streamlit/
    │   ├── config.toml            ← Theme
    │   └── secrets.toml           ← Credentials (never commit)
    ├── shared/
    │   ├── constants.py           ← All constants (topics, types …)
    │   ├── database.py            ← All Supabase operations
    │   ├── email_utils.py         ← Gmail SMTP helper
    │   └── ui.py                  ← CSS, reusable components
    └── pages/
        ├── 1_Add_Activity.py      ← Create new questions
        ├── 2_Browse_Questions.py  ← Filter & delete
        ├── 3_Export.py            ← JSON export + email
        └── 4_Settings.py          ← Connection, users, info
    ```
    **JSON key language policy:**
    - All keys in English (`type`, `content`, `correct_index` …)
    - Content fields only in German (`de`) and Turkish (`tr`)
    """)