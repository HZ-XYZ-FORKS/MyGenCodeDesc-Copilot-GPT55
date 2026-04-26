# Test Case: test_diagnostics

## Purpose

This test verifies package-level diagnostics configuration without the CLI. It focuses on separate logger instances so tests can capture DEBUG output without leaking log level or stream state across test cases.

## Status

Implemented / Passing

## Covered

- US-010 / AC-010-7: log level can be configured programmatically without CLI flags.
- Logger instance isolation: DEBUG capture in one logger does not affect another logger configured at ERROR.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_diagnostics.py -v`.
