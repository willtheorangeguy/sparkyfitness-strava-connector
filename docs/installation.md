# Installation

## Requirements

Docker Engine or Docker Desktop with Compose v2 supports the Linux amd64/arm64 deployments. Source development requires Python 3.12+. The tested source API is SparkyFitness `v1.8.0`. Use an API key with diary and plan read access.

## Install methods

=== "Current source"

    ```sh
    git clone https://github.com/willtheorangeguy/sparkyfitness-strava-connector.git
    cd sparkyfitness-strava-connector
    cp .env.example .env
    docker compose -f compose.build.yaml build
    docker compose -f compose.build.yaml run --rm connector --help
    ```

    Configure your actual credentials before following [getting started](getting-started.md). Keep using `-f compose.build.yaml` for this source deployment.

=== "Published release"

    On 2026-10-22, [v0.1.0](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/releases/tag/v0.1.0) was the latest published release. Download its `docker-compose.yml` and `env.example`, rename the environment file to `.env` and supply credentials:

    ```sh
    docker compose pull
    docker compose run --rm connector --help
    ```

    Use that release's own matched files and behavior. The current source version `0.2.0` and its automatic-worker features were not yet a published release. Use the source tab for the behavior documented by this site.

=== "Python development"

    ```sh
    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.lock
    pip install --no-deps -e .
    sparkyfitness-strava --help
    ```

    Export settings yourself: the CLI does not load `.env`. Set `DATA_DIR=./runtime` for writable host state instead of the default `/data`.

## Verify the installation

`--help` prints subcommands without opening state or contacting APIs. After authorization, run the `check` and `preview` steps in [getting started](getting-started.md).

## Upgrading

For a source deployment, update the checkout and rebuild with `compose.build.yaml`, then recreate the service with that same file. For a published release, change `CONNECTOR_VERSION` to a version that exists, pull and recreate. Keep the state volume. Source and published standalone deployments share their project/volume, so stop one before switching.

## Uninstalling

For the source deployment, `docker compose -f compose.build.yaml down` removes containers/network while preserving named volumes. Keep journal and browser-profile backups for recovery. Losing state can duplicate exports.
