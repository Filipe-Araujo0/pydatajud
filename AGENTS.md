# pydatajud Development Guide

## Project Vision

`pydatajud` is a Python wrapper for Brazil's public DataJud/CNJ API. Its purpose
is to make process lookup and movement extraction easier, safer, and more
predictable for Brazilian developers, legal operations teams, researchers, and
automation workflows that need to consume public judicial data.

The library should feel like a practical public utility: small API surface,
clear behavior, explicit failures, and enough structure that users do not need
to understand every DataJud endpoint before performing a common query.

The project is not affiliated with CNJ. It must be careful not to imply official
status, guaranteed data availability, or legal authorization beyond what the
official public API and its terms allow.

## Audience And Language Policy

The first audience is Brazilian. General user-facing documentation may use
Portuguese (Brazilian Portuguese) because the wrapped system is Brazilian, the
legal domain is Brazilian, and most first users are expected to be Brazilian.

Code-facing material should follow international Python norms and be written in
English:

- Source code, module names, function names, class names, variables, and comments
  should be in English.
- Public Python docstrings and exception class names should be in English.
- Technical contribution guidance about coding standards may be in English.
- User-facing README examples and explanatory documentation may remain in
  Portuguese when that makes adoption easier for the target audience.
- Error messages may be Portuguese when exposed mainly through the CLI, but API
  contracts and exception types should remain language-neutral and explicit.

## What New Contributors Should Assume

- This is a package-first project intended for PyPI.
- The package uses a `src/` layout.
- The primary public interface is the synchronous `DataJudClient`.
- The CLI is a thin layer over the Python API.
- Brazilian judiciary-specific resolver behavior is documented in
  `docs/datajud-resolver.md`; do not duplicate all of that domain explanation in
  code comments.
- Tests must not call the real CNJ API by default.
- Real integration checks must be marked with `@pytest.mark.e2e`, require an
  explicit API key, and not run in the normal test suite.
- DataJud can change response details, endpoint availability, limits, and terms;
  code should fail clearly when assumptions no longer hold.
- Public judicial data may still contain sensitive personal data. Do not commit
  real API keys, secrets, or unnecessary raw process data.

## Quality Bar

The library should optimize for trust:

- Keep the public API small and stable.
- Prefer explicit exceptions over silent fallbacks.
- Preserve raw API data when possible so users are not locked into a narrow
  interpretation of the DataJud payload.
- Add typed interfaces and keep `mypy --strict` passing.
- Keep tests deterministic and independent from external network availability.
- Use mocks for HTTP behavior in unit tests.
- Avoid broad dependencies unless they clearly reduce complexity for users.
- Document limitations directly. Do not hide CNJ/API constraints behind a nicer
  interface.

## Documentation Is Mandatory

Documentation review is required for every project change. Treat docs as part
of the implementation, not as a follow-up task.

For each change, explicitly check whether any of these files must be updated:

- `README.md`: user-facing behavior, installation, examples, public limitations,
  and API key instructions.
- `docs/`: domain-specific explanations, especially DataJud/CNJ behavior and
  Brazilian judiciary assumptions.
- `CONTRIBUTING.md`: contributor workflow, local setup, validation, and PR
  expectations.
- `AGENTS.md`: project direction, quality anchors, architecture rules, and
  agent/new-contributor guidance.
- `CHANGELOG.md`: all user-visible behavior, public API, packaging, CLI, and
  documentation changes.
- `gitree.txt`: repository map when versionable files are added or removed.

If no documentation file changes, the change author should be able to explain
why the current docs are still accurate. Any change to resolver behavior,
response shape, CLI output, exceptions, packaging, public workflow, or DataJud
assumptions must include documentation updates.

## Coding Standards

- Python support starts at Python 3.10.
- Use type hints for new code.
- Keep imports at the top of the file.
- Prefer dataclasses or typed structures for stable return objects.
- Keep functions small when that makes behavior easier to test.
- Keep the client transport testable by allowing an injectable session-like
  object.
- Use `requests` for the synchronous client unless there is a deliberate API
  decision to add async support.
- Do not add automatic retry, pagination, caching, or rate-limit behavior without
  tests and clear public API semantics.

