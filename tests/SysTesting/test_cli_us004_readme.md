# Test Case: test_cli_us004

## Purpose

This test verifies root `aggregateGenCodeDesc.py` behavior for US-004 line-level ownership transfer through the Algorithm B CLI path. It focuses on an AI-generated line edited by a human, a manual line rewritten by AI, and the line ownership policy emitted in aggregate diagnostics.

## Status

Implemented / Passing

## Covered

- US-004 / AC-004-1: human edits to AI-generated lines transfer attribution to the human edit commit in root CLI output.
- US-004 / AC-004-2: AI rewrites of manual lines transfer attribution to the AI rewrite commit in root CLI output.
- US-004 / AC-004-3: Algorithm B aggregate diagnostics document the whitespace-only change policy.
- Root CLI boundary: `aggregateGenCodeDesc.py` with `--algorithm B` and `--commitPatchDir`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us004.py -v`.
