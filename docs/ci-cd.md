# CI/CD

`test.yml` runs unit/release tests, validates deployment examples, and smoke-tests the non-root container on pushes and pull requests. Its real-SparkyFitness integration job runs only on manual dispatch. `media.yml` runs browser tests and renders review assets when relevant paths change or it is dispatched.

```sh
gh workflow run test.yml
```

`publish.yml` runs on published GitHub releases. It verifies package/tag versions, gates publication on both test workflows, and publishes core and `-media` images for amd64 and arm64. Stable releases get full, minor and latest tags; prereleases get complete versions only. The setup-files job attaches version-matched Compose/environment files and art previews. See [release preparation](https://github.com/willtheorangeguy/sparkyfitness-strava-connector/blob/HEAD/RELEASING.md).

`docs-lint.yml` calls the shared Markdown, strict-build and external-link checks on documentation PRs. `docs.yml` calls the shared Pages build on main/master pushes and manual dispatch. GitHub Pages must use Actions as its source. Theme dependencies and assets are owned by the shared MkDocs repository.
