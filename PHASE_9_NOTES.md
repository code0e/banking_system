# Phase 9 — Final documentation and release

## Delivered

- Reworked the root README into a complete project guide covering features, requirements, installation, launch, tests, architecture, monetary precision, authentication, development history, and project scope.
- Added `SECURITY.md` to document implemented safeguards, known limitations, and safe handling guidance.
- Added `CHANGELOG.md` for the first complete release milestone.
- Added a plain-text `VERSION` file set to `1.0.0`.
- Retained the individual phase notes as implementation history.
- Confirmed the source archive contains the project source and tests without a virtual environment, Git internals, Python cache, or local SQLite database.

## Verification

Run from the project root:

```powershell
python -m unittest discover -s tests -v
python main.py
```

The automated test suite was run against the release candidate during preparation. A local CLI smoke test should also be performed after extracting the release archive.

## Release scope

Version 1.0.0 is a complete educational banking simulation. It is not production banking software and must not be used to manage real customer funds or sensitive production data.
