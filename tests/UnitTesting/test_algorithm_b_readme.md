# Test Case: test_algorithm_b

## Purpose

This test verifies the package-level Algorithm B patch replay path for US-001. It checks that v26.03 sparse DETAIL records join correctly with offline unified diffs, that omitted manual lines are treated as `genRatio=0`, that later patches replay over earlier snapshot state instead of being appended as independent additions, that Git parent metadata and SVN numeric revisions control replay order, and that the ordered patch artifact is generated for audit output.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- US-007 / AC-007-2: SVN numeric `revisionId` behavior for Algorithm B replay ordering.
- US-009 / AC-009-4: Algorithm B ordered diff replay and final surviving snapshot behavior, covered for synthetic single-file and multi-file/multi-hunk fixtures.
- Algorithm B package API: `collect_algorithm_b_lines()`.
- v26.03 sparse DETAIL lookup for generated lines.
- Manual/unattributed omitted line handling.
- Add-only unified diff replay for the first Algorithm B vertical slice.
- Multi-patch replay where later diffs delete existing lines, modify existing lines, and add new surviving lines.
- Multi-file, multi-hunk patch replay where every file section and hunk affects the final snapshot.
- Final snapshot line numbering after deletion and modification.
- Git `parentRevisionIds` replay ordering when child timestamps sort before parent timestamps.
- SVN numeric `revisionId` replay ordering when timestamps sort out of revision order.
- Ordered `commitStart2EndTime.patch` text with run headers and per-revision commit markers.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b.py -v`.
