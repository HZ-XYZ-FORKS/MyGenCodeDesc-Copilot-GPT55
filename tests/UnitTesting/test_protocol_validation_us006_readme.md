# Test Case: test_protocol_validation_us006

## Purpose

This test verifies package-level protocol loader validation for US-006 destructive and misuse conditions. It focuses on required top-level fields, required field types, BASE v26.03 optional/conditional fields, line-position requirements, Algorithm C embedded-blame required fields, summary/detail diagnostics, and strict production Git/SVN revision ID validation.

## Status

Implemented / Passing with focused US-006 verification

## Covered

- US-006 / AC-006-2: malformed genCodeDesc records are rejected with field-specific validation errors.
- US-006 / AC-006-5: invalid line attribution entries are rejected before downstream algorithms can silently ignore them.
- US-007 / AC-007-1 and AC-007-2: malformed Git and SVN revision IDs are rejected when the synthetic-fixture compatibility switch is not enabled.
- US-009 / AC-009-7 through AC-009-9 support: malformed v26.04 embedded blame revision IDs are rejected before Algorithm C accumulation.
- Schema validation breadth: required top-level fields, object/list/integer types, v26.03 line locations, and v26.04 add-entry blame timestamps.
- BASE v26.03 requiredness sync: optional documentation SUMMARY counters when no doc lines are represented, optional `REPOSITORY.vcsType` defaulting to Git validation, and mandatory presence of at least one `DETAIL[].codeLines` or `DETAIL[].docLines` collection.
- BASE v26.03 summary/detail relationship: expanded `lineRange` counts drive generated-line diagnostics, sparse omitted manual lines do not create false total-count warnings, and mismatched full/partial generated counters are reported as recoverable warnings.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_protocol_validation_us006.py -v`.
