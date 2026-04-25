# Test Case: test_algorithm_b

## Purpose

This test verifies the package-level Algorithm B patch replay path for US-001. It checks that a v26.03 sparse DETAIL record joins correctly with an offline add-only unified diff and treats the omitted manual line as `genRatio=0`.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- Algorithm B package API: `collect_algorithm_b_lines()`.
- v26.03 sparse DETAIL lookup for generated lines.
- Manual/unattributed omitted line handling.
- Add-only unified diff replay for the first Algorithm B vertical slice.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b.py -v`.
