# CropGuard AI

**Detect Early. Act Smart. Protect Every Crop.**

AI-powered crop health monitoring platform prototype for the SIH problem
statement "Early Detection and Management of Crop Damage and Pest
Infestation."

---

## Stage 1 — UI/UX & Page Architecture (this delivery)

Stage 1 builds the complete frontend page architecture as a clickable
prototype: every route from the plan exists, styled with a dedicated design
system, wired together with client-side navigation, and running on
**mock/demo data only**. No backend, database, or AI model calls are wired
yet — those are Stage 2 onward.

### Design system

- **Palette**: sage-paper background (`#F3F6EE`), forest green primary
  (`#1B4332`), growth green for actions (`#4C7A3F`), marigold accent for
  the AI/scan motif (`#DFA23C`), muted brick-red for high risk (`#B4432E`)
  — deliberately steering away from the generic "warm cream + terracotta"
  AI-template look toward colors pulled from an actual field: soil, leaf,
  turmeric, unripe fruit.
- **Type**: Fraunces (display/headlines, organic and a little handcrafted),
  IBM Plex Sans (UI/body), IBM Plex Mono (confidence scores, risk numbers,
  data readouts — anywhere a sensor or model is "speaking").
- **Signature motif**: viewfinder scan-brackets (`.scan-frame` in
  `globals.css`) on the hero image, upload box, and detection result — a
  literal echo of the product's core action (framing a crop to scan it),
  not decorative chrome.
- Full source: `frontend/app/globals.css`, `frontend/tailwind.config.ts`.

### Pages built

| Route | Status |
|---|---|
| `/` | Landing page — hero, how it works, features, why, tech, demo-labeled impact stats, CTA |
| `/login`, `/register`, `/forgot-password` | Auth screens with shared branding layout |
| `/dashboard` | Stats row, field cards, recent alerts |
| `/fields`, `/fields/new`, `/fields/[id]`, `/fields/[id]/history` | Field list, add-field form, field detail, disease progression chart + table |
| `/scan` | Field select → upload/camera → animated analysis pipeline |
| `/scan/result/[id]` | Bounding-box visualization, severity, risk gauge, weather, recommendation (with AI-vs-verified-guidance disclaimer) |
| `/map` | Color-coded field markers on a placeholder grid (Leaflet swap is a drop-in for Stage 2+) |
| `/alerts` | Alert list with working mark-as-read state |
| `/settings` | Profile + language + notification preferences |

### Files changed

Everything under `frontend/` is new: `app/` (13 routes), `components/ui/`
and `components/shared/` (17 reusable components), `lib/mock-data.ts`
(clearly labeled demo data matching the future API contract), `lib/i18n/`
(English + Hindi translation keys, structured for 7 more languages),
`types/index.ts`. Root: `.env.example`, `.gitignore`, this `README.md`.
Empty `backend/`, `ml/`, `database/` folders are scaffolded with
`.gitkeep` for Stage 2+.

### How to run it

```bash
cd frontend
npm install
cp ../.env.example .env.local   # fill in real values, never commit this file
npm run dev
```

Then open `http://localhost:3000`. Every page is reachable from the nav —
try `/scan` end-to-end (upload → animated analysis → result screen).

### Known limitations / remaining issues (by design, for later stages)

- All data is mock (`lib/mock-data.ts`). No Supabase, FastAPI, or YOLO
  calls exist yet.
- `/map` uses a lightweight CSS grid placeholder instead of real
  Leaflet/OpenStreetMap tiles — swapping it in is a Stage 2 task once the
  package can be installed (this sandbox has no network access to fetch
  packages).
- Auth forms don't call Supabase Auth yet; buttons navigate straight to
  `/dashboard` so the flow can be demoed.
- I have **not** run `npm install` / `npm run build` in this environment
  (no network access here) — the code is written to compile cleanly
  against the pinned versions in `package.json`, but please run a build
  locally before your first demo rehearsal and flag anything that breaks.
- Full shadcn/ui CLI wasn't run (also needs network); component styling
  instead follows the same tokens by hand in `components/ui/`. Swapping
  in real shadcn primitives later is optional, not required.

### Security note carried over from setup

The Supabase **service_role** key you shared earlier should be rotated in
your Supabase dashboard before this goes anywhere near a real deployment,
since it was pasted into a chat transcript. It is not present anywhere in
this codebase — `.env.example` only has placeholder names.

---

---

## Stage 2 — Full Frontend Implementation

Stage 2 makes the prototype functional end-to-end on the frontend: real
state management, form validation with inline errors, loading/error/empty
states wired to an API layer, and a mock backend that behaves like the
real one so Stage 3 is a drop-in swap.

### What changed

- **`lib/api/`** — one file per domain (`auth.ts`, `fields.ts`, `scans.ts`,
  `alerts.ts`), all going through a shared `client.ts`. A single
  `USE_MOCK_API` flag in `client.ts` is the only thing Stage 3 needs to
  flip once `/api/*` routes exist — no page or component changes required.
  Each mock function simulates realistic latency and can throw a typed
  `ApiError`, so error states have something real to handle.
- **`context/auth-context.tsx`** — real login/register/logout with a demo
  credential check (`9876543210` / `cropguard1`) so the login form has an
  actual success/failure path, not just a straight pass-through. Session
  persists via `localStorage` for the browser session (resets on Stage 3
  when Supabase Auth takes over).
- **`context/language-context.tsx`** — English/Hindi switch that applies
  instantly across the sidebar; persisted per-browser.
- **Route protection** — `(app)/layout.tsx` redirects to `/login` if
  there's no session, with a loading spinner while auth state resolves.
- **Form validation** (`lib/validation.ts`) — login, register, forgot
  password, and add-field forms all validate inline (required fields,
  email/phone format, password strength, positive numbers, image
  type/size) and show field-level error text instead of failing silently.
