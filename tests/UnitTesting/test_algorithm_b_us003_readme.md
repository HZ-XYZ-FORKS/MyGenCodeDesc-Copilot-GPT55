# Test Case: test_algorithm_b_us003

## Purpose

This test verifies package-level Algorithm B behavior for US-003 commit workflow conditions. It focuses on synthetic offline patch replay for merge, squash merge, cherry-pick, revert, amend/force-push, and rebase revisionId behavior.

## Status

Implemented / Passing

## Covered

- US-003 / AC-003-1: merge commits with no file changes preserve feature-commit line attribution.
- US-003 / AC-003-2: squash merge lines are attributed to the squash commit genCodeDesc.
- US-003 / AC-003-3: cherry-picked lines are attributed to the cherry-picked revisionId.
- US-003 / AC-003-4: reverted lines are absent from the final Algorithm B snapshot.
- US-003 / AC-003-5: amended old revisionIds absent from patch history are treated as orphaned and ignored.
- US-003 / AC-003-6: rebased old revisionIds absent from patch history are treated as orphaned and ignored in favor of regenerated revisionIds.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UnitTesting/test_algorithm_b_us003.py -v`.
