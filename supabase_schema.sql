-- ═══════════════════════════════════════════════════════════════
-- Noor Play – Supabase Schema
-- Paste and run once in Supabase Dashboard → SQL Editor
-- Safe to re-run: uses IF EXISTS / ON CONFLICT DO NOTHING
-- ═══════════════════════════════════════════════════════════════


-- ╔═══════════════════════════════════════════════════════════════╗
-- ║  SECTION 1 – DROP ALL TABLES (reverse dependency order)      ║
-- ╚═══════════════════════════════════════════════════════════════╝

drop table if exists word_timings  cascade;
drop table if exists pages         cascade;
drop table if exists questions     cascade;
drop table if exists chapters      cascade;
drop table if exists books         cascade;
drop table if exists audio_files   cascade;
drop table if exists images        cascade;
drop table if exists activity_types cascade;
drop table if exists topics        cascade;
drop table if exists users         cascade;


-- ╔═══════════════════════════════════════════════════════════════╗
-- ║  SECTION 2 – CREATE TABLES (forward dependency order)        ║
-- ╚═══════════════════════════════════════════════════════════════╝

-- ── 1. users ────────────────────────────────────────────────────
-- CMS users. Role must be one of: teacher, admin, viewer.
create table if not exists users (
  id            text        primary key,
  email         text        unique not null,
  display_name  text        not null,
  role          text        not null default 'teacher',  -- teacher | admin | viewer
  last_seen     timestamptz default now(),
  created_at    timestamptz default now(),
  constraint users_role_check check (role in ('teacher', 'admin', 'viewer'))
);

-- ── 2. topics ───────────────────────────────────────────────────
-- Content categories for questions.
create table if not exists topics (
  id         text        primary key,
  name       text        unique not null,
  created_at timestamptz default now()
);

-- ── 3. activity_types ───────────────────────────────────────────
-- Lookup table for question/activity types (used in JSON and Unity).
create table if not exists activity_types (
  key        text primary key,
  label      text not null,
  icon       text,
  created_at timestamptz default now()
);

-- ── 4. images ───────────────────────────────────────────────────
-- Image asset library stored in Supabase Storage.
create table if not exists images (
  id           text   primary key,
  filename     text   not null,
  storage_path text   not null,
  image_url    text   not null,
  mime_type    text,
  size_bytes   int4   not null default 0,
  uploaded_at  timestamptz default now()
);

-- ── 5. audio_files ──────────────────────────────────────────────
-- Audio asset library stored in Supabase Storage.
create table if not exists audio_files (
  id           text   primary key,
  storage_path text   not null,
  public_url   text   not null,
  language     text   not null,
  filename     text   not null,
  size_bytes   int4   not null default 0,
  duration_ms  int4   not null default 0,
  created_at   timestamptz default now()
);

-- ── 6. books ────────────────────────────────────────────────────
-- Top-level book containers.
create table if not exists books (
  id                text   primary key,
  slug              text   unique not null,
  title_i18n        jsonb  not null default '{}',
  description_i18n  jsonb  not null default '{}',
  cover_image_url   text,
  sort_order        int4   not null default 0,
  is_published      bool   not null default false,
  created_at        timestamptz default now()
);

-- ── 7. chapters ─────────────────────────────────────────────────
-- Chapters belong to a book; deleted when their book is deleted.
create table if not exists chapters (
  id           text   primary key,
  book_id      text   not null references books(id) on delete cascade,
  title_i18n   jsonb  not null default '{}',
  sort_order   int4   not null default 0,
  is_published bool   not null default false,
  created_at   timestamptz default now()
);

-- ── 8. pages ────────────────────────────────────────────────────
-- Pages belong to a chapter; page_number is unique within a chapter.
create table if not exists pages (
  id                text   primary key,
  chapter_id        text   not null references chapters(id) on delete cascade,
  page_number       int4   not null,
  sentences         jsonb  not null default '[]',
  illustration_url  text,
  created_at        timestamptz default now(),
  constraint pages_chapter_page_unique unique (chapter_id, page_number)
);

-- ── 9. word_timings ─────────────────────────────────────────────
-- One row per page per language. Stores Whisper-generated word timings.
create table if not exists word_timings (
  id            text   primary key,
  page_id       text   not null references pages(id) on delete cascade,
  language      text   not null,
  audio_url     text,
  tts_audio_url text,
  timings       jsonb  not null default '[]',
  generated_at  timestamptz default now(),
  constraint word_timings_page_language_unique unique (page_id, language)
);

