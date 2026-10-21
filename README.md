# SparkyFitness → Strava connector

Export logged SparkyFitness strength workouts to Strava with structured exercises,
sets, repetitions, kilogram loads, and timed sets. This separate Docker service
reads SparkyFitness without modifying it. Based on
[wger-strava-connector v0.2.1](https://github.com/willtheorangeguy/wger-strava-connector),
using Strava's documented [strength JSON uploads](https://developers.strava.com/docs/uploads/#json---strength-training-limited).
Targets SparkyFitness v1.8.0, pinned by the sibling addon harness.

Download the setup files from [release v0.1.0](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/releases/tag/v0.1.0).
The release workflow publishes regular/media images and attaches version-matched
Compose and environment downloads.

## Selection rules

- Export grouped workout instances linked to a preset or plan, keeping separate
  instances separate even on the same day.
- Combine ungrouped plan logs by plan template, scheduled session (session index
  or weekday), and diary date. Skip unresolved assignments rather than guessing.
- Exclude standalone exercises, unlinked freeform workouts, and prescribed templates.
- Export only sets with a completion timestamp. Wait five minutes after the latest
  completion and recorded end; exclude future workouts and empty workouts.
- Skip missing/invalid timing with a reason in preview. Corrected source data can
  become eligible later. Block the whole workout for unmapped/invalid completed sets.

**Partial workouts export once.** Later completed sets report `changed`; they are
not appended or reuploaded. Increase `SETTLE_SECONDS` for long breaks.

SparkyFitness stores weights in kg even when displaying pounds. Export these kg
directly, including positive added bodyweight loads; never add body mass. Unloaded
bodyweight sets omit load. Negative assistance, distance sets, unknown modalities,
invalid numbers, and fractional repetitions are blocked. Timed sets use seconds.

Activity timing spans earliest recorded exercise start through latest recorded end
or completion. `WORKOUT_TIMEZONE` interprets local times; ambiguous/nonexistent DST
times are skipped. Completion times are not mislabeled as set start times. Workout
and exercise notes appear in descriptions. Calories, GPS, heart rate, RPE/RIR,
supersets, and rest targets are not uploaded as structured metrics.

## Docker setup

The connector is an always-running companion service to SparkyFitness. After
one-time authorization and exercise mapping, run
`docker compose up -d` to start `watch`. Keep it running
alongside SparkyFitness; daily manual sync
commands are unnecessary. The existing-stack overlay runs the same watcher on the
main service's network; standalone deployment reaches SparkyFitness by URL.

The watcher checks immediately, then every `SYNC_INTERVAL_SECONDS` (900 seconds).
It automatically uploads newly eligible preset/plan workouts after the five-minute
settling period, then polls Strava until processing finishes. Defaults normally
mean 5–20 minutes after the last completion/recorded end. Your completed-set-only
selection remains in effect: unfinished sets are omitted, and later completed sets
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
docker compose run --rm connector exercises
docker compose run --rm connector map EXERCISE_UUID BARBELL_BENCH_PRESS
docker compose run --rm connector mappings
docker compose run --rm connector sync
docker compose up -d
```

Replace `EXERCISE_UUID` with an ID from preview. Mappings explicitly approve an
identifier from the inherited 656-exercise Strava catalog; names are never guessed.
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
processing upload exists; failed uploads need explicit retry too. Rate limits persist
cooldowns, including next UTC day for daily exhaustion. Uncertain OAuth refresh needs
reauthorization. Errors omit response bodies/secrets. The source client permits GET only.

## Experimental cards and browser tools

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
Automatic generation/attachment during production sync remains pending. The
attachment helper rejects live Strava URLs. See [design notes](design/README.md).

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
