# Test Case: test_algorithm_a_hosted_provider

## Purpose

This UserTesting file provides an opt-in hosted Git provider fixture for Algorithm A. It lets maintainers verify the real remote clone and live blame workflow without `--repoPath` when provider credentials and fixture metadata are available.

## Status

Implemented / Skipped unless fixture environment variables are configured

## Covered

- README_UserGuide Algorithm A remote Git workflow with hosted `--repoUrl` and no `--repoPath`.
- US-008 / provider-scale readiness: establishes a repeatable real-provider verification path outside deterministic local fixtures.
- US-009 Algorithm A behavior: hosted remote clone, live blame, aggregate output, and patch artifact creation.

## Manual

1. Choose a small hosted Git fixture repository/branch with one known generated line.
2. Export all required variables:
   - `AGGREGATE_GCD_HOSTED_GIT_REPO_URL`
   - `AGGREGATE_GCD_HOSTED_GIT_REPO_BRANCH`
   - `AGGREGATE_GCD_HOSTED_GIT_REVISION_ID`
   - `AGGREGATE_GCD_HOSTED_GIT_REVISION_TIMESTAMP`
   - `AGGREGATE_GCD_HOSTED_GIT_FILE`
   - `AGGREGATE_GCD_HOSTED_GIT_LINE`
3. Ensure any required Git credentials are available to `git clone`.
4. Run `python3 -m pytest tests/UserTesting/test_algorithm_a_hosted_provider.py -v`.
5. Confirm `genCodeDescV26.03.json` and `commitStart2EndTime.patch` are written and the aggregate counts at least one generated line.