- **Loading/error/empty states everywhere data is fetched** — dashboard,
  fields list, field detail, field history, scan result, alerts, and map
  each have a skeleton or spinner state, a real error state with retry,
  and an empty state where relevant.
- **Functional scan flow** — uploading an image and hitting Analyze calls
  `analyzeImage()`, which returns a different demo outcome depending on
  the selected field (Field A → early blight/high risk, Field B → a
  deliberately low-confidence result to exercise that UI path, Field C →
  healthy/no detections) so the SIH demo can show range without feeling
  hardcoded to one path. A high-risk result also generates a real alert
  that shows up immediately in the sidebar badge and `/alerts`.
- **Field creation persists for the session** — adding a field via
  `/fields/new` immediately appears on the dashboard, `/fields`, and
  `/map`.

### How to run it

Same as Stage 1:

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

Log in with **9876543210 / cropguard1** (or just register a new account —
both work). Try: log in → add a field → scan it → watch the risk-based
alert appear in the sidebar → mark it read.

### Known limitations / remaining issues

- All state still lives in the browser (`localStorage` + in-memory
  arrays in `lib/api/*.ts`). Nothing is shared across devices or persists
  past a cache clear — that's what Stage 3 (Supabase Postgres) is for.
- I still haven't been able to run `npm install` / `npm run build` in this
  sandbox (no network access here) — please run both locally and let me
  know if anything doesn't compile.
- The map is still a CSS-grid placeholder, not real Leaflet tiles.
- Settings page save is simulated (no real profile persistence yet).

---

---

## Stage 3 — FastAPI Backend + Supabase Schema

Stage 3 builds the real backend: every route from section 25, a full
Postgres schema with RLS, and the AI/risk/recommendation pipeline
architecture — running in demo mode today, with a documented, well-marked
seam for Stage 6's real YOLO model. The frontend's mock API layer
(`lib/api/*.ts`) now has a real counterpart to call.

### What was built

- **`database/schema.sql`** — `users`, `fields`, `scans`, `alerts`,
  `weather` tables matching section 24, with indexes, a trigger that
  auto-creates a `public.users` profile row on Supabase Auth signup, and
  Row Level Security policies scoping every table to `auth.uid()`.
- **`backend/app/main.py`** — FastAPI app with CORS, a consistent
  `{status, error}` error envelope (matches the frontend's `ApiError`
  class), and all routers registered.
- **`backend/app/api/`** — `auth.py`, `fields.py`, `scans.py`, `alerts.py`,
  `dashboard.py`, covering every route in section 25 (register, login,
  forgot-password, field CRUD, `/api/analyze`, scan history, risk,
  weather, field history, alerts + mark-read, dashboard summary).
