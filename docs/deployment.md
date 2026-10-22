# Deployment

Current source version `0.2.0` was not yet a published release on 2026-10-22. The overlay below describes the checked-in service arrangement. To use it with a local image, build the core with `compose.build.yaml`, then set `STRAVA_CONNECTOR_IMAGE=sparkyfitness-strava-connector` and `STRAVA_CONNECTOR_VERSION=local` in the source stack's `.env`. Do not pull that local image. Published deployments must use the matched files/version from an existing release.

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

## Continuous operation

`watch` checks immediately, then every 900 seconds by default. It waits at least 300 seconds after the latest completion and activity end, uploads up to ten new workouts per cycle, and polls accepted jobs later. `restart: unless-stopped` resumes the container after process or Docker restarts. Recover uncertain writes explicitly rather than restarting with an empty journal.

```sh
docker compose -f compose.build.yaml logs -f connector
```

## State and backups

Stop the core service before copying its state volume. Preserve `/data/state.sqlite3`, optional `/data/media` jobs/receipts, and the separate media browser-profile volume. The core uses a process lock and SQLite `settings`/`exports` tables. Restore state before starting a replacement container. Never reuse the wger connector's state.

For media setup, point `CONNECTOR_STATE_VOLUME` at the existing core volume and follow [workout images](media.md).
