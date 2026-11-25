# Releasing mcp-caretaker

These steps are for the repository owner, run by hand on the owner's machine.
No AI agent runs them, and no token, password or API key ever goes into this
repository, a commit, an issue, a pull request, or a chat window. Publishing is
not automated here: PR 7 adds no publish workflow and no credentials.

The commands use the syntax from the official Python Packaging User Guide
("Packaging and distributing projects", "Using TestPyPI") and the twine
documentation. Anything not confirmed from those pages is marked NOT VERIFIED.

## Before you start

1. Every CI job on `main` is green: the four test jobs, the four package jobs.
2. PR 8 (the case study) is merged, as decided for this project.
3. The version is the one you intend to publish. It is `0.0.0.dev0` today, and a
   release needs a version without `.dev0`, for example `0.1.0`.
4. You have a TestPyPI account and a PyPI account, and an API token for each.
   Keep both tokens in your own password manager, or in the environment variable
   `TWINE_PASSWORD` for the length of one command. Never commit them.

## The one place to change the version

The version lives in exactly one file, `src/mcp_caretaker/__init__.py`:

```python
__version__ = "0.0.0.dev0"
```

`pyproject.toml` reads it through hatchling (`[tool.hatch.version]`), and the
`--version` output and the JSON report read the same value. Change that one
line, remove the `.dev0` part for a release, and rebuild. Do not edit a version
anywhere else; there is no second copy.

## Build and check the distributions

Run one command per line, from the repository root, in an activated virtual
environment:

```sh
python -m pip install --upgrade build twine
rm -rf dist
python -m build
twine check dist/*
```

`python -m build` writes one wheel and one sdist into `dist/`. `twine check`
must print PASSED for both. Rebuild every time the source changes; stale files
in `dist/` are how the wrong artifact gets uploaded.

## TestPyPI first

```sh
twine upload --repository testpypi dist/*
```

Then install what you uploaded into a brand-new virtual environment, outside
the checkout, and try it:

```sh
python -m venv /tmp/release-check
/tmp/release-check/bin/python -m pip install "mcp>=2.3.0,<2.4" "mcp-types>=2.3.0,<2.4"
/tmp/release-check/bin/python -m pip install --index-url https://test.pypi.org/simple/ --no-deps --only-binary=:all: mcp-caretaker
/tmp/release-check/bin/python -m pip check
/tmp/release-check/bin/mcp-caretaker --version
```

On Windows, use `py -m venv %TEMP%\release-check` and
`%TEMP%\release-check\Scripts\mcp-caretaker.exe --version`.

The dependencies are installed first from the real index, because TestPyPI does
not hold them. The official TestPyPI guide warns against mixing the two indexes
with `--extra-index-url`: pip does not prioritise one index over the other.
That is why the dependency step above names the exact ranges and the package
install uses `--no-deps`.

Expected on TestPyPI: `pip check` reports no broken requirements, and
`mcp-caretaker --version` prints the version you set in
`src/mcp_caretaker/__init__.py`.

## PyPI

Only after the TestPyPI install works:

```sh
twine upload dist/*
```

Then check the project page and install once more from the real index:

```sh
python -m venv /tmp/pypi-check
/tmp/pypi-check/bin/python -m pip install mcp-caretaker
/tmp/pypi-check/bin/python -m pip check
/tmp/pypi-check/bin/mcp-caretaker --version
```

Clean install with pipx, which is the check people actually use:

```sh
pipx install mcp-caretaker
mcp-caretaker --version
pipx uninstall mcp-caretaker
```

## README lines to change after publishing

Today the README says the package is not published and installs from a local
clone. After the first successful PyPI upload, replace the "Install" section's
clone commands with the index commands, and delete the sentence that says the
package is not published. The three lines that change:

1. "The package is not published on an index yet, so install it from a local clone."
2. `git clone https://github.com/sarooo43/mcp-caretaker.git`
3. `cd mcp-caretaker`
4. `python -m pip install .` becomes `python -m pip install mcp-caretaker`
5. `pipx install .` becomes `pipx install mcp-caretaker`

Keep the `--version` line and the Python 3.11 requirement sentence as they are.

## If an upload is wrong

PyPI does not let a version number be reused, so the safe fix is always a new
version:

1. Fix the problem in the tree and bump the version in
   `src/mcp_caretaker/__init__.py`.
2. Rebuild, run `twine check dist/*`, and upload the new version.
3. If the bad release must not be installed by resolvers, yank it in the
   project's file management page on PyPI. Yanking keeps the files visible but
   stops new installs from resolving to it; it does not delete them.
4. Do not try to upload over the old version; the index rejects it.

The exact wording and behaviour of the PyPI yank and delete buttons are NOT
VERIFIED here, because they are part of the PyPI web interface and can change.
Check the PyPI help page before you rely on them.

## What this document does not cover

- No trusted publishing, no OpenID Connect, no CI upload job: this project
  publishes from the owner's machine only.
- No signing, no attestations: NOT VERIFIED for this project.
- No git tag and no GitHub release: the owner decides those separately.
