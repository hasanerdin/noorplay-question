"""
Database layer — all Supabase interactions live here.
Pages import these functions; they never call supabase directly.
"""

from __future__ import annotations
import uuid
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timezone


# ── Utilities ────────────────────────────────────────────────────

def new_id(prefix: str) -> str:
    """Generate a short random ID with the given prefix, e.g. 'book_3f9a1b2c'."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Connection ───────────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    """Return a cached Supabase client using credentials from st.secrets."""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


# ── Topics ───────────────────────────────────────────────────────

def get_topics() -> list[dict]:
    db = get_client()
    res = db.table("topics").select("*").order("name").execute()
    return res.data or []


def upsert_topic(topic_id: str, name: str) -> dict | None:
    db = get_client()
    row = {"id": topic_id, "name": name}
    res = db.table("topics").upsert(row).execute()
    return res.data[0] if res.data else None


# ── Activity Types ───────────────────────────────────────────────

def get_question_types() -> list[dict]:
    db = get_client()
    res = db.table("activity_types").select("*").order("label").execute()
    return res.data or []


# ── Questions ────────────────────────────────────────────────────

def insert_question(
    question_id: str,
    activity_type_key: str,
    topic_id: str,
    age_group: str,
    difficulty: str,
    languages: list[str],
    content: dict,
    audio_file: str | None = None,
    chapter_id: str | None = None,
) -> dict | None:
    db = get_client()
    row = {
        "id":                question_id,
        "activity_type_key": activity_type_key,
        "topic_id":          topic_id,
        "age_group":         age_group,
        "difficulty":        difficulty,
        "languages":         languages,
        "content":           content,
        "audio_file":        audio_file,
        "chapter_id":        chapter_id,
        "created_at":        datetime.now(timezone.utc).isoformat(),
    }
    res = db.table("questions").insert(row).execute()
    return res.data[0] if res.data else None


def get_questions(
    topic_ids: list[str] | None = None,
    type_keys: list[str] | None = None,
    age_group: str | None = None,
    difficulty: str | None = None,
    published_only: bool = False,
) -> list[dict]:
    db = get_client()
    q  = db.table("questions").select(
        "*, topics(name), activity_types(label)"
    ).order("created_at", desc=True)

    if topic_ids:
        q = q.in_("topic_id", topic_ids)
    if type_keys:
        q = q.in_("activity_type_key", type_keys)
    if age_group:
        q = q.eq("age_group", age_group)
    if difficulty:
        q = q.eq("difficulty", difficulty)
    if published_only:
        q = q.eq("is_published", True)

    return q.execute().data or []


def delete_question(question_id: str) -> None:
    db = get_client()
    db.table("questions").delete().eq("id", question_id).execute()


def get_question_by_id(question_id: str) -> dict | None:
    db = get_client()
    res = db.table("questions").select("*").eq("id", question_id).single().execute()
    return res.data


# ── Users ────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    db = get_client()
    res = db.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None


def upsert_user(user_id: str, email: str, display_name: str, role: str = "teacher") -> dict | None:
    db = get_client()
    row = {
        "id":           user_id,
        "email":        email,
        "display_name": display_name,
        "role":         role,
        "last_seen":    datetime.now(timezone.utc).isoformat(),
    }
    res = db.table("users").upsert(row).execute()
    return res.data[0] if res.data else None


def get_all_users() -> list[dict]:
    db = get_client()
    res = db.table("users").select("*").order("display_name").execute()
    return res.data or []


# ── Export helpers ───────────────────────────────────────────────

def export_questions_as_payload(questions: list[dict]) -> dict:
    """Convert DB rows into the Unity-ready JSON format."""
    return {
        "version":    "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total":      len(questions),
        "questions":  [
            {
                "id":                q["id"],
                "type":              q["activity_type_key"],
                "topic":             q.get("topics", {}).get("name", q["topic_id"]),
                "age_group":         q["age_group"],
                "difficulty":        q["difficulty"],
                "languages":         q["languages"],
                "audio_file":        q.get("audio_file"),
                "content":           q["content"],
                "created_at":        q["created_at"],
            }
            for q in questions
        ],
    }


# ── Storage ──────────────────────────────────────────────────────

BUCKET = "images"


def upload_image(
    file_bytes: bytes,
    original_filename: str,
    mime_type: str = "image/webp",
) -> dict | None:
    """
    Upload image bytes to Supabase Storage.
    Converts to WebP via Pillow before uploading (smaller size, Unity-friendly).
    Returns the saved image row from the images table, or None on failure.
    """
    import io
    import uuid
    from PIL import Image

    db = get_client()

    # ── Convert to WebP ──────────────────────────────────────────
    try:
        img      = Image.open(io.BytesIO(file_bytes))
        # Preserve transparency for PNG; otherwise use RGB
        if img.mode in ("RGBA", "LA"):
            output_format = "WEBP"
            mime_type     = "image/webp"
            img_converted = img.convert("RGBA")
        else:
            output_format = "WEBP"
            mime_type     = "image/webp"
            img_converted = img.convert("RGB")

        buf = io.BytesIO()
        img_converted.save(buf, format=output_format, quality=85, method=6)
        buf.seek(0)
        final_bytes = buf.read()
    except Exception as e:
        raise RuntimeError(f"Image conversion failed: {e}")

    # ── Build storage path ───────────────────────────────────────
    uid          = uuid.uuid4().hex[:12]
    base_name    = original_filename.rsplit(".", 1)[0]          # strip extension
    storage_path = f"images/{uid}_{base_name}.webp"

    # ── Upload to Storage bucket ─────────────────────────────────
    db.storage.from_(BUCKET).upload(
        path         = storage_path,
        file         = final_bytes,
        file_options = {"content-type": mime_type, "upsert": "false"},
    )

    # ── Get public URL ───────────────────────────────────────────
    public_url = db.storage.from_(BUCKET).get_public_url(storage_path)

    # ── Save metadata to images table ────────────────────────────
    image_id = f"img_{uuid.uuid4().hex[:8]}"
    row = {
        "id":           image_id,
        "filename":     original_filename,
        "storage_path": storage_path,
        "image_url":    public_url,
        "mime_type":    mime_type,
        "size_bytes":   len(final_bytes),
        "uploaded_at":  datetime.now(timezone.utc).isoformat(),
    }
    res = db.table("images").insert(row).execute()
    return res.data[0] if res.data else None


def get_images(limit: int = 50) -> list[dict]:
    """Return most recently uploaded images."""
    db  = get_client()
    res = db.table("images").select("*").order("uploaded_at", desc=True).limit(limit).execute()
    return res.data or []


def delete_image(image_id: str, storage_path: str) -> None:
    """Delete from both Storage bucket and images table."""
    db = get_client()
    db.storage.from_(BUCKET).remove([storage_path])
    db.table("images").delete().eq("id", image_id).execute()


def set_question_published(question_id: str, published: bool) -> None:
    get_client().table("questions").update({"is_published": published}).eq("id", question_id).execute()


# ── BOOKS ────────────────────────────────────────────────────────

def get_books() -> list[dict]:
    return get_client().table("books").select("*").order("sort_order").execute().data or []


def upsert_book(id: str, slug: str, title_i18n: dict, description_i18n: dict,
                cover_image_url: str = None, sort_order: int = 0) -> dict:
    row = dict(id=id, slug=slug, title_i18n=title_i18n,
               description_i18n=description_i18n,
               cover_image_url=cover_image_url, sort_order=sort_order)
    return get_client().table("books").upsert(row).execute().data[0]


def set_book_published(book_id: str, published: bool) -> None:
    get_client().table("books").update({"is_published": published}).eq("id", book_id).execute()


# ── CHAPTERS ─────────────────────────────────────────────────────

def get_chapters(book_id: str) -> list[dict]:
    return get_client().table("chapters").select("*").eq("book_id", book_id).order("sort_order").execute().data or []


def get_all_chapters() -> list[dict]:
    """Return all chapters across all books (used for chapter_id linking on questions)."""
    return get_client().table("chapters").select("*, books(title_i18n)").order("sort_order").execute().data or []


def upsert_chapter(id: str, book_id: str, title_i18n: dict, sort_order: int = 0) -> dict:
    row = dict(id=id, book_id=book_id, title_i18n=title_i18n, sort_order=sort_order)
    return get_client().table("chapters").upsert(row).execute().data[0]


def set_chapter_published(chapter_id: str, published: bool) -> None:
    get_client().table("chapters").update({"is_published": published}).eq("id", chapter_id).execute()


def delete_chapter(chapter_id: str) -> None:
    get_client().table("chapters").delete().eq("id", chapter_id).execute()


# ── PAGES ────────────────────────────────────────────────────────

def get_pages(chapter_id: str) -> list[dict]:
    return get_client().table("pages").select("*").eq("chapter_id", chapter_id).order("page_number").execute().data or []


def upsert_page(id: str, chapter_id: str, page_number: int,
                sentences: list[dict], illustration_url: str = None) -> dict:
    row = dict(id=id, chapter_id=chapter_id, page_number=page_number,
               sentences=sentences, illustration_url=illustration_url)
    return get_client().table("pages").upsert(row).execute().data[0]


def delete_page(page_id: str) -> None:
    get_client().table("pages").delete().eq("id", page_id).execute()


# ── WORD TIMINGS ─────────────────────────────────────────────────

def get_word_timings(page_id: str) -> list[dict]:
    return get_client().table("word_timings").select("*").eq("page_id", page_id).execute().data or []


def upsert_word_timings(page_id: str, language: str, timings: list[dict],
                        audio_url: str = None, tts_audio_url: str = None) -> dict:
    existing = get_client().table("word_timings")\
        .select("id").eq("page_id", page_id).eq("language", language).execute().data
    row_id = existing[0]["id"] if existing else new_id("wt")
    row = dict(id=row_id, page_id=page_id, language=language,
               timings=timings, audio_url=audio_url, tts_audio_url=tts_audio_url)
    return get_client().table("word_timings").upsert(row).execute().data[0]


# ── AUDIO FILES ──────────────────────────────────────────────────

def upload_audio(file_bytes: bytes, original_filename: str, language: str) -> dict:
    import time
    stem = original_filename.rsplit(".", 1)[0]
    ext  = original_filename.rsplit(".", 1)[-1].lower()
    storage_path = f"audio/{language}/{stem}_{int(time.time())}.{ext}"
    client = get_client()
    client.storage.from_("audio").upload(
        storage_path, file_bytes,
        file_options={"content-type": f"audio/{ext}", "upsert": "true"},
    )
    public_url = client.storage.from_("audio").get_public_url(storage_path)
    row_id = new_id("aud")
    row = dict(id=row_id, storage_path=storage_path, public_url=public_url,
               language=language, filename=original_filename,
               size_bytes=len(file_bytes))
    return client.table("audio_files").insert(row).execute().data[0]


def get_audio_files(language: str = None) -> list[dict]:
    q = get_client().table("audio_files").select("*").order("created_at", desc=True)
    if language:
        q = q.eq("language", language)
    return q.execute().data or []


def delete_audio(audio_id: str, storage_path: str) -> None:
    get_client().storage.from_("audio").remove([storage_path])
    get_client().table("audio_files").delete().eq("id", audio_id).execute()