-- ═══════════════════════════════════════════════════════════════
-- Noor Play – Supabase Schema
-- Run this once in Supabase Dashboard → SQL Editor
-- ═══════════════════════════════════════════════════════════════

-- ── 1. users ────────────────────────────────────────────────────
create table if not exists users (
  id            text        primary key,
  email         text        unique not null,
  display_name  text        not null,
  role          text        not null default 'teacher',   -- teacher | admin | viewer
  last_seen     timestamptz default now(),
  created_at    timestamptz default now()
);

-- ── 2. topics ───────────────────────────────────────────────────
create table if not exists topics (
  id         text        primary key,
  name       text        unique not null,    -- e.g. "Prayer (Salah)"
  created_at timestamptz default now()
);

-- Seed default topics
insert into topics (id, name) values
  ('topic_salah',     'Prayer (Salah)'),
  ('topic_sawm',      'Fasting (Sawm)'),
  ('topic_wudu',      'Ablution (Wudu)'),
  ('topic_quran',     'Quran'),
  ('topic_prophets',  'Prophets'),
  ('topic_names',     'Names of Allah'),
  ('topic_akhlaq',    'Ethics (Akhlaq)'),
  ('topic_dua',       'Supplication (Dua)'),
  ('topic_holidays',  'Islamic Holidays'),
  ('topic_other',     'Other')
on conflict (id) do nothing;

-- ── 3. activity_types ───────────────────────────────────────────
create table if not exists activity_types (
  key        text primary key,   -- used in JSON / Unity
  label      text not null,      -- human-readable
  icon       text,
  created_at timestamptz default now()
);

-- Seed activity types
insert into activity_types (key, label, icon) values
  ('multiple_choice',   'Multiple Choice Question', '🔤'),
  ('image_matching',    'Image Matching',            '🖼️'),
  ('drag_drop_sorting', 'Drag & Drop Sorting',       '🔀'),
  ('story_dialogue',    'Story / Dialogue',           '📖')
on conflict (key) do nothing;

-- ── 4. questions ────────────────────────────────────────────────
create table if not exists questions (
  id                text        primary key,
  activity_type_key text        not null references activity_types(key),
  topic_id          text        not null references topics(id),
  age_group         text        not null,      -- "6–8 years (pre-reader)" | ...
  difficulty        text        not null,      -- "Beginner" | "Intermediate" | "Advanced"
  languages         text[]      not null default '{de,tr}',
  content           jsonb       not null,      -- bilingual content (de + tr)
  audio_file        text,                      -- optional: "prayer_q1.mp3"
  created_at        timestamptz default now()
);

-- Index for common filters
create index if not exists idx_questions_topic    on questions(topic_id);
create index if not exists idx_questions_type     on questions(activity_type_key);
create index if not exists idx_questions_age      on questions(age_group);
create index if not exists idx_questions_created  on questions(created_at desc);

-- ── Row Level Security ───────────────────────────────────────────
-- All tables use service_role key from Streamlit (full access).
-- If you later add Supabase Auth, replace these with user-scoped policies.

alter table users          enable row level security;
alter table topics         enable row level security;
alter table activity_types enable row level security;
alter table questions      enable row level security;

create policy "service_role_all" on users          for all using (true);
create policy "service_role_all" on topics         for all using (true);
create policy "service_role_all" on activity_types for all using (true);
create policy "service_role_all" on questions      for all using (true);