# Test Case: test_cli_us005

## Purpose

This test verifies root `aggregateGenCodeDesc.py` behavior for US-005 branch and history conditions through the Algorithm B CLI path. It focuses on multiple merged branch contributions being counted once, submodule gitlink patches being excluded from parent metrics, and the history policy emitted in aggregate diagnostics.

## Status

Implemented / Passing

## Covered

- US-005 / AC-005-2: multiple merged branches contribute distinct live lines exactly once in root CLI output.
- US-005 / AC-005-5: submodule gitlink patches contribute no parent-repo lines and require an independent aggregate run.
- Root CLI boundary: `aggregateGenCodeDesc.py` with `--algorithm B` and `--commitPatchDir`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us005.py -v`.
