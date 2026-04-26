# Test Case: test_cli_us010

## Purpose

This test verifies the root `aggregateGenCodeDesc.py` diagnostics and logging behavior for US-010. It focuses on structured stderr logs for the current synthetic Algorithm C CLI path: default INFO phase logs, DEBUG detail logs, and WARN logs for recoverable SUMMARY/DETAIL mismatch.

## Status

Implemented / Passing

## Covered

- US-010 / AC-010-1: default `--logLevel INFO` emits LOAD, PROCESS, and SUMMARY phase logs for a successful root CLI run.
- US-010 / AC-010-2: `--logLevel DEBUG` emits algorithm, file, and line detail for a successful Algorithm C run.
- US-010 / AC-010-3: SUMMARY/DETAIL mismatch emits WARN and processing continues.
- US-010 / AC-010-6: emitted log lines use timestamp, level, component, and message fields on stderr.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us010.py -v`.
