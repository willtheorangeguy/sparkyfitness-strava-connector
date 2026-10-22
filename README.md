# SparkyFitness → Strava connector

Export logged SparkyFitness strength workouts to Strava with structured exercises,
sets, repetitions, kilogram loads, and timed sets. This separate Docker service
reads SparkyFitness without modifying it. Based on
[wger-strava-connector v0.2.1](https://github.com/willtheorangeguy/wger-strava-connector),
using Strava's documented [strength JSON uploads](https://developers.strava.com/docs/uploads/#json---strength-training-limited).
Targets SparkyFitness v1.8.0, pinned by the sibling addon harness.

Download the setup files from [release v0.2.0](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/releases/tag/v0.2.0).
The release workflow publishes regular/media images and attaches version-matched
Compose and environment downloads.

## Selection rules

- Export only native SparkyFitness workouts (`source: sparky` or the API's
  native default `manual`). Exclude Garmin and other provider imports, including
  native groups containing imported exercises. Entries with no source evidence
  are excluded. Imported workouts never require exercise mappings.
- Export grouped workout instances linked to a preset or plan, keeping separate
  instances separate even on the same day.
- Combine ungrouped plan logs by plan template, scheduled session (session index
  or weekday), and diary date. Skip unresolved assignments rather than guessing.
- Exclude standalone exercises, unlinked freeform workouts, and prescribed templates.
- Export only sets with a completion timestamp; unfinished sets remain excluded. Wait five
  minutes after the latest completion and activity end; exclude future and empty workouts.
- Prefer SparkyFitness's `total_duration_minutes` for the activity duration. This
  is the sum of exercise durations, and may exclude pauses. Use the earliest
  recorded exercise start; if all starts are missing, estimate the start as the
  final set completion minus the reported total. No individual set times are uploaded.
- Skip missing/invalid timing when neither a recorded start nor an estimated
  start is available, with a reason in preview. Corrected source data can
  become eligible later. Block the whole workout for unmapped/invalid completed sets.

**Partial workouts export once.** Later completed sets report `changed`; they are
not appended or reuploaded. Increase `SETTLE_SECONDS` for long breaks.

SparkyFitness stores weights in kg even when displaying pounds. Export these kg
directly, including positive added bodyweight loads; never add body mass. Unloaded
bodyweight sets omit load. Negative assistance, distance sets, unknown modalities,
invalid numbers, and fractional repetitions are blocked. Timed sets use seconds.

Without a reported total, activity timing spans earliest recorded exercise start
through latest recorded end or completion. `WORKOUT_TIMEZONE` interprets local times; ambiguous/nonexistent DST
times are skipped. Completion times are not mislabeled as set start times. Workout
start timestamps are serialized in UTC with a `Z` suffix: live Strava processing
rejects the otherwise equivalent `+00:00` form. Fractional seconds are preserved.
Workout and exercise notes appear in descriptions. Calories, GPS, heart rate, RPE/RIR,
supersets, and rest targets are not uploaded as structured metrics.

## Docker setup

The connector is an always-running companion service to SparkyFitness. After
one-time authorization, run
`docker compose up -d` to start `watch`. Keep it running
alongside SparkyFitness; daily manual sync
commands are unnecessary. The existing-stack overlay runs the same watcher on the
main service's network; standalone deployment reaches SparkyFitness by URL.

The watcher checks immediately, then every `SYNC_INTERVAL_SECONDS` (900 seconds).
It automatically uploads newly eligible preset/plan workouts after the five-minute
settling period, then polls Strava until processing finishes. Defaults normally
mean 5–20 minutes after the last completion/recorded end. Your completed-set-only
selection remains in effect for native workouts: unfinished sets are omitted, and later completed sets
do not update an activity already exported.

Temporary main-service/Strava API failures are retried on later cycles.
`restart: unless-stopped` restarts a failed container or resumes it after a Docker
restart. Keep state; missing mappings hold workouts, and uncertain uploads need
reconciliation. Neither condition silently creates a duplicate activity.

Requires Docker Desktop/Linux containers and Compose. Download `docker-compose.yml`
and `env.example` from the release into an empty directory. Rename `env.example`
to `.env`, fill in the settings below, then run `docker compose pull`. No source
checkout, Python installation, or local build is needed.

Configure `.env`:

- `SPARKYFITNESS_BASE_URL`: origin reachable from the container, without `/api`.
  Default `http://host.docker.internal:8102` reaches the local harness.
- `SPARKYFITNESS_API_KEY`: key with diary and plan read access; the harness uses
  a full-scope key.
- `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET`: your own application from
  [Strava API settings](https://www.strava.com/settings/api), callback domain `localhost`.
- `WORKOUT_TIMEZONE`: IANA timezone, for example `America/Edmonton`.
- `EXPORT_SINCE`: inclusive diary-date boundary (`YYYY-MM-DD`). Blank persists
  today's UTC date on first preview/sync. Set explicitly for historical backfill.

```sh
docker compose run --rm connector auth-url
docker compose run --rm -i connector auth-complete
```

Open the link and grant `read`, `activity:write`, and `activity:read_all`. The localhost
redirect gives an expected connection error; no callback server is needed. Paste
the complete callback URL into `auth-complete`. Keep it private. Authorization
validates the nonce, its 15-minute expiry, and scopes. Tokens persist and rotate.

```sh
docker compose run --rm connector check
docker compose run --rm connector preview
docker compose run --rm connector sync
docker compose up -d
```

Exercises match automatically against the bundled 656-exercise Strava catalog
using normalized names and common library aliases. Preview's `exercise_mappings`
lists each chosen `strava_type` and its matching `method`: `catalog`, `alias`, or
`manual`. Some aliases use a broader supported category where Strava lacks the
exact variation (for example, Pec Static Stretch uses `STRETCH`). Garmin and other
imports remain excluded before matching.

Manual overrides are optional and take priority over automatic matches:

```sh
docker compose run --rm connector exercises
docker compose run --rm connector map EXERCISE_UUID BARBELL_BENCH_PRESS
docker compose run --rm connector mappings
```

Replace `EXERCISE_UUID` with an ID from preview. `mappings` lists saved manual
overrides; automatic matches are recalculated without writing overrides. Unknown
or ambiguous names remain blocked rather than receiving a fuzzy guess. Preview
lists their IDs in `missing`, names in `missing_exercises`, and a reason. Unmatched
sets are omitted from the preview payload; the whole workout is held until resolved.
Background sync defaults to 900 seconds, five-minute settling, and ten new uploads
per cycle. Later cycles poll asynchronous jobs. One account/athlete per instance.
Stop the background service before opening the same state with maintenance commands.

## Add to an existing SparkyFitness stack

`docker-compose.yml` pulls a versioned image without a checkout/build. Use with `.env`
or set `CONNECTOR_IMAGE` / `CONNECTOR_VERSION` for your registry.
It shares the developer deployment's project and volume; stop one before switching.

For an existing stack, add `examples/docker-compose.sparkyfitness.yml` as an overlay
and merge `examples/sparkyfitness.env.example` into the stack's `.env`. Set
`STRAVA_SPARKYFITNESS_BASE_URL` for your service name; default is
`http://sparkyfitness-server:3010`, while the harness uses `http://server:3010`.
Attach the connector to the server's Compose network.

```sh
docker compose -f docker-compose.yml -f docker-compose.sparkyfitness.yml run --rm strava-connector preview
docker compose -f docker-compose.yml -f docker-compose.sparkyfitness.yml up -d strava-connector
```

The overlay owns a different state volume; migrate state before switching.
Never reuse wger state. Avoid overlapping export paths for the same workouts;
cross-app duplicate prevention is not guaranteed. Visibility follows Strava settings.

## State and recovery

Retain/back up state with the service stopped: it holds account bindings, OAuth,
mappings, the export boundary, and upload journal. Deleting it can cause duplicates.
Edits/deletions never update or delete an existing Strava activity. Account or
application changes require separate state.

A timeout/crash/server error during upload leaves an `uncertain` job that is never
automatically resubmitted. Use the exact session key from preview/status, including
its `preset:` or `plan:` prefix, through Compose `run --rm connector`:

```sh
sparkyfitness-strava reconcile SESSION_KEY UPLOAD_ID
sparkyfitness-strava reconcile-activity SESSION_KEY ACTIVITY_ID
sparkyfitness-strava retry SESSION_KEY --confirm-no-activity
```

Reconciliation verifies the external ID. Retry only after confirming no activity or
processing upload exists; failed uploads need explicit retry too. For a known upload
ID, retry checks Strava's status and refuses successful or still-processing jobs.
An approved retry keeps the workout identity and previous attempt history, but
uses a fresh `.retryN.json` file identifier because Strava caches failed jobs by
external ID. It revalidates the source on the next sync and never retries merely
because the source was edited. Rate limits persist
cooldowns, including next UTC day for daily exhaustion. Uncertain OAuth refresh needs
reauthorization. Errors omit response bodies/secrets. The source client permits GET only.

## Card previews and browser login

```sh
docker compose -f compose.media.yaml run --rm preview
docker compose -f compose.media.yaml run --rm --service-ports media-login
```

The commands above build media tools from a checkout. For the published image, use
the release's `docker-compose.media.yml` instead of `compose.media.yaml`.
Preview writes synthetic SparkyFitness cards and 30 illustrated comparisons to
`design/previews/`. Login opens `http://localhost:6080/vnc.html`; enter the printed
viewer password and sign into Strava yourself, including MFA. Stop with Ctrl+C to
persist cookies. Tunnel port 6080 over SSH for remote hosts. Keep profiles private.
Automatic generation and attachment are available through the companion worker below.
The separate mock test helper rejects live Strava URLs. See [design notes](design/README.md).

## Validation and releases

Developers can copy `.env.example` to `.env` and build with
`docker compose -f compose.build.yaml build`. Add `-f compose.build.yaml` to all
connector commands when using the local image. Stop the published-image deployment
first; the local build shares its project and state volume.

```sh
python test_harness.py
# Optional: --sparkyfitness-harness /path/to/sparkyfitness-addon-harness
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python -m pytest -q -m 'not integration'
docker compose -f compose.media.test.yaml build test
docker compose -f compose.media.test.yaml up -d --wait mock-strava-web
docker compose -f compose.media.test.yaml run --rm test
docker compose -f compose.media.test.yaml down
```

Integration uses real SparkyFitness and mock Strava, creates/removes a dedicated
account, and preserves demo history. No real Strava credentials or uploads.
Results: `reports/junit.xml`. CI covers units, Compose, container smoke checks, and
media; manual dispatch also runs the harness. Release workflows prepare regular/media
amd64/arm64 images and setup downloads. See [RELEASING.md](RELEASING.md) and
[VALIDATION.md](VALIDATION.md). MIT licensed; inherited assets retain their notices.

## Automatic workout images

Set `MEDIA_ENABLED=true` and `MEDIA_UNITS=lb` (or `kg`) in `.env`, then recreate the core connector. Each new successful export creates an immutable image job. The activity description also includes total external weight times repetitions; timed holds and unrecorded body weight add no volume.

Download `docker-compose.media.yml` from the same release beside your standalone `.env`, then sign into the same Strava account once:

```sh
docker compose -f docker-compose.media.yml pull
docker compose -f docker-compose.media.yml run --rm --service-ports media-login
docker compose -f docker-compose.media.yml up -d media-worker
docker compose -f docker-compose.media.yml run --rm --no-deps media-worker status
```

The standalone core connector must already have created its state volume. For an existing source stack, set `STRAVA_MEDIA_ENABLED=true` and `STRAVA_MEDIA_UNITS=lb` in that stack's environment, and set `CONNECTOR_STATE_VOLUME` beside the media Compose file to the actual `<stack>_strava_connector_state` volume name. For source-checkout builds, use `compose.media.yaml` in the commands above and build `media-worker` first.

Stop `media-worker` before interactive login, and start it again afterwards. Browser cookies are separate from API OAuth. The companion shares the core state volume but never opens its SQLite database. It attaches two 1080 x 1080 cards generated from the exact exported sets, without changing activity fields. Missing muscle metadata is shown as unavailable. Existing exports are not backfilled automatically.

Jobs and receipts persist under `/data/media`. An interrupted file selection or Save is held as `uncertain`; inspect the activity and receipt before any manual recovery. Never delete a receipt simply to retry an upload. Browser login expiry leaves new jobs pending; log in again to resume. Existing activity photos are held for review. API workout exports continue independently of browser failures.

Automatic images are included in v0.2.0. Older releases provide only preview/login tools. The mock-only attachment helper retains its origin restriction.

Muscle highlighting uses explicit source metadata: SparkyFitness's completed-exercise snapshots or wger's exercise-info API (`muscles` and `muscles_secondary`). Source names and Latin anatomy names are translated into the diagram's regions. Primary takes precedence when an area is also secondary in another exercise. Uncompleted SparkyFitness exercises are excluded. Unknown names remain unhighlighted and are recorded under `unmapped_muscles` in the image job; wger metadata fetch failures are recorded under `unavailable_exercises` and do not block the workout upload. Previously attached image files are not rewritten automatically.
