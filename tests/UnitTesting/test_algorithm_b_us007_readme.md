# Test Case: test_algorithm_b_us007

## Purpose

This test verifies package-level Algorithm B behavior for US-007 Git vs SVN differences. It focuses on accepted Git SHA-1/SHA-256 revision IDs, SVN numeric revision ordering, SVN branch path normalization, SVN merge-blame limitations, and skipping Git-only rebase/amend assumptions for SVN.

## Status

Implemented / Passing

## Covered

- US-007 / AC-007-1: Git SHA-1 and SHA-256 revision IDs are accepted.
- US-007 / AC-007-2: SVN numeric revision IDs are accepted and replayed in revision order.
- US-007 / AC-007-3: SVN merge blame imprecision is documented as a known limitation.
- US-007 / AC-007-4: Git-only rebase/amend assumptions are skipped for SVN.
- US-007 / AC-007-5: SVN branch paths normalize leading-slash differences.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b_us007.py -v`.
