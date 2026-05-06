# Test Case: test_algorithm_a_scale_smoke

## Purpose

This UserTesting file verifies a deterministic local Algorithm A scale smoke. It exercises the root CLI over multiple files and generated lines before maintainers run expensive provider-scale or full reference-scale benchmarks.

## Status

Implemented / Passing

## Covered

- US-001 / AC-001-1 through AC-001-6: aggregate metrics remain correct over a larger live Git snapshot.
- US-008 / AC-008-1: Algorithm A scale policy remains visible while local scale-smoke coverage grows.
- US-009 Algorithm A behavior: live Git blame runs across multiple files and writes a non-empty `commitStart2EndTime.patch`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UserTesting/test_algorithm_a_scale_smoke.py -v`.
3. Optionally raise the fixture size with `AGGREGATE_GCD_ALGA_SCALE_SMOKE_FILES` and `AGGREGATE_GCD_ALGA_SCALE_SMOKE_LINES_PER_FILE` before running the test.
4. Confirm the aggregate counts `files * lines_per_file` fully generated lines and the patch contains the first and last generated files.