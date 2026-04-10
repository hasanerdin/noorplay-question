"""
Unit tests for pure utility functions in shared/database.py.
No database or network access required.
"""
import re
from datetime import datetime, timezone

from shared.database import export_questions_as_payload, new_id


class TestNewId:
    def test_format(self):
        result = new_id("book")
        assert re.match(r"^book_[0-9a-f]{8}$", result), (
            f"Unexpected format: {result!r}"
        )

    def test_prefix_respected(self):
        for prefix in ("book", "chap", "page", "wt", "img", "aud"):
            result = new_id(prefix)
            assert result.startswith(f"{prefix}_"), (
                f"Expected prefix '{prefix}_', got {result!r}"
            )

    def test_suffix_is_8_hex_chars(self):
        _, suffix = new_id("x").split("_", 1)
        assert re.match(r"^[0-9a-f]{8}$", suffix)

    def test_uniqueness(self):
        ids = {new_id("x") for _ in range(200)}
        assert len(ids) == 200, "new_id() generated duplicate IDs"


class TestExportPayload:
    """Tests for export_questions_as_payload() — no DB required."""

    def _make_question(self, langs=("de", "tr"), q_type="multiple_choice"):
        return {
            "id":                f"q_{q_type[:3]}_test",
            "activity_type_key": q_type,
            "topic_id":          "topic_test",
            "topics":            {"name": "Prayer (Salah)"},
            "age_group":         "6-8 years (pre-reader)",
            "difficulty":        "Beginner",
            "languages":         list(langs),
            "audio_file":        None,
            "content":           {lang: {"question": f"Q in {lang}"} for lang in langs},
            "created_at":        datetime.now(timezone.utc).isoformat(),
        }

    # ── Top-level structure ───────────────────────────────────────

    def test_top_level_keys_present(self):
        payload = export_questions_as_payload([])
        assert {"version", "exported_at", "total", "questions"}.issubset(payload.keys())

    def test_version_is_1_0(self):
        assert export_questions_as_payload([])["version"] == "1.0"

    def test_total_matches_input_length(self):
        questions = [self._make_question() for _ in range(3)]
        payload = export_questions_as_payload(questions)
        assert payload["total"] == 3
        assert len(payload["questions"]) == 3

    def test_empty_input_returns_empty_list(self):
        payload = export_questions_as_payload([])
        assert payload["total"] == 0
        assert payload["questions"] == []

    def test_exported_at_is_parseable_iso8601(self):
        payload = export_questions_as_payload([])
        datetime.fromisoformat(payload["exported_at"])  # raises if malformed

    # ── Per-question item structure ───────────────────────────────

    def test_question_item_required_keys(self):
        payload = export_questions_as_payload([self._make_question()])
        item = payload["questions"][0]
        required = {
            "id", "type", "topic", "age_group", "difficulty",
            "languages", "audio_file", "content", "created_at",
        }
        assert required.issubset(item.keys())

    def test_type_key_uses_activity_type_key(self):
        payload = export_questions_as_payload([self._make_question(q_type="image_matching")])
        assert payload["questions"][0]["type"] == "image_matching"

    def test_topic_name_resolved_from_join(self):
        """topics.name should be used when the join data is present."""
        payload = export_questions_as_payload([self._make_question()])
        assert payload["questions"][0]["topic"] == "Prayer (Salah)"

    def test_topic_fallback_to_topic_id(self):
        """When the topics join is missing, fall back to topic_id."""
        q = self._make_question()
        q.pop("topics")
        payload = export_questions_as_payload([q])
        assert payload["questions"][0]["topic"] == "topic_test"

    def test_audio_file_none_preserved(self):
        payload = export_questions_as_payload([self._make_question()])
        assert payload["questions"][0]["audio_file"] is None

    # ── Language contract ─────────────────────────────────────────

    def test_all_declared_languages_appear_in_content(self):
        for langs in [("de",), ("de", "tr"), ("de", "tr", "en")]:
            payload = export_questions_as_payload([self._make_question(langs=langs)])
            item = payload["questions"][0]
            for lang in langs:
                assert lang in item["content"], (
                    f"Language '{lang}' declared in languages[] "
                    f"but missing from content (langs={langs})"
                )

    def test_content_not_stripped(self):
        """export_questions_as_payload must not mutate or strip content."""
        q = self._make_question(langs=("de", "tr"))
        original_content = dict(q["content"])
        export_questions_as_payload([q])
        assert q["content"] == original_content
