# Test Case: test_cli_us010

## Purpose

This test verifies the root `aggregateGenCodeDesc.py` diagnostics and logging behavior for US-010. It focuses on structured stderr logs for synthetic Algorithm A/B/C CLI paths, DEBUG origin-detail logs, WARN logs for recoverable SUMMARY/DETAIL mismatch, and the stdout metric-result contract.

## Status

Implemented / Passing

## Covered

- US-010 / AC-010-1: default `--logLevel INFO` emits LOAD, PROCESS, and SUMMARY phase logs for a successful root CLI run.
- US-010 / AC-010-2: `--logLevel DEBUG` emits algorithm, file, line, and origin-detail decisions for successful Algorithm A, B, and C runs.
- US-010 / AC-010-3: SUMMARY/DETAIL mismatch emits WARN and processing continues.
- US-010 / AC-010-5: `--logLevel ERROR` suppresses INFO/WARN stderr output on success while the final metric result is written to stdout.
- US-010 / AC-010-6: emitted log lines use timestamp, level, component, and message fields on stderr; stdout is reserved for the final JSON metric result.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us010.py -v`.
