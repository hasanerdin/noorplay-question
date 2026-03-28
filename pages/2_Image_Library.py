"""
Page: Image Library
Upload images to Supabase Storage, browse and copy URLs, delete unused images.
"""

import streamlit as st
from shared.ui import inject_css, page_header, tip, success_banner, add_navigation
from shared import database as db

st.set_page_config(page_title="Image Library", page_icon="🖼️", layout="wide")
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────
add_navigation()

# ── Main ─────────────────────────────────────────────────────────
page_header("🖼️ Image Library", "Upload images for use in Image Matching activities.")

# ── Upload section ───────────────────────────────────────────────
st.markdown("### Upload New Image")
tip(
    "Supported formats: PNG, JPG, WEBP, GIF. "
    "Images are automatically converted to <b>WebP</b> (quality 85) before storage — "
    "smaller file size, Unity-friendly. Max recommended size: 2 MB."
)

uploaded_files = st.file_uploader(
    "Choose image(s)",
    type=["png", "jpg", "jpeg", "webp", "gif"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected.**")
    preview_cols = st.columns(min(len(uploaded_files), 4))
    for i, f in enumerate(uploaded_files):
        with preview_cols[i % 4]:
            st.image(f, caption=f.name, use_container_width=True)

    if st.button("⬆️ Upload All to Supabase", type="primary"):
        results    = []
        errors     = []
        prog       = st.progress(0, text="Uploading...")
        total      = len(uploaded_files)

        for idx, f in enumerate(uploaded_files):
            try:
                row = db.upload_image(
                    file_bytes        = f.read(),
                    original_filename = f.name,
                )
                results.append(row)
            except Exception as e:
                errors.append(f"{f.name}: {e}")
            prog.progress((idx + 1) / total, text=f"Uploading {f.name}…")

        prog.empty()

        if results:
            success_banner(f"✅ {len(results)} image(s) uploaded successfully.")
        if errors:
            for err in errors:
                st.error(err)
        st.rerun()

st.markdown("---")

# ── Image browser ────────────────────────────────────────────────
st.markdown("### Saved Images")

try:
    images = db.get_images(limit=100)

    if not images:
        st.info("No images yet. Upload some above.")
    else:
        st.caption(f"{len(images)} image(s) in the library.")

        # Search filter
        search = st.text_input("🔍 Filter by filename", placeholder="e.g. mosque")
        if search:
            images = [img for img in images if search.lower() in img["filename"].lower()]
            st.caption(f"{len(images)} result(s)")

        # Grid display — 4 per row
        cols_per_row = 4
        for row_start in range(0, len(images), cols_per_row):
            row_imgs = images[row_start : row_start + cols_per_row]
            cols     = st.columns(cols_per_row)

            for col, img in zip(cols, row_imgs):
                with col:
                    # Image preview
                    st.image(img["image_url"], use_container_width=True)

                    # Filename + size
                    size_kb = round(img.get("size_bytes", 0) / 1024, 1)
                    st.caption(f"**{img['filename']}**")
                    st.caption(f"{size_kb} KB · `{img['id']}`")

                    # Copy URL button (shows URL in a code block)
                    if st.button("📋 Show URL", key=f"url_{img['id']}"):
                        st.session_state[f"show_url_{img['id']}"] = True

                    if st.session_state.get(f"show_url_{img['id']}"):
                        st.code(img["image_url"], language=None)

                    # Delete
                    if st.button("🗑️ Delete", key=f"del_{img['id']}"):
                        st.session_state[f"confirm_del_{img['id']}"] = True

                    if st.session_state.get(f"confirm_del_{img['id']}"):
                        st.warning("Delete this image?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Yes", key=f"yes_del_{img['id']}", type="primary"):
                                try:
                                    db.delete_image(img["id"], img["storage_path"])
                                    st.session_state.pop(f"confirm_del_{img['id']}", None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Delete failed: {e}")
                        with c2:
                            if st.button("No", key=f"no_del_{img['id']}"):
                                st.session_state.pop(f"confirm_del_{img['id']}", None)
                                st.rerun()

        st.markdown("---")
        st.caption(
            "💡 To use an image in an activity, copy its URL and it will be saved "
            "automatically when you pick the image in the Add Activity form."
        )

except Exception as e:
    st.error(f"Could not load images: {e}")