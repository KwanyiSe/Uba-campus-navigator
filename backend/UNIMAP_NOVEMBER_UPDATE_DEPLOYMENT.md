# UNIMAP November update — deployment and verification

This update adds map-page community/feedback UI, a protected health-check option,
and draft compensation-geofence storage/import support. It does **not** connect
to or modify the live Neon database automatically.

## Important data safety
- No database is dropped, flushed, or reset.
- Migration `0018_building_compensation_geofence` only adds four columns to
  `campus_building`; it does not delete or rewrite existing SiteVisit,
  DailyStats, DailyVisit, buildings, or attendance data.
- Geofence import is a separate, opt-in management command. It defaults to a
  dry run and writes fences as `draft`, never `approved`.
- Back up Neon before applying any migration.

## 1. Install and migrate
From `backend/` with the project virtual environment active:

    pip install -r requirements.txt
    python manage.py check
    python manage.py migrate
    python manage.py test campus.tests

Configure the existing Neon connection variables in Render. Do not commit or
share `.env`; use Render Environment settings for production secrets.

## 2. Draft geofence import (only after visual approval)
The included `campus/data/geofence_review_draft.json` is the review dataset.
It is still a draft: the radial 10 m compensation boundary is illustrative,
and the field-facing LC Block extension / final Block 17 shape still need
human confirmation.

First inspect exact name matches:

    python manage.py load_geofence_review

Only if every intended building matches the right database record and the map
has been approved, run:

    python manage.py load_geofence_review --apply

The command writes `geofence` and `compensation_geofence` as draft values.
It does not activate attendance or mark fences approved. Names that do not
match exactly are skipped and reported; no fuzzy matching is performed.

## 3. Cron-job.org health monitor
The `/health/` endpoint already exists and returns plain-text `ok` without
querying the database. `SiteVisitMiddleware` excludes `/health/`, so monitor
requests do not create SiteVisit rows or increment DailyStats/DailyVisit.

For authenticated monitoring:
1. Generate a long random token locally (for example with Python
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
2. Add `HEALTH_CHECK_TOKEN` to Render Environment using that token.
3. In cron-job.org create a GET job for `https://unimaps.tech/health/`.
4. Set the schedule to every 5 minutes.
5. Add request header `X-UNIMAP-HEALTH-TOKEN` with the same token.
6. Save and use cron-job.org's execution history to verify HTTP 200.

If `HEALTH_CHECK_TOKEN` is blank, `/health/` remains public for simple checks.
When configured, missing/wrong header receives HTTP 401. Do not put the token
in the URL or commit it to Git.

A five-minute monitor is best-effort and does not guarantee that a Render free
service will never spin down; the scheduler may be delayed and the host may
restart independently.

## 4. Map community popup and Report a Problem
On the campus map, both guests and authenticated users see the community
invitation unless they marked “I've joined” or dismissed it for the current
login/session. WhatsApp membership cannot be verified by UNIMAP; “I've joined”
is a user confirmation stored in that browser's local storage.

The map now has:
- a permanent “Report a problem” floating button;
- a “Report a problem” button inside the community popup;
- a form for category and description;
- name/email fields for guests;
- submission through the existing `/api/feedback/submit/` endpoint.

Feedback remains stored in the existing Feedback table. This does not add a
new feedback model or change old records.

## 5. Test checklist
- Guest: open `/map/`; verify community popup; dismiss; refresh same tab and
  verify it stays dismissed for that session.
- Guest: click Report a problem, enter name/email/category/description, submit,
  and verify success.
- Logged-in user: open map; verify popup; choose “I've joined”; reload and
  verify it no longer appears in that browser for that account.
- Logged-in user: submit a map report and verify it appears in Django admin
  under Feedback.
- Health without configured token: GET `/health/` should return 200 `ok`.
- Health with token configured: correct header returns 200; missing/wrong
  header returns 401.
- Check admin analytics before/after several `/health/` calls; health checks
  should not change visitors, DailyStats, DailyVisit, or SiteVisit.
- Check Neon migration history and verify migration 0018 is applied once.

## Scope deliberately not included
- Offline/PWA attendance queue (deferred as requested).
- Automatic timetable-aware attendance approval or GPS compensation logic.
  The new fields only store both polygons; attendance policy must be designed
  and tested before use.
- Final geofence approval. Block 17 and LC Block still require visual review
  and LC's field-facing side must be confirmed.
