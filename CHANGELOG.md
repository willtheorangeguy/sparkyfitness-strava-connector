# Changelog

## 0.2.0 — 2026-10-21

- Export only native SparkyFitness preset/plan workouts, excluding Garmin imports and unfinished sets.
- Automatically map supported exercise names and aliases, explain unresolved mappings, and use recorded total workout duration when available.
- Add automatic summary and weight-comparison images from the exact exported sets, plus total lifting volume in the Strava description.
- Carry primary/secondary source muscle metadata through the image queue; normalize anatomical names and verify actual diagram colors.
- Add a persistent companion browser worker with account checks, unchanged-field validation, durable upload intent and duplicate prevention.
- Correct Strava strength JSON timestamps to use UTC Z suffixes; preserve failed-attempt history and use fresh external IDs for explicit retries.
- Include the automatic media worker in downloadable setup files; publish regular and media images for amd64/arm64.

## 0.1.0 — 2026-10-21

- Port the v0.2.1 wger connector to SparkyFitness v1.8.0.
- Export completed strength sets from logged preset/plan workouts only.
- Group plan logs by scheduled session/date; skip missing timing.
- Preserve OAuth, durable uploads, mappings, recovery, and rate-limit handling.
- Port experimental cards, artwork, browser login, and media tests.
- Add real SparkyFitness integration tests and release configuration.
