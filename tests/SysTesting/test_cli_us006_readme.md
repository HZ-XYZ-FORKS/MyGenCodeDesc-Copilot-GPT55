# Test Case: test_cli_us006

## Purpose

This test verifies the `aggregateGenCodeDesc` root CLI validation behavior for US-006 destructive and edge conditions. It checks that missing input records, mismatched repository identity, duplicate revision IDs, and invalid `genRatio` values fail explicitly before any aggregate output is written.

## Status

Implemented / Passing

## Covered

- US-006 / AC-006-1: empty `genCodeDescDir` is reported as missing genCodeDesc input for the current CLI boundary.
- US-006 / AC-006-2: mismatched `REPOSITORY.repoURL` and `REPOSITORY.repoBranch` are rejected with field-specific validation errors.
- US-006 / AC-006-3: duplicate `REPOSITORY.revisionId` values are rejected.
- US-006 / AC-006-5: `genRatio` values outside 0-100 are rejected and no partial data from the invalid record is used.
- System behavior: top-level `aggregateGenCodeDesc.py` returns exit code 2 and does not write `genCodeDescV26.03.json` or `commitStart2EndTime.patch` on fatal validation errors.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us006.py -v`.
