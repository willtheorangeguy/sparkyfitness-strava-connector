# Testing

Developers can copy `.env.example` to `.env` and build with
`docker compose -f compose.build.yaml build`. Add `-f compose.build.yaml` to all
connector commands when using the local image. Stop the published-image deployment
first; the local build shares its project and state volume.

```sh
python test_harness.py
# Optional: --sparkyfitness-harness /path/to/sparkyfitness-addon-harness
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python -m pytest -q -m 'not integration'
docker compose -f compose.media.test.yaml build test
docker compose -f compose.media.test.yaml up -d --wait mock-strava-web
docker compose -f compose.media.test.yaml run --rm test
docker compose -f compose.media.test.yaml down
```

Integration uses real SparkyFitness and mock Strava, creates/removes a dedicated
account, and preserves demo history. No real Strava credentials or uploads.
Results: `reports/junit.xml`. CI covers units, Compose, container smoke checks, and
media; manual dispatch also runs the harness. Release workflows prepare regular/media
amd64/arm64 images and setup downloads. See [RELEASING.md](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/blob/HEAD/RELEASING.md) and
[VALIDATION.md](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/blob/HEAD/VALIDATION.md). MIT licensed; inherited assets retain their notices.

## Test boundaries

Source-selection, mapping, conversion and journal tests run without a production account. Integration creates a dedicated temporary SparkyFitness account and exercises the actual source API against mock Strava. Browser tests use a local fixture, not live selectors. Historical validation is evidence for the recorded version and environment; it is not a new live acceptance test.
