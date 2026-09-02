-- CropGuard AI — Supabase/Postgres schema
-- Run this in the Supabase SQL editor (or via `supabase db push`).
-- Assumes Supabase Auth is enabled — auth.users is Supabase's built-in table.
--
-- This file is the full snapshot for a brand-new project — running it once
-- gets you everything (including Storage + hardening from migration 0002).
-- Going forward, prefer applying database/migrations/*.sql in order for
-- incremental changes to an existing project, so you don't have to diff
-- this file by hand to see what changed.

-- ============================================================================
-- USERS (profile data — auth itself lives in Supabase's auth.users)
-- ============================================================================
create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  email text,
  phone text,
  location text,
  -- Keep in sync with SUPPORTED_LANGUAGE_CODES in backend/app/schemas/auth.py
  -- and SUPPORTED_LANGUAGES in frontend/lib/i18n/index.ts. A value the app
  -- offers but this constraint rejects fails *inside* the signup trigger,
  -- which rolls back the auth.users insert — so registration dies with an
  -- opaque 500 rather than a field error.
  language text not null default 'en' check (language in ('en', 'hi', 'mr', 'ta', 'te')),
  created_at timestamptz not null default now()
);

-- ============================================================================
-- FIELDS
-- ============================================================================
create table if not exists public.fields (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  name text not null,
  crop text not null,
  area numeric not null check (area > 0),
  latitude double precision not null,
  longitude double precision not null,
  health_status text not null default 'healthy' check (health_status in ('healthy', 'moderate', 'high')),
  last_scan_at timestamptz,
  last_disease text,
  last_risk text check (last_risk in ('healthy', 'moderate', 'high')),
  created_at timestamptz not null default now()
);
create index if not exists idx_fields_user_id on public.fields(user_id);

-- ============================================================================
-- SCANS
-- ============================================================================
create table if not exists public.scans (
  id uuid primary key default gen_random_uuid(),
  field_id uuid not null references public.fields(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  image_url text not null,
  "timestamp" timestamptz not null default now(),
  crop text not null,
  is_demo boolean not null default true,
  detections jsonb not null default '[]',
  severity jsonb not null,
  risk jsonb not null,
  weather jsonb,
  recommendation jsonb not null,
  created_at timestamptz not null default now()
);
create index if not exists idx_scans_field_id on public.scans(field_id);
create index if not exists idx_scans_user_id on public.scans(user_id);

-- ============================================================================
-- ALERTS
-- ============================================================================
create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  field_id uuid not null references public.fields(id) on delete cascade,
  message text not null,
  severity text not null check (severity in ('healthy', 'moderate', 'high')),
  read boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_alerts_user_id on public.alerts(user_id);

-- ============================================================================
-- WEATHER (cached snapshots per field)
-- ============================================================================
create table if not exists public.weather (
  id uuid primary key default gen_random_uuid(),
  field_id uuid not null references public.fields(id) on delete cascade,
  temperature numeric,
  humidity numeric,
  rainfall numeric,
  wind numeric,
  condition text,
  "timestamp" timestamptz not null default now()
);
create index if not exists idx_weather_field_id on public.weather(field_id);

-- ============================================================================
-- ROW LEVEL SECURITY
-- The backend also enforces authorization at the API layer (see
-- backend/app/utils/auth.py), but RLS is the source of truth so data is
-- protected even if a client talks to Supabase directly in a later stage.
-- ============================================================================
alter table public.users enable row level security;
alter table public.fields enable row level security;
alter table public.scans enable row level security;
alter table public.alerts enable row level security;
alter table public.weather enable row level security;

create policy "Users read own profile" on public.users
  for select using (auth.uid() = id);
create policy "Users update own profile" on public.users
  for update using (auth.uid() = id);

create policy "Users manage own fields" on public.fields
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "Users manage own scans" on public.scans
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "Users manage own alerts" on public.alerts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "Users read weather for own fields" on public.weather
  for select using (
    exists (select 1 from public.fields f where f.id = weather.field_id and f.user_id = auth.uid())
  );

-- ============================================================================
-- Auto-create a public.users row whenever someone signs up via Supabase Auth
-- ============================================================================
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, name, email, phone, location, language)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', 'Farmer'),
    new.email,
    new.raw_user_meta_data->>'phone',
    coalesce(new.raw_user_meta_data->>'location', ''),
    coalesce(new.raw_user_meta_data->>'language', 'en')
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
-- Apply after 0001_init.sql. Safe to re-run (uses IF NOT EXISTS / OR REPLACE
-- throughout).

-- ============================================================================
-- STORAGE: crop-images bucket
-- Images are stored at "<user_id>/<field_id>/<scan_id>.<ext>" so per-user
-- storage policies can scope access by folder name, mirroring the RLS
-- pattern used on the tables themselves.
-- ============================================================================
insert into storage.buckets (id, name, public)
values ('crop-images', 'crop-images', true)
on conflict (id) do nothing;

create policy "Users upload to their own folder"
  on storage.objects for insert
  with check (
    bucket_id = 'crop-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users read their own crop images"
  on storage.objects for select
  using (
    bucket_id = 'crop-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Public can view crop images"
  on storage.objects for select
  using (bucket_id = 'crop-images');

create policy "Users delete their own crop images"
  on storage.objects for delete
  using (
    bucket_id = 'crop-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ============================================================================
-- HARDENING: updated_at columns + trigger, so callers (and support staff
-- debugging a farmer's issue) can tell when a row last changed vs. when it
-- was created. Applied to the two tables that get mutated after creation.
-- ============================================================================
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

alter table public.fields add column if not exists updated_at timestamptz not null default now();
alter table public.users add column if not exists updated_at timestamptz not null default now();

drop trigger if exists set_fields_updated_at on public.fields;
create trigger set_fields_updated_at
  before update on public.fields
  for each row execute procedure public.set_updated_at();

drop trigger if exists set_users_updated_at on public.users;
create trigger set_users_updated_at
  before update on public.users
  for each row execute procedure public.set_updated_at();

-- ============================================================================
-- HARDENING: guard against an empty/whitespace field name slipping through
-- (the frontend and backend both validate this, but the DB should not rely
-- solely on application-layer checks for data integrity).
-- ============================================================================
alter table public.fields
  add constraint fields_name_not_blank check (btrim(name) <> '');

