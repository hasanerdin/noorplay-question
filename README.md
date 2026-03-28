# 🕌 Noor Play – Content Editor

A Streamlit app for preparing Islamic lesson content. The teacher fills in the form, clicks send, and the JSON file lands in the developer's inbox automatically.

---

## 🚀 Deploy to Streamlit Cloud (Free, ~5 minutes)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "initial version"
git remote add origin https://github.com/YOUR_USERNAME/islam-editor.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click **New app** → select your repo → set `app.py` as the main file → **Deploy**

A shareable URL will be ready within a few minutes.

---

## 📁 JSON Output Format

All keys are in English. Only the `de` / `tr` content fields contain German and Turkish text.

```json
{
  "topic_id": "topic_a3f2b1c4",
  "topic_name": "Daily Prayer Times",
  "age_group": "6–8 years (pre-reader)",
  "difficulty": "Beginner",
  "languages": ["de", "tr"],
  "created_at": "2025-01-15T14:30:00",
  "question_count": 2,
  "questions": [
    {
      "id": "mc_d4e5f6a7",
      "type": "multiple_choice",
      "audio": "prayer_q1.mp3",
      "content": {
        "de": {
          "question": "Wie viele Gebete gibt es am Tag?",
          "options": ["3", "5", "7"],
          "correct_index": 1
        },
        "tr": {
          "question": "Günde kaç vakit namaz vardır?",
          "options": ["3", "5", "7"],
          "correct_index": 1
        }
      }
    },
    {
      "id": "dd_a1b2c3d4",
      "type": "drag_drop_sorting",
      "instruction": {
        "de": "Bringe die Schritte in die richtige Reihenfolge!",
        "tr": "Adımları doğru sıraya koy!"
      },
      "items": [
        {
          "correct_order": 0,
          "text": { "de": "Intention (Niyyah)", "tr": "Niyet" },
          "image_file": "step_1.png"
        },
        {
          "correct_order": 1,
          "text": { "de": "Takbir sprechen", "tr": "Tekbir getir" },
          "image_file": "step_2.png"
        }
      ]
    },
    {
      "id": "im_f1e2d3c4",
      "type": "image_matching",
      "instruction": {
        "de": "Ordne die Bilder den Begriffen zu!",
        "tr": "Resimleri kavramlarla eşleştir!"
      },
      "pairs": [
        {
          "image_file": "fajr.png",
          "label": { "de": "Morgengebet", "tr": "Sabah namazı" }
        },
        {
          "image_file": "maghrib.png",
          "label": { "de": "Abendgebet", "tr": "Akşam namazı" }
        }
      ]
    },
    {
      "id": "sd_b2c3d4e5",
      "type": "story_dialogue",
      "title": {
        "de": "Alis erster Gebetstag",
        "tr": "Ali'nin ilk namaz günü"
      },
      "lines": [
        {
          "character": "Narrator",
          "text": {
            "de": "Ali wacht früh morgens auf.",
            "tr": "Ali sabah erken uyandı."
          }
        },
        {
          "character": "Ali",
          "text": {
            "de": "Heute bete ich zum ersten Mal!",
            "tr": "Bugün ilk kez namaz kılıyorum!"
          }
        }
      ]
    }
  ]
}
```

## Question Types

| Type key | Description |
|---|---|
| `multiple_choice` | 2–4 options, stores `correct_index` (0-based) |
| `image_matching` | Image filename + DE/TR label pairs |
| `drag_drop_sorting` | Ordered items, shuffled by Unity at runtime |
| `story_dialogue` | Character + bilingual text lines |
