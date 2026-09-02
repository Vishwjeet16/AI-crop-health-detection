-- 0003 — widen the users.language constraint from 2 languages to 5
--
-- Apply after 0002_storage_and_hardening.sql. Safe to re-run.
--
-- Why this exists: Stage 8 widened the app from English/Hindi to English,
-- Hindi, Marathi, Tamil and Telugu. The register page, the settings page, the
-- sidebar picker and the assistant all offer five. This constraint still
-- allowed two.
--
-- The failure mode was worse than a rejected update. public.handle_new_user()
-- runs as an AFTER INSERT trigger on auth.users and copies
-- raw_user_meta_data->>'language' into this column. A farmer choosing Marathi
-- at signup therefore tripped the constraint *inside the signup transaction*,
-- which rolled back the auth.users insert too — so account creation failed
-- with an opaque 500 instead of a message naming the field.
--
-- If you are setting up a brand-new project from database/schema.sql you do
-- not need this file; that snapshot already carries the five-language check.

alter table public.users
  drop constraint if exists users_language_check;

alter table public.users
  add constraint users_language_check
  check (language in ('en', 'hi', 'mr', 'ta', 'te'));
