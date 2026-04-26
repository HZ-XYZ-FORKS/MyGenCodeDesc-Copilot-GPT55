# Test Case: test_algorithm_b_us006

## Purpose

This test verifies package-level Algorithm B behavior for US-006 missing genCodeDesc records. It focuses on the offline patch-replay path where a patch revision exists in `commitPatchDir`, but no matching v26.03 genCodeDesc record exists.

## Status

Implemented / Passing

## Covered

- US-006 / AC-006-1: a patch revision without genCodeDesc is still replayed and its new live lines are treated as `genRatio 0` / `Manual`.
- Diagnostics: the missing patch revision is reported in `missingRevisions`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b_us006.py -v`.
