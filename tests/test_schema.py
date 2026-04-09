def test_all_tables_exist(sb):
    required = ["books", "chapters", "pages", "word_timings",
                "audio_files", "questions", "topics", "activity_types"]
    for table in required:
        result = sb.table(table).select("*").limit(1).execute()
        assert result.data is not None, f"Table '{table}' missing or inaccessible"

def test_questions_has_new_columns(sb):
    # Insert a minimal question with the new fields and verify they save
    import uuid
    qid = f"q_pytest_{uuid.uuid4().hex[:6]}"
    sb.table("questions").insert({
        "id": qid,
        "activity_type_key": "multiple_choice",
        "topic_id": "topic_salah",
        "age_group": "6-8 years",
        "difficulty": "Beginner",
        "languages": ["de"],
        "content": {"de": {"question": "Test?", "options": ["A","B"], "correct_index": 0}},
        "audio_file": None,
        "is_published": False,
        "chapter_id": None,
    }).execute()
    row = sb.table("questions").select("*").eq("id", qid).execute().data[0]
    assert "is_published" in row
    assert "chapter_id" in row
    assert row["is_published"] == False
    sb.table("questions").delete().eq("id", qid).execute()
