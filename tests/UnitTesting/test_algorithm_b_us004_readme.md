# Test Case: test_algorithm_b_us004

## Purpose

This test verifies package-level Algorithm B behavior for US-004 line-level ownership transfer conditions. It focuses on synthetic offline patch replay where modified, replaced, re-added, and moved lines receive attribution from the commit that introduces their current form.

## Status

Implemented / Passing

## Covered

- US-004 / AC-004-1: human edits to AI-generated lines transfer attribution to the human edit commit.
- US-004 / AC-004-2: AI rewrites of manual lines transfer attribution to the AI rewrite commit.
- US-004 / AC-004-3: whitespace-only delete/add patch hunks transfer attribution and Algorithm B reports that policy.
- US-004 / AC-004-4: file-wide replacement patches transfer all replaced lines to the replacing commit.
- US-004 / AC-004-5: identical deleted and re-added content receives new attribution.
- US-004 / AC-004-6: moved lines represented as delete/add hunks receive move-commit attribution.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b_us004.py -v`.
