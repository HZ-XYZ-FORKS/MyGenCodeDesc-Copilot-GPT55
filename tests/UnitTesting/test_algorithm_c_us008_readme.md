# Test Case: test_algorithm_c_us008

## Purpose

This test verifies package-level Algorithm C behavior for the US-008 scale and performance slice. It focuses on the empty-window edge case and on diagnostics that document current reference-scale runtime and memory policy.

## Status

Implemented / Passing

## Covered

- US-008 / AC-008-1: Algorithm A reference-scale behavior is documented as correctness-over-speed sequential processing policy.
- US-008 / AC-008-2: Algorithm C reference-scale behavior and current streaming limitation are documented.
- US-008 / AC-008-3: an empty time window returns no included lines without error.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_c_us008.py -v`.
