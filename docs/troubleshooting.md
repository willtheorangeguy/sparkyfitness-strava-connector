# Troubleshooting

## Another connector command is using this state volume

Stop the resident watcher before opening the journal:

```sh
docker compose stop connector
docker compose run --rm connector status
docker compose up -d
```

## Source identity or history pagination error

Use a key for the intended account with diary and plan access. Set `SPARKYFITNESS_BASE_URL` to the origin without `/api`. The active and authenticated identity must match. Verify the source API version; malformed or repeated history pages are rejected.

## Preview has no workouts or reports skipped

Check native provenance, preset/plan links and diary-date boundary. Standalone exercises and provider imports are excluded. Only timestamped completed sets are included. Inspect `reason` for unavailable timing, invalid local time around DST or missing duration/start data. Corrected source data can become eligible later.

## Preview reports missing exercises

Read `missing_exercises` for UUIDs and names. Use `exercises` to find a supported type and `map` to save a manual override. Do not map numeric wger IDs. Invalid completed sets still block the workout after mapping.

## Callback fails or OAuth refresh is uncertain

The browser's localhost connection error is expected. Copy its full callback URL into `auth-complete` within 15 minutes of `auth-url` and grant all requested scopes. Reauthorize after an uncertain refresh.

## Upload is uncertain or failed

Inspect the remote activity before retrying. Use the exact `preset:` or `plan:` session key when reconciling; quote plan keys as a single argument. A new external ID is created only after an explicit approved retry. See [usage](usage.md) for the recovery sequence.

## Browser cards are pending or held

Confirm the worker uses the core state volume. Stop the worker for interactive login as the same Strava athlete, then resume it. Inspect job receipts and error files before recovery. Do not delete receipts to force another browser write. Core API exports continue independently.
