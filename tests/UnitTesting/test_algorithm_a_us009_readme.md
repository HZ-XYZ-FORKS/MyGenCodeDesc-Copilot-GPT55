# Test Case: test_algorithm_a_us009

## Purpose

This test verifies package-level Algorithm A behavior for US-009 live-blame conditions. It focuses on configurable Git blame options, v26.03 attribution lookup by blame origin coordinates, cross-file moved code detection through Git blame copy detection, and clear failure reporting when Algorithm A cannot access the VCS repository.

## Status

Implemented / Passing with focused US-009 verification

## Covered

- US-009 / AC-009-1: Algorithm A invokes `git blame -M` for rename detection.
- README_AlgABC Algorithm A join contract: Algorithm A uses blame origin file path and origin line/range for v26.03 `DETAIL` lookup, not the current `endTime` file path and line number.
- README_AlgABC Algorithm A diagnostics: Algorithm A policy documents the origin-coordinate join contract.
- US-004 / AC-004-3 and US-009 / AC-009-1: Algorithm A maps `blameWhitespace` and `renameDetection` policies to the expected `git blame` flags.
- US-009 / AC-009-2: cross-file moved lines are attributed to their original commit when `git blame -C -C` is enabled.
- US-009 / AC-009-3: VCS access failures include the repository URL and suggest retrying or using Algorithm C.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_a_us009.py -v`.
