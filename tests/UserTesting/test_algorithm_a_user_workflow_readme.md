# Test Case: test_algorithm_a_user_workflow

## Purpose

This UserTesting file verifies the maintainer-facing Algorithm A workflow from `README_UserGuide.md`. It focuses on running the root CLI without the BASE-removed `--endRev` option, measuring the repository snapshot at `endTime`, auto-cloning a Git remote when `--repoPath` is omitted, warning when shallow Git history can make blame partial, and keeping SVN patch artifacts within `[startTime, endTime]`.

## Status

Implemented / Passing

## Covered

- README_UserGuide Algorithm A local Git workflow: maintainer runs `aggregateGenCodeDesc.py` with documented inputs and no `--endRev`.
- US-001 / AC-001-8: JSON metrics aggregate the alive subset at `endTime`, not lines deleted after the measurement window.
- US-009 Algorithm A: live blame remains the line-origin authority for v26.03 lookup.
- CLI public contract: help text does not advertise the BASE-removed `--endRev` option.
- README_UserGuide git remote Algorithm A workflow: caller can omit `--repoPath` and let the fork clone a Git remote working copy.
- README_UserStories / AC-005-4: shallow Git history is surfaced as a warning because blame may stop at the shallow boundary.
- README_AlgABC shared goal: SVN Algorithm A metrics and `commitStart2EndTime.patch` use the logical repository snapshot at `endTime`, excluding pre-window and post-window revisions from the audit artifact.

## Manual

1. Install test dependencies with `python3 -m pip install -e .[test]`.
2. Run `python3 -m pytest tests/UserTesting/test_algorithm_a_user_workflow.py -v`.
3. Confirm the generated aggregate counts one fully generated line even when the source repository has later commits after `endTime`.
4. Confirm the SVN patch-window case includes `src/window.py` but excludes `src/pre.py` and `src/post.py`.