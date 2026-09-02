-- Migration 0002 — Storage for scan images + updated_at hardening
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
