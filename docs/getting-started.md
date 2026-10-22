# Getting started

## Prerequisites

Use Docker with Compose v2, a SparkyFitness v1.8.0 instance and an API key with diary and plan read access. Register your own Strava application with callback domain `localhost`. Check Docker with `docker compose version`.

## Install

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

## What just happened

The connector bound the API key owner and Strava athlete to a persistent journal. It selected native preset/plan workouts and exported eligible completed sets. Preview records its initial date boundary but does not upload activities.

## Next steps

- Read [selection and recovery](usage.md) before exporting partial workouts.
- Use [configuration](configuration.md) for defaults and the existing-stack variable names.
- Add [workout images](media.md) after core exports work.
