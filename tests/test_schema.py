"""
Integration tests — verify the Supabase schema matches what the app expects.
Auto-skipped when SUPABASE_URL / SUPABASE_KEY are absent.
"""
import pytest

REQUIRED_TABLES = [
    "books",
    "chapters",
    "pages",
    "word_timings",
    "audio_files",
    "questions",
    "topics",
    "activity_types",
]


@pytest.mark.parametrize("table", REQUIRED_TABLES)
def test_table_exists(requires_db, table):
    """Every required table must be accessible via the service-role client."""
    from shared.database import get_client
    try:
        get_client().table(table).select("*").limit(1).execute()
    except Exception as exc:
        pytest.fail(f"Table '{table}' is inaccessible: {exc}")


def test_questions_has_is_published(requires_db):
    from shared.database import get_client
    get_client().table("questions").select("is_published").limit(1).execute()


def test_questions_has_chapter_id(requires_db):
    from shared.database import get_client
    get_client().table("questions").select("chapter_id").limit(1).execute()


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


def test_audio_files_columns(requires_db):
    from shared.database import get_client
    cols = "id, storage_path, public_url, language, filename, size_bytes, duration_ms, created_at"
    get_client().table("audio_files").select(cols).limit(1).execute()


def test_word_timings_unique_constraint_enforced(requires_db):
    """Upserting twice for the same (page_id, language) must update, not insert a duplicate."""
    from shared.database import (
        get_client, get_word_timings,
        new_id, upsert_book, upsert_chapter, upsert_page, upsert_word_timings,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")

    upsert_book(id=book_id, slug=f"schema-unique-{book_id[-6:]}",
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
        "Unique constraint may be missing or upsert is broken."
    )
    assert de_rows[0]["timings"] == t2, "Upsert did not overwrite the existing timings row"

    # Cleanup (cascade handles chapters → pages → word_timings)
    get_client().table("books").delete().eq("id", book_id).execute()


def test_pages_unique_constraint_enforced(requires_db):
    """Two pages with the same (chapter_id, page_number) must conflict (upsert updates)."""
    from shared.database import (
        get_client, get_pages,
        new_id, upsert_book, upsert_chapter, upsert_page,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id_a  = new_id("page")
    page_id_b  = new_id("page")

    upsert_book(id=book_id, slug=f"schema-page-uniq-{book_id[-6:]}",
                title_i18n={"de": "Dup-Page Test"}, description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id, title_i18n={"de": "Kap"})

    # First insert
    upsert_page(id=page_id_a, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Erste Version."}])
    # Second insert with the same page_number — should upsert on (chapter_id, page_number)
    upsert_page(id=page_id_a, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Zweite Version."}])

    pages = get_pages(chapter_id)
    page_1_rows = [p for p in pages if p["page_number"] == 1]
    assert len(page_1_rows) == 1, (
        f"Expected 1 page with page_number=1, got {len(page_1_rows)}"
    )
    assert page_1_rows[0]["sentences"][0]["de"] == "Zweite Version."

    # Cleanup
    get_client().table("books").delete().eq("id", book_id).execute()
