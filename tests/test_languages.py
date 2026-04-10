"""
Unit tests — language constants must be complete and internally consistent.
No database or network access required.
"""
from shared.constants import LANGUAGE_LABELS, LANGUAGE_PLACEHOLDERS, LANGUAGES, QUESTION_TYPES


def test_german_in_languages():
    assert "de" in LANGUAGES


def test_turkish_in_languages():
    assert "tr" in LANGUAGES


def test_english_in_languages():
    assert "en" in LANGUAGES


def test_german_label_has_flag():
    assert "de" in LANGUAGE_LABELS
    assert "🇩🇪" in LANGUAGE_LABELS["de"]


def test_turkish_label_has_flag():
    assert "tr" in LANGUAGE_LABELS
    assert "🇹🇷" in LANGUAGE_LABELS["tr"]


def test_english_label_has_flag():
    assert "en" in LANGUAGE_LABELS
    assert "🇬🇧" in LANGUAGE_LABELS["en"]


def test_every_language_has_a_label():
    for lang in LANGUAGES:
        assert lang in LANGUAGE_LABELS, f"No label for language '{lang}'"


def test_no_orphan_labels():
    """Every key in LANGUAGE_LABELS must also appear in LANGUAGES."""
    for lang in LANGUAGE_LABELS:
        assert lang in LANGUAGES, (
            f"LANGUAGE_LABELS defines '{lang}' but it is not listed in LANGUAGES"
        )


def test_placeholder_languages_match_languages_constant():
    """Every placeholder entry must supply text for every language in LANGUAGES."""
    for activity_type, placeholders in LANGUAGE_PLACEHOLDERS.items():
        for lang in LANGUAGES:
            assert lang in placeholders, (
                f"LANGUAGE_PLACEHOLDERS['{activity_type}'] is missing '{lang}'"
            )


def test_placeholder_keys_are_valid_languages():
    """Placeholder dict must not reference languages outside LANGUAGES."""
    for activity_type, placeholders in LANGUAGE_PLACEHOLDERS.items():
        for lang in placeholders:
            assert lang in LANGUAGES, (
                f"LANGUAGE_PLACEHOLDERS['{activity_type}'] "
                f"uses unknown language '{lang}'"
            )


def test_all_question_types_have_placeholders():
    for q_type in QUESTION_TYPES:
        assert q_type in LANGUAGE_PLACEHOLDERS, (
            f"No LANGUAGE_PLACEHOLDERS entry for question type '{q_type}'"
        )
