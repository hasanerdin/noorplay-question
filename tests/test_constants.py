"""
Unit tests for shared/constants.py.
No database or network access required.
"""
from shared.constants import (
    AGE_GROUPS,
    ACTIVITY_ICONS,
    APP_ICON,
    APP_TITLE,
    APP_VERSION,
    DIFFICULTY_LEVELS,
    LANGUAGE_LABELS,
    LANGUAGE_PLACEHOLDERS,
    LANGUAGES,
    QUESTION_TYPES,
    TOPICS,
)


class TestLanguages:
    def test_languages_are_defined(self):
        assert LANGUAGES == ["de", "tr", "en"]

    def test_all_languages_have_labels(self):
        for lang in LANGUAGES:
            assert lang in LANGUAGE_LABELS, f"Missing label for language '{lang}'"

    def test_language_labels_have_flag_emoji(self):
        for lang, label in LANGUAGE_LABELS.items():
            # Flag emojis are above the basic ASCII range
            assert any(ord(c) > 127 for c in label), (
                f"Label for '{lang}' has no flag/emoji: {label!r}"
            )

    def test_no_extra_labels_without_language(self):
        for lang in LANGUAGE_LABELS:
            assert lang in LANGUAGES, (
                f"LANGUAGE_LABELS has '{lang}' but it is not in LANGUAGES"
            )

    def test_placeholders_cover_all_question_types(self):
        for q_type in QUESTION_TYPES:
            assert q_type in LANGUAGE_PLACEHOLDERS, (
                f"No placeholder entry for question type '{q_type}'"
            )

    def test_placeholders_cover_all_languages(self):
        for q_type, placeholders in LANGUAGE_PLACEHOLDERS.items():
            for lang in LANGUAGES:
                assert lang in placeholders, (
                    f"LANGUAGE_PLACEHOLDERS['{q_type}'] missing language '{lang}'"
                )


class TestTopics:
    def test_topics_not_empty(self):
        assert len(TOPICS) > 0

    def test_topics_are_non_empty_strings(self):
        for t in TOPICS:
            assert isinstance(t, str) and t.strip(), f"Invalid topic: {t!r}"

    def test_no_duplicate_topics(self):
        assert len(TOPICS) == len(set(TOPICS)), "Duplicate topic names found"


class TestAgeGroups:
    def test_age_groups_not_empty(self):
        assert len(AGE_GROUPS) > 0

    def test_age_groups_are_strings(self):
        for ag in AGE_GROUPS:
            assert isinstance(ag, str) and ag.strip(), f"Invalid age group: {ag!r}"


class TestDifficulty:
    def test_expected_difficulty_levels(self):
        assert set(DIFFICULTY_LEVELS) == {"Beginner", "Intermediate", "Advanced"}

    def test_no_duplicates(self):
        assert len(DIFFICULTY_LEVELS) == len(set(DIFFICULTY_LEVELS))


class TestQuestionTypes:
    def test_expected_types_present(self):
        expected = {
            "multiple_choice",
            "image_matching",
            "drag_drop_sorting",
            "story_dialogue",
        }
        assert set(QUESTION_TYPES.keys()) == expected

    def test_all_types_have_labels(self):
        for q_type, label in QUESTION_TYPES.items():
            assert isinstance(label, str) and label.strip(), (
                f"Empty label for type '{q_type}'"
            )

    def test_all_types_have_icons(self):
        for q_type in QUESTION_TYPES:
            assert q_type in ACTIVITY_ICONS, f"No icon for type '{q_type}'"

    def test_no_extra_icons_without_type(self):
        for icon_key in ACTIVITY_ICONS:
            assert icon_key in QUESTION_TYPES, (
                f"ACTIVITY_ICONS has '{icon_key}' but it is not in QUESTION_TYPES"
            )


class TestAppMeta:
    def test_app_title_set(self):
        assert APP_TITLE and isinstance(APP_TITLE, str)

    def test_app_icon_set(self):
        assert APP_ICON and isinstance(APP_ICON, str)

    def test_app_version_format(self):
        parts = APP_VERSION.split(".")
        assert len(parts) == 3 and all(p.isdigit() for p in parts), (
            f"APP_VERSION should be 'X.Y.Z', got {APP_VERSION!r}"
        )
