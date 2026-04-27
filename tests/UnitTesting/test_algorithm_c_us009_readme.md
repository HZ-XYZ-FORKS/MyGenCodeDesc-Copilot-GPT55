# Test Case: test_algorithm_c_us009

## Purpose

This test verifies package-level Algorithm C behavior for US-009 embedded-blame conditions. It focuses on add/delete accumulation, duplicate add entries for the same current file line, and SUMMARY/DETAIL mismatch diagnostics.

## Status

Implemented / Passing with focused US-009 verification

## Covered

- US-009 / AC-009-7: add/delete entries build the expected surviving line set.
- US-009 / AC-009-8: duplicate add entries for the same current line are detected and later entries overwrite earlier entries by fork-defined policy.
- US-009 / AC-009-9: SUMMARY/DETAIL mismatches are reported with revision context.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_c_us009.py -v`.
