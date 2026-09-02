-- CropGuard AI — Supabase/Postgres schema
-- Run this in the Supabase SQL editor (or via `supabase db push`).
-- Assumes Supabase Auth is enabled — auth.users is Supabase's built-in table.

-- ============================================================================
-- USERS (profile data — auth itself lives in Supabase's auth.users)
-- ============================================================================
create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  email text,
  phone text,
  location text,
  language text not null default 'en' check (language in ('en', 'hi')),
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
