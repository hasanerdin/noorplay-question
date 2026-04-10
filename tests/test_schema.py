"""
Integration tests — verify the Supabase schema matches what the app expects.
Auto-skipped when SUPABASE_URL / SUPABASE_KEY are absent.

Schema source of truth: supabase_schema.sql
"""
import pytest

# Every table created in supabase_schema.sql Section 2
REQUIRED_TABLES = [
    "users",
    "topics",
    "activity_types",
    "images",
    "audio_files",
    "books",
    "chapters",
    "pages",
    "word_timings",
    "questions",
]

# Seed data from supabase_schema.sql Section 3 ─────────────────────────────
SEEDED_TOPIC_IDS = [
    "topic_salah",
    "topic_sawm",
    "topic_wudu",
    "topic_quran",
    "topic_prophets",
    "topic_names",
    "topic_akhlaq",
    "topic_dua",
    "topic_holidays",
    "topic_other",          # present in DB seed but NOT in constants.TOPICS
]

SEEDED_TOPIC_NAMES = [
    "Prayer (Salah)",
    "Fasting (Sawm)",
    "Ablution (Wudu)",
    "Quran",
    "Prophets",
    "Names of Allah",
    "Ethics (Akhlaq)",
    "Supplication (Dua)",
    "Islamic Holidays",
    "Other",                # seeded in DB but absent from constants.TOPICS
]

SEEDED_ACTIVITY_TYPE_KEYS = [
    "multiple_choice",
    "image_matching",
    "drag_drop_sorting",
    "story_dialogue",
]

SEEDED_BOOK_ID   = "book_4magic"
SEEDED_BOOK_SLUG = "4-magic-words"


# ── Table existence ───────────────────────────────────────────────

@pytest.mark.parametrize("table", REQUIRED_TABLES)
def test_table_exists(requires_db, table):
    """Every table defined in supabase_schema.sql must be accessible."""
    from shared.database import get_client
    try:
        get_client().table(table).select("*").limit(1).execute()
    except Exception as exc:
        pytest.fail(f"Table '{table}' is inaccessible: {exc}")


# ── Column presence (one test per table) ─────────────────────────

def test_users_columns(requires_db):
    from shared.database import get_client
    cols = "id, email, display_name, role, last_seen, created_at"
    get_client().table("users").select(cols).limit(1).execute()


def test_topics_columns(requires_db):
    from shared.database import get_client
    get_client().table("topics").select("id, name, created_at").limit(1).execute()


def test_activity_types_columns(requires_db):
    from shared.database import get_client
    get_client().table("activity_types").select("key, label, icon, created_at").limit(1).execute()


def test_images_columns(requires_db):
    """images table uses uploaded_at (not created_at)."""
    from shared.database import get_client
    cols = "id, filename, storage_path, image_url, mime_type, size_bytes, uploaded_at"
    get_client().table("images").select(cols).limit(1).execute()


def test_audio_files_columns(requires_db):
    from shared.database import get_client
    cols = "id, storage_path, public_url, language, filename, size_bytes, duration_ms, created_at"
    get_client().table("audio_files").select(cols).limit(1).execute()


def test_books_columns(requires_db):
    from shared.database import get_client
    cols = "id, slug, title_i18n, description_i18n, cover_image_url, sort_order, is_published, created_at"
    get_client().table("books").select(cols).limit(1).execute()


def test_chapters_columns(requires_db):
    from shared.database import get_client
    cols = "id, book_id, title_i18n, sort_order, is_published, created_at"
    get_client().table("chapters").select(cols).limit(1).execute()


def test_pages_columns(requires_db):
    from shared.database import get_client
    cols = "id, chapter_id, page_number, sentences, illustration_url, created_at"
    get_client().table("pages").select(cols).limit(1).execute()


def test_word_timings_columns(requires_db):
    from shared.database import get_client
    cols = "id, page_id, language, timings, audio_url, tts_audio_url, generated_at"
    get_client().table("word_timings").select(cols).limit(1).execute()


def test_questions_columns(requires_db):
    from shared.database import get_client
    cols = (
        "id, activity_type_key, topic_id, chapter_id, age_group, difficulty, "
        "languages, content, audio_file, is_published, created_at"
    )
    get_client().table("questions").select(cols).limit(1).execute()


# ── Seed data ─────────────────────────────────────────────────────

@pytest.mark.parametrize("topic_id,topic_name", list(zip(SEEDED_TOPIC_IDS, SEEDED_TOPIC_NAMES)))
def test_seeded_topic_exists(requires_db, topic_id, topic_name):
    """All topics from the seed block must be in the database."""
    from shared.database import get_client
    res = get_client().table("topics").select("name").eq("id", topic_id).execute()
    assert res.data, f"Seeded topic '{topic_id}' not found"
    assert res.data[0]["name"] == topic_name, (
        f"Topic '{topic_id}' name mismatch: "
        f"expected {topic_name!r}, got {res.data[0]['name']!r}"
    )


@pytest.mark.parametrize("key", SEEDED_ACTIVITY_TYPE_KEYS)
def test_seeded_activity_type_exists(requires_db, key):
    """All activity types from the seed block must be in the database."""
    from shared.database import get_client
    res = get_client().table("activity_types").select("key").eq("key", key).execute()
    assert res.data, f"Seeded activity_type '{key}' not found in database"


