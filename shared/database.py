"""
Database layer — all Supabase interactions live here.
Pages import these functions; they never call supabase directly.
"""

from __future__ import annotations
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timezone


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
        "created_at":        datetime.now(timezone.utc).isoformat(),
    }
    res = db.table("questions").insert(row).execute()
    return res.data[0] if res.data else None


def get_questions(
    topic_ids: list[str] | None = None,
    type_keys: list[str] | None = None,
    age_group: str | None = None,
    difficulty: str | None = None,
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