- **`backend/app/services/`**:
  - `ai_service.py` — the pipeline from section 21 (validate →
    preprocess → detect → severity). Demo mode picks from a small set of
    realistic outcomes deterministically from the image itself (same
    photo → same result, useful for a repeatable SIH demo). Production
    mode is a documented stub: if `AI_MODE=production` but no weights
    file exists at `backend/models/cropguard-yolo.pt`, it logs a warning
    and falls back to demo rather than crashing — see `_yolo_available()`.
  - `risk_service.py` — rule-based, explainable risk scoring (detection
    confidence + affected area + humidity + trend), documented rather
    than a second opaque model, matching the SIH novelty framing.
  - `recommendation_service.py` — static, reviewed templates per disease
    class. Deliberately **not** LLM-generated, so it can never invent a
    pesticide name or dose (section 33's hard requirement).
  - `weather_service.py` — real OpenWeatherMap-compatible call when
    `WEATHER_API_KEY` is set, with a clearly-labeled demo fallback if the
    key is missing or the API call fails.
  - `supabase_client.py` — thin httpx wrapper around Supabase's REST
    (PostgREST) and Auth (GoTrue) APIs. Uses the service_role key from
    the trusted backend context; authorization is enforced at the API
    layer (every query scoped to the caller's user id) with RLS as the
    backstop.
- **`backend/app/utils/auth.py`** — `get_current_user` dependency;
  validates the bearer token against Supabase Auth and loads the caller's
  profile row. Every protected route depends on it.
- **Frontend wiring** — `lib/api/*.ts` now branch on `USE_MOCK_API`
  (driven by `NEXT_PUBLIC_USE_MOCK_API` in `.env.local`, default `true`).
  Set it to `false` once the backend is running and Supabase is
  configured, and every page starts hitting real endpoints — no page or
  component code changes needed. The real-mode branches handle the
  camelCase (frontend) ↔ snake_case (backend) translation and multipart
  image upload.
- **`docker-compose.yml`** + Dockerfiles for both services, for running
  the whole stack with one command once `.env` files are filled in.

### How to run it

```bash
# 1. Supabase: create a project, run database/schema.sql in the SQL editor.

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, WEATHER_API_KEY
uvicorn app.main:app --reload

# 3. Frontend
cd ../frontend
# in .env.local, set NEXT_PUBLIC_USE_MOCK_API=false
npm run dev
```

Or `docker compose up` from the repo root once both `.env` files exist.

### Known limitations / remaining issues

- **I could not install or run any of this in the sandbox** — no network
  access here means no `pip install`, no `uvicorn`, no live request ever
  hit these routes. Every file compiles (`python -m py_compile` passed on
  all of them) and the logic has been reasoned through carefully, but
  please treat this as reviewed-but-unexecuted code: run it locally,
  hit `/health`, and try the full register → add field → scan flow
  before trusting it for a demo rehearsal.
- **Image storage isn't wired yet** — `/api/analyze` currently stores a
  placeholder `image_url` instead of uploading to Supabase Storage. Worth
  doing before Stage 4/5 if the result screen needs to show the actual
  uploaded photo rather than a fixed demo image.
- **Phone-based password reset** isn't implemented — Supabase's recovery
  endpoint used here only covers email; the `/api/auth/forgot-password`
  route currently just validates input and returns success.
- **YOLO inference itself is unimplemented on purpose** — that's Stage 6.
  `_run_yolo_inference()` in `ai_service.py` has the intended
  implementation sketched in a comment.
- The register-flow's Supabase path may require **email confirmation**
  depending on your Supabase project's auth settings, in which case
  `access_token` won't come back immediately — the route surfaces that
  as a 202 with a clear message rather than silently failing.

---

## Stage 4 — Database Hardening + Image Storage + Seed Data

Stage 4 closes the two gaps flagged at the end of Stage 3: scan images had
nowhere real to live, and there was no way to get realistic data into a
fresh Supabase project without going through the UI by hand.

### What was built

- **`database/migrations/`** — going forward, incremental schema changes
  live here as numbered files (`0001_init.sql` is the Stage 3 schema,
  `0002_storage_and_hardening.sql` is this stage's changes) instead of
  hand-diffing one growing `schema.sql`. `schema.sql` itself still works
  as a single-file setup for a brand-new project — it now includes
  migration 0002's changes too, so you only need to run one file to get a
  fully set-up project from scratch.
- **Supabase Storage** — a `crop-images` bucket (public, so result screens
  can render images directly) with per-user folder policies mirroring the
  RLS pattern on the tables: uploads and reads are scoped to
  `<user_id>/...`, matching how `backend/app/services/storage_service.py`
  paths each upload.
- **`backend/app/services/storage_service.py`** — uploads the scanned
  image to that bucket and returns a public URL. `/api/analyze` now uses
  this instead of a placeholder path, so `scans.image_url` in the database
  points at something real. If Supabase isn't configured yet (e.g. still
  in early local setup), it degrades to a placeholder instead of crashing
  the whole analyze request.
- **`updated_at` columns + trigger** on `fields` and `users`, and a
  not-blank check constraint on `fields.name` — small integrity
  hardening that doesn't rely solely on the frontend/backend validation
  layers.
- **`backend/scripts/seed_demo_data.py`** — creates (or reuses) a real
  demo Supabase Auth account and seeds three sample fields + one alert,
  so you can rehearse the full app against real backend data instead of
  the frontend's mock layer. Re-run-safe — it checks for the demo user by
  email before creating anything.

### How to run it

```bash
# 1. Apply the schema (fresh project): run database/schema.sql in the
#    Supabase SQL editor. Already-set-up project: run
#    database/migrations/0002_storage_and_hardening.sql on top of 0001.

# 2. Seed demo data
cd backend
source .venv/bin/activate   # from Stage 3 setup
python -m scripts.seed_demo_data
```

Then log in (with `NEXT_PUBLIC_USE_MOCK_API=false`) using the
`demo.farmer@cropguard.test` / `cropguard-demo-1` credentials the script
prints.

### Known limitations / remaining issues

- **Still entirely unexecuted** — same caveat as every backend stage so
  far: no network access in this sandbox means none of this has touched a
  real Supabase project. The SQL is written to be idempotent
  (`if not exists`, `on conflict do nothing`) so it should be safe to run
  and re-run, but please verify on a real project before a demo.
- The storage bucket is fully public — anyone with a scan's URL can view
  that image, even without being logged in. Fine for an SIH demo; worth
  revisiting (signed URLs) before any real farmer's data goes through this.
- No migration *runner* (like Alembic or Supabase CLI's migration tooling)
  is wired up — `migrations/*.sql` are meant to be applied by hand or via
  `supabase db push` for now. Worth automating once the schema is
  changing frequently.
- The seed script only covers fields/alerts, not sample scans — a seeded
  scan would need a real image uploaded to Storage first, which felt like
  more seed-script complexity than this stage's gap justified. Easy to
  add later if the demo needs pre-populated history without scanning live.

---

## Stage 5 — Demo AI Mode, Properly Built Out

Stage 3 shipped a working but thin demo pipeline: three fixed outcomes, all
loosely modeled on a tomato. Stage 5 makes Demo AI Mode something you'd
actually want to demo — varied, crop-aware, and exercising every UI state
the app has, without needing a trained model.

### What changed

- **Crop-aware outcome pools** — `backend/app/services/demo_outcomes.py`
  now holds a `CROP_DEMO_OUTCOMES` registry covering all five crops the
  "Add Field" form offers (Tomato, Cotton, Soybean, Wheat, Rice), each
  with 2-3 outcomes. A Cotton field now always returns a cotton-relevant
  result — never a tomato disease — because outcomes are selected by the
  field's actual crop, not a fixed index.
- **Full severity range represented** — the pool now includes a
  **critical** severity case (Tomato late blight, 58% affected area) in
  addition to low/moderate/high, so the severity badge's full color range
  actually shows up somewhere in a demo run, not just moderate.
- **A genuine low-confidence path** — Cotton's leaf-curl outcome sits at
  42% confidence, below the 0.6 threshold, so the "AI is not confident
  enough — please capture a clearer image or consult an agricultural
  expert" message (section 27) is reachable without hand-editing data.
- **Recommendation coverage matches the expanded disease list** —
  `recommendation_service.py` now has reviewed templates for late blight,
  bollworm damage, soybean rust, wheat rust, and rice blast, each with
  disease-specific (not generic) action text, still deliberately free of
  any invented pesticide name or dose.
- **Deterministic-per-image selection preserved** — both backend
  (`demo_outcomes.get_demo_outcome`) and frontend
  (`lib/api/scans.ts`'s `pickDemoOutcome`) pick from the crop's pool using
  a hash/size signal from the uploaded file, so scanning the same photo
  twice in a live demo still gives the same result — it just also now
  varies sensibly by crop.
- **Frontend mock layer mirrors the backend registry** — `USE_MOCK_API`
  mode (the default, no-backend-required path) tells the same richer demo
  story as the real backend now does, so you don't need Supabase running
  just to see the full range of outcomes during rehearsal.

### How to see the range

With `USE_MOCK_API=true` (default), add fields with different crops and
scan each — Tomato, Cotton, Soybean, Wheat, and Rice each have their own
outcome pool. Scan the same field/photo twice to see the deterministic
repeat; scan a different-sized photo to see a different outcome from that
crop's pool.

### Known limitations / remaining issues

- Outcome selection is still a hash of the image, not real image content —
  a photo of a healthy leaf can still "detect" late blight if the hash
  happens to land there. That's the nature of demo mode; it's clearly
  labeled everywhere (`isDemo` / "Demo Mode" banner / "Demo estimate"
  badge) so this should never be mistaken for a real diagnosis.
- Wheat and Rice fields aren't in the seeded demo data
  (`backend/scripts/seed_demo_data.py` from Stage 4 only seeds Tomato/
  Cotton/Soybean) — add one manually via "Add Field" to see those pools,
  or extend the seed script.
- As with every backend stage so far, this hasn't been run against a live
  Supabase project — please verify the `crop` matching is case-insensitive
  as intended (`"Tomato"` from the DB vs `"tomato"` in the registry keys)
  once you can test end-to-end.

---

## Stage 6 — Real YOLO Model Integration

Stage 6 is a different kind of stage from 1-5: it needs a labeled dataset
and a GPU, neither of which exist in the environment I build in. I could
not train a model here. What's built instead is the full pipeline you run
yourself, plus real inference code wired into the backend so flipping
`AI_MODE=production` actually does something the moment weights exist.

### What was built

- **`ml/training/data.yaml`** — YOLO dataset config. Class list
  deliberately matches the `class_` keys already used in
  `demo_outcomes.py` and `recommendation_service.py`, so a trained
  model's labels line up with existing recommendation templates with no
  remapping layer needed.
- **`ml/training/train.py`** — runnable training script (ultralytics
  YOLOv8), once a dataset exists at `ml/dataset/yolo_format/`. Copies the
  best checkpoint straight to `backend/models/cropguard-yolo.pt` on
  completion — the exact path `ai_service.py` already looks for.
- **`ml/inference/test_inference.py`** — sanity-checks a trained model
  against one image before you trust it in a live demo.
- **`backend/app/services/ai_service.py`** — `_run_yolo_inference()` is no
  longer a stub. It loads the model once (process-wide cache, not
  reloaded per request), converts YOLO's pixel-coordinate boxes into the
  percentage-based `bbox` format the frontend's `DetectionResult`
  component already expects, and estimates affected area from summed box
  area as a coarse proxy for real segmentation.
- **`ml/dataset/README.md` + `prepare_dataset.py`** — implemented for
  PlantDoc specifically (see the decision writeup below for what that
  means and its real coverage gap).

### The one real decision this stage needed — resolved: PlantDoc

You chose **PlantDoc** ([pratikkayal/PlantDoc-Object-Detection-Dataset](https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset),
real bounding boxes, smaller than PlantVillage).
`ml/dataset/prepare_dataset.py` is now a working implementation for that
path specifically, not a generic skeleton — it clones the repo, parses its
Pascal VOC XML annotations, maps PlantDoc's class-folder names onto this
project's 7-class taxonomy, converts boxes to YOLO's normalized format,
and splits into train/val/test.

**Read this before running it.** Two things came with this choice that
are worth understanding rather than discovering during training:

1. **The class-folder name mapping (`CLASS_MAP` in the script) was written
   from memory, without live access to the repo to verify it.** Clone
   PlantDoc yourself first, check the actual class folder names, and fix
   any mismatches in `CLASS_MAP` before trusting a training run — a wrong
   folder name just means that class silently gets skipped, not an error.
2. **Only 2 of the 7 classes in `data.yaml` have a confirmed real match in
   PlantDoc** — `early_blight` and `late_blight`, both Tomato. PlantDoc's
   classes are mostly tomato/apple/corn/potato/grape/bell pepper; it has
   no cotton, wheat, or rice annotations, and its soybean folder is
   healthy-only (no rust class). Practically: running
   `prepare_dataset.py` + `train.py` today gives you **a tomato-only
   detector**. `leaf_curl`, `bollworm_damage`, `soybean_rust`,
   `wheat_rust`, and `rice_blast` will have zero training examples. The
   script prints exactly which PlantDoc classes it saw but couldn't map,
   so this isn't silent. Before your first real training run, either:
   - remove those 5 classes from `ml/training/data.yaml` and ship a
     tomato-only model — genuinely detecting 2 diseases is a stronger SIH
     story than claiming coverage of 5 crops never actually trained on, or
   - add a second data source for the other crops (this script doesn't
     merge multiple sources for you — see `ml/dataset/README.md` for the
     options, in roughly increasing effort), or
   - keep Cotton/Soybean/Wheat/Rice on Demo AI Mode indefinitely even
     after Tomato goes live — `AI_MODE` is an all-or-nothing switch today
     (see "Known limitations" below), so this needs a small code change,
     not just a config flip.

This is exactly the kind of thing worth being upfront with SIH judges
about: the model covers what it was actually trained on, and the gap for
Indian-specific crops is a known, stated limitation rather than something
papered over with a coverage claim it can't back up.


### How to actually run this (on your own machine or Colab)

```bash
# 1. Prepare the PlantDoc dataset (clones + converts automatically)
python ml/dataset/prepare_dataset.py

# 2. Train (needs a GPU for reasonable speed — Colab's free tier works)
pip install ultralytics
python ml/training/train.py --epochs 100

# 3. Validate before trusting it
python ml/inference/test_inference.py --image path/to/test_leaf.jpg

# 4. Go live
# in backend/.env: AI_MODE=production
uvicorn app.main:app --reload
```

### Known limitations / remaining issues

- **No model has been trained. No dataset has been downloaded or
  prepared.** This stage is pipeline + integration code only — treat
  `backend/models/cropguard-yolo.pt` as not existing until you put it
  there yourself.
- **`_run_yolo_inference()` is unexecuted**, same as everything else in
  this backend so far — the box-coordinate conversion math has been
  reasoned through carefully but not run against real YOLO output. Test
  it with `test_inference.py` and a few known images before trusting the
  bounding boxes on the actual result screen.
- **Affected-area estimation is a coarse proxy** (summed box area, capped
  at 100%) — a real segmentation model or mask head would give a genuine
  pixel-level estimate. Worth flagging to judges as a known
  simplification if asked, per section 13's "demo estimate" honesty
  requirement — though note `Severity.is_demo` is correctly `False` for
  this live-model path, so the frontend won't mislabel it as a demo
  value once it's live; the imprecision itself just isn't visible in the
  UI yet.
- **Class imbalance and per-crop coverage aren't addressed** — depending
  on the dataset chosen, some crops/diseases may have far more training
  images than others. Worth checking `results.csv` from training before
  trusting per-class confidence scores equally.
- **`AI_MODE` is all-or-nothing** — there's no way today to run tomato
  detections through a trained model while cotton/wheat/rice keep using
  Demo AI Mode, even though that's the realistic path given PlantDoc's
  coverage gap. `ai_service.analyze_image()` would need a per-crop check
  (e.g., "does the loaded model's class list include this crop's
  diseases?") before falling back to demo per-crop instead of globally —
  worth building if training only covers a subset of crops.

---

## Stage 7 — Real Severity Estimation

Stage 6 shipped `_run_yolo_inference()` with a known, stated gap: affected
area was estimated by summing YOLO box area, which over-counts (a
rectangle around an irregular lesion isn't the lesion) and ignores how
much of the tissue *inside* that box is actually diseased versus healthy
leaf sharing the same box. Stage 7 replaces that with real pixel-level
segmentation — and this stage is different from every one before it in
one important way: **it's the first backend code in this project that has
actually been executed and verified**, not just reasoned through.

### Why this stage could be tested when the others couldn't

`severity_service.py`'s logic — HSV color segmentation via OpenCV — only
needs `opencv-python`, `numpy`, and `PIL`, all of which happen to already
be installed in the sandbox this was built in. No network, no GPU, no
Supabase project needed. So unlike `ai_service.py`'s YOLO path,
`supabase_client.py`, or anything touching FastAPI/pydantic (none of
which are installed here), this module could genuinely be run against
real synthetic test images and checked against known ground truth.

### What was built — and tested

- **`backend/app/services/severity_service.py`** — segments each photo
  into "plant tissue" (green + yellow/brown/necrotic tones) versus
  background, then "healthy green" versus "lesion" within that plant
  region. `affected_area_percent` = lesion pixels ÷ plant pixels,
  restricted to the union of YOLO's detection boxes when available.
- **Actually run against synthetic test images** (a green square with a
  circular lesion of known size) across lesion sizes from 0% to 75% of
  leaf area — estimates tracked ground truth within ~0.5 percentage
  points at every size tested.
- **A real bug caught and fixed via this testing**: the first hue
  threshold for "healthy green" was wide enough to also classify yellow
  lesions (chlorosis, early rust) as healthy tissue — a synthetic yellow
  lesion came back as 0.0% affected area before the fix, 8.2% after
  (ground truth was ~8%). This is exactly the kind of bug that would have
  shipped silently without executable tests, given every earlier backend
  stage in this project was written but never run.
- **`backend/tests/test_severity_service.py`** — a pytest suite encoding
  everything above (ground-truth tracking, empty-plant edge case, the
  yellow-lesion regression, box-restriction behavior, the 100% cap,
  severity threshold boundaries) so this stays verified as the code
  changes, not just verified once in this conversation.
- **`ai_service.py`'s `_run_yolo_inference()` now calls this** instead of
  summing box area — `Severity.affected_area_percent` for a real
  (non-demo) scan is now a genuine per-pixel estimate.

### How to verify this yourself

```bash
cd backend
pip install -r requirements-dev.txt  # includes pytest
# also uncomment opencv-python-headless in requirements.txt first
pytest tests/test_severity_service.py -v
```

All 8 tests (20 assertions across parametrized cases) passed when run
during this build — this isn't a "should work" claim like the rest of
this backend, it's a "did work, here's how to check yourself" one.

### Known limitations / remaining issues

- **This is still a heuristic, not ground truth**, even though it's
  tested. HSV color segmentation will misfire on: non-green cultivars,
  heavy shadow or glare, photos with other green things in frame (grass,
  neighboring plants), and diseases that don't discolor tissue much
  (some viral symptoms, early-stage pest damage before visible browning).
  The severity_service.py docstring states this directly — treat its
  output the same way the rest of the app treats any model number: a
  decision-support estimate, not a lab measurement.
- **Real segmentation testing used synthetic images**, not real leaf
  photos — clean geometric shapes with solid colors. Real photos have
  texture, uneven lighting, and blurred lesion boundaries that synthetic
  test images don't capture. Worth re-validating against actual PlantDoc
  images (or your own photos) once you can run this outside the sandbox,
  before trusting it in front of judges.
- **The rest of the backend remains unexecuted** — this stage validates
  `severity_service.py` specifically; `ai_service.py`'s integration of it
  (the `_run_yolo_inference` function as a whole), the FastAPI route
  layer, and everything touching Supabase are still reasoned-through
  code, not run code, for the same reason as every prior stage: FastAPI,
  pydantic, and ultralytics aren't installable without network access
  here.
- **Only tested at even, filled-circle lesion shapes.** Real disease
  lesions are irregular, sometimes speckled rather than solid, and can
  cluster in patterns morphological opening might partially erase. Worth
  a stress test with more irregular synthetic shapes if you want higher
  confidence before relying on this for a demo.

---

## Stage 8 — Dataset Connected, Auth Fixed, Google Sign-in, 5-Language AI Assistant

Four things were asked for here: connect the dataset, fix login and
sign-up, add Google login, and add an AI assistant that converses in five
languages. All four are done. This is also the stage where a lot of the
earlier "reasoned through but never run" code finally got executed —
**230 backend tests pass**, the dataset conversion has actually been run
end to end, and the frontend builds clean.

### 1. Dataset connected (PlantDoc → YOLO)

`ml/dataset/prepare_dataset.py` was rewritten and **run**. It clones
PlantDoc, reads the real Pascal VOC XML annotations, and converts them to
YOLO format.

What it produces, measured — not estimated:

| Split | Images | Backgrounds | Boxes |
|---|---|---|---|
| train | 724 | 65 | 1,893 |
| val | 127 | 12 | 250 |
| test | 158 | 14 | 269 |

- **`CLASS_MAP` covers all 29 PlantDoc labels.** 18 disease labels map to
  14 canonical classes; the 11 "healthy" labels map to `None`, which
  makes them background/negative samples (empty `.txt` files) rather than
  being silently dropped. That's what teaches the model to *not* fire on
  a healthy leaf.
- **`ml/training/data.yaml` is now generated, with real box counts per
  class** — it used to be hand-written and wrong.
- `spider_mite_damage` is dropped automatically at 1 instance
  (`--min-instances`, default 20). A class with one example teaches
  nothing and inflates the class list.
- The source TRAIN/TEST split is honoured; val is carved out of train at
  15% with a fixed seed, so results are reproducible.
- Two of the 1,279 XML files have a zero `<size>` element — recovered by
  reading the real dimensions with Pillow instead of discarding them.

**The recommendation engine was the actual bug this exposed.** TEMPLATES
covered 7 classes while the dataset produces 14, and the fallback
returned `TEMPLATES["early_blight"]` — so a corn rust detection would
have shown a farmer tomato early-blight advice under a corn rust
heading. Now: 19 disease/pest templates plus `healthy`, `low_confidence`
and an explicit `unknown` fallback, with
`test_every_model_class_has_a_template` failing the build if
`data.yaml` ever gains a class without reviewed guidance.

```bash
python ml/dataset/prepare_dataset.py          # clones + converts
python ml/dataset/prepare_dataset.py --no-download   # re-convert an existing clone
```

### 2. Login and sign-up fixed

These were the real defects, not cosmetic ones:

- **Infinite spinner on a corrupt session.** A malformed `cg_user` in
  localStorage made `JSON.parse` throw inside the auth provider's mount
  effect, so `loading` never became `false` and the app hung on a
  spinner forever — unrecoverable without devtools. `readStoredUser()`
  now parses defensively and clears the bad entry.
- **No session validation on load.** A stale token painted a logged-in
  UI that then 401'd on every request. The provider now calls
  `GET /api/auth/me` on mount and only clears the session on a real
  401/403 — a network blip no longer logs you out.
- **No refresh token.** Sessions died when the access token expired.
  `cg_refresh_token` is now stored and `apiFetch` refreshes once on a
  401 and retries. The refresh is **single-flight**: Supabase invalidates
  a refresh token the moment it's used, so concurrent 401s share one
  refresh promise instead of racing each other into a logout.
- **"Confirm your email" was rendered as a failure.** Sign-up with email
  confirmation on returned a response the client threw on, so a
  successful registration told the user it had failed. There's now a
  proper "Almost there" screen.
- **Password reset promised mail it could never send.** The form accepted
  a mobile number and then said "check your inbox". Supabase's recover
  endpoint is email-only, so the form is email-only and the API returns
  `{sent: false, message}` for anything else.
- **FormData uploads had `Content-Type: application/json` forced onto
  them**, which breaks multipart boundary parsing. Now omitted for
  `FormData` bodies.
- **422s rendered as "Request failed (422)".** `main.py` now has a
  `RequestValidationError` handler that flattens pydantic errors into the
  same `{status, error}` envelope as everything else, naming the field.
- Supabase error mapping is specific instead of generic: duplicate
  account → 409, unconfirmed email → 403, rate limit → 429, upstream 5xx
  → 502, timeout → 504, and phone-signup-not-enabled → 400 with the
  actual fix in the message.

26 offline auth tests cover this (`backend/tests/test_supabase_auth.py`).

### 3. Google sign-in

Supabase Auth PKCE flow, browser-side: `signInWithOAuth` →
`/auth/callback` → `exchangeCodeForSession` → the app adopts the session
and calls `/api/auth/me`, which provisions the `public.users` profile row
from the Google `full_name` if it's the first sign-in.

**You must do these two things in the Supabase dashboard — the code
cannot do them for you:**

1. **Authentication → Providers → Google**: enable it, and paste the
   client ID and secret from a Google Cloud OAuth 2.0 Web client. In that
   Google Cloud client, the authorised redirect URI is
   `https://<your-project-ref>.supabase.co/auth/v1/callback` (Supabase's
   URL, not yours).
2. **Authentication → URL Configuration → Redirect URLs**: add
   `http://localhost:3000/auth/callback`, plus your deployed origin's
   equivalent. Without this, Google returns to Supabase and Supabase
   refuses to bounce back to your app.

Then set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
in `frontend/.env.local` (see `frontend/.env.example`). If either is
missing the Google button hides itself rather than rendering a control
that can only fail — email/password login is unaffected.

### 4. AI assistant, five languages

`POST /api/assistant/chat` — a real conversational assistant on
`claude-opus-5`, reachable at `/assistant` in the app.

**English, हिंदी, मराठी, தமிழ், తెలుగు.** It answers in the language on
the farmer's profile even when they type in another one or in
transliterated Latin script.

It is grounded, not free-floating: the system prompt carries the app's
own reviewed recommendation templates plus that farmer's actual fields
and recent scans, so "what does my latest scan mean?" gets an answer
about their scan, and its advice stays consistent with what's on screen
next to it. Demo-mode scans are labelled `SIMULATED` in the context so it
can't present a simulated result as a real diagnosis.

**The safety rule is enforced twice, and the second one is what actually
guarantees it.** The prompt states the rule; then
`backend/app/services/crop_safety.py` scans every generated reply for
named active ingredients (49 patterns), doses per unit volume or area,
bare unit ratios, formulation strengths, and spray concentrations. A
reply that trips any rule is **replaced wholesale** — not redacted, since
a redacted dose still tells a farmer a chemical was recommended — with a
pre-translated message directing them to their KVK or state agriculture
department. Prompt instructions can be argued with; a regex cannot, which
is also why a prompt-injection attempt hidden in a field name can't turn
this into a spray advisor.

The same scan now also runs against the hand-written templates in
`test_recommendation_service.py`, so generated and reviewed text are held
to one standard, and a rule added for the assistant automatically starts
checking the templates too.

Also in this stage, because it was hollow before: the language picker
drove a UI where nothing changed. Sidebar navigation now actually
translates, and the picker in the sidebar, the settings page and the
register page all read from the `SUPPORTED_LANGUAGES` registry — three of
the five languages were previously unreachable from settings because the
`<option>`s were hardcoded.

```bash
# Assistant setup — one key, then it works.
# In backend/.env:  ANTHROPIC_API_KEY=sk-ant-...    (console.anthropic.com)
cd backend && uvicorn app.main:app --reload
```

Without the key the app is unharmed: `/assistant` shows "not set up on
this server yet" and every other feature works normally.

### How to verify all of this yourself

```bash
cd backend && pip install -r requirements.txt && python -m pytest -q   # 291 passed
cd ../frontend && npx tsc --noEmit && npm run build                    # clean
python ml/dataset/prepare_dataset.py --no-download                      # 1,009 images
```

`tests/test_i18n_dictionaries.py` is worth knowing about: it lives in the
backend suite because the frontend has no test runner, and it reads
`frontend/lib/i18n/*.json` directly. It fails the build if a language is
missing a key (which would silently render in English), if a string is
left as its English original, if a dictionary names a chemical, or if a
character has been copied in from the wrong script. That last check found
a real bug during this stage — a Tamil keyword in the assistant's mock
path began with a Devanagari **म** instead of a Tamil **ம**, so it could
never match. The two characters render almost identically, which is
exactly why a test has to look at the codepoints.

### Known limitations / remaining issues

- **Still no trained model.** The dataset is now genuinely prepared and
  `data.yaml` is real, but `ml/training/train.py` has not been run and
  `backend/models/cropguard-yolo.pt` does not exist. `AI_MODE=demo`
  remains the only working mode.
- **The assistant's model calls are covered by a stubbed client, not by
  live API calls.** 49 tests verify the prompt construction, the
  guardrail replacement path, the refusal path, and the error mapping
  without spending a token — but nobody has yet read a real Tamil or
  Telugu reply from the live model and judged its quality. Do that before
  demoing in a language you don't read.
- **The five translation dictionaries are unreviewed by native
  speakers.** They're careful translations, not verified ones. The
  assistant's *replies* are generated by the model and are likely to read
  more naturally than these static UI strings.
- **The guardrail's ingredient list is not exhaustive** and no such list
  could be. That's why the dose patterns matter: a chemical the list
  misses is still blocked the moment a quantity is attached to it. It
  also errs toward over-blocking, and a false positive is invisible in
  the UI — it looks identical to the guard working correctly.
  `test_crop_safety.py` pins 15 innocent sentences that must *not* trip
  as a defence against that.
- **The app has no mobile navigation.** The sidebar is `hidden md:flex`
  and the hamburger button in the topbar has no handler, so on a phone
  the assistant — and the dashboard, fields, and scan pages — can't be
  reached at all. This predates this stage and affects the whole app, but
  it matters more now: the assistant is written for a farmer standing in
  a field with a phone. Worth fixing before any demo on a handset.
- **The settings page still doesn't persist.** "Save Changes" is a
  `mockDelay` — there's no `PATCH /api/users/me`. The language choice
  does persist (localStorage), but a name or location edit is lost on
  reload.
- **Rotate the Supabase `service_role` key.** It was pasted into a chat
  transcript during setup. Do this in the Supabase dashboard before this
  goes anywhere near a real deployment.

---

## Stage 9 — MongoDB Replaces Supabase Postgres (data + image storage)

Requested: *"use mongoDB database (mongodb://localhost:27017)"*, with
Firebase Auth chosen for login/signup and Supabase to be removed entirely.
This stage does the **data half**, which is everything except login. It is
also the first stage where the backend was not just written but **run
against a real database** — 291 tests pass, and the round-trip ones talk
to a live `mongod`.

Why the data half first: it needs no credentials I don't have, and it
removes the error the app was actually failing with. The old stack read
tables through PostgREST, `database/schema.sql` had never been applied,
and so every screen died with `Could not find the table 'public.users' in
the schema cache`. MongoDB has no DDL step — collections appear on first
write — so that class of failure is gone rather than fixed.

### What was built

- **`backend/app/services/mongo_client.py`** — the whole data layer, in
  ~250 lines. It deliberately keeps the *shape* of the calls the API layer
  already made (`{"column": "eq.<value>"}` filters, `order`, `limit`,
  `select`), so the five route modules that use it needed an import swap
  and nothing else. Three decisions worth knowing:
  - Timestamps are **ISO-8601 UTC strings**, not BSON datetimes, because
    that is what PostgREST returned and every consumer downstream — the
    pydantic schemas, the assistant's context formatter, the frontend —
    was written against strings. ISO-8601 UTC also sorts
    lexicographically in chronological order, which is the only thing
    this app does with them.
  - `id` is an explicit UUID string field and Mongo's own `_id` is
    **never** exposed, so API responses stay byte-identical to the
    Postgres ones.
  - An unrecognised filter operator **raises** instead of being dropped.
    Silently discarding a filter here would widen a query from one
    farmer's rows to every farmer's rows, which is the worst failure this
    module could have. `_DEFAULTS` and `_insert_defaults()` carry what
    Postgres used to enforce in DDL (`gen_random_uuid()`, the
    `updated_at` trigger, column defaults).
- **`backend/app/services/storage_service.py`** — rewritten onto
  **GridFS**, replacing Supabase Storage. GridFS rather than a plain
  document because a document caps at 16 MB and a phone JPEG can approach
  it; GridFS rather than local disk because the rest of the state already
  lives in Mongo. Served by a new **`app/api/images.py`**.
- **`/health` now reports the database**, not just the process. It returns
  200 either way with an explicit `database: up | unreachable`, because
  "the API is alive" and "the data layer works" are different facts and a
  monitor that conflates them can't tell a crashed API from a stopped
  `mongod`.
- **Index creation runs at startup** and is deliberately non-fatal: a
  developer whose `mongod` isn't running still gets a server that boots
  and explains itself, rather than a process that refuses to start.
- **`scripts/seed_demo_data.py`** now takes `--user-id`, so you can load
  your own signed-in account with demo data. Every row is scoped by
  `user_id` and the API only returns rows matching the authenticated
  caller, so seeded data is invisible unless that uid matches.

### Verification — what was actually run

```bash
cd backend && python -m pytest -q                     # 291 passed
curl -s http://localhost:8000/health                  # {"status":"ok","database":"up"}
python -m scripts.seed_demo_data --user-id <your-uid> # idempotent, re-run safe
```

- **`tests/test_mongo_client.py`** (28) — the query-dialect parsers and
  insert defaults offline, plus round-trips against a live server. The
  most important one asserts that `neq.`/`gt.`/`in.` and a bare value all
  *raise*.
- **`tests/test_image_storage.py`** (10) — GridFS round-trip, chunk
  reassembly past the 255 KB chunk size, replace-not-duplicate on
  re-upload, and the HTTP route.
- **`tests/test_routes_mongo.py`** (22) — the real FastAPI routes with
  auth stubbed, because the seam this migration crossed is the *call
  sites*, not the layer in isolation. Covers the full scan flow, which is
  the one request that writes three collections and GridFS at once.
- Round-trip tests **skip** rather than fail without a `mongod`, and each
  uses a throwaway database, so they can never touch real scan data.
- Two of these were checked for teeth by breaking the code on purpose:
  making `image_url` relative failed 2 tests, and dropping the `user_id`
  filter from `GET /api/fields/{id}` failed the cross-user leak test.
  Both were restored and re-verified green.

### Known limitations / remaining issues

- **Auth is still Supabase.** `app/api/auth.py`, `app/utils/auth.py`'s
  `get_current_user`, and the `auth_*` half of `supabase_client.py` are
  untouched, and the frontend still uses `@supabase/supabase-js`. The
  Firebase swap is the other half of the decision and is not done. The
  app works today only because those Supabase Auth accounts still exist.
- **`mongodb://localhost:27017` has no authentication.** Fine while bound
  to 127.0.0.1 for development; it must not stay that way if this is ever
  reachable from anywhere else. Enable auth and use a credentialed URI
  before deploying.
- **Image URLs are unauthenticated**, exactly as the old public Storage
  bucket was. An `<img>` tag can't send a bearer header, so the
  protection is an unguessable UUID4 in the path and a leaked URL stays
  valid. Not a regression, but the right fix is short-lived signed URLs
  minted by the scan routes — not a bearer check on the image route.
- **No foreign keys.** Postgres cascaded deletes; Mongo doesn't. Deleting
  a field would now orphan its scans and alerts. The alerts route already
  degrades gracefully (a test pins the `"Field"` fallback), but there is
  no delete endpoint yet — worth building the cleanup *with* it rather
  than after.
- **`database/schema.sql` and the three migrations are now dead code**,
  along with `test_database_accepts_every_language_the_app_offers`, which
  reads the SQL. They're kept until the Firebase swap lands so nothing is
  deleted while a rollback is still plausible; the language-list invariant
  needs a new home on the Mongo path rather than simply being dropped.
- **`pip install motor` upgraded pymongo 4.6.0 → 4.9.2 globally** on this
  machine, which affects other MongoDB projects sharing the interpreter.
  A virtualenv per project would have avoided this.

---

## Next stage

Say **"START STAGE 8"** for weather/risk prediction polish, or
**"START STAGE 9"** for history/alerts UI work, or **"START STAGE 10"**
for testing and deployment — though given the honest state of things, it
might be worth circling back to actually run the full backend (install
deps, start Supabase, hit real endpoints) before adding more unexecuted
code on top of it.
