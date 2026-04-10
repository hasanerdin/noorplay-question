"""
Integration tests — CRUD operations for books, chapters, pages, and word_timings.
Auto-skipped when SUPABASE_URL / SUPABASE_KEY are absent.

All tests in this module share a single book/chapter/page hierarchy
that is created once (module scope) and torn down by cascade-deleting
the book at the end.  Tests that need their own isolated data create
and clean up independently.
"""
from __future__ import annotations

import pytest

from shared.database import (
    delete_chapter,
    get_books,
    get_chapters,
    get_client,
    get_pages,
    get_word_timings,
    new_id,
    set_book_published,
    set_chapter_published,
    upsert_book,
    upsert_chapter,
    upsert_page,
    upsert_word_timings,
)


# ── Shared hierarchy fixture ──────────────────────────────────────

@pytest.fixture(scope="module")
def hierarchy(requires_db):
    """
    Create book → chapter → page → word_timings once per module.
    Yields a dict of IDs; cascade-deletes the book on teardown.
    """
    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")

    upsert_book(
        id=book_id,
        slug=f"integration-test-{book_id[-6:]}",
        title_i18n={"de": "Integrations-Testbuch", "tr": "Entegrasyon Test Kitabı"},
        description_i18n={"de": "Nur für Tests.", "tr": "Sadece testler için."},
        sort_order=99,
    )
    upsert_chapter(
        id=chapter_id,
        book_id=book_id,
        title_i18n={"de": "Kapitel 1", "tr": "Bölüm 1"},
        sort_order=1,
    )
    upsert_page(
        id=page_id,
        chapter_id=chapter_id,
        page_number=1,
        sentences=[
            {"sentence_id": "s_001", "de": "Hallo.", "tr": "Merhaba.", "en": "Hello."},
        ],
    )
    upsert_word_timings(
        page_id=page_id,
        language="de",
        timings=[{"word": "Hallo", "start_ms": 0, "end_ms": 300}],
    )

    yield {"book_id": book_id, "chapter_id": chapter_id, "page_id": page_id}

    # Teardown — cascade: book → chapters → pages → word_timings
    get_client().table("books").delete().eq("id", book_id).execute()


# ── Book tests ────────────────────────────────────────────────────

def test_book_appears_in_get_books(hierarchy):
    ids = [b["id"] for b in get_books()]
    assert hierarchy["book_id"] in ids


def test_book_title_i18n_saved(hierarchy):
    book = next(b for b in get_books() if b["id"] == hierarchy["book_id"])
    assert book["title_i18n"]["de"] == "Integrations-Testbuch"
    assert book["title_i18n"]["tr"] == "Entegrasyon Test Kitabı"


def test_book_description_i18n_saved(hierarchy):
    book = next(b for b in get_books() if b["id"] == hierarchy["book_id"])
    assert book["description_i18n"]["de"] == "Nur für Tests."


def test_book_is_not_published_by_default(hierarchy):
    book = next(b for b in get_books() if b["id"] == hierarchy["book_id"])
    assert book["is_published"] is False


def test_set_book_published_true(hierarchy):
    set_book_published(hierarchy["book_id"], True)
    book = next(b for b in get_books() if b["id"] == hierarchy["book_id"])
    assert book["is_published"] is True
    # Reset so other tests see is_published=False
    set_book_published(hierarchy["book_id"], False)


def test_book_slug_saved(hierarchy):
    book = next(b for b in get_books() if b["id"] == hierarchy["book_id"])
    assert book["slug"].startswith("integration-test-")


# ── Chapter tests ─────────────────────────────────────────────────

def test_chapter_appears_under_book(hierarchy):
    ids = [c["id"] for c in get_chapters(hierarchy["book_id"])]
    assert hierarchy["chapter_id"] in ids


def test_chapter_book_id_link(hierarchy):
    chapter = next(
        c for c in get_chapters(hierarchy["book_id"])
        if c["id"] == hierarchy["chapter_id"]
    )
    assert chapter["book_id"] == hierarchy["book_id"]


def test_chapter_title_i18n_saved(hierarchy):
    chapter = next(
        c for c in get_chapters(hierarchy["book_id"])
        if c["id"] == hierarchy["chapter_id"]
    )
    assert chapter["title_i18n"]["de"] == "Kapitel 1"
    assert chapter["title_i18n"]["tr"] == "Bölüm 1"


