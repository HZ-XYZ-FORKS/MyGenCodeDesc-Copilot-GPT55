# Test Case: test_algorithm_c

## Purpose

This test verifies package-level Algorithm C validation for clock-skew-sensitive replay ordering. It focuses on rejecting a child revision whose `revisionTimestamp` is earlier than its parent revision, because Algorithm C uses timestamps to order embedded-blame records.

## Status

Implemented / Passing

## Covered

- US-006 / AC-006-4: Algorithm C detects non-monotonic parent/child timestamps and rejects the input as clock skew.
- Algorithm C package API: `collect_algorithm_c_lines()`.
- v26.04 `REPOSITORY.parentRevisionIds` ordering validation.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_c.py -v`.
