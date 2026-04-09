"""
Page: Audio Library
Upload audio files to Supabase Storage, browse by language, preview, and delete.
Requires a Supabase Storage bucket named 'audio' (create manually in the dashboard).
"""

import streamlit as st
from shared.ui import inject_css, page_header, tip, success_banner, add_navigation
from shared.constants import LANGUAGE_LABELS, LANGUAGES
from shared import database as db

st.set_page_config(page_title="Audio Library", page_icon="🎵", layout="wide")
inject_css()

add_navigation()

page_header("🎵 Audio Library", "Upload and manage audio files for the digital reader.")

# ── Upload section ───────────────────────────────────────────────
st.markdown("### Upload New Audio")
tip(
    "Supported formats: MP3, WAV, OGG, M4A. "
    "Files are stored in the <b>audio</b> Supabase Storage bucket. "
    "Make sure to create that bucket in the Supabase dashboard first."
)

upload_lang = st.selectbox(
    "Language *",
    options=LANGUAGES,
    format_func=lambda k: LANGUAGE_LABELS[k],
    key="upload_audio_lang",
)

uploaded_files = st.file_uploader(
    "Choose audio file(s)",
    type=["mp3", "wav", "ogg", "m4a"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected for language: {LANGUAGE_LABELS[upload_lang]}**")

    if st.button("⬆️ Upload All to Supabase", type="primary"):
        results = []
        errors  = []
        prog    = st.progress(0, text="Uploading…")
        total   = len(uploaded_files)

        for idx, f in enumerate(uploaded_files):
            try:
                row = db.upload_audio(
                    file_bytes=f.read(),
                    original_filename=f.name,
                    language=upload_lang,
                )
                results.append(row)
            except Exception as e:
                errors.append(f"{f.name}: {e}")
            prog.progress((idx + 1) / total, text=f"Uploading {f.name}…")

        prog.empty()

        if results:
            success_banner(f"✅ {len(results)} file(s) uploaded successfully.")
        if errors:
            for err in errors:
                st.error(err)
        st.rerun()

st.markdown("---")

# ── Browser ──────────────────────────────────────────────────────
st.markdown("### Saved Audio Files")

filter_lang = st.selectbox(
    "Filter by language",
    options=["All"] + LANGUAGES,
    format_func=lambda k: "All languages" if k == "All" else LANGUAGE_LABELS[k],
    key="browse_audio_lang",
)

try:
    audio_files = db.get_audio_files(
        language=None if filter_lang == "All" else filter_lang
    )

    if not audio_files:
        st.info("No audio files yet. Upload some above.")
    else:
        st.caption(f"{len(audio_files)} file(s) found.")

        search = st.text_input("🔍 Filter by filename", placeholder="e.g. bismillah")
        if search:
            audio_files = [a for a in audio_files if search.lower() in a["filename"].lower()]
            st.caption(f"{len(audio_files)} result(s)")

        for audio in audio_files:
            with st.expander(f"🎵 {audio['filename']} [{LANGUAGE_LABELS.get(audio['language'], audio['language'])}]"):
                col_prev, col_meta, col_act = st.columns([3, 3, 2])

                with col_prev:
                    st.audio(audio["public_url"])

                with col_meta:
                    size_kb = round(audio.get("size_bytes", 0) / 1024, 1)
                    st.markdown(f"**ID:** `{audio['id']}`")
                    st.markdown(f"**Language:** {LANGUAGE_LABELS.get(audio['language'], audio['language'])}")
                    st.markdown(f"**Size:** {size_kb} KB")
                    st.markdown(f"**Uploaded:** {audio['created_at'][:19].replace('T', ' ')}")

                with col_act:
                    if st.button("📋 Show URL", key=f"url_{audio['id']}"):
                        st.session_state[f"show_url_{audio['id']}"] = True

                    if st.session_state.get(f"show_url_{audio['id']}"):
                        st.code(audio["public_url"], language=None)

                    if st.button("🗑️ Delete", key=f"del_{audio['id']}"):
                        st.session_state[f"confirm_del_{audio['id']}"] = True

                    if st.session_state.get(f"confirm_del_{audio['id']}"):
                        st.warning("Delete this audio file?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Yes", key=f"yes_del_{audio['id']}", type="primary"):
                                try:
                                    db.delete_audio(audio["id"], audio["storage_path"])
                                    st.session_state.pop(f"confirm_del_{audio['id']}", None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Delete failed: {e}")
                        with c2:
                            if st.button("No", key=f"no_del_{audio['id']}"):
                                st.session_state.pop(f"confirm_del_{audio['id']}", None)
                                st.rerun()

except Exception as e:
    st.error(f"Could not load audio files: {e}")
