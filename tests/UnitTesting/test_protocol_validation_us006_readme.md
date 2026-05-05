# Test Case: test_protocol_validation_us006

## Purpose

This test verifies package-level protocol loader validation for US-006 destructive and misuse conditions. It focuses on required top-level fields, required field types, line-location requirements, and Algorithm C embedded-blame required fields.

## Status

Implemented / Passing with focused US-006 verification

## Covered

- US-006 / AC-006-2: malformed genCodeDesc records are rejected with field-specific validation errors.
- US-006 / AC-006-5: invalid line attribution entries are rejected before downstream algorithms can silently ignore them.
- Schema validation breadth: required top-level fields, object/list/integer types, v26.03 line locations, and v26.04 add-entry blame timestamps.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_protocol_validation_us006.py -v`.
