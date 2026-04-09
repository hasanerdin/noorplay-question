-- books
create table if not exists books (
  id              text        primary key,
  slug            text        unique not null,
  title_i18n      jsonb       not null default '{}',
  description_i18n jsonb      not null default '{}',
  cover_image_url text,
  sort_order      int         not null default 0,
  is_published    bool        not null default false,
  created_at      timestamptz default now()
);

-- chapters
create table if not exists chapters (
  id           text        primary key,
  book_id      text        not null references books(id) on delete cascade,
  title_i18n   jsonb       not null default '{}',
  sort_order   int         not null default 0,
  is_published bool        not null default false,
  created_at   timestamptz default now()
);

-- pages
create table if not exists pages (
  id                text        primary key,
  chapter_id        text        not null references chapters(id) on delete cascade,
  page_number       int         not null,
  sentences         jsonb       not null default '[]',
  illustration_url  text,
  created_at        timestamptz default now(),
  unique(chapter_id, page_number)
);

-- word_timings
create table if not exists word_timings (
  id             text        primary key,
  page_id        text        not null references pages(id) on delete cascade,
  language       text        not null,
  audio_url      text,
  tts_audio_url  text,
  timings        jsonb       not null default '[]',
  generated_at   timestamptz default now(),
  unique(page_id, language)
);

-- audio_files
create table if not exists audio_files (
  id           text        primary key,
  storage_path text        not null,
  public_url   text        not null,
  language     text        not null,
  filename     text        not null,
  size_bytes   int         default 0,
  duration_ms  int         default 0,
  created_at   timestamptz default now()
);

-- alter questions: add chapter_id and is_published
alter table questions
  add column if not exists chapter_id  text references chapters(id) on delete set null,
  add column if not exists is_published bool not null default false;

-- RLS
alter table books        enable row level security;
alter table chapters     enable row level security;
alter table pages        enable row level security;
alter table word_timings enable row level security;
alter table audio_files  enable row level security;

create policy "service_role_all" on books        for all using (true);
create policy "service_role_all" on chapters     for all using (true);
create policy "service_role_all" on pages        for all using (true);
create policy "service_role_all" on word_timings for all using (true);
create policy "service_role_all" on audio_files  for all using (true);

-- Seed the first book
insert into books (id, slug, title_i18n, description_i18n, sort_order, is_published)
values (
  'book_magic_words',
  '4-magic-words',
  '{"de": "4 Zauberwörter", "tr": "4 Sihirli Kelime", "en": "4 Magic Words"}',
  '{"de": "Lerne die 4 wichtigsten islamischen Wörter", "tr": "4 önemli İslami kelimeyi öğren", "en": "Learn the 4 most important Islamic words"}',
  1, false
) on conflict (id) do nothing;
