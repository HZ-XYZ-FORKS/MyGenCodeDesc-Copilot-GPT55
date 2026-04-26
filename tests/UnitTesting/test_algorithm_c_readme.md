# Test Case: test_algorithm_c

## Purpose

This test verifies package-level Algorithm C validation for destructive and ordering-sensitive replay conditions. It focuses on rejecting a child revision whose `revisionTimestamp` is earlier than its parent revision, and on rejecting parent chains that reference a missing genCodeDesc record.

## Status

Implemented / Passing

## Covered

- US-006 / AC-006-4: Algorithm C detects non-monotonic parent/child timestamps and rejects the input as clock skew.
- US-006 / AC-006-1: Algorithm C reports a missing parent genCodeDesc record as a chain break error.
- Algorithm C package API: `collect_algorithm_c_lines()`.
- v26.04 `REPOSITORY.parentRevisionIds` ordering validation.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_c.py -v`.
