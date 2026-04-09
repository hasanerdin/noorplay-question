"""
Page: Add Question
Language-tab based form: user picks languages → one tab per language.
Each tab has its own question content + audio file field.
All selected languages must be filled before saving.
"""

import streamlit as st
from shared.ui import add_navigation, inject_css, page_header, success_banner, tip
from shared.constants import ( AGE_GROUPS, DIFFICULTY_LEVELS,
    QUESTION_TYPES, LANGUAGE_LABELS, LANGUAGE_PLACEHOLDERS, LANGUAGES,
)
from shared import database as db
from shared.database import new_id

st.set_page_config(page_title="Add Question", page_icon="➕", layout="wide")
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────
add_navigation()


def ensure_topic(name: str) -> str:
    existing = db.get_topics()
    for t in existing:
        if t["name"] == name:
            return t["id"]
    tid = new_id("topic")
    db.upsert_topic(tid, name)
    return tid


def validate_filled(content: dict, selected_langs: list[str], required_keys: list[str]) -> list[str]:
    """Return list of error messages for any missing fields."""
    errors = []
    for lang in selected_langs:
        label = LANGUAGE_LABELS[lang]
        for key in required_keys:
            val = content.get(lang, {}).get(key, "")
            if isinstance(val, list):
                if not any(v.strip() for v in val):
                    errors.append(f"{label}: '{key}' is empty.")
            elif not str(val).strip():
                errors.append(f"{label}: '{key}' is empty.")
    return errors


# ── Main ─────────────────────────────────────────────────────────
page_header("➕ Add Question", "Select languages, fill in each tab, then save.")

# ── Load topics from DB ──────────────────────────────────────────
try:
    _db_topics   = db.get_topics()
    topic_names  = [t["name"] for t in _db_topics]
except Exception:
    topic_names  = []

if not topic_names:
    st.warning("No topics found. Please add topics in **Manage Topics** first.")
    st.stop()

# ── Top selectors ────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1: topic      = st.selectbox("Topic *",     topic_names)
with col2: age_group  = st.selectbox("Age group *", AGE_GROUPS)
with col3: difficulty = st.selectbox("Difficulty",  DIFFICULTY_LEVELS)

col4, col5 = st.columns([2, 2])
with col4:
    que_type = st.selectbox(
        "Question type",
        list(QUESTION_TYPES.keys()),
        format_func=lambda k: QUESTION_TYPES[k],
    )
with col5:
    selected_langs = st.multiselect(
        "Languages *",
        options=LANGUAGES,
        default=["de", "tr"],
        format_func=lambda k: LANGUAGE_LABELS[k],
    )

if not selected_langs:
    st.warning("Please select at least one language.")
    st.stop()

# ── Optional chapter link ─────────────────────────────────────────
try:
    _all_chapters = db.get_all_chapters()
    chapter_opts  = {"— None —": None}
    for ch in _all_chapters:
        book_title = (ch.get("books") or {}).get("title_i18n", {}).get("en", "Book")
        ch_title   = ch.get("title_i18n", {}).get("en", ch["id"])
        chapter_opts[f"{book_title} › {ch_title}"] = ch["id"]
    selected_ch_label = st.selectbox("Link to chapter (optional)", list(chapter_opts.keys()))
    selected_chapter_id = chapter_opts[selected_ch_label]
