# Validation — October 21, 2026

Live Strava upload fix: **all three native workouts uploaded successfully**.
The original JSON timestamps ended in `+00:00`; Strava accepted those requests
but later returned `Error Processing Data`. Controlled retries of the pull
workout with a fresh file identifier reproduced failures for both fractional and
whole-second `+00:00` timestamps. Changing only the suffix to `Z` succeeded,
including with fractional seconds intact. Production serialization now emits UTC
`Z` timestamps, retaining the original precision and local display offset.

Strava also returned a cached failed upload when its external ID was reused.
Explicit retries now retain attempt history and use a new `.retryN.json` file
identifier. Known remote successes or still-processing jobs cannot be retried,
and queued retries must pass current source validation before upload.

Successful activities, verified by API readback:

- Squat: `20682657491`, 12 uploaded sets, 31:12.
- Pull: `20682679076`, 21 uploaded sets, 28:36.
- Push: `20682708763`, 29 uploaded sets, 54:12.

Names, UTC start times, durations, sport types, external IDs, and exactly one
matching activity per workout were verified. The initial squat probe used whole
seconds; its journal fingerprint was normalized to production precision only
after proving all other content identical and checking the remote activity.
The public API and inspected desktop pages expose activity summaries, so mobile
exercise-log rendering has not been independently verified. Read-only browser
inspection used a temporary copy of the existing profile. Private verification
artifacts are under ignored `runtime/`, including `live-upload-verification.json`.

Final regression checks: **157 unit tests passed**, then **163 tests passed** in
the real SparkyFitness/mock Strava suite (one media collection skip). The mock now
rejects non-`Z` timestamps and reproduces cached failures. Tests exercise distinct
retry jobs, persistent attempt history, restart, source revalidation, successful
upload protection, and no duplicate submissions. Reports:
`reports/live-upload-fix-unit.xml` and `reports/junit.xml`.

The local `.env` now selects the rebuilt `sparkyfitness-strava-connector:local`
image for normal Compose commands. The companion watcher is running with durable
state. Its first verified cycle reported three exported workouts, zero new
submissions, zero changed workouts, and zero blocked workouts.

Automatic exercise matching: **151 unit tests passed**, followed by **156 tests
passed** in the real SparkyFitness/mock Strava suite (one media collection skip).
Reports: `reports/automapping-unit.xml` and `reports/junit.xml`. Coverage includes
catalog names, library aliases, punctuation/case normalization, ambiguous and
unknown names, explicit override priority, native-only filtering, and automatic
upload selection without manual mappings or duplicates across restart.

The rebuilt local image's live preview marks all three native workouts ready:
12 squat-workout sets, 21 pull-workout sets, and 29 push-workout sets. All three
also translate successfully with an empty override dictionary. Preview exposes
the exercise names, chosen identifiers, and match methods. Garmin imports remain
excluded. This automatic-matching validation preceded the live attempt above.

Workout-total timing follow-up: **110 unit tests passed** (one media collection
skip, five integration cases deselected), followed by **115 tests passed** in
the real SparkyFitness/mock Strava harness (one media collection skip).
Reports: `reports/timing-unit.xml` and `reports/junit.xml`. Tests cover reported
total duration, estimating missing starts from final completion, native
unfinished-set filtering, invalid totals,
and settling after recent completions. The integration fixture without timing
now lacks both start and positive duration; it remains ineligible.

Native-only selection subsequently excludes Garmin and other imports, including
mixed-source groups and entries without source evidence. Native `sparky`,
`manual`, and `Manual` origins remain eligible. The final real SparkyFitness/mock
Strava suite passed **123 tests**, with one media collection skip; its dedicated
account was removed successfully. Report: `reports/junit.xml`.
All three Garmin imports in the export window are absent from preview.
Private source/preview files stay under ignored
`runtime/`. No live Strava uploads were performed by these checks.

Companion-service follow-up: all regular Compose setups explicitly run `watch`,
restart unless stopped, and retain `/data`. The overlay was merged with the actual
SparkyFitness harness and its shared main-service network checked. The updated unit
suite passed **98 tests** (one media collection skip, five integration cases
deselected), including watcher tests for startup before the source is available,
later set completion, exactly one upload, asynchronous polling, and durable state.
These tests did not contact live Strava. Report: `reports/watch-unit.xml`.

Environment: Windows, Docker Desktop Linux containers, Python 3.14.6 on the host,
Python 3.12.13 in the regular container, and real Chromium in the media container.

## Results

- Windows unit/contract suite: **96 passed**, one media collection skip, five
  integration cases deselected. `reports/unit.xml`.
- Real SparkyFitness harness run: **99 passed**, one media collection skip. This
  includes all **five integration cases** and the unit suite at that point; two
  additional grouping/pagination unit cases subsequently passed on Windows.
  `reports/junit.xml`.
- Chromium/media suite: **17 passed**. `reports/media-tests.xml`.
- Standalone, local-build, existing-stack, experimental-media, and generated
  release-download Compose configurations validated successfully.
- Regular and media Docker images built locally. Regular image CLI smoke test
  passed and runs as UID 10001. SparkyFitness-branded PNG previews regenerated.
