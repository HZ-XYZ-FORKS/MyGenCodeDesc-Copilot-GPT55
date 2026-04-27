# Test Case: test_cli_us008

## Purpose

This test verifies root `aggregateGenCodeDesc.py` behavior for the US-008 scale and performance slice. It focuses on empty-window zero metrics, documented scale policy in aggregate diagnostics, and safe abort behavior when a genCodeDesc file cannot be read mid-input.

## Status

Implemented / Passing

## Covered

- US-008 / AC-008-1: Algorithm A reference-scale behavior is documented as correctness-over-speed sequential processing policy.
- US-008 / AC-008-2: Algorithm C reference-scale behavior and current streaming limitation are documented.
- US-008 / AC-008-3: an empty time window returns zero metrics and total lines without error.
- US-008 / AC-008-4: genCodeDesc read failures abort clearly with file context and no partial output.
- Root CLI boundary: `aggregateGenCodeDesc.py` with `--algorithm C`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us008.py -v`.
