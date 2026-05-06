import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ENV_VARS = (
    "AGGREGATE_GCD_HOSTED_GIT_REPO_URL",
    "AGGREGATE_GCD_HOSTED_GIT_REPO_BRANCH",
    "AGGREGATE_GCD_HOSTED_GIT_REVISION_ID",
    "AGGREGATE_GCD_HOSTED_GIT_REVISION_TIMESTAMP",
    "AGGREGATE_GCD_HOSTED_GIT_FILE",
    "AGGREGATE_GCD_HOSTED_GIT_LINE",
)


# OVERVIEW
# [WHAT] Opt-in UserTesting for Algorithm A against a real hosted Git provider fixture.
# [WHERE] Root CLI `aggregateGenCodeDesc.py` using v26.03 genCodeDesc and a hosted Git remote URL.
# [WHY] Production readiness needs a repeatable path for provider-backed clone/blame/output verification.
# SCOPE: Covers hosted Git remote auto-clone without `--repoPath`, live blame, and output artifact creation.
# OUT OF SCOPE: Provider credential provisioning, provider outage simulation, and full reference-scale benchmarking.
#
# USER TESTING DESIGN
# US-UAT-HOSTED-001: As a maintainer, I want an opt-in hosted Git fixture for Algorithm A, so that provider-backed production behavior can be verified when credentials and fixture metadata are available.
# AC-UAT-HOSTED-001: GIVEN hosted Git fixture environment variables are not configured, WHEN the test suite runs locally, THEN the provider test is skipped without failing deterministic tests.
# AC-UAT-HOSTED-002: GIVEN hosted Git fixture environment variables identify a generated line, WHEN the maintainer runs the test, THEN Algorithm A clones the hosted remote, blames the endTime snapshot, writes outputs, and counts at least that line.
#
# TEST CASE SPECIFICATIONS
# [@AC-UAT-HOSTED-001,US-UAT-HOSTED-001]
#  TC-UAT-HOSTED-001 P2 Design / Configuration
#    @[Name]: verifyAlgAHostedProvider_withoutFixtureEnv_expectSkip
#    @[Purpose]: Keeps normal local runs deterministic while documenting required provider inputs.
#    @[Brief]: Checks for required environment variables before invoking the hosted provider workflow.
#    @[Expect]: Missing fixture configuration skips the hosted provider test.
# [@AC-UAT-HOSTED-002,US-UAT-HOSTED-001]
#  TC-UAT-HOSTED-002 P1 Functional / Typical
#    @[Name]: verifyAlgAHostedProvider_withFixtureEnv_expectRemoteBlameOutputs
#    @[Purpose]: Proves the production remote-provider path can be exercised end to end.
#    @[Brief]: Writes a v26.03 fixture from environment metadata and runs Algorithm A without `--repoPath`.
#    @[Expect]: Aggregate and patch outputs exist, repo metadata matches, and at least one line is counted.
#
# TODO/TRACKING
# - TC-UAT-HOSTED-001: TODO -> GREEN
# - TC-UAT-HOSTED-002: TODO -> GREEN when provider fixture env is configured


def _hosted_fixture_env():
    values = {name: os.environ.get(name, "") for name in REQUIRED_ENV_VARS}
    missing = [name for name, value in values.items() if not value]
    if missing:
        pytest.skip("hosted Git Algorithm A fixture env missing: " + ", ".join(missing))
    return values


def _write_v2603_record(path, fixture):
    line_number = int(fixture["AGGREGATE_GCD_HOSTED_GIT_LINE"])
    record = {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "HostedProviderUserTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 1,
            "fullGeneratedCodeLines": 1,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": fixture["AGGREGATE_GCD_HOSTED_GIT_FILE"],
                "codeLines": [{"lineLocation": line_number, "genRatio": 100, "genMethod": "codeCompletion"}],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": fixture["AGGREGATE_GCD_HOSTED_GIT_REPO_URL"],
            "repoBranch": fixture["AGGREGATE_GCD_HOSTED_GIT_REPO_BRANCH"],
            "revisionId": fixture["AGGREGATE_GCD_HOSTED_GIT_REVISION_ID"],
            "revisionTimestamp": fixture["AGGREGATE_GCD_HOSTED_GIT_REVISION_TIMESTAMP"],
        },
    }
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _run_root_cli(args):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "aggregateGenCodeDesc.py"), *args],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


# USER TESTING IMPLEMENTATION
# [@TC-UAT-HOSTED-001,@TC-UAT-HOSTED-002]
# @[Name]: verifyAlgAHostedProvider_withFixtureEnv_expectRemoteBlameOutputs
# @[Steps]: SETUP env-backed genCodeDesc -> BEHAVIOR run AlgA hosted remote CLI -> VERIFY outputs and counted lines -> CLEANUP tmp_path
def test_alg_a_hosted_provider_fixture_runs_remote_blame_when_configured(tmp_path):
    fixture = _hosted_fixture_env()
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_v2603_record(gen_code_desc_dir / "hosted-fixture.json", fixture)

    completed = _run_root_cli(
        [
            "--repoUrl",
            fixture["AGGREGATE_GCD_HOSTED_GIT_REPO_URL"],
            "--repoBranch",
            fixture["AGGREGATE_GCD_HOSTED_GIT_REPO_BRANCH"],
            "--startTime",
            fixture["AGGREGATE_GCD_HOSTED_GIT_REVISION_TIMESTAMP"],
            "--endTime",
            fixture["AGGREGATE_GCD_HOSTED_GIT_REVISION_TIMESTAMP"],
            "--genCodeDescDir",
            str(gen_code_desc_dir),
            "--algorithm",
            "A",
            "--scope",
            "A",
            "--outputDir",
            str(output_dir),
        ]
    )

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert aggregate["REPOSITORY"]["repoURL"] == fixture["AGGREGATE_GCD_HOSTED_GIT_REPO_URL"]
    assert aggregate["SUMMARY"]["totalCodeLines"] >= 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] > 0
    assert fixture["AGGREGATE_GCD_HOSTED_GIT_FILE"] in patch_text