# Usage

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

## Inspect matches

Stop the watcher before maintenance:

```sh
docker compose -f compose.build.yaml stop connector
docker compose -f compose.build.yaml run --rm connector preview
docker compose -f compose.build.yaml run --rm connector mappings
docker compose -f compose.build.yaml up -d
```

`exercise_mappings` reports `catalog`, `alias`, or `manual` for each selected match. Manual UUID overrides take priority. Automatic matches are recalculated without saving overrides. Unknown or ambiguous names remain in `missing` and `missing_exercises`, blocking the whole workout. Provider imports are excluded before matching.

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

Copy the entire session key from preview/status, including punctuation. Quote `plan:` keys as a single shell argument because their encoded schedule contains JSON. After an approved retry, run `sync` while the watcher remains stopped, then restart it.

`preview` states include `ready`, `blocked`, `skipped`, `processing`, `exported`, `changed`, `uncertain`, `failed` and `retry`. `skipped` includes a reason for timing/data that prevents a usable payload. Moving or regrouping previously exported source entries is treated as a source edit rather than a new export intent.
