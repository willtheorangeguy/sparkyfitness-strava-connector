# Roadmap

The implemented selector deliberately limits exports to native preset/plan workouts. These boundaries are documented behavior, not a promised schedule.

- Provider imports, mixed-source groups and unlinked/freeform exercises are excluded.
- Partial workouts export once. Later sets, edits and deletions do not update an existing activity.
- Negative assistance, distance sets, unknown modalities, fractional repetitions and invalid values are blocked.
- Timing with no valid recorded or estimated start is skipped. Ambiguous or nonexistent local DST times require source correction.
- RPE/RIR, supersets, rest targets, GPS, heart rate and calories are not structured exports in this path.
- Exercise matching uses a finite catalog and explicit aliases. Unknown/ambiguous names require a manual supported mapping.
- Existing activities do not automatically receive image jobs; live browser layout/session changes can require operator attention.

Inspect real selection reasons with `docker compose run --rm connector preview`. Read [usage](usage.md) before choosing a larger settling window or historical boundary.
