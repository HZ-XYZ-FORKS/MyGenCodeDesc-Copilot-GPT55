# Test Case: test_algorithm_a_user_workflow

## Purpose

This UserTesting file verifies the maintainer-facing Algorithm A workflow from `README_UserGuide.md`. It focuses on running the root CLI without the BASE-removed `--endRev` option while still measuring the repository snapshot at `endTime`.

## Status

Implemented / Passing

## Covered

- README_UserGuide Algorithm A local Git workflow: maintainer runs `aggregateGenCodeDesc.py` with documented inputs and no `--endRev`.
- US-001 / AC-001-8: JSON metrics aggregate the alive subset at `endTime`, not lines deleted after the measurement window.
- US-009 Algorithm A: live blame remains the line-origin authority for v26.03 lookup.
- CLI public contract: help text does not advertise the BASE-removed `--endRev` option.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UserTesting/test_algorithm_a_user_workflow.py -v`.
3. Confirm the generated aggregate counts one fully generated line even though the same file is deleted after `endTime`.