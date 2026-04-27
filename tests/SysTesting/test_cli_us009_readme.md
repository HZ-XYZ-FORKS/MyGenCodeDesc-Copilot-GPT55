# Test Case: test_cli_us009

## Purpose

This test verifies root `aggregateGenCodeDesc.py` behavior for US-009 algorithm-specific conditions. It focuses on Algorithm A VCS access failures and Algorithm C duplicate add plus SUMMARY/DETAIL mismatch diagnostics.

## Status

Implemented / Passing with focused US-009 verification

## Covered

- US-009 / AC-009-3: Algorithm A VCS access failures include the repository URL, retry guidance, Algorithm C fallback guidance, and no partial output.
- US-009 / AC-009-8: Algorithm C reports duplicate add entries and overwrites by later entry as fork-defined policy.
- US-009 / AC-009-9: Algorithm C reports SUMMARY/DETAIL mismatches with revision context.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us009.py -v`.
