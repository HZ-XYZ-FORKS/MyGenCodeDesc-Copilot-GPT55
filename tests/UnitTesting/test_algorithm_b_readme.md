# Test Case: test_algorithm_b

## Purpose

This test verifies the package-level Algorithm B patch replay path for US-001. It checks that v26.03 sparse DETAIL records join correctly with offline unified diffs, that omitted manual lines are treated as `genRatio=0`, that later patches replay over earlier snapshot state instead of being appended as independent additions, that rename/copy metadata preserves the expected file-level attribution, that Git parent metadata and SVN numeric revisions control replay order, and that the ordered patch artifact is generated for audit output.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- US-002 / AC-002-1: pure rename preserves line attribution for Algorithm B synthetic fixtures.
- US-002 / AC-002-2: rename plus modify keeps unchanged-line attribution and applies changed-line genRatio from the rename commit.
- US-002 / AC-002-3: deleted files contribute zero lines to the final Algorithm B snapshot.
- US-002 / AC-002-4: copied files are attributed to the copy commit while the original source file retains its prior attribution.
- US-007 / AC-007-2: SVN numeric `revisionId` behavior for Algorithm B replay ordering.
- US-009 / AC-009-4: Algorithm B ordered diff replay and final surviving snapshot behavior, covered for synthetic single-file and multi-file/multi-hunk fixtures.
- US-009 / AC-009-5: Algorithm B chained rename replay, covered for a synthetic two-step rename chain.
- Algorithm B package API: `collect_algorithm_b_lines()`.
- v26.03 sparse DETAIL lookup for generated lines.
- Manual/unattributed omitted line handling.
- Add-only unified diff replay for the first Algorithm B vertical slice.
- Multi-patch replay where later diffs delete existing lines, modify existing lines, and add new surviving lines.
- Multi-file, multi-hunk patch replay where every file section and hunk affects the final snapshot.
- Pure rename, rename plus modify, and chained rename replay through Git rename metadata.
- Deleted-file replay through `/dev/null` patches and copied-file replay through Git copy metadata.
- Final snapshot line numbering after deletion and modification.
- Git `parentRevisionIds` replay ordering when child timestamps sort before parent timestamps.
- SVN numeric `revisionId` replay ordering when timestamps sort out of revision order.
- Ordered `commitStart2EndTime.patch` text with run headers and per-revision commit markers.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b.py -v`.
