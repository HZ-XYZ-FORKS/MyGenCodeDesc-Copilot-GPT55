# Test Case: test_cli_us007

## Purpose

This test verifies root `aggregateGenCodeDesc.py` behavior for US-007 Git vs SVN differences through the Algorithm B CLI path and a real local SVN Algorithm A fixture. It focuses on Git SHA-1/SHA-256 revision IDs, SVN numeric revision IDs, SVN branch path normalization, SVN merge-blame limitation logging, skipping Git-only rewrite assumptions for SVN, and actual `svn blame` attribution from a working copy.

## Status

Implemented / Passing

## Covered

- US-007 / AC-007-1: root CLI accepts Git SHA-1 and SHA-256 revision IDs.
- US-007 / AC-007-2: root CLI accepts SVN numeric revision IDs.
- US-007 / AC-007-3: SVN merge blame imprecision is logged as a known limitation.
- US-007 / AC-007-3: Algorithm A can run real local `svn blame` and aggregate the blamed SVN revision.
- US-007 / AC-007-4: Git-only rebase/amend assumptions are skipped for SVN.
- US-007 / AC-007-5: SVN branch paths normalize leading-slash differences.
- Root CLI boundary: `aggregateGenCodeDesc.py` with `--algorithm B` and `--commitPatchDir`, plus `--algorithm A` over a local SVN working copy.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/SysTesting/test_cli_us007.py -v`.
