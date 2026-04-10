"""
Shared UI utilities — CSS injection, reusable components, navigation.
"""

import streamlit as st
from shared.constants import APP_ICON, APP_VERSION


# ── Global CSS ───────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Nunito:wght@400;600;700&display=swap');

/* Base */
html, body, [class*="css"]  { font-family: 'Nunito', sans-serif; }
h1, h2, h3                  { font-family: 'Amiri', serif; color: #1a3a2a; }
.stApp                      { background: #faf8f4; }
.block-container            { padding-top: 1.5rem; }

/* ── Sidebar ─────────────────────────────────────────────────── */
section[data-testid="stSidebar"] > div:first-child {
    background: #1a3a2a;
    padding: 1.5rem 1rem;
}

/* All text inside sidebar — force light color */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] a,
section[data-testid="stSidebar"] .stMarkdown {
    color: #e8f5ee !important;
}

/* Sidebar input backgrounds */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #254d38 !important;
    color: #e8f5ee !important;
    border-color: #3d7a58 !important;
}

/* Sidebar checkbox label */
section[data-testid="stSidebar"] .stCheckbox label span {
    color: #e8f5ee !important;
}

/* Sidebar headings via markdown */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #a8d5b8 !important;
}

/* Tip box — override sidebar's global light-color rule */
section[data-testid="stSidebar"] .tip-box,
section[data-testid="stSidebar"] .tip-box p,
section[data-testid="stSidebar"] .tip-box span,
section[data-testid="stSidebar"] .tip-box div {
    color: #1a3a2a !important;
}

/* ── Main content area ────────────────────────────────────────── */
.main p, .main span, .main label,
.stMarkdown p, .stMarkdown li        { color: #1a1a1a; }

input, textarea                      { color: #1a1a1a !important; background: #ffffff !important; }
.stSelectbox > div > div             { color: #1a1a1a !important; background: #ffffff !important; }
.stNumberInput input                 { color: #1a1a1a !important; }

/* ── Custom components ────────────────────────────────────────── */
.tip-box {
    background: #e8f5ee;
    border-left: 4px solid #2d7a4f;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0 16px 0;
    font-size: 0.9rem;
    color: #1a3a2a !important;
}

.tip-box p, .tip-box span, .tip-box div {
    color: #1a3a2a !important;
}

.info-card {
    background: #ffffff;
    border: 1px solid #d4c9b0;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 8px 0;
    color: #1a1a1a;
}

.info-card h4 { margin: 0 0 4px 0; color: #1a3a2a; font-size: 0.95rem; }
.info-card p  { margin: 0; color: #555; font-size: 0.85rem; }

.success-banner {
    background: #2d7a4f;
    color: #ffffff !important;
    padding: 16px 24px;
    border-radius: 10px;
    text-align: center;
    font-size: 1rem;
    margin: 12px 0;
}

.json-preview {
    background: #1e2a1e;
    color: #7dda8a;
    padding: 16px;
    border-radius: 10px;
    font-family: monospace;
    font-size: 0.82rem;
    max-height: 340px;
    overflow-y: auto;
    white-space: pre;
}

.page-header {
    border-bottom: 2px solid #2d7a4f;
    padding-bottom: 8px;
    margin-bottom: 24px;
    color: #1a3a2a;
}

hr { border: none; border-top: 1px solid #d4c9b0; margin: 20px 0; }
</style>
"""

# ── Navigation links ─────────────────────────────────────────────
# Single source of truth for all sidebar navigation.
# Add or rename pages here — all pages pick it up automatically.

NAV_LINKS: list[tuple[str, str]] = [
    ("app.py",                       "🏠 Dashboard"),
    ("pages/1_Manage_Books.py",      "📚 Manage Books"),
    ("pages/2_Image_Library.py",     "🖼️ Image Library"),
    ("pages/3_Audio_Library.py",     "🎵 Audio Library"),
    ("pages/4_Word_Timings.py",      "⏱️ Word Timings"),
    ("pages/5_Manage_Topics.py",     "🏷️ Manage Topics"),
    ("pages/6_Add_Questions.py",     "➕ Add Questions"),
    ("pages/7_Browse_Questions.py",  "📋 Browse Questions"),
    ("pages/8_Export.py",            "📤 Export JSON"),
    ("pages/9_Settings.py",          "⚙️ Settings"),
]


def add_navigation() -> None:
    """
    Render sidebar header + navigation links.
    Call once per page inside a `with st.sidebar:` block — or standalone.
    """
    with st.sidebar:
        st.markdown(f"## {APP_ICON} Content Editor")
        st.markdown(f"*v{APP_VERSION}*")
        st.markdown("---")
        st.markdown("### Navigation")
        for path, label in NAV_LINKS:
            st.page_link(path, label=label)


# ── CSS helpers ──────────────────────────────────────────────────

def inject_css() -> None:
    """Inject global CSS. Call once at the top of every page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── Component helpers ────────────────────────────────────────────

def tip(text: str) -> None:
    st.markdown(f'<div class="tip-box">{text}</div>', unsafe_allow_html=True)


def success_banner(text: str) -> None:
    st.markdown(f'<div class="success-banner">{text}</div>', unsafe_allow_html=True)


def json_preview(json_str: str) -> None:
    st.markdown(f'<div class="json-preview">{json_str}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="page-header"><h2>{title}</h2></div>', unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)