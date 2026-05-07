# Test Case: test_cli_us001

## Purpose

This test verifies the `aggregateGenCodeDesc` CLI contract for US-001 using Algorithm A over v26.03 sparse metadata plus live Git blame, Algorithm B over v26.03 sparse metadata plus offline patch replay, and Algorithm C over v26.04 embedded-blame input. It checks that a real CLI invocation writes a v26.03-shaped aggregate JSON result with the expected metrics, writes the Algorithm B audit patch artifact, preserves Algorithm B rename/copy attribution under final paths, and reports clear Algorithm B patch-directory errors.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- US-002 / AC-002-1: pure rename preserves line attribution through the real CLI.
- US-002 / AC-002-2: rename plus modify keeps unchanged-line attribution and applies changed-line genRatio from the rename commit through the real CLI.
- US-002 / AC-002-3: deleted files contribute zero lines through the real CLI.
- US-002 / AC-002-4: copied files are attributed to the copy commit while the original source file retains its prior attribution through the real CLI.
- US-007 / AC-007-2: SVN numeric `revisionId` behavior through the real CLI.
- US-009 / AC-009-4: Algorithm B ordered replay and final surviving snapshot behavior, covered for synthetic single-file and multi-file/multi-hunk fixtures.
- US-009 / AC-009-5: Algorithm B chained rename replay through the real CLI, covered for a synthetic two-step rename chain.
- US-009 / AC-009-6: Algorithm B missing patch directory reports a fatal CLI error.
- AC-001-1: Weighted mode calculates sum of genRatio.
- AC-001-2: Fully AI mode counts only genRatio==100.
- AC-001-3: Mostly AI mode counts genRatio >= threshold.
- AC-001-6: No in-window lines yields zero denominator.
- AC-001-7: Sparse v26.03 DETAIL treats omitted lines as manual.
- CLI arguments: `--repoUrl`, `--repoBranch`, `--startTime`, `--endTime`, `--genCodeDescDir`, `--algorithm`, `--scope`, `--threshold`, `--repoPath`, `--commitPatchDir`, `--outputDir`.
- System behavior: top-level `aggregateGenCodeDesc.py` writes `aggregatedGenCodeDescV26.03.json` and `commitStart2EndTime.patch`.
- Algorithm coverage: A, B, and C.
- Protocol coverage: v26.03 and v26.04.
- Algorithm B replay coverage: add-only patches, multi-patch delete/modify/add replay, multi-file/multi-hunk patch replay, pure rename, rename plus modify, chained rename, deleted file exclusion, copied file attribution, Git parent-before-child ordering, SVN numeric revision ordering, final snapshot denominator, ordered patch artifact output, and missing patch directory diagnostics.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us001.py -v`.
