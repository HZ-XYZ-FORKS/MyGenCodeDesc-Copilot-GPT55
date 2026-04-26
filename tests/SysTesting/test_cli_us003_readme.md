# Test Case: test_cli_us003

## Purpose

This test verifies root `aggregateGenCodeDesc.py` behavior for US-003 commit workflow conditions that require the CLI to honor the Algorithm B patch history. It focuses on amend/force-push and rebase cases where stale genCodeDesc records exist but their old revisionIds are absent from the replay patch directory.

## Status

Implemented / Passing

## Covered

- US-003 / AC-003-5: amended old revisionIds absent from the patch history are ignored and reported as orphaned diagnostics.
- US-003 / AC-003-6: rebased old revisionIds absent from the patch history are ignored while regenerated revisionIds drive the output metrics and patch artifact order.
- Root CLI boundary: `aggregateGenCodeDesc.py` with `--algorithm B` and `--commitPatchDir`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us003.py -v`.