except Exception:
    selected_chapter_id = None

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# MULTIPLE CHOICE
# ════════════════════════════════════════════════════════════════
if que_type == "multiple_choice":
    st.markdown("### 🔤 Multiple Choice Question")
    tip("Fill in the question and all options for each language tab. Mark the correct option per language.")

    n_opt = st.number_input("Number of options", min_value=2, max_value=4, value=3, key="mc_n")
    n_opt = int(n_opt)

    # Build tabs
    tabs = st.tabs([LANGUAGE_LABELS[l] for l in selected_langs])
    mc_content   = {}
    mc_audio     = {}

    for tab, lang in zip(tabs, selected_langs):
        with tab:
            ph_q = LANGUAGE_PLACEHOLDERS["multiple_choice"].get(lang, "")
            ph_o = LANGUAGE_PLACEHOLDERS["option"].get(lang, "")

            question = st.text_area(
                "Question",
                placeholder=ph_q,
                key=f"mc_q_{lang}",
            )
            options = [
                st.text_input(f"Option {i+1}", placeholder=ph_o, key=f"mc_opt_{lang}_{i}")
                for i in range(n_opt)
            ]
            correct = st.selectbox(
                "Correct option",
                range(1, n_opt + 1),
                format_func=lambda x: f"Option {x}",
                key=f"mc_correct_{lang}",
            )
            audio = st.text_input(
                "Audio file (optional)",
                placeholder=f"prayer_q1_{lang}.mp3",
                key=f"mc_audio_{lang}",
            )
            mc_content[lang] = {
                "question":      question,
                "options":       options,
                "correct_index": correct - 1,
            }
            mc_audio[lang] = audio or None

    if st.button("💾 Save to Database", type="primary", key="mc_save"):
        errors = validate_filled(mc_content, selected_langs, ["question"])
        # Also check options
        for lang in selected_langs:
            empty_opts = [i+1 for i, o in enumerate(mc_content[lang]["options"]) if not o.strip()]
            if empty_opts:
                errors.append(f"{LANGUAGE_LABELS[lang]}: Option(s) {empty_opts} are empty.")
        if errors:
            for e in errors:
                st.warning(e)
        else:
            content = mc_content
            # Merge audio per language into content
            for lang in selected_langs:
                if mc_audio[lang]:
                    content[lang]["audio_file"] = mc_audio[lang]
            tid    = ensure_topic(topic)
            result = db.insert_question(
                new_id("mc"), "multiple_choice", tid,
                age_group, difficulty, selected_langs, content,
                chapter_id=selected_chapter_id,
            )
            if result:
                success_banner(f"✅ Saved! ID: <code>{result['id']}</code>")
                st.balloons()
            else:
                st.error("Save failed. Check Supabase connection.")


# ════════════════════════════════════════════════════════════════
# IMAGE MATCHING
# ════════════════════════════════════════════════════════════════
elif que_type == "image_matching":
    st.markdown("### 🖼️ Image Matching")
    tip(
        "Upload images directly here <b>or</b> pick from previously uploaded ones. "
        "Images are stored in Supabase Storage and shared across all languages."
    )

    n_pairs = st.number_input("Number of pairs", min_value=2, max_value=6, value=3, key="im_n")
    n_pairs = int(n_pairs)

    # ── Image selection — upload new or pick from library ────────
    st.markdown("#### Images (shared across all languages)")

    # Load existing images from library for picker
    try:
        library_images = db.get_images(limit=200)
        library_map    = {img["filename"]: img for img in library_images}
        library_opts   = ["— Upload new —"] + [img["filename"] for img in library_images]
    except Exception:
        library_images = []
        library_map    = {}
        library_opts   = ["— Upload new —"]

    image_urls  = []   # final URLs, one per pair slot
    image_names = []   # display names

    for i in range(n_pairs):
        st.markdown(f"**Image {i + 1}**")
        col_pick, col_prev = st.columns([3, 1])

        with col_pick:
            pick = st.selectbox(
                f"Pick from library or upload new",
                options=library_opts,
                key=f"im_pick_{i}",
                label_visibility="collapsed",
            )

            if pick == "— Upload new —":
                new_file = st.file_uploader(
                    f"Upload image {i + 1}",
                    type=["png", "jpg", "jpeg", "webp", "gif"],
                    key=f"im_upload_{i}",
                    label_visibility="collapsed",
                )
                if new_file is not None:
                    # Auto-upload on selection
                    upload_key = f"im_uploaded_row_{i}"
                    if upload_key not in st.session_state:
                        try:
                            with st.spinner(f"Uploading {new_file.name}…"):
                                row = db.upload_image(
                                    file_bytes        = new_file.read(),
                                    original_filename = new_file.name,
                                )
                            st.session_state[upload_key] = row
                            st.success(f"Uploaded: {new_file.name}")
                        except Exception as e:
                            st.error(f"Upload failed: {e}")
                            st.session_state[upload_key] = None

                    saved = st.session_state.get(upload_key)
                    if saved:
                        image_urls.append(saved["image_url"])
                        image_names.append(saved["filename"])
                    else:
                        image_urls.append("")
                        image_names.append("")
                else:
                    # Clear cached upload if user removed the file
                    st.session_state.pop(f"im_uploaded_row_{i}", None)
                    image_urls.append("")
                    image_names.append("")
            else:
                # Picked from library
                chosen = library_map.get(pick)
                if chosen:
                    image_urls.append(chosen["image_url"])
                    image_names.append(chosen["filename"])
                else:
                    image_urls.append("")
                    image_names.append("")

        with col_prev:
            url = image_urls[i] if i < len(image_urls) else ""
            if url:
                st.image(url, use_container_width=True)
            else:
                st.caption("No image")

        st.markdown("---")

    # ── Language tabs ────────────────────────────────────────────
    tabs = st.tabs([LANGUAGE_LABELS[l] for l in selected_langs])
    im_content = {}

    for tab, lang in zip(tabs, selected_langs):
        with tab:
            ph      = LANGUAGE_PLACEHOLDERS["image_matching"].get(lang, "")
            ph_inst = LANGUAGE_PLACEHOLDERS["instruction"].get(lang, "")

            instruction = st.text_input(
                "Instruction",
                placeholder=ph_inst,
                key=f"im_inst_{lang}",
            )
            labels = [
                st.text_input(
                    f"Label {i+1}" + (f" — {image_names[i]}" if i < len(image_names) and image_names[i] else ""),
                    placeholder=ph,
                    key=f"im_lbl_{lang}_{i}",
                )
                for i in range(n_pairs)
            ]
            audio = st.text_input(
                "Audio file (optional)",
                placeholder=f"matching_{lang}.mp3",
                key=f"im_audio_{lang}",
            )
            im_content[lang] = {
                "instruction": instruction,
                "labels":      labels,
                "audio_file":  audio or None,
            }

    if st.button("💾 Save to Database", type="primary", key="im_save"):
        errors = validate_filled(im_content, selected_langs, ["instruction"])
        for lang in selected_langs:
            empty_lbls = [i+1 for i, l in enumerate(im_content[lang]["labels"]) if not l.strip()]
            if empty_lbls:
                errors.append(f"{LANGUAGE_LABELS[lang]}: Label(s) {empty_lbls} are empty.")
        valid_pairs = [u for u in image_urls if u]
        if not valid_pairs:
            errors.append("Please select or upload at least one image.")
        if errors:
            for e in errors:
                st.warning(e)
        else:
            content = {}
            for lang in selected_langs:
                pairs = [
                    {
                        "image_url": image_urls[i],
                        "filename":  image_names[i],
                        "label":     im_content[lang]["labels"][i],
                    }
                    for i in range(n_pairs) if image_urls[i]
                ]
                content[lang] = {
                    "instruction": im_content[lang]["instruction"],
                    "pairs":       pairs,
                }
                if im_content[lang]["audio_file"]:
                    content[lang]["audio_file"] = im_content[lang]["audio_file"]

            tid    = ensure_topic(topic)
            result = db.insert_question(
                new_id("im"), "image_matching", tid,
                age_group, difficulty, selected_langs, content,
                chapter_id=selected_chapter_id,
            )
            if result:
                success_banner(f"✅ Saved! ID: <code>{result['id']}</code>")
                # Clear upload cache
                for i in range(n_pairs):
                    st.session_state.pop(f"im_uploaded_row_{i}", None)
                st.balloons()
            else:
                st.error("Save failed. Check Supabase connection.")


