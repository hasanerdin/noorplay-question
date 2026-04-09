import pytest

def test_page_sentences_shape(sb, test_page_id):
    """Unity expects sentences as a list of objects with sentence_id + language keys."""
    # Re-create the test page (assumes test_book_layer ran first or use a known page)
    rows = sb.table("pages").select("sentences").limit(1).execute().data
    if not rows:
        pytest.skip("No pages in database yet")
    sentences = rows[0]["sentences"]
    assert isinstance(sentences, list)
    for s in sentences:
        assert "sentence_id" in s, "Missing sentence_id — Unity cannot sync word timings"
        assert "de" in s or "tr" in s or "en" in s, "No language content in sentence"

def test_word_timings_shape(sb):
    """Unity expects timings as [{word, start_ms, end_ms}]."""
    rows = sb.table("word_timings").select("timings").limit(1).execute().data
    if not rows:
        pytest.skip("No word timings yet")
    for t in rows[0]["timings"]:
        assert "word"     in t, "Missing 'word' key"
        assert "start_ms" in t, "Missing 'start_ms' — Unity highlight will break"
        assert "end_ms"   in t, "Missing 'end_ms' — Unity highlight will break"
        assert isinstance(t["start_ms"], int), "start_ms must be int (milliseconds)"

def test_questions_export_shape(sb):
    """Unity expects questions with content keyed by language code."""
    rows = sb.table("questions").select("content, languages").limit(5).execute().data
    for row in rows:
        for lang in row["languages"]:
            assert lang in row["content"], \
                f"Language '{lang}' declared but missing from content JSON"
