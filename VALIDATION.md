# Validation — October 21, 2026

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
