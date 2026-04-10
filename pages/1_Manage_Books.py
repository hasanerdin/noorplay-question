"""
Page: Manage Books
Edit books, chapters, and pages for the "4 Magic Words" digital children's book.
"""

import streamlit as st
from shared.ui import add_navigation, inject_css, page_header, tip, success_banner
from shared.constants import LANGUAGE_LABELS
from shared import database as db
from shared.database import new_id

st.set_page_config(page_title="Manage Books", page_icon="📚", layout="wide")
inject_css()

add_navigation()

page_header("📚 Manage Books", "Manage books, chapters, and pages for the digital reader.")

# ── Load books ───────────────────────────────────────────────────
try:
    books = db.get_books()
except Exception as e:
    st.error(f"Could not load books: {e}")
    st.stop()

if not books:
    st.info("No books found. Run the migration SQL in Supabase to seed the first book.")
    st.stop()

# ════════════════════════════════════════════════════════════════
# SECTION 1 — Book selector
# ════════════════════════════════════════════════════════════════
st.markdown("### 📖 Select Book")

book_labels = {
    b["id"]: (
        b.get("title_i18n", {}).get("en")
        or b.get("title_i18n", {}).get("de")
        or b["id"]
    )
    for b in books
}

selected_book_id = st.selectbox(
    "Book",
    options=[b["id"] for b in books],
    format_func=lambda bid: book_labels[bid],
    label_visibility="collapsed",
)

selected_book = next((b for b in books if b["id"] == selected_book_id), None)
if not selected_book:
    st.stop()

# Show title in all 3 languages + publish toggle
ti = selected_book.get("title_i18n", {})
col_de, col_tr, col_en, col_pub = st.columns([2, 2, 2, 1])
with col_de: st.markdown(f"**DE:** {ti.get('de', '—')}")
with col_tr: st.markdown(f"**TR:** {ti.get('tr', '—')}")
with col_en: st.markdown(f"**EN:** {ti.get('en', '—')}")
with col_pub:
    pub = st.toggle(
        "Published",
        value=selected_book.get("is_published", False),
        key=f"book_pub_{selected_book_id}",
    )
    if pub != selected_book.get("is_published", False):
        try:
            db.set_book_published(selected_book_id, pub)
            st.rerun()
        except Exception as e:
            st.error(f"Could not update: {e}")

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SECTION 2 — Chapter list
# ════════════════════════════════════════════════════════════════
st.markdown("### 📑 Chapters")

try:
    chapters = db.get_chapters(selected_book_id)
except Exception as e:
    st.error(f"Could not load chapters: {e}")
    chapters = []

if not chapters:
    st.info("No chapters yet. Add one below.")