## Error Handling Principles

- Invalid CNJ number: raise a dedicated validation exception.
- Unsupported tribunal/branch: raise a dedicated resolver exception.
- HTTP/authentication failures: raise client-level exceptions that preserve the
  useful context without leaking secrets.
- Unexpected response shape: raise a clear invalid-response exception.
- Process not found: keep this explicit and configurable when useful.

Do not swallow malformed data just to return a partial success unless the public
API explicitly documents that behavior.

## Testing Expectations

Before opening a PR, run:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -m "not e2e"
python -m build
twine check dist/*
```

Optional real-network E2E:

```bash
export DATAJUD_API_KEY="..."
pytest -m e2e -ra
```

Expected test coverage for changes:

- Resolver changes need CNJ validation and endpoint mapping cases.
- Client changes need HTTP success, auth failure, malformed response, and empty
  result cases.
- CLI changes need output and exit-code tests.
- Documentation-only changes do not need new tests, but should keep examples in
  sync with the current public API.

## Project Organization

- `src/pydatajud/resolver.py`: CNJ parsing, normalization, validation, and
  endpoint resolution.
- `src/pydatajud/client.py`: HTTP client and result object.
- `src/pydatajud/cli.py`: command-line interface only; keep business logic in
  the Python API.
- `src/pydatajud/exceptions.py`: public exception hierarchy.
- `docs/datajud-resolver.md`: Brazilian judiciary and CNJ-number context behind
  endpoint resolution.
- `tests/`: deterministic tests, normally without network calls.
- `.github/workflows/`: CI and PyPI publishing workflow.
- `gitree.txt`: generated repository tree used as a fast navigation aid.

When adding a new capability, first decide whether it belongs to endpoint
resolution, HTTP transport, response modeling, or CLI presentation. Avoid mixing
those concerns in the same module.

## Release Discipline

- Update `CHANGELOG.md` for user-visible changes.
- Keep package metadata in `pyproject.toml` accurate.
- Build and validate the distribution before publishing.
- Publish through GitHub Actions and PyPI Trusted Publishing/OIDC.
- Do not commit build artifacts from `dist/`.

## Effective Change Workflow

For normal changes, use this workflow:

```bash
ruff format --check .
ruff check .
mypy src tests
pytest -m "not e2e"
```

If the change affects packaging or release readiness, also run:

```bash
python -m build
twine check dist/*
```

Before committing:

- Review and update all relevant documentation listed in
  "Documentation Is Mandatory".
- Regenerate `gitree.txt` if versionable files were added or removed.
- Keep local query outputs and build artifacts out of the commit.

Commit and push:

```bash
git add <changed-files>
git commit -m "<type>: <short imperative summary>"
git push origin main
```

For a PyPI release:

- Update `version` in `pyproject.toml`.
- Move the relevant `CHANGELOG.md` entries from `Unreleased` to the release
  version.
- Run the full validation including build and `twine check`.
- Commit and push the release prep.
- Create and push a matching tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Do not tag a release without updating `pyproject.toml`; PyPI will reject a
second upload of the same version.

## gitree.txt

Keep `gitree.txt` tracked at the repository root. It is a compact map of
versionable files and line counts, useful for new contributors and agents that
need to understand the project quickly.

If `gitree.txt` does not exist, or whenever adding/removing versionable files,
regenerate it with:

```bash
tmp="$(mktemp)" && (echo "Legend: path:{lines}  (lines = total number of lines via wc -l)"; git ls-files -co --exclude-standard -z | while IFS= read -r -d '' f; do printf './%s:%s\n' "$f" "$(wc -l < "$f")"; done | tree --fromfile) > "$tmp" && mv "$tmp" gitree.txt
```

Do not include local query outputs, build artifacts, virtualenvs, caches, or
process data dumps in `gitree.txt`; keep those ignored.

## Non-Goals For Now

- Scraping court websites.
- Bypassing CNJ/API limitations.
- Treating DataJud data as legally complete case history.
- Running network integration tests as part of default CI.
- Making E2E depend on fixed movement counts or unstable payload fields.
- Adding async support before the synchronous API is mature.