# ════════════════════════════════════════════════════════════════
# DRAG & DROP SORTING
# ════════════════════════════════════════════════════════════════
elif que_type == "drag_drop_sorting":
    st.markdown("### 🔀 Drag & Drop Sorting")
    tip("Enter steps in correct order for each language. Optionally add one image per step (shared across languages).")

    n_items = st.number_input("Number of steps", min_value=2, max_value=6, value=4, key="dd_n")
    n_items = int(n_items)

    has_images = st.checkbox("Include an image per step? (shared across languages)", key="dd_has_img")
    image_files = []
    if has_images:
        st.markdown("**Image file names** (in correct order)")
        img_cols = st.columns(min(n_items, 3))
        for i in range(n_items):
            with img_cols[i % 3]:
                img = st.text_input(f"Step {i+1} image", placeholder=f"step_{i+1}.png", key=f"dd_img_{i}")
                image_files.append(img)

    st.markdown("---")

    tabs = st.tabs([LANGUAGE_LABELS[l] for l in selected_langs])
    dd_content = {}

    for tab, lang in zip(tabs, selected_langs):
        with tab:
            ph      = LANGUAGE_PLACEHOLDERS["drag_drop_sorting"].get(lang, "")
            ph_inst = LANGUAGE_PLACEHOLDERS["instruction"].get(lang, "")

            instruction = st.text_input(
                "Instruction",
                placeholder=ph_inst,
                key=f"dd_inst_{lang}",
            )
            steps = [
                st.text_input(f"Step {i+1}", placeholder=ph, key=f"dd_step_{lang}_{i}")
                for i in range(n_items)
            ]
            audio = st.text_input(
                "Audio file (optional)",
                placeholder=f"sorting_{lang}.mp3",
                key=f"dd_audio_{lang}",
            )
            dd_content[lang] = {
                "instruction": instruction,
                "steps":       steps,
                "audio_file":  audio or None,
            }

    if st.button("💾 Save to Database", type="primary", key="dd_save"):
        errors = validate_filled(dd_content, selected_langs, ["instruction"])
        for lang in selected_langs:
            empty_steps = [i+1 for i, s in enumerate(dd_content[lang]["steps"]) if not s.strip()]
            if empty_steps:
                errors.append(f"{LANGUAGE_LABELS[lang]}: Step(s) {empty_steps} are empty.")
        if errors:
            for e in errors:
                st.warning(e)
        else:
            content = {}
            for lang in selected_langs:
                items = []
                for i in range(n_items):
                    item = {
                        "correct_order": i,
                        "text":          dd_content[lang]["steps"][i],
                    }
                    if has_images and i < len(image_files) and image_files[i]:
                        item["image_file"] = image_files[i]
                    items.append(item)
                content[lang] = {
                    "instruction": dd_content[lang]["instruction"],
                    "items":       items,
                }
                if dd_content[lang]["audio_file"]:
                    content[lang]["audio_file"] = dd_content[lang]["audio_file"]

            tid    = ensure_topic(topic)
            result = db.insert_question(
                new_id("dd"), "drag_drop_sorting", tid,
                age_group, difficulty, selected_langs, content,
                chapter_id=selected_chapter_id,
            )
            if result:
                success_banner(f"✅ Saved! ID: <code>{result['id']}</code>")
                st.balloons()
            else:
                st.error("Save failed. Check Supabase connection.")


