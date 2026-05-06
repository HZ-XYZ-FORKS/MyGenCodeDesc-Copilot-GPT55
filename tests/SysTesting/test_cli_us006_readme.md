# Test Case: test_cli_us006

## Purpose

This test verifies the `aggregateGenCodeDesc` root CLI validation behavior for US-006 destructive and edge conditions, plus the first US-010 diagnostics/logging contract. It checks that missing input records, mismatched repository identity, duplicate revision IDs, invalid `genRatio` values, corrupted JSON, required-field/type schema failures, and AlgC parent/child clock skew fail explicitly before any aggregate output is written. It also covers Algorithm A and Algorithm B manual-attribution policies for revisions that lack genCodeDesc, UserGuide policy flag exposure, recoverable duplicate/clock-skew policies, and non-empty patch artifacts for Algorithm A and Algorithm C successful runs.

## Status

Implemented / Passing

## Covered

- US-006 / AC-006-1: empty `genCodeDescDir` is reported as missing genCodeDesc input for the current CLI boundary, Algorithm A live blame revisions without genCodeDesc are reported and treated as `Manual` / `genRatio 0` lines, Algorithm B patch revisions without genCodeDesc are replayed as `Manual` / `genRatio 0` lines by default, and `--onMissing abort` rejects missing Algorithm B genCodeDesc records before output.
- US-006 / AC-006-1: Algorithm C reports missing parent genCodeDesc records as chain break errors.
- US-006 / AC-006-2: mismatched `REPOSITORY.repoURL` and `REPOSITORY.repoBranch` are rejected with field-specific validation errors.
- US-006 / AC-006-3: duplicate `REPOSITORY.revisionId` values are rejected by default and accepted with warning under `--onDuplicate last-wins`.
- US-006 / AC-006-4: Algorithm C rejects parent/child clock skew where a child revision timestamp is earlier than its parent timestamp by default and continues with warning under `--onClockSkew ignore`.
- US-006 / AC-006-5: `genRatio` values outside 0-100 are rejected and no partial data from the invalid record is used.
- US-006 / AC-006-6: mandatory lower-camel CLI argument names are enforced by the root parser, and optional UserGuide policy flags are exposed by root CLI help.
- Validation breadth: corrupted JSON is rejected with file context before any partial output is written.
- Validation breadth: missing required protocol fields and invalid required field types are rejected before any partial output is written.
- US-010 / AC-010-4: fatal clock-skew errors are logged to stderr.
- US-010 / AC-010-5: `--logLevel ERROR` suppresses logs for successful runs.
- US-010 / AC-010-6: fatal errors use a structured timestamp/level/component/message log format.
- System behavior: top-level `aggregateGenCodeDesc.py` returns exit code 2 and does not write `genCodeDescV26.03.json` or `commitStart2EndTime.patch` on fatal validation errors.
- Output contract: successful Algorithm A and Algorithm C root CLI runs write non-empty `commitStart2EndTime.patch` artifacts with algorithm headers.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us006.py -v`.