-- ── 10. questions ───────────────────────────────────────────────
-- Activities and quiz questions linked to topics and optionally chapters.
create table if not exists questions (
  id                text    primary key,
  activity_type_key text    not null references activity_types(key),
  topic_id          text    not null references topics(id),
  chapter_id        text    references chapters(id) on delete set null,
  age_group         text    not null,
  difficulty        text    not null,
  languages         text[]  not null default '{de,tr}',
  content           jsonb   not null,
  audio_file        text,
  is_published      bool    not null default false,
  created_at        timestamptz default now()
);

-- Indexes for common filters on questions
create index if not exists idx_questions_topic      on questions(topic_id);
create index if not exists idx_questions_type       on questions(activity_type_key);
create index if not exists idx_questions_age        on questions(age_group);
create index if not exists idx_questions_chapter    on questions(chapter_id);
create index if not exists idx_questions_published  on questions(is_published);
create index if not exists idx_questions_created    on questions(created_at desc);


-- ╔═══════════════════════════════════════════════════════════════╗
-- ║  SECTION 3 – SEED DATA                                       ║
-- ╚═══════════════════════════════════════════════════════════════╝

-- ── Topics ──────────────────────────────────────────────────────
insert into topics (id, name) values
  ('topic_salah',    'Prayer (Salah)'),
  ('topic_sawm',     'Fasting (Sawm)'),
  ('topic_wudu',     'Ablution (Wudu)'),
  ('topic_quran',    'Quran'),
  ('topic_prophets', 'Prophets'),
  ('topic_names',    'Names of Allah'),
  ('topic_akhlaq',   'Ethics (Akhlaq)'),
  ('topic_dua',      'Supplication (Dua)'),
  ('topic_holidays', 'Islamic Holidays'),
  ('topic_other',    'Other')
on conflict (id) do nothing;

-- ── Activity Types ───────────────────────────────────────────────
insert into activity_types (key, label, icon) values
  ('multiple_choice',   'Multiple Choice Question', '🔤'),
  ('image_matching',    'Image Matching',            '🖼️'),
  ('drag_drop_sorting', 'Drag & Drop Sorting',       '🔀'),
  ('story_dialogue',    'Story / Dialogue',          '📖')
on conflict (key) do nothing;

-- ── Books – 4 Magic Words ────────────────────────────────────────
insert into books (id, slug, title_i18n, description_i18n, sort_order, is_published) values
  (
    'book_4magic',
    '4-magic-words',
    '{"de": "4 Zauberworte", "tr": "4 Sihirli Kelime", "en": "4 Magic Words"}',
    '{"de": "Ein islamisches Kinderbuch über die vier wichtigsten Worte im Leben eines Muslims.", "tr": "Bir Müslümanın hayatındaki dört önemli kelimeyi anlatan İslami bir çocuk kitabı.", "en": "An Islamic children''s book about the four most important words in a Muslim''s life."}',
    1,
    false
  )
on conflict (id) do nothing;


-- ╔═══════════════════════════════════════════════════════════════╗
-- ║  SECTION 4 – ROW LEVEL SECURITY                              ║
-- ╚═══════════════════════════════════════════════════════════════╝
-- The Streamlit CMS connects via the service_role key which bypasses
-- RLS, but policies are required for RLS to be enabled. A single
-- permissive policy per table grants full access so future auth
-- integrations can layer on top without schema changes.

alter table users          enable row level security;
alter table topics         enable row level security;
alter table activity_types enable row level security;
alter table images         enable row level security;
alter table audio_files    enable row level security;
alter table books          enable row level security;
alter table chapters       enable row level security;
alter table pages          enable row level security;
alter table word_timings   enable row level security;
alter table questions      enable row level security;

create policy "service_role_all" on users          for all using (true);
create policy "service_role_all" on topics         for all using (true);
create policy "service_role_all" on activity_types for all using (true);
create policy "service_role_all" on images         for all using (true);
create policy "service_role_all" on audio_files    for all using (true);
create policy "service_role_all" on books          for all using (true);
create policy "service_role_all" on chapters       for all using (true);
create policy "service_role_all" on pages          for all using (true);
create policy "service_role_all" on word_timings   for all using (true);
create policy "service_role_all" on questions      for all using (true);