- Git whitespace validation passed. Original wger connector working tree remained clean.

## Real source contract

Tests use the sibling `sparkyfitness-addon-harness`: SparkyFitness v1.8.0,
upstream revision `28d32d8536877d765ad03ca3727409c679b847a7`, with the harness's
digest-pinned frontend/server images. The runner creates its own account through
the real API, seeds preset/plan sessions and exclusion controls, then deletes only
that generated account. Cleanup succeeded. The existing demo's latest strength
history still contained three exercises and nine sets afterward.

Integration covers structured multipart strength uploads, actual values rather
than prescribed targets, completed-set filtering, preset/plan selection, skipped
timing, asynchronous polling after restart, lost-response recovery by upload or
activity ID, mapping holds, token rotation, and source edits without reupload.
Unit coverage additionally exercises plan grouping, partial completion, regrouping,
UUID mappings' underlying source identity, kg/bodyweight/timed sets, invalid values,
DST boundaries, account binding, read-only source access, and pagination safety.

## Limits

Strava API and browser tests use local doubles. No live Strava authorization,
strength upload, or photo upload was performed for this project. Production card
generation/attachment remains outside this version. At initial local validation, hosted CI and multi-platform publishing had not run.
Local images were linux/amd64; hosted release results are recorded separately.

## Automatic image cards — October 21, 2026

The export engine now snapshots the exact uploaded sets and atomically enqueues image work after the activity ID is known. Queue failures retain successful workout state. A separate Chromium worker attaches two actual-data cards and journals intent before file selection. Existing receipts prevent a second upload, including receipts left uncertain after a crash. The worker checks the logged-in athlete, activity ownership and unchanged activity fields before and after Save. The renderer uses local fonts/artwork; total volume is external kg times repetitions, converted for display. Unrecorded body mass and timed holds do not add lifting volume.

A new clearly labeled synthetic workout was uploaded to the consenting account, dated October 21 in America/Edmonton: 900 seconds, four sets, three exercises, rounded total 1,245 lb. The export created its image job automatically. Both generated PNGs persisted on the activity after browser restart, and Only You visibility was retained. Source fixtures, upload/attachment journals, image hashes, screenshots and destination details remain under ignored `runtime/` directories. The normal source journal and mock source journal were kept separate; API tokens were used from the existing authorized store without making token copies.

Live testing caught a stale Chromium profile lock, an editor prompt that disappears after images exist, and privacy controls that hydrate after the Save button. Verification now waits for the relevant controls and loaded thumbnails. The wger pre-Save hold was inspected read-only; no photos had persisted, so its prior receipt was retained as an attempt record before one explicit recovery. The recovered job saved successfully and was verified after browser restart. No extra workout activity was created by recovery.

Automatic card generation is enabled in both local connector configs, and both companion workers run persistently. The configured SparkyFitness source watcher is running. The standalone wger config still has no source token or Strava client credentials; its real-source watcher was not started. The wger mock upload reused the consenting account's existing OAuth store in isolation.

Validation results for this change: full core/harness suites passed (SparkyFitness 165, wger 98; each skipped the separate media suite). The additional image-queue failure test passed in each project. Browser suites passed their existing cases after rerunning one short login timeout under load; all three new production-worker browser regressions passed in both projects after fixing the PNG/JavaScript test fixtures. Successful Save, post-Save uncertainty, immutable queue replay, persisted photos and prevention of repeat file selection are covered. The live Strava checks above were separate from the intercepted/mock browser tests.

## Muscle metadata regression fix — October 21, 2026

Both engines now preserve primary and secondary anatomy through the durable media job into the rendered summary. SparkyFitness reads only completed exercise snapshots. wger fetches exercise-info for the distinct logged exercise IDs of a new export and translates its English/Latin muscle names. A shared normalization table maps explicit anatomy to supported diagram regions; unknown labels are retained for diagnosis, not guessed. A muscle that is primary anywhere in the workout takes precedence over secondary classification elsewhere. Failed optional wger anatomy reads do not prevent a strength upload.

Regression coverage exercises engine synchronization through the saved image outbox, excludes unfinished exercise metadata, verifies name aliases and unknown labels, and checks actual CSS fill colors on mirrored front/back SVG paths with Chromium. Both projects' browser color tests passed. A separate read-only preview used the configured SparkyFitness instance's real native Barbell Squat workout: primary calves/hamstrings/quads; secondary glutes/lower back; no unmapped source names. The rendered result was inspected visually and is stored privately under ignored `runtime/native-muscle-preview/`. No Strava activity or existing photos were changed by this verification. Existing immutable export jobs and uploaded images remain unchanged; the fix applies to new exports.

Final checks for the muscle fix: SparkyFitness core/harness 170 passed, wger core/harness 105 passed; each skipped the three separately run browser modules. The new Chromium color regression passed independently in both projects. Local images were rebuilt, both image workers restarted, and the configured SparkyFitness core watcher restarted.

## Release v0.2.0

Release includes native strength upload/recovery fixes and automatic workout images with source muscle highlights. Core/harness and browser verification are recorded above. Downloadable media setup now includes the persistent worker and configurable shared state volume. No production credentials or private runtime artifacts are packaged.
