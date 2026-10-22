# FAQ

???+ question "Why are Garmin imports and standalone exercises absent?"

    Selection accepts only native preset/plan workouts with source evidence. Provider imports, mixed native/imported groups and unlinked standalone exercises are excluded before exercise matching.

??? question "Why did later completed sets not appear on Strava?"

    A partial workout exports once. Later completions report `changed`; this version does not append sets. Increase `SETTLE_SECONDS` when long breaks are expected before the first export.

??? question "Should I convert pounds to kilograms?"

    No. SparkyFitness stores loads in kg even when it displays pounds. Those stored values are exported directly. Body mass is never added; unloaded bodyweight sets omit load.

??? question "Why is a matched exercise broader than my source name?"

    The bundled alias table can choose a supported broader category when Strava lacks the exact variation. `preview` identifies the matching method. A manual UUID override takes priority. Unknown and ambiguous names remain blocked.

??? question "Can I share the wger connector state?"

    No. The CLI rejects a journal containing a wger account. Each instance binds one SparkyFitness account, Strava athlete and application.

??? question "Does preview upload anything?"

    No activity is uploaded. It does bind identity and persist the initial boundary. Set `EXPORT_SINCE` before the first preview if you need historical backfill.