else:
    for ch in chapters:
        ch_ti   = ch.get("title_i18n", {})
        ch_de   = ch_ti.get("de", "—")
        ch_tr   = ch_ti.get("tr", "—")
        ch_en   = ch_ti.get("en", ch["id"])
        exp_label = f"📑 {ch_en} (sort: {ch.get('sort_order', 0)})"

        with st.expander(exp_label):
            r1, r2, r3, r4 = st.columns([3, 3, 3, 3])
            with r1: st.markdown(f"**DE:** {ch_de}")
            with r2: st.markdown(f"**TR:** {ch_tr}")
            with r3: st.markdown(f"**EN:** {ch_en}")
            with r4:
                ch_pub = st.toggle(
                    "Published",
                    value=ch.get("is_published", False),
                    key=f"ch_pub_{ch['id']}",
                )
                if ch_pub != ch.get("is_published", False):
                    try:
                        db.set_chapter_published(ch["id"], ch_pub)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update: {e}")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("✏️ Edit pages", key=f"edit_pg_{ch['id']}"):
                    st.session_state["editing_chapter_id"] = ch["id"]
                    st.session_state["editing_chapter_title"] = ch_en
                    # Clear any pending new-page sentence state
                    st.session_state.pop("add_page_sentence_ids", None)
                    st.rerun()
            with btn_col2:
                if st.button("🗑️ Delete chapter", key=f"del_ch_{ch['id']}"):
                    st.session_state[f"confirm_del_ch_{ch['id']}"] = True

            if st.session_state.get(f"confirm_del_ch_{ch['id']}"):
                st.warning("Delete this chapter and ALL its pages?")
                y_col, n_col = st.columns(2)
                with y_col:
                    if st.button("Yes, delete", key=f"yes_del_ch_{ch['id']}", type="primary"):
                        try:
                            db.delete_chapter(ch["id"])
                            if st.session_state.get("editing_chapter_id") == ch["id"]:
                                st.session_state.pop("editing_chapter_id", None)
                            st.session_state.pop(f"confirm_del_ch_{ch['id']}", None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
                with n_col:
                    if st.button("Cancel", key=f"no_del_ch_{ch['id']}"):
                        st.session_state.pop(f"confirm_del_ch_{ch['id']}", None)
                        st.rerun()

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SECTION 3 — Add chapter form
# ════════════════════════════════════════════════════════════════
st.markdown("### ➕ Add Chapter")

with st.form("add_chapter_form", clear_on_submit=True):
    tip("Enter chapter titles in all three languages and set a sort order.")
    fc1, fc2, fc3, fc4 = st.columns([3, 3, 3, 1])
    with fc1: new_ch_de = st.text_input("Title DE *", placeholder="Kapitel 1 — Bismillah")
    with fc2: new_ch_tr = st.text_input("Title TR *", placeholder="Bölüm 1 — Bismillah")
    with fc3: new_ch_en = st.text_input("Title EN *", placeholder="Chapter 1 — Bismillah")
    with fc4: new_ch_sort = st.number_input("Sort", min_value=0, value=len(chapters))

    if st.form_submit_button("💾 Save Chapter", type="primary"):
        if not all([new_ch_de.strip(), new_ch_tr.strip(), new_ch_en.strip()]):
            st.warning("All three language titles are required.")
        else:
            try:
                ch_id = new_id("ch")
                db.upsert_chapter(
                    id=ch_id,
                    book_id=selected_book_id,
                    title_i18n={"de": new_ch_de, "tr": new_ch_tr, "en": new_ch_en},
                    sort_order=int(new_ch_sort),
                )
                success_banner(f"✅ Chapter '{new_ch_en}' saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SECTION 4 — Page editor
# ════════════════════════════════════════════════════════════════
editing_chapter_id = st.session_state.get("editing_chapter_id")
editing_chapter_title = st.session_state.get("editing_chapter_title", "")

if not editing_chapter_id:
    st.info("Click **Edit pages** on a chapter above to manage its pages.")
    st.stop()

st.markdown(f"### 📄 Pages — *{editing_chapter_title}*")

if st.button("← Back to chapter list"):
    st.session_state.pop("editing_chapter_id", None)
    st.session_state.pop("editing_chapter_title", None)
    st.session_state.pop("add_page_sentence_ids", None)
    st.rerun()

# Load image library for illustration picker
try:
    library_images = db.get_images(limit=200)
    library_map    = {img["filename"]: img for img in library_images}
    library_opts   = ["— None —"] + [img["filename"] for img in library_images]
except Exception:
    library_images = []
    library_map    = {}
    library_opts   = ["— None —"]

# ── Existing pages ───────────────────────────────────────────────
try:
    pages = db.get_pages(editing_chapter_id)
except Exception as e:
    st.error(f"Could not load pages: {e}")
    pages = []

if not pages:
    st.info("No pages yet. Add one below.")
else:
    for pg in pages:
        with st.expander(f"Page {pg['page_number']}"):
            pg_col1, pg_col2 = st.columns([4, 1])
            with pg_col1:
                if pg.get("illustration_url"):
                    st.image(pg["illustration_url"], width=160)
                sentences = pg.get("sentences", [])
                if sentences:
                    for sent in sentences:
                        st.markdown(
                            f"- **DE:** {sent.get('de','—')} | "
                            f"**TR:** {sent.get('tr','—')} | "
                            f"**EN:** {sent.get('en','—')}"
                        )
                else:
                    st.caption("No sentences.")
            with pg_col2:
                if st.button("🗑️ Delete page", key=f"del_pg_{pg['id']}"):
                    st.session_state[f"confirm_del_pg_{pg['id']}"] = True

            if st.session_state.get(f"confirm_del_pg_{pg['id']}"):
                st.warning("Delete this page?")
                yd, nd = st.columns(2)
                with yd:
                    if st.button("Yes", key=f"yes_del_pg_{pg['id']}", type="primary"):
                        try:
                            db.delete_page(pg["id"])
                            st.session_state.pop(f"confirm_del_pg_{pg['id']}", None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
                with nd:
                    if st.button("No", key=f"no_del_pg_{pg['id']}"):
                        st.session_state.pop(f"confirm_del_pg_{pg['id']}", None)
                        st.rerun()

st.markdown("---")

# ── Add page form ─────────────────────────────────────────────────
st.markdown("#### ➕ Add Page")

existing_page_numbers = {pg["page_number"] for pg in pages}
next_page_num = max(existing_page_numbers, default=0) + 1

col_pn, col_ill = st.columns([1, 3])
with col_pn:
    new_page_num = st.number_input(
        "Page number",
        min_value=1,
        value=next_page_num,
        key="new_page_num",
    )
with col_ill:
    ill_pick = st.selectbox(
        "Illustration (from image library)",
        options=library_opts,
        key="new_page_ill",
    )
    ill_url = None
    if ill_pick != "— None —":
        chosen_img = library_map.get(ill_pick)
        if chosen_img:
            ill_url = chosen_img["image_url"]
            st.image(ill_url, width=120)

st.markdown("**Sentences**")
tip(
    "Click <b>Add sentence</b> to add a row. Each sentence needs DE, TR, and EN text. "
    "The order here is the display order."
)

# Sentence builder via session state
if "add_page_sentence_ids" not in st.session_state:
    st.session_state["add_page_sentence_ids"] = []

if st.button("➕ Add sentence"):
    st.session_state["add_page_sentence_ids"].append(new_id("s"))
    st.rerun()

sentence_ids = st.session_state["add_page_sentence_ids"]
sentences_to_save = []

for sid in sentence_ids:
    sc1, sc2, sc3, sc4 = st.columns([3, 3, 3, 1])
    with sc1: de_val = st.text_input("DE", key=f"sde_{sid}", placeholder="Auf Deutsch…")
    with sc2: tr_val = st.text_input("TR", key=f"str_{sid}", placeholder="Türkçe…")
    with sc3: en_val = st.text_input("EN", key=f"sen_{sid}", placeholder="In English…")
    with sc4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✕", key=f"srm_{sid}"):
            st.session_state["add_page_sentence_ids"].remove(sid)
            st.rerun()
    sentences_to_save.append({"sentence_id": sid, "de": de_val, "tr": tr_val, "en": en_val})

if st.button("💾 Save Page", type="primary", key="save_page_btn"):
    if int(new_page_num) in existing_page_numbers:
        st.warning(f"Page {new_page_num} already exists for this chapter. Choose a different number.")
    elif not sentences_to_save:
        st.warning("Add at least one sentence before saving.")
    else:
        empty = [
            i + 1
            for i, s in enumerate(sentences_to_save)
            if not s["de"].strip() or not s["tr"].strip() or not s["en"].strip()
        ]
        if empty:
            st.warning(f"Sentence(s) {empty} have empty fields. Fill in all three languages.")
        else:
            try:
                pg_id = new_id("pg")
                db.upsert_page(
                    id=pg_id,
                    chapter_id=editing_chapter_id,
                    page_number=int(new_page_num),
                    sentences=sentences_to_save,
                    illustration_url=ill_url,
                )
                st.session_state["add_page_sentence_ids"] = []
                success_banner(f"✅ Page {new_page_num} saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")
