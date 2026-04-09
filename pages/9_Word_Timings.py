"""
Page: Word Timings
Generate word-level timestamps for book pages using the OpenAI Whisper API.
Requires OPENAI_API_KEY in st.secrets.
"""

import streamlit as st
from shared.ui import add_navigation, inject_css, page_header, tip, success_banner
from shared.constants import LANGUAGE_LABELS, LANGUAGES
from shared import database as db

st.set_page_config(page_title="Word Timings", page_icon="⏱️", layout="wide")
inject_css()

add_navigation()

page_header("⏱️ Word Timings", "Generate word-level timestamps for book pages via OpenAI Whisper.")

tip(
    "Select a page, assign audio files per language, then click "
    "<b>Generate timings with Whisper</b>. "
    "Requires <code>OPENAI_API_KEY</code> in your secrets."
)

# ── Cascading selectors: Book → Chapter → Page ───────────────────
st.markdown("### Select Page")

try:
    books = db.get_books()
except Exception as e:
    st.error(f"Could not load books: {e}")
    st.stop()

if not books:
    st.info("No books found. Run the migration SQL first.")
    st.stop()

book_labels = {
    b["id"]: (b.get("title_i18n", {}).get("en") or b["id"])
    for b in books
}
selected_book_id = st.selectbox(
    "Book",
    options=[b["id"] for b in books],
    format_func=lambda bid: book_labels[bid],
    key="wt_book",
)

try:
    chapters = db.get_chapters(selected_book_id)
except Exception as e:
    st.error(f"Could not load chapters: {e}")
    st.stop()

if not chapters:
    st.info("No chapters for this book yet.")
    st.stop()

ch_labels = {
    ch["id"]: (ch.get("title_i18n", {}).get("en") or ch["id"])
    for ch in chapters
}
selected_chapter_id = st.selectbox(
    "Chapter",
    options=[ch["id"] for ch in chapters],
    format_func=lambda cid: ch_labels[cid],
    key="wt_chapter",
)

try:
    pages = db.get_pages(selected_chapter_id)
except Exception as e:
    st.error(f"Could not load pages: {e}")
    st.stop()

if not pages:
    st.info("No pages for this chapter yet.")
    st.stop()

pg_labels = {pg["id"]: f"Page {pg['page_number']}" for pg in pages}
selected_page_id = st.selectbox(
    "Page",
    options=[pg["id"] for pg in pages],
    format_func=lambda pid: pg_labels[pid],
    key="wt_page",
)

selected_page = next((pg for pg in pages if pg["id"] == selected_page_id), None)
if not selected_page:
    st.stop()

st.markdown("---")

# ── Sentence reference ────────────────────────────────────────────
st.markdown("### Sentences on this page")
sentences = selected_page.get("sentences", [])
if sentences:
    for sent in sentences:
        st.markdown(
            f"- **DE:** {sent.get('de','—')} | "
            f"**TR:** {sent.get('tr','—')} | "
            f"**EN:** {sent.get('en','—')}"
        )
else:
    st.caption("No sentences on this page.")

st.markdown("---")

# ── Load existing word timings for this page ─────────────────────
try:
    existing_timings = db.get_word_timings(selected_page_id)
    timings_by_lang  = {wt["language"]: wt for wt in existing_timings}
except Exception as e:
    st.error(f"Could not load word timings: {e}")
    timings_by_lang = {}

# ── Load audio files for selectors ───────────────────────────────
try:
    all_audio = {lang: db.get_audio_files(language=lang) for lang in LANGUAGES}
except Exception as e:
    st.error(f"Could not load audio files: {e}")
    all_audio = {lang: [] for lang in LANGUAGES}

# ── Per-language section ──────────────────────────────────────────
st.markdown("### Generate Word Timings")

for lang in LANGUAGES:
    lang_label = LANGUAGE_LABELS[lang]
    with st.expander(f"{lang_label}", expanded=True):
        existing_wt = timings_by_lang.get(lang)

        # Show current audio URL if timings already exist
        if existing_wt:
            current_url = existing_wt.get("audio_url") or existing_wt.get("tts_audio_url")
            if current_url:
                st.markdown("**Current audio:**")
                st.audio(current_url)
            wt_count = len(existing_wt.get("timings", []))
            st.caption(f"{wt_count} word timing(s) already generated for this language.")

        # Audio selector
        audio_files_for_lang = all_audio.get(lang, [])
        audio_opts = {"— None —": None}
        for af in audio_files_for_lang:
            audio_opts[af["filename"]] = af

        selected_audio_label = st.selectbox(
            "Select audio file",
            options=list(audio_opts.keys()),
            key=f"wt_audio_{lang}_{selected_page_id}",
        )
        selected_audio = audio_opts[selected_audio_label]

        if selected_audio:
            st.audio(selected_audio["public_url"])

        # Generate button
        if st.button(f"🎙️ Generate timings with Whisper ({lang_label})", key=f"wt_gen_{lang}_{selected_page_id}"):
            if not selected_audio:
                st.warning("Please select an audio file first.")
            else:
                try:
                    import openai
                    import httpx

                    openai_key = st.secrets.get("OPENAI_API_KEY", "")
                    if not openai_key:
                        st.error("OPENAI_API_KEY is missing from secrets.")
                        st.stop()

                    audio_url   = selected_audio["public_url"]
                    audio_fname = selected_audio["filename"]
                    ext = audio_fname.rsplit(".", 1)[-1].lower() if "." in audio_fname else "mp3"
                    mime = f"audio/{ext}"

                    with st.spinner(f"Fetching audio and running Whisper for {lang_label}…"):
                        client      = openai.OpenAI(api_key=openai_key)
                        audio_bytes = httpx.get(audio_url).content
                        transcript  = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=(audio_fname, audio_bytes, mime),
                            response_format="verbose_json",
                            timestamp_granularities=["word"],
                        )

                    timings = [
                        {
                            "word":     w.word.strip(),
                            "start_ms": int(w.start * 1000),
                            "end_ms":   int(w.end * 1000),
                        }
                        for w in transcript.words
                    ]

                    db.upsert_word_timings(
                        page_id=selected_page_id,
                        language=lang,
                        timings=timings,
                        audio_url=audio_url,
                    )
                    st.session_state[f"wt_timings_{lang}_{selected_page_id}"] = timings
                    success_banner(f"✅ {len(timings)} word timings generated for {lang_label}.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Whisper call failed: {e}")

        # ── Preview / edit table ──────────────────────────────────
        # Show timings from session state (just generated) or from DB
        preview_timings = st.session_state.get(
            f"wt_timings_{lang}_{selected_page_id}",
            existing_wt.get("timings", []) if existing_wt else [],
        )

        if preview_timings:
            st.markdown(f"**Word timings preview ({len(preview_timings)} words)**")
            import pandas as pd
            df = pd.DataFrame(preview_timings)
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key=f"wt_edit_{lang}_{selected_page_id}",
            )
            if st.button(f"💾 Save edited timings ({lang_label})", key=f"wt_save_{lang}_{selected_page_id}"):
                try:
                    updated_timings = edited_df.to_dict("records")
                    audio_url_to_save = (
                        selected_audio["public_url"]
                        if selected_audio
                        else (existing_wt.get("audio_url") if existing_wt else None)
                    )
                    db.upsert_word_timings(
                        page_id=selected_page_id,
                        language=lang,
                        timings=updated_timings,
                        audio_url=audio_url_to_save,
                    )
                    success_banner(f"✅ Updated {len(updated_timings)} word timings for {lang_label}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Save failed: {e}")
