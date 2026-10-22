# Development

Create a Python 3.12+ virtual environment and install the lock file and editable package as shown in [installation](installation.md). Run the [test suite](testing.md) before changing conversion or journal behavior.

```sh
pip install -r requirements.lock
pip install --no-deps -e .
pytest -q -m 'not integration'
```

Use `compose.build.yaml` for local core images and `compose.media.yaml` for local browser images. Keep production state separate from tests. Preserve write-intent and account-binding checks when modifying recovery behavior.

## Documentation preview

With the shared [MkDocs repository](https://github.com/willtheorangeguy/mkdocs) checked out beside this project, run:

```sh
../mkdocs/scripts/docs-serve.sh --build
../mkdocs/scripts/docs-serve.sh
```

The helper stages the shared theme and installs documentation dependencies when needed. Do not add project-level plugin or Markdown-extension lists: they replace inherited lists.
