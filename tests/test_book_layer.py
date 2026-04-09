import uuid

def test_book_crud(sb, test_book_id):
    # Create
    sb.table("books").upsert({
        "id": test_book_id,
        "slug": "pytest-book",
        "title_i18n": {"de": "Testbuch", "tr": "Test Kitabı", "en": "Test Book"},
        "description_i18n": {"de": "Test", "tr": "Test", "en": "Test"},
        "sort_order": 99,
        "is_published": False,
    }).execute()
    row = sb.table("books").select("*").eq("id", test_book_id).execute().data[0]
    assert row["slug"] == "pytest-book"
    assert row["title_i18n"]["en"] == "Test Book"

def test_chapter_crud(sb, test_book_id, test_chapter_id):
    sb.table("chapters").upsert({
        "id": test_chapter_id,
        "book_id": test_book_id,
        "title_i18n": {"de": "Kapitel 1", "tr": "Bölüm 1", "en": "Chapter 1"},
        "sort_order": 1,
        "is_published": False,
    }).execute()
    rows = sb.table("chapters").select("*").eq("book_id", test_book_id).execute().data
    assert any(r["id"] == test_chapter_id for r in rows)

def test_page_crud(sb, test_chapter_id, test_page_id):
    sentences = [
        {"sentence_id": "s_001", "de": "Hallo Welt.", "tr": "Merhaba Dünya.", "en": "Hello World."},
        {"sentence_id": "s_002", "de": "Zweiter Satz.", "tr": "İkinci cümle.", "en": "Second sentence."},
    ]
    sb.table("pages").upsert({
        "id": test_page_id,
        "chapter_id": test_chapter_id,
        "page_number": 1,
        "sentences": sentences,
        "illustration_url": None,
    }).execute()
    row = sb.table("pages").select("*").eq("id", test_page_id).execute().data[0]
    assert len(row["sentences"]) == 2
    assert row["sentences"][0]["sentence_id"] == "s_001"
    assert row["sentences"][1]["en"] == "Second sentence."

def test_word_timings_crud(sb, test_page_id):
    wt_id = f"wt_pytest_{uuid.uuid4().hex[:6]}"
    timings = [
        {"word": "Hello", "start_ms": 0,   "end_ms": 400},
        {"word": "World", "start_ms": 450, "end_ms": 900},
    ]
    sb.table("word_timings").upsert({
        "id": wt_id,
        "page_id": test_page_id,
        "language": "en",
        "timings": timings,
        "audio_url": None,
        "tts_audio_url": None,
    }).execute()
    rows = sb.table("word_timings").select("*").eq("page_id", test_page_id).execute().data
    assert len(rows) == 1
    assert rows[0]["timings"][0]["word"] == "Hello"
    assert rows[0]["timings"][1]["end_ms"] == 900

def test_cleanup(sb, test_book_id):
    # Cascade delete cleans chapters, pages, word_timings automatically
    sb.table("books").delete().eq("id", test_book_id).execute()
    remaining = sb.table("books").select("*").eq("id", test_book_id).execute().data
    assert len(remaining) == 0
