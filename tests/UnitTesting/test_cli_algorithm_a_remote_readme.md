# Test Case: test_cli_algorithm_a_remote

## Purpose

This UnitTesting file verifies Algorithm A remote Git preparation at the CLI helper boundary. It focuses on clone command construction for production-sized hosted repositories where fetching unrelated branches adds avoidable cost and risk.

## Status

Implemented / Passing

## Covered

- Algorithm A remote workflow: `--repoUrl` plus `--repoBranch` without `--repoPath` prepares a working copy for the requested branch.
- US-008 scale/performance pressure: remote preparation should avoid unnecessary branch fetches.
- US-009 Algorithm A-specific behavior: CLI remote preparation remains explicit and testable before live blame begins.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_cli_algorithm_a_remote.py -v`.
3. Confirm the captured clone command contains `--single-branch --branch <repoBranch>` before the remote URL separator.