-- ============================================================================
-- Charvi O — Schema Supabase
-- ============================================================================
-- JALANKAN SEMUA ISI FILE INI di Supabase → SQL Editor → New query → RUN
-- (Setelah login, pastikan project sudah aktif)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabel 1: licenses
-- ----------------------------------------------------------------------------
create table licenses (
  device_id text primary key,
  shared boolean default false,
  shared_at timestamptz,
  trial_used boolean default false,
  trial_end timestamptz,
  active_until timestamptz,
  created_at timestamptz default now()
);

-- ----------------------------------------------------------------------------
-- Tabel 2: user_profiles
-- ----------------------------------------------------------------------------
create table user_profiles (
  device_id text primary key,
  full_name text not null,
  nickname text,
  whatsapp text,
  email text,
  city_hk text,
  employer_name text,
  job_type text,
  years_in_hk int,
  avatar_url text,
  bio text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ----------------------------------------------------------------------------
-- Tabel 3: payment_orders
-- ----------------------------------------------------------------------------
create table payment_orders (
  id bigserial primary key,
  device_id text not null,
  buyer_name text not null,
  buyer_wa text not null,
  buyer_email text,
  package_key text not null,
  package_label text not null,
  price int not null,
  status text not null default 'pending',
  license_code text,
  admin_note text,
  created_at timestamptz default now(),
  paid_at timestamptz,
  code_generated_at timestamptz,
  activated_at timestamptz
);

create index payment_orders_status_idx on payment_orders (status, created_at desc);
create index payment_orders_device_idx on payment_orders (device_id);

-- ----------------------------------------------------------------------------
-- Tabel 4: learn_progress
-- ----------------------------------------------------------------------------
create table learn_progress (
  id bigserial primary key,
  device_id text not null,
  phrase_id text not null,
  category text not null,
  indo text not null,
  yue text not null,
  jyutping text not null,
  status text not null default 'learning',
  correct_count int default 0,
  wrong_count int default 0,
  last_seen timestamptz default now(),
  created_at timestamptz default now(),
  unique(device_id, phrase_id)
);

-- ----------------------------------------------------------------------------
-- Tabel 5: quiz_sessions
-- ----------------------------------------------------------------------------
create table quiz_sessions (
  id bigserial primary key,
  device_id text not null,
  category text not null,
  quiz_type text not null,
  total_questions int not null,
  correct_answers int not null,
  score_pct int not null,
  completed_at timestamptz default now()
);

-- ----------------------------------------------------------------------------
-- Storage: avatar bucket + policy public
-- ----------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true) on conflict do nothing;

create policy "Public read avatars"
  on storage.objects for select using (bucket_id = 'avatars');

create policy "Public insert avatars"
  on storage.objects for insert with check (bucket_id = 'avatars');

create policy "Public update avatars"
  on storage.objects for update using (bucket_id = 'avatars');

-- ----------------------------------------------------------------------------
-- Paket pembayaran (dipakai di backend FastAPI & app.py)
-- ----------------------------------------------------------------------------
-- PACKAGES = {
--     "30_hari":  {"label": "Aktif 30 Hari",  "price": 50000,  "days": 30},
--     "90_hari":  {"label": "Aktif 90 Hari",  "price": 100000, "days": 90},
--     "180_hari": {"label": "Aktif 180 Hari", "price": 150000, "days": 180},
-- }
