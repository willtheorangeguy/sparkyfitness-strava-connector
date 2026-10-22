# Release preparation

Repository: [willtheorangeguy/sparkyfitness-strava-connector](https://github.com/willtheorangeguy/sparkyfitness-strava-connector). Push the intended release commit to `main` and dispatch the test workflow to exercise the public sparkyfitness harness before publishing. No production Strava credentials are needed for tests.

1. Update `pyproject.toml` and `src/sparkyfitness_strava/__init__.py` to the same version. Update the default version in the standalone, existing-sparkyfitness and media Compose/environment examples, the changelog, and validation notes.
2. Run `python test_harness.py`, validate Compose examples, and inspect `git diff --check`.
3. Create and push an annotated `vMAJOR.MINOR.PATCH` tag. Publish the corresponding GitHub release. A tag push alone does not publish a container.
4. `.github/workflows/publish.yml` validates the version, gates publication on connector and media tests, then builds both regular and media GHCR images for Linux amd64 and arm64 with provenance and an SBOM. It uses `GITHUB_TOKEN` and needs Packages write permission.
5. Stable releases receive the full version, minor version, and `latest` tags. The media image uses corresponding `-media` suffixes, for example `0.1.0-media`, `0.1-media` and `latest-media`. Prereleases receive only their complete version (plus `-media` for that image); GitHub's prerelease flag must match the version suffix. Set package visibility to public if needed and verify anonymous pulls of both variants.

After publishing both images, the workflow attaches `docker-compose.yml`, `env.example`, `docker-compose.sparkyfitness.yml`, `sparkyfitness.env.example`, and `docker-compose.media.yml` to the GitHub release, along with the selected card previews and comparison catalog. `scripts/release_assets.py` renders the Compose/environment files with the actual lowercase image repository and release version, including forked repositories and prereleases. Users rename `env.example` to `.env`; the non-hidden asset name avoids GitHub renaming dotfiles.

Verify a clean deployment using only the standalone pair of downloads. Both deployed examples pull the published image and contain no build context. Developer builds use `compose.build.yaml` from a checkout. Never put real tokens or `.env` in a release.

The media Compose download must include `media-worker`, use the released image version, and share the configured core state volume through `CONNECTOR_STATE_VOLUME`. Keep automatic media opt-in until the browser profile is authenticated.
