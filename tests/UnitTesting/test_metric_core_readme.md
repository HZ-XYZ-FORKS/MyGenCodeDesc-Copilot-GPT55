# Test Case: test_metric_core

## Purpose

This test verifies the pure Python metric calculation package API for US-001. It focuses on Weighted, Fully AI, Mostly AI, threshold handling, all-human input, all-AI input, and zero-denominator behavior.

## Status

Implemented / Passing

## Covered

- US-001: Core Metric Calculation.
- AC-001-1: Weighted mode calculates sum of genRatio.
- AC-001-2: Fully AI mode counts only genRatio==100.
- AC-001-3: Mostly AI mode counts genRatio >= threshold.
- AC-001-4: All lines are human-written.
- AC-001-5: All lines are fully AI-generated.
- AC-001-6: No lines changed within the time window.
- Python package API: `aggregate_gen_code_desc.metrics`.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_metric_core.py -v`.
