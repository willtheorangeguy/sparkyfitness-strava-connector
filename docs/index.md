# SparkyFitness → Strava connector

Export completed native SparkyFitness preset/plan workouts as structured Strava strength activities. Run this Docker companion for one source account and one athlete. It reads SparkyFitness without modifying it and optionally attaches two image cards through a separate browser worker.

## Key features

- Select native preset/plan instances and completed sets.
- Match exercise names through catalog/aliases with explicit UUID overrides.
- Preserve stored kilogram loads and validated workout timing.
- Persist upload intent, recovery history and immutable image jobs.

## Quick start

Download the released Compose and environment files and configure your source API key and Strava app, then run:

```sh
docker compose pull
docker compose run --rm connector auth-url
docker compose run --rm -i connector auth-complete
docker compose run --rm connector preview
```

Follow [getting started](getting-started.md) for permissions and the first export.

## Where to next

<div class="grid cards" markdown>

- [Installation](installation.md): published and development deployments.
- [Configuration](configuration.md): API keys, dates, timezone and media defaults.
- [Usage](usage.md): selection, mappings, partial workouts and recovery.
- [Workout images](media.md): browser login, queue and receipts.
- [Architecture](architecture.md): selection, conversion and journal boundaries.
- [Testing](testing.md): isolated source and mock destination fixtures.

</div>

## Support

Open a [discussion](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/discussions/new) or an [issue](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/issues/new/choose).