def test_chapter_is_not_published_by_default(hierarchy):
    chapter = next(
        c for c in get_chapters(hierarchy["book_id"])
        if c["id"] == hierarchy["chapter_id"]
    )
    assert chapter["is_published"] is False


def test_set_chapter_published(hierarchy):
    set_chapter_published(hierarchy["chapter_id"], True)
    chapter = next(
        c for c in get_chapters(hierarchy["book_id"])
        if c["id"] == hierarchy["chapter_id"]
    )
    assert chapter["is_published"] is True
    set_chapter_published(hierarchy["chapter_id"], False)


# ── Page tests ────────────────────────────────────────────────────

def test_page_appears_under_chapter(hierarchy):
    ids = [p["id"] for p in get_pages(hierarchy["chapter_id"])]
    assert hierarchy["page_id"] in ids


def test_page_number_saved(hierarchy):
    page = next(
        p for p in get_pages(hierarchy["chapter_id"])
        if p["id"] == hierarchy["page_id"]
    )
    assert page["page_number"] == 1


def test_page_sentences_is_list(hierarchy):
    page = next(
        p for p in get_pages(hierarchy["chapter_id"])
        if p["id"] == hierarchy["page_id"]
    )
    assert isinstance(page["sentences"], list)
    assert len(page["sentences"]) > 0


def test_page_sentences_have_sentence_id(hierarchy):
    page = next(
        p for p in get_pages(hierarchy["chapter_id"])
        if p["id"] == hierarchy["page_id"]
    )
    for sent in page["sentences"]:
        assert "sentence_id" in sent, "sentence_id missing from stored sentence"
        assert isinstance(sent["sentence_id"], str) and sent["sentence_id"]


def test_page_sentences_have_language_keys(hierarchy):
    page = next(
        p for p in get_pages(hierarchy["chapter_id"])
        if p["id"] == hierarchy["page_id"]
    )
    for sent in page["sentences"]:
        for lang in ("de", "tr", "en"):
            assert lang in sent, f"Language key '{lang}' missing from stored sentence"


# ── Word timings tests ────────────────────────────────────────────

def test_word_timings_created(hierarchy):
    assert get_word_timings(hierarchy["page_id"]), "No word_timings rows returned"


def test_word_timings_language_saved(hierarchy):
    languages = [r["language"] for r in get_word_timings(hierarchy["page_id"])]
    assert "de" in languages


def test_word_timings_data_shape(hierarchy):
    rows = get_word_timings(hierarchy["page_id"])
    de_row = next(r for r in rows if r["language"] == "de")
    assert isinstance(de_row["timings"], list)
    for timing in de_row["timings"]:
        assert "word" in timing and isinstance(timing["word"], str)
        assert "start_ms" in timing and isinstance(timing["start_ms"], int)
        assert "end_ms" in timing and isinstance(timing["end_ms"], int)
        assert timing["end_ms"] >= timing["start_ms"]


def test_upsert_word_timings_updates_existing(hierarchy):
    """Calling upsert twice for the same (page_id, language) must update, not duplicate."""
    page_id = hierarchy["page_id"]
    new_timings = [{"word": "Updated", "start_ms": 0, "end_ms": 999}]
    upsert_word_timings(page_id=page_id, language="de", timings=new_timings)

    rows = get_word_timings(page_id)
    de_rows = [r for r in rows if r["language"] == "de"]
    assert len(de_rows) == 1, "Upsert created a duplicate row instead of updating"
    assert de_rows[0]["timings"] == new_timings


# ── Cascade delete ────────────────────────────────────────────────

def test_cascade_delete_chapter_removes_pages_and_timings(requires_db):
    """Deleting a chapter must cascade-delete its pages and their word_timings."""
    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")

    upsert_book(id=book_id, slug=f"cascade-test-{book_id[-6:]}",
                title_i18n={"de": "Cascade Test"}, description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id, title_i18n={"de": "Kap"})
    upsert_page(id=page_id, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Test."}])
    upsert_word_timings(page_id=page_id, language="de",
                        timings=[{"word": "Test", "start_ms": 0, "end_ms": 100}])

    delete_chapter(chapter_id)

    assert get_pages(chapter_id) == [], (
        "Pages were not cascade-deleted when chapter was deleted"
    )
    assert get_word_timings(page_id) == [], (
        "Word timings were not cascade-deleted when chapter was deleted"
    )

    # Cleanup remaining book row
    get_client().table("books").delete().eq("id", book_id).execute()
