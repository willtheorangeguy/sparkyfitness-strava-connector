# Configuration

## Precedence

The process reads explicit environment values before code defaults. The CLI has no settings flags and does not read configuration files. Standalone Compose supplies `.env` through `env_file`; Compose interpolation chooses the image and version separately. The existing-stack overlay translates its prefixed variables into the process environment. `EXPORT_SINCE`, when set, overrides the saved boundary.

## Process environment

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `DATA_DIR` | path | `/data` | State directory; example `./runtime` for a host Python install. |
| `SPARKYFITNESS_BASE_URL` | URL | `http://host.docker.internal:8102` | SparkyFitness API origin reachable from the container; example `https://sparkyfitness.example.org`. |
| `SPARKYFITNESS_API_KEY` | string | `empty` | API key with diary and plan read access; example `your-sparkyfitness-api-key`. |
| `STRAVA_CLIENT_ID` | string | `empty` | Your application ID; example `12345`. |
| `STRAVA_CLIENT_SECRET` | string | `empty` | Your application secret; example `your-client-secret`. |
| `STRAVA_BASE_URL` | URL | `https://www.strava.com` | Override for tests; example `http://mock-strava:8080`. |
| `WORKOUT_TIMEZONE` | IANA timezone | `UTC` | Local display offset; example `America/Edmonton`. |
| `EXPORT_SINCE` | date | `empty` | Inclusive diary-date boundary; example `2026-01-01`. Empty uses saved boundary, then today UTC. |
| `SYNC_INTERVAL_SECONDS` | integer | `900` | Watcher delay in seconds, at least 60; example `900`. |
| `SETTLE_SECONDS` | integer | `300` | Minimum age after completion, at least zero; example `300`. |
| `MAX_UPLOADS_PER_SYNC` | integer | `10` | New uploads per cycle, 1–100; example `10`. |
| `MEDIA_ENABLED` | boolean | `false` | Only case-insensitive `true` enables new image jobs; example `true`. |
| `MEDIA_UNITS` | enum | `lb` | `lb` or `kg` for cards and description totals; example `kg`. |

Invalid integers, dates, ranges, timezones, or `MEDIA_UNITS` cause an error. API URLs must use HTTP(S) without embedded credentials, queries, or fragments.

## Compose settings

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `CONNECTOR_IMAGE` | image repository | `ghcr.io/willtheorangeguy/sparkyfitness-strava-connector` | Image without tag; example `ghcr.io/your-account/sparkyfitness-strava-connector`. |
| `CONNECTOR_VERSION` | string | `0.2.0` | Released tag without `v`; example `0.2.0`. |
| `CONNECTOR_STATE_VOLUME` | volume name | `sparkyfitness-strava-connector_state` | Media worker's external core volume; example `fitness_strava_connector_state`. |

The existing-stack overlay uses `STRAVA_CONNECTOR_IMAGE`, `STRAVA_CONNECTOR_VERSION`, `STRAVA_SPARKYFITNESS_BASE_URL`, `STRAVA_SPARKYFITNESS_API_KEY`, `STRAVA_WORKOUT_TIMEZONE`, `STRAVA_EXPORT_SINCE`, `STRAVA_SYNC_INTERVAL_SECONDS`, `STRAVA_SETTLE_SECONDS`, `STRAVA_MAX_UPLOADS_PER_SYNC`, `STRAVA_MEDIA_ENABLED`, and `STRAVA_MEDIA_UNITS`. These map to the corresponding unprefixed settings above. Its SparkyFitness URL defaults to `http://sparkyfitness-server:3010`; timezone defaults to `UTC`. Client ID and secret keep their `STRAVA_CLIENT_*` names. See the [overlay source](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/blob/HEAD/examples/docker-compose.sparkyfitness.yml).

## Examples

Copy the [tracked environment example](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/blob/HEAD/.env.example) and supply your own credentials:

```dotenv title=".env"
SPARKYFITNESS_BASE_URL=http://host.docker.internal:8102
SPARKYFITNESS_API_KEY=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
# Published container version, without a leading v.
CONNECTOR_VERSION=0.2.0
# Local timezone used to display workouts correctly on Strava.
WORKOUT_TIMEZONE=America/Edmonton
# Blank: first preview/sync stores today's UTC date as the initial boundary.
# Set YYYY-MM-DD to include older sessions (inclusive diary-date boundary).
EXPORT_SINCE=
SYNC_INTERVAL_SECONDS=900
SETTLE_SECONDS=300
MAX_UPLOADS_PER_SYNC=10

# Companion browser worker attaches two cards to new exports.
MEDIA_ENABLED=false
MEDIA_UNITS=lb

# Optional: existing stack state volume for docker-compose.media.yml.
# CONNECTOR_STATE_VOLUME=my_stack_strava_connector_state
```

OAuth access/refresh tokens live in the journal, separate from `.env`. Browser login is a second credential store; see [workout images](media.md).
