def test_english_in_constants():
    from shared.constants import LANGUAGES, LANGUAGE_LABELS
    assert "en" in LANGUAGES, "English not added to LANGUAGES constant"
    assert "en" in LANGUAGE_LABELS, "English not added to LANGUAGE_LABELS"
    assert LANGUAGE_LABELS["en"] == "🇬🇧 English"
