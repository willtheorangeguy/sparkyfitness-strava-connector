# Installation

## Requirements

Released Linux amd64 and arm64 images run under Docker Desktop or Docker Engine with Compose v2. Source development requires Python 3.12 or later. The integration target is SparkyFitness v1.8.0 pinned in its addon harness.

## Install methods

=== "Released container"

    Download `docker-compose.yml` and `env.example` from [v0.2.0](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/releases/tag/v0.2.0). Rename `env.example` to `.env` and supply credentials:

    ```sh
    docker compose pull
    docker compose run --rm connector --help
    ```

=== "Source container"

    ```sh
    git clone https://github.com/willtheorangeguy/sparkyfitness-strava-connector.git
    cd sparkyfitness-strava-connector
    cp .env.example .env
    docker compose -f compose.build.yaml build
    docker compose -f compose.build.yaml run --rm connector --help
    ```

    Keep using `-f compose.build.yaml` for local-build commands. The published-image deployment shares its project and volume; stop one before switching.

=== "Python development"

    ```sh
    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.lock
    pip install --no-deps -e .
    sparkyfitness-strava --help
    ```

    Export configuration variables yourself. The Python entry point does not load `.env`; set `DATA_DIR=./runtime` for writable host state. Windows timezone data is a declared dependency.

## Verify the installation

`--help` prints the command list without contacting a source or destination. Follow [getting started](getting-started.md) to authorize and run `check` and `preview`.

## Upgrading

Set the released `CONNECTOR_VERSION` without `v`, run `docker compose pull`, then `docker compose up -d`. Keep state and update any companion media image to match.

## Uninstalling

`docker compose down` removes containers and the project network while preserving named volumes. Retain the state and browser profile for recovery. Deleting the export journal can create duplicate activities after reinstalling.
