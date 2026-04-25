# Test Case: test_algorithm_b

## Purpose

This test verifies the package-level Algorithm B patch replay path for US-001. It checks that v26.03 sparse DETAIL records join correctly with offline unified diffs, that omitted manual lines are treated as `genRatio=0`, and that later patches replay over earlier snapshot state instead of being appended as independent additions.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- Algorithm B package API: `collect_algorithm_b_lines()`.
- v26.03 sparse DETAIL lookup for generated lines.
- Manual/unattributed omitted line handling.
- Add-only unified diff replay for the first Algorithm B vertical slice.
- Multi-patch replay where later diffs delete existing lines, modify existing lines, and add new surviving lines.
- Final snapshot line numbering after deletion and modification.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b.py -v`.
