<!-- Logo -->
<h1 align="center">SparkyFitness → Strava connector</h1>
<!-- Tagline -->
<h4 align="center">Export completed native SparkyFitness strength workouts to Strava with structured sets and optional cards.</h4>
<!-- Badges -->
<div align="center">
<img alt="Issues" src="https://img.shields.io/github/issues/willtheorangeguy/sparkyfitness-strava-connector">
<img alt="Pull requests" src="https://img.shields.io/github/issues-pr/willtheorangeguy/sparkyfitness-strava-connector">
<img alt="License" src="https://img.shields.io/github/license/willtheorangeguy/sparkyfitness-strava-connector">
<img alt="docs-lint workflow" src="https://github.com/willtheorangeguy/sparkyfitness-strava-connector/actions/workflows/docs-lint.yml/badge.svg">
<img alt="docs workflow" src="https://github.com/willtheorangeguy/sparkyfitness-strava-connector/actions/workflows/docs.yml/badge.svg">
<img alt="media workflow" src="https://github.com/willtheorangeguy/sparkyfitness-strava-connector/actions/workflows/media.yml/badge.svg">
<img alt="publish workflow" src="https://github.com/willtheorangeguy/sparkyfitness-strava-connector/actions/workflows/publish.yml/badge.svg">
<img alt="test workflow" src="https://github.com/willtheorangeguy/sparkyfitness-strava-connector/actions/workflows/test.yml/badge.svg">
</div>
<!-- Nav -->
<p align="center"><a href="#key-features">Key Features</a> • <a href="#installation">Installation</a> • <a href="#usage">Usage</a> • <a href="#documentation">Documentation</a> • <a href="#support">Support</a> • <a href="#license">License</a></p>

## Key Features

- Export completed sets from native preset/plan workouts; exclude provider imports.
- Match exercise names automatically, with optional manual UUID overrides.
- Export stored kilogram loads, actual repetitions and timed holds.
- Persist OAuth, account bindings and upload/recovery history.
- Attach optional summary and comparison images through a separate worker.

## Installation

Current source version `0.2.0` was not yet published as a release on 2026-10-22. Build the checkout for the features documented here. See [installation](docs/installation.md) for the published version.

```sh
git clone https://github.com/willtheorangeguy/sparkyfitness-strava-connector.git
cd sparkyfitness-strava-connector
cp .env.example .env
# Fill in the source API key/token, Strava app credentials and timezone.
docker compose -f compose.build.yaml build
docker compose -f compose.build.yaml run --rm connector auth-url
docker compose -f compose.build.yaml run --rm -i connector auth-complete
```

Open the consent URL and paste the complete localhost callback into the prompt. Follow [getting started](docs/getting-started.md) for account setup.

## Usage

```sh
docker compose -f compose.build.yaml run --rm connector check
docker compose -f compose.build.yaml run --rm connector preview
docker compose -f compose.build.yaml run --rm connector sync
docker compose -f compose.build.yaml up -d
```

Inspect selection reasons and mappings before uploading. Partial workouts export once; later completed sets report `changed`. Stop the watcher for stateful maintenance and retain its volume.

## Documentation

Read the [documentation site](https://williamvdg.me/sparkyfitness-strava-connector/) or browse [`docs/`](docs/index.md):
[Getting started](docs/getting-started.md) · [Installation](docs/installation.md) · [Usage](docs/usage.md) · [Configuration](docs/configuration.md) · [Troubleshooting](docs/troubleshooting.md).

## Automatic workout images

Version 0.2.0 includes optional automatic cards. Follow [workout images](docs/media.md) for the matching media container, browser login and recovery.

## Attribution

Based on [wger-strava-connector](https://github.com/willtheorangeguy/wger-strava-connector). Retain the bundled [Inter license](src/sparkyfitness_strava/media/assets/INTER-LICENSE.txt) and [carrier attribution](src/sparkyfitness_strava/media/assets/carrier-LICENSE.txt).

## Support

Open an [issue](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/issues/new/choose).

## Contributing

Contributions welcome. See the org-wide [Contributing Guide](https://github.com/willtheorangeguy/.github/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://github.com/willtheorangeguy/.github/blob/main/CODE_OF_CONDUCT.md).

## License

MIT — see [`LICENSE`](LICENSE). Inherited assets retain their notices; the carrier illustration is CC BY-SA 4.0.
