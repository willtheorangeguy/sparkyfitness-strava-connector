# API

The supported interface is the `sparkyfitness-strava` CLI, also used as the container entry point. Start with `--help`. JSON results go to stdout; handled API/configuration errors go to stderr and exit 1. No HTTP server is exposed.

Stop the watcher before stateful commands. Examples with numeric IDs and UUIDs show the argument format; substitute your own IDs before recovery.

## `auth-url`

Print consent URL and persist a 15-minute nonce.

```sh
docker compose run --rm connector auth-url
```

## `auth-complete`

Read full callback URL from stdin and store OAuth credentials.

```sh
docker compose run --rm -i connector auth-complete
```

## `check`

Verify source API key owner and Strava athlete bindings.

```sh
docker compose run --rm connector check
```

## `preview`

Read eligible sessions, mappings and problems; save initial boundary.

```sh
docker compose run --rm connector preview
```

## `exercises`

Print supported Strava identifiers without opening state.

```sh
docker compose run --rm connector exercises
```

## `map`

Override automatic matching for a SparkyFitness exercise UUID. Use an ID from preview.

| Argument | Type and constraint |
| --- | --- |
| `exercise` | UUID |
| `strava_type` | supported identifier |

```sh
docker compose run --rm connector map 00000000-0000-0000-0000-000000000001 BARBELL_BENCH_PRESS
```

## `mappings`

Print saved manual overrides. Automatic choices appear in preview, not this list.

```sh
docker compose run --rm connector mappings
```

## `sync`

Poll pending jobs, then submit ready sessions up to the cycle limit.

```sh
docker compose run --rm connector sync
```

## `watch`

Run sync repeatedly using SYNC_INTERVAL_SECONDS.

```sh
docker compose run --rm connector watch
```

## `status`

Print authorization, athlete, source, exports and cooldown.

```sh
docker compose run --rm connector status
```

## `reconcile`

Verify the remote external ID and attach a known upload.

| Argument | Type and constraint |
| --- | --- |
| `session` | exact preset: or plan: key from preview/status |
| `upload_id` | integer |

```sh
docker compose run --rm connector reconcile preset:00000000-0000-0000-0000-000000000001 1
```

## `reconcile-activity`

Verify the remote external ID and attach a known activity.

| Argument | Type and constraint |
| --- | --- |
| `session` | exact preset: or plan: key from preview/status |
| `activity_id` | integer |

```sh
docker compose run --rm connector reconcile-activity preset:00000000-0000-0000-0000-000000000001 1
```

## `retry`

After checking Strava, approve an unresolved failed or uncertain attempt for resubmission.

| Argument | Type and constraint |
| --- | --- |
| `session` | exact preset: or plan: key from preview/status |
| `--confirm-no-activity` | required flag |

```sh
docker compose run --rm connector retry preset:00000000-0000-0000-0000-000000000001 --confirm-no-activity
```

## External APIs

The source client permits GET only and sends `x-api-key`. It consumes `/api/identity/user`, paginated `/api/v2/exercise-entries/history` (`page`, `pageSize=100`) and `/api/workout-plan-templates` when plan assignments require resolution. The identity response must identify the same authenticated and active user.

History responses contain `sessions` and pagination with the requested page number and boolean `hasMore`. Repeated/empty pages with more data and malformed pagination cause errors. Sessions are deduplicated by type and ID.

Strava uses OAuth and API v3 athlete, multipart JSON uploads, upload polling and activity lookup. `check` returns `sparkyfitness` (URL and user) and `strava_athlete`. `preview` returns plans with source keys, mapping choices, missing names, problems and reasons. `sync` returns submitted/export/blocked/changed/skipped information, or a rate-limited state with `retry_at`. See [the engine](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/blob/HEAD/src/sparkyfitness_strava/engine.py) for the output construction.
