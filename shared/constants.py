"""
Shared constants used across all pages.
Only question/answer text content is in DE/TR/EN — everything else is in English.
"""

TOPICS: list[str] = [
    "Prayer (Salah)",
    "Fasting (Sawm)",
    "Ablution (Wudu)",
    "Quran",
    "Prophets",
    "Names of Allah",
    "Ethics (Akhlaq)",
    "Supplication (Dua)",
    "Islamic Holidays",
]

AGE_GROUPS: list[str] = [
    "6-8 years (pre-reader)",
    "8-10 years (reader)",
    "Both groups",
]

DIFFICULTY_LEVELS: list[str] = [
    "Beginner",
    "Intermediate",
    "Advanced",
]

LANGUAGES: list[str] = ["de", "tr", "en"]

LANGUAGE_LABELS: dict[str, str] = {
    "de": "🇩🇪 German",
    "tr": "🇹🇷 Turkish",
    "en": "🇬🇧 English",
}

# Placeholder texts per activity type per language
LANGUAGE_PLACEHOLDERS: dict[str, dict[str, str]] = {
    "multiple_choice": {
        "de": "Wie viele Gebete gibt es am Tag?",
        "tr": "Günde kaç vakit namaz vardır?",
        "en": "How many daily prayers are there?",
    },
    "option": {
        "de": "Antwort auf Deutsch...",
        "tr": "Türkçe cevap...",
        "en": "Answer in English...",
    },
    "drag_drop_sorting": {
        "de": "Schritt auf Deutsch...",
        "tr": "Türkçe adım...",
        "en": "Step in English...",
    },
    "image_matching": {
        "de": "Beschriftung auf Deutsch...",
        "tr": "Türkçe etiket...",
        "en": "Label in English...",
    },
    "story_dialogue": {
        "de": "Auf Deutsch schreiben...",
        "tr": "Türkçe yaz...",
        "en": "Write in English...",
    },
    "instruction": {
        "de": "Anweisung auf Deutsch...",
        "tr": "Türkçe talimat...",
        "en": "Instruction in English...",
    },
    "title": {
        "de": "Titel auf Deutsch...",
        "tr": "Türkçe başlık...",
        "en": "Title in English...",
    },
}

# Maps DB/JSON type key → human-readable label
QUESTION_TYPES: dict[str, str] = {
    "multiple_choice":   "Multiple Choice Question",
    "image_matching":    "Image Matching",
    "drag_drop_sorting": "Drag & Drop Sorting",
    "story_dialogue":    "Story / Dialogue",
}

ACTIVITY_ICONS: dict[str, str] = {
    "multiple_choice":   "🔤",
    "image_matching":    "🖼️",
    "drag_drop_sorting": "🔀",
    "story_dialogue":    "📖",
}

APP_TITLE    = "Islamic Education - Content Editor"
APP_ICON     = "🕌"
APP_VERSION  = "1.0.0"