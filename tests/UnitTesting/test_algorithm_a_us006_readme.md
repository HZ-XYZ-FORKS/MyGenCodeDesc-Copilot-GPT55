# Test Case: test_algorithm_a_us006

## Purpose

This test verifies package-level Algorithm A behavior for US-006 missing genCodeDesc records using a real local Git repository and live `git blame` output.

## Status

Implemented / Passing with focused US-006 verification

## Covered

- US-006 / AC-006-1: lines blamed to a revision without genCodeDesc are treated as `Manual` / `genRatio 0` for Algorithm A.
- US-006 / AC-006-1: missing blamed revisions are surfaced in `diagnostics.missingRevisions`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_a_us006.py -v`.
