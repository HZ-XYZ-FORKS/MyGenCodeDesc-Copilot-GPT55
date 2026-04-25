# Test Case: test_cli_us001

## Purpose

This test verifies the `aggregateGenCodeDesc` CLI contract for US-001 using Algorithm A over v26.03 sparse metadata plus live Git blame, Algorithm B over v26.03 sparse metadata plus offline patch replay, and Algorithm C over v26.04 embedded-blame input. It checks that a real CLI invocation writes a v26.03-shaped aggregate JSON result with the expected metrics.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- AC-001-1: Weighted mode calculates sum of genRatio.
- AC-001-2: Fully AI mode counts only genRatio==100.
- AC-001-3: Mostly AI mode counts genRatio >= threshold.
- AC-001-6: No in-window lines yields zero denominator.
- AC-001-7: Sparse v26.03 DETAIL treats omitted lines as manual.
- CLI arguments: `--repoUrl`, `--repoBranch`, `--startTime`, `--endTime`, `--genCodeDescDir`, `--algorithm`, `--scope`, `--threshold`, `--repoPath`, `--endRev`, `--commitPatchDir`, `--outputDir`.
- System behavior: top-level `aggregateGenCodeDesc.py` writes `genCodeDescV26.03.json`.
- Algorithm coverage: A, B, and C.
- Protocol coverage: v26.03 and v26.04.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us001.py -v`.
