# Test Case: test_protocol_loader

## Purpose

This test verifies protocol-loading helper behavior that is easy to break when accepting JSONC-style comments. It specifically protects URL strings containing `https://` from being corrupted by comment stripping.

## Status

Implemented / Passing

## Covered

- Protocol JSON/JSONC loading support.
- Preservation of `REPOSITORY.repoURL` string values containing `//`.
- Regression coverage for CLI fixture parsing.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_protocol_loader.py -v`.
