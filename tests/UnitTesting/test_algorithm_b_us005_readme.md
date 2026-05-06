# Test Case: test_algorithm_b_us005

## Purpose

This test verifies package-level Algorithm B behavior for US-005 branch and history conditions. It focuses on synthetic offline patch replay for time-window filtering, multiple merge uniqueness, long-lived branch origins, shallow-history and replay-context limitation documentation, and submodule exclusion policy.

## Status

Implemented / Passing

## Covered

- US-005 / AC-005-1: surviving lines whose origin timestamp is before `startTime` are excluded.
- US-005 / AC-005-2: multiple merged branches contribute distinct live lines exactly once.
- US-005 / AC-005-3: long-lived branch fixtures include in-window feature origins and exclude old base origins.
- US-005 / AC-005-4: Algorithm B reports shallow-history and replay-context limitation policies.
- US-005 / AC-005-5: submodule gitlink patches contribute no parent-repo lines and require an independent run.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b_us005.py -v`.
