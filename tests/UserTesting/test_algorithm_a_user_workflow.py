import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


# OVERVIEW
# [WHAT] UserTesting for the documented Algorithm A maintainer workflow.
# [WHERE] Root CLI `aggregateGenCodeDesc.py` using v26.03 genCodeDesc and a real local Git repository.
# [WHY] A maintainer should be able to follow README_UserGuide without knowing an internal blame revision flag.
# SCOPE: Covers local Git Algorithm A endTime snapshot behavior and public help surface.
# OUT OF SCOPE: Remote auto-clone, SVN merge blame, and reference-scale performance.
#
# USER TESTING DESIGN
# US-UAT-001: As a codebase maintainer, I want Algorithm A to resolve the endTime repository snapshot from documented inputs, so that I can run the UserGuide workflow without `--endRev`.
# AC-UAT-001: GIVEN a line is introduced inside the window and deleted after endTime, WHEN the maintainer runs Algorithm A without `--endRev`, THEN the result counts the line as alive at endTime.
# AC-UAT-002: GIVEN the maintainer asks for CLI help, WHEN the help text is printed, THEN the removed BASE option `--endRev` is not advertised.
#
# TEST CASE SPECIFICATIONS
# [@AC-UAT-001,US-UAT-001]
#  TC-UAT-001 P1 Functional / Typical
#    @[Name]: verifyAlgAWorkflow_withoutEndRev_expectEndTimeSnapshotMetrics
#    @[Purpose]: Proves the documented AlgA command is enough for a maintainer workflow.
#    @[Brief]: Creates a Git repo where a generated line is alive at endTime but deleted later, then runs the root CLI without `--endRev`.
#    @[Expect]: The aggregate JSON counts the generated line and the audit patch contains the in-window addition.
# [@AC-UAT-002,US-UAT-001]
#  TC-UAT-002 P2 Design / Capability
#    @[Name]: verifyCliHelp_afterBaseEndRevRemoval_expectNoEndRevOption
#    @[Purpose]: Keeps the public CLI aligned with BASE UserGuide after `--endRev` removal.
#    @[Brief]: Reads root CLI help text.
#    @[Expect]: `--endRev` is absent from help output.
#
# TODO/TRACKING
# - TC-UAT-001: TODO -> RED -> GREEN
# - TC-UAT-002: TODO -> RED -> GREEN


def _run_git(repo_path, *args, env=None):
    completed = subprocess.run(["git", *args], cwd=repo_path, check=False, env=env, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _commit_all(repo_path, message, timestamp):
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": timestamp,
        "GIT_COMMITTER_DATE": timestamp,
        "GIT_AUTHOR_NAME": "UserTesting",
        "GIT_AUTHOR_EMAIL": "user-testing@example.test",
        "GIT_COMMITTER_NAME": "UserTesting",
        "GIT_COMMITTER_EMAIL": "user-testing@example.test",
    }
    _run_git(repo_path, "add", "-A", env=env)
    _run_git(repo_path, "commit", "-q", "-m", message, env=env)
    return _run_git(repo_path, "rev-parse", "HEAD")


def _write_v2603_record(path, repo_url, revision_id):
    record = {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "UserTestingFixture",
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
                "fileName": "src/main.py",
                "codeLines": [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": repo_url,
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": "2026-01-10T00:00:00Z",
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
# [@TC-UAT-001]
# @[Name]: verifyAlgAWorkflow_withoutEndRev_expectEndTimeSnapshotMetrics
# @[Steps]: SETUP real repo and genCodeDesc -> BEHAVIOR run documented CLI -> VERIFY aggregate metrics and patch -> CLEANUP tmp_path
def test_alg_a_user_workflow_without_end_rev_uses_end_time_snapshot(tmp_path):
    repo_path = tmp_path / "repo"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    repo_path.mkdir()
    gen_code_desc_dir.mkdir()
    _run_git(repo_path, "init", "-q")
    _run_git(repo_path, "checkout", "-b", "main")
    (repo_path / "src").mkdir()
    (repo_path / "src" / "main.py").write_text("generated = True\n", encoding="utf-8")
    revision_id = _commit_all(repo_path, "add generated line", "2026-01-10T00:00:00+0000")
    _write_v2603_record(gen_code_desc_dir / f"{revision_id}.json", str(repo_path), revision_id)
    _run_git(repo_path, "rm", "-q", "src/main.py")
    _commit_all(repo_path, "delete after measurement window", "2026-02-01T00:00:00+0000")

    completed = _run_root_cli(
        [
            "--repoUrl",
            str(repo_path),
            "--repoBranch",
            "main",
            "--startTime",
            "2026-01-01T00:00:00Z",
            "--endTime",
            "2026-01-31T00:00:00Z",
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
    assert {
        "totalCodeLines": aggregate["SUMMARY"]["totalCodeLines"],
        "weighted": aggregate["AGGREGATE"]["metrics"]["weighted"]["value"],
        "patchContainsGeneratedLine": "+generated = True" in patch_text,
    } == {"totalCodeLines": 1, "weighted": 1.0, "patchContainsGeneratedLine": True}


# [@TC-UAT-002]
# @[Name]: verifyCliHelp_afterBaseEndRevRemoval_expectNoEndRevOption
# @[Steps]: SETUP root CLI command -> BEHAVIOR print help -> VERIFY public option surface -> CLEANUP none
def test_cli_help_does_not_expose_removed_end_rev_option():
    completed = _run_root_cli(["--help"])

    assert completed.returncode == 0
    assert "--endRev" not in completed.stdout