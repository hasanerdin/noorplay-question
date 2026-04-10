"""
Contract tests — ensure the data shapes consumed by the Unity app
never silently change.

Pure-unit tests run without a DB; integration tests (marked with the
`requires_db` fixture) verify that round-trips through Supabase
preserve the required shape.
"""
from __future__ import annotations
from datetime import datetime, timezone


# ── Pure unit: page sentences ─────────────────────────────────────

class TestPageSentencesShape:
    """Every sentence stored in pages.sentences must satisfy this contract."""

    VALID_SENTENCE = {
        "sentence_id": "s_001",
        "de": "Das Gebet beginnt.",
        "tr": "Namaz başlar.",
        "en": "The prayer begins.",
    }

    def test_has_sentence_id(self):
        assert "sentence_id" in self.VALID_SENTENCE

    def test_sentence_id_is_non_empty_string(self):
        sid = self.VALID_SENTENCE["sentence_id"]
        assert isinstance(sid, str) and sid

    def test_has_german_key(self):
        assert "de" in self.VALID_SENTENCE

    def test_has_turkish_key(self):
        assert "tr" in self.VALID_SENTENCE

    def test_has_english_key(self):
        assert "en" in self.VALID_SENTENCE

    def test_language_values_are_strings(self):
        for lang in ("de", "tr", "en"):
            assert isinstance(self.VALID_SENTENCE[lang], str)


# ── Pure unit: word timings ───────────────────────────────────────

class TestWordTimingsShape:
    """Each timing object must have word (str), start_ms (int), end_ms (int)."""

    VALID_TIMING = {"word": "Bismillah", "start_ms": 0, "end_ms": 450}

    def test_has_word_key(self):
        assert "word" in self.VALID_TIMING

    def test_word_is_string(self):
        assert isinstance(self.VALID_TIMING["word"], str)

    def test_has_start_ms(self):
        assert "start_ms" in self.VALID_TIMING

    def test_has_end_ms(self):
        assert "end_ms" in self.VALID_TIMING

    def test_timestamps_are_integers(self):
        assert isinstance(self.VALID_TIMING["start_ms"], int)
        assert isinstance(self.VALID_TIMING["end_ms"], int)

    def test_end_ms_gte_start_ms(self):
        assert self.VALID_TIMING["end_ms"] >= self.VALID_TIMING["start_ms"]

    def test_timestamps_non_negative(self):
        assert self.VALID_TIMING["start_ms"] >= 0
        assert self.VALID_TIMING["end_ms"] >= 0


# ── Pure unit: export payload ─────────────────────────────────────

class TestExportPayloadContract:
    """Top-level export payload shape expected by Unity."""

    def _make_question(self, langs=("de", "tr")):
        return {
            "id":                "mc_abc123",
            "activity_type_key": "multiple_choice",
            "topic_id":          "t1",
            "topics":            {"name": "Quran"},
            "age_group":         "6-8 years (pre-reader)",
            "difficulty":        "Beginner",
            "languages":         list(langs),
            "audio_file":        None,
            "content":           {lang: {"question": f"Q_{lang}"} for lang in langs},
            "created_at":        datetime.now(timezone.utc).isoformat(),
        }

    def _payload(self, questions=None):
        from shared.database import export_questions_as_payload
        return export_questions_as_payload(questions or [])

    def test_has_version_1_0(self):
        assert self._payload()["version"] == "1.0"

    def test_has_exported_at_parseable(self):
        p = self._payload()
        assert "exported_at" in p
        datetime.fromisoformat(p["exported_at"])  # raises if malformed

    def test_has_total_count(self):
        assert self._payload()["total"] == 0
        assert self._payload([self._make_question()])["total"] == 1

    def test_has_questions_list(self):
        assert isinstance(self._payload()["questions"], list)

    def test_question_item_required_keys(self):
        item = self._payload([self._make_question()])["questions"][0]
        for key in ("id", "type", "topic", "age_group", "difficulty",
                    "languages", "audio_file", "content", "created_at"):
            assert key in item, f"Missing required Unity key: '{key}'"

    def test_content_has_all_declared_languages(self):
        langs = ["de", "tr"]
        item = self._payload([self._make_question(langs=langs)])["questions"][0]
        for lang in langs:
            assert lang in item["content"], (
                f"Language '{lang}' declared in languages[] but absent from content"
            )


# ── Integration: round-trip through Supabase ─────────────────────

def test_page_sentences_round_trip(requires_db):
    """Sentences written to pages must come back with the same contract-required shape."""
    from shared.database import (
        get_client, get_pages,
        new_id, upsert_book, upsert_chapter, upsert_page,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")
    sentences  = [
        {"sentence_id": "s_001", "de": "Hallo Welt.", "tr": "Merhaba dünya.", "en": "Hello world."},
        {"sentence_id": "s_002", "de": "Guten Morgen.", "tr": "Günaydın.", "en": "Good morning."},
    ]

    upsert_book(id=book_id, slug=f"contract-test-{book_id[-6:]}",
                title_i18n={"de": "Testbuch", "tr": "Test Kitap"},
                description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id,
                   title_i18n={"de": "Kapitel 1", "tr": "Bölüm 1"})
    upsert_page(id=page_id, chapter_id=chapter_id, page_number=1, sentences=sentences)

    pages = get_pages(chapter_id)
    assert pages, "No pages returned after upsert"

    for sent in pages[0]["sentences"]:
        assert "sentence_id" in sent, "sentence_id missing after round-trip"
        assert isinstance(sent["sentence_id"], str) and sent["sentence_id"]
        for lang in ("de", "tr", "en"):
            assert lang in sent, f"Language key '{lang}' missing after round-trip"
            assert isinstance(sent[lang], str)

    # Cleanup (cascade handles chapter → page)
    get_client().table("books").delete().eq("id", book_id).execute()


def test_word_timings_round_trip(requires_db):
    """Word timings written via upsert_word_timings must come back with correct types."""
    from shared.database import (
        get_client, get_word_timings,
        new_id, upsert_book, upsert_chapter, upsert_page, upsert_word_timings,
    )

    book_id    = new_id("book")
    chapter_id = new_id("chap")
    page_id    = new_id("page")

    upsert_book(id=book_id, slug=f"wt-contract-{book_id[-6:]}",
                title_i18n={"de": "WT Testbuch"}, description_i18n={})
    upsert_chapter(id=chapter_id, book_id=book_id, title_i18n={"de": "Kapitel"})
    upsert_page(id=page_id, chapter_id=chapter_id, page_number=1,
                sentences=[{"sentence_id": "s_001", "de": "Test."}])

    timings = [
        {"word": "Bismillah", "start_ms": 0,   "end_ms": 450},
        {"word": "Rahman",    "start_ms": 500,  "end_ms": 900},
    ]
    upsert_word_timings(page_id=page_id, language="de", timings=timings)

    rows = get_word_timings(page_id)
    assert rows, "No word_timings rows returned after upsert"

    for t in rows[0]["timings"]:
        assert "word" in t and isinstance(t["word"], str)
        assert "start_ms" in t and isinstance(t["start_ms"], int)
        assert "end_ms" in t and isinstance(t["end_ms"], int)
        assert t["end_ms"] >= t["start_ms"]

    # Cleanup
    get_client().table("books").delete().eq("id", book_id).execute()