# ════════════════════════════════════════════════════════════════
# STORY / DIALOGUE
# ════════════════════════════════════════════════════════════════
elif que_type == "story_dialogue":
    st.markdown("### 📖 Story / Dialogue")
    tip("Character names are shared across languages. Fill in the text for each language tab.")

    n_lines = st.number_input("Number of dialogue lines", min_value=1, max_value=12, value=4, key="sd_n")
    n_lines = int(n_lines)

    # Characters are language-independent
    st.markdown("**Characters** (one per line, shared across languages)")
    char_cols = st.columns(min(n_lines, 4))
    characters = []
    for i in range(n_lines):
        with char_cols[i % 4]:
            char = st.text_input(f"Line {i+1} character", placeholder="Ali", key=f"sd_char_{i}")
            characters.append(char)

    st.markdown("---")

    tabs = st.tabs([LANGUAGE_LABELS[l] for l in selected_langs])
    sd_content = {}

    for tab, lang in zip(tabs, selected_langs):
        with tab:
            ph_title = LANGUAGE_PLACEHOLDERS["title"].get(lang, "")
            ph_text  = LANGUAGE_PLACEHOLDERS["story_dialogue"].get(lang, "")

            title = st.text_input(
                "Story title",
                placeholder=ph_title,
                key=f"sd_title_{lang}",
            )
            lines = [
                st.text_area(
                    f"Line {i+1} — {characters[i] or '?'}",
                    placeholder=ph_text,
                    height=80,
                    key=f"sd_line_{lang}_{i}",
                )
                for i in range(n_lines)
            ]
            audio = st.text_input(
                "Audio file (optional)",
                placeholder=f"story_{lang}.mp3",
                key=f"sd_audio_{lang}",
            )
            sd_content[lang] = {
                "title":      title,
                "lines":      lines,
                "audio_file": audio or None,
            }

    if st.button("💾 Save to Database", type="primary", key="sd_save"):
        errors = validate_filled(sd_content, selected_langs, ["title"])
        for lang in selected_langs:
            empty_lines = [i+1 for i, l in enumerate(sd_content[lang]["lines"]) if not l.strip()]
            if empty_lines:
                errors.append(f"{LANGUAGE_LABELS[lang]}: Line(s) {empty_lines} are empty.")
        if errors:
            for e in errors:
                st.warning(e)
        else:
            content = {}
            for lang in selected_langs:
                content[lang] = {
                    "title": sd_content[lang]["title"],
                    "lines": [
                        {
                            "character": characters[i],
                            "text":      sd_content[lang]["lines"][i],
                        }
                        for i in range(n_lines)
                    ],
                }
                if sd_content[lang]["audio_file"]:
                    content[lang]["audio_file"] = sd_content[lang]["audio_file"]

            tid    = ensure_topic(topic)
            result = db.insert_question(
                new_id("sd"), "story_dialogue", tid,
                age_group, difficulty, selected_langs, content,
                chapter_id=selected_chapter_id,
            )
            if result:
                success_banner(f"✅ Saved! ID: <code>{result['id']}</code>")
                st.balloons()
            else:
                st.error("Save failed. Check Supabase connection.")