def test_seeded_book_4magic_exists(requires_db):
    """The seed book 'book_4magic' must be present with the correct slug."""
    from shared.database import get_client
    res = (
        get_client()
        .table("books")
        .select("id, slug")
        .eq("id", SEEDED_BOOK_ID)
        .execute()
    )
    assert res.data, f"Seeded book '{SEEDED_BOOK_ID}' not found"
    assert res.data[0]["slug"] == SEEDED_BOOK_SLUG, (
        f"Book slug mismatch: expected {SEEDED_BOOK_SLUG!r}, got {res.data[0]['slug']!r}"
    )


# ── Schema / constant discrepancy ────────────────────────────────

def test_topics_constant_missing_other(requires_db):
    """
    The DB seed includes 'Other' (topic_other) but constants.TOPICS does not.
    This test documents that intentional gap — if 'Other' is added to constants,
    this test should be updated/removed.
    """
    from shared.constants import TOPICS
    from shared.database import get_client

    # Confirm 'Other' is seeded in DB
    res = get_client().table("topics").select("name").eq("id", "topic_other").execute()
    assert res.data, "topic_other should be seeded in the database"

    # Confirm it is intentionally absent from the UI constant
    assert "Other" not in TOPICS, (
        "'Other' was added to constants.TOPICS — remove this test and update "
        "test_seeded_topics_count_matches_constant if the gap is now closed"
    )


# ── Constraints ───────────────────────────────────────────────────

def test_users_role_constraint_rejects_invalid_role(requires_db):
    """users.role must only accept 'teacher', 'admin', or 'viewer' (check constraint)."""
    from shared.database import get_client, new_id
    import pytest

    with pytest.raises(Exception, match=r"(?i)(check|constraint|violat)"):
        get_client().table("users").insert({
            "id":           new_id("usr"),
            "email":        f"bad-role-{new_id('x')}@test.com",
            "display_name": "Bad Role User",
            "role":         "superadmin",   # not in ('teacher','admin','viewer')
        }).execute()


def test_word_timings_unique_constraint_enforced(requires_db):
    """Upserting twice for the same (page_id, language) must update, not duplicate."""
    from shared.database import (
        get_client, get_word_timings,
        new_id, upsert_book, upsert_chapter, upsert_page, upsert_word_timings,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")

    upsert_book(id=book_id, slug=f"schema-wt-uniq-{book_id[-6:]}",
                title_i18n={"de": "Schema Test"}, description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id, title_i18n={"de": "Kap"})
    upsert_page(id=page_id, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Test."}])

    t1 = [{"word": "Eins", "start_ms": 0, "end_ms": 300}]
    t2 = [{"word": "Zwei", "start_ms": 0, "end_ms": 400}]
    upsert_word_timings(page_id=page_id, language="de", timings=t1)
    upsert_word_timings(page_id=page_id, language="de", timings=t2)  # must update

    rows = get_word_timings(page_id)
    de_rows = [r for r in rows if r["language"] == "de"]
    assert len(de_rows) == 1, (
        f"Expected 1 word_timings row for (page_id, 'de'), got {len(de_rows)}. "
        "Unique constraint word_timings_page_language_unique may be missing."
    )
    assert de_rows[0]["timings"] == t2, "Upsert did not overwrite the existing timings row"

    get_client().table("books").delete().eq("id", book_id).execute()


def test_pages_unique_constraint_enforced(requires_db):
    """Two upserts with the same (chapter_id, page_number) must update, not duplicate."""
    from shared.database import (
        get_client, get_pages,
        new_id, upsert_book, upsert_chapter, upsert_page,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")

    upsert_book(id=book_id, slug=f"schema-pg-uniq-{book_id[-6:]}",
                title_i18n={"de": "Dup-Page Test"}, description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id, title_i18n={"de": "Kap"})

    upsert_page(id=page_id, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Erste Version."}])
    upsert_page(id=page_id, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Zweite Version."}])

    pages = get_pages(chapter_id)
    page_1_rows = [p for p in pages if p["page_number"] == 1]
    assert len(page_1_rows) == 1, (
        f"Expected 1 page with page_number=1, got {len(page_1_rows)}. "
        "Unique constraint pages_chapter_page_unique may be missing."
    )
    assert page_1_rows[0]["sentences"][0]["de"] == "Zweite Version."

    get_client().table("books").delete().eq("id", book_id).execute()


def test_questions_chapter_id_set_null_on_chapter_delete(requires_db):
    """
    questions.chapter_id has ON DELETE SET NULL — deleting the linked chapter
    must nullify chapter_id, not delete the question.
    """
    from shared.database import (
        get_client, delete_chapter, get_question_by_id, insert_question,
        new_id, upsert_book, upsert_chapter, upsert_topic,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    topic_id   = new_id("topic")
    q_id       = new_id("mc")

    upsert_book(id=book_id, slug=f"schema-q-null-{book_id[-6:]}",
                title_i18n={"de": "Test"}, description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id, title_i18n={"de": "Kap"})
    upsert_topic(topic_id, "Schema Test Topic")

    insert_question(
        question_id=q_id,
        activity_type_key="multiple_choice",
        topic_id=topic_id,
        age_group="Both groups",
        difficulty="Beginner",
        languages=["de"],
        content={"de": {"question": "Test?"}},
        chapter_id=chapter_id,
    )

    delete_chapter(chapter_id)

    question = get_question_by_id(q_id)
    assert question is not None, "Question was deleted instead of having chapter_id set NULL"
    assert question["chapter_id"] is None, (
        f"Expected chapter_id=None after chapter delete, got {question['chapter_id']!r}"
    )

    # Cleanup
    get_client().table("questions").delete().eq("id", q_id).execute()
    get_client().table("topics").delete().eq("id", topic_id).execute()
    get_client().table("books").delete().eq("id", book_id).execute()
