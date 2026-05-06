import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


# OVERVIEW
# [WHAT] UserTesting for the documented Algorithm A maintainer workflow.
# [WHERE] Root CLI `aggregateGenCodeDesc.py` using v26.03 genCodeDesc and real local Git/SVN repositories.
# [WHY] A maintainer should be able to follow README_UserGuide without knowing internal revision flags.
# SCOPE: Covers local Git/SVN Algorithm A endTime snapshot behavior, Git remote preparation, shallow-history warning, and public help surface.
# OUT OF SCOPE: SVN merge blame, hosted-provider outages, and reference-scale performance.
#
# USER TESTING DESIGN
# US-UAT-001: As a codebase maintainer, I want Algorithm A to resolve the endTime repository snapshot from documented inputs, so that I can run the UserGuide workflow without `--endRev`.
# US-UAT-002: As a codebase maintainer, I want Algorithm A to prepare a working copy for a remote Git URL when `--repoPath` is omitted, so that the documented remote workflow is usable.
# US-UAT-003: As a codebase maintainer, I want Algorithm A to flag shallow Git history, so that I do not mistake partial blame for authoritative production output.
# US-UAT-004: As a codebase maintainer using SVN, I want Algorithm A patch artifacts to honor `[startTime, endTime]`, so that audit output does not include outside-window revisions.
# US-UAT-005: As a codebase maintainer, I want remote Git outage failures to be explicit and non-partial, so that I can retry safely or switch algorithms.
# AC-UAT-001: GIVEN a line is introduced inside the window and deleted after endTime, WHEN the maintainer runs Algorithm A without `--endRev`, THEN the result counts the line as alive at endTime.
# AC-UAT-002: GIVEN the maintainer asks for CLI help, WHEN the help text is printed, THEN the removed BASE option `--endRev` is not advertised.
# AC-UAT-003: GIVEN a Git remote URL and no `--repoPath`, WHEN the maintainer runs Algorithm A, THEN the tool clones/checks out the branch and writes valid metrics.
# AC-UAT-004: GIVEN a shallow Git working copy, WHEN the maintainer runs Algorithm A, THEN diagnostics warn that blame may be partial at the shallow boundary.
# AC-UAT-005: GIVEN an SVN file is added inside the window and deleted after endTime, WHEN the maintainer runs Algorithm A, THEN metrics and `commitStart2EndTime.patch` use the SVN snapshot at endTime.
# AC-UAT-006: GIVEN a Git remote URL cannot be cloned and no `--repoPath` is provided, WHEN the maintainer runs Algorithm A, THEN the CLI exits with runtime failure guidance and writes no partial outputs.
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
# [@AC-UAT-003,US-UAT-002]
#  TC-UAT-003 P1 Functional / Typical
#    @[Name]: verifyAlgARemoteWorkflow_withoutRepoPath_expectAutoCloneMetrics
#    @[Purpose]: Proves the documented Git remote AlgA workflow is usable without pre-cloning.
#    @[Brief]: Publishes a bare file:// Git remote, runs the root CLI without `--repoPath`, and verifies metrics.
#    @[Expect]: The aggregate JSON counts the generated line at the endTime snapshot.
# [@AC-UAT-004,US-UAT-003]
#  TC-UAT-004 P3 Quality / Robust
#    @[Name]: verifyAlgAShallowWorkflow_withShallowClone_expectPartialBlameWarning
#    @[Purpose]: Prevents shallow history from silently looking production-authoritative.
#    @[Brief]: Runs Algorithm A against a depth-1 Git working copy.
#    @[Expect]: The aggregate diagnostics and stderr warn about shallow history.
# [@AC-UAT-005,US-UAT-004]
#  TC-UAT-005 P1 Functional / Boundary
#    @[Name]: verifyAlgASvnWorkflow_withPostWindowDelete_expectEndTimePatchWindow
#    @[Purpose]: Proves SVN audit artifacts and metrics are constrained to the documented measurement window.
#    @[Brief]: Creates SVN revisions before, inside, and after the window, deletes the in-window file after endTime, and runs the root CLI.
#    @[Expect]: The aggregate JSON counts the in-window file and the patch includes only the in-window add.
# [@AC-UAT-006,US-UAT-005]
#  TC-UAT-006 P1 Functional / Fault
#    @[Name]: verifyAlgARemoteWorkflow_whenCloneFails_expectGuidanceAndNoPartialOutput
#    @[Purpose]: Makes remote outage behavior safe and actionable for production users.
#    @[Brief]: Points Algorithm A at a missing Git remote without `--repoPath`.
#    @[Expect]: The CLI exits 1, reports Algorithm A VCS recovery guidance, and writes no aggregate or patch files.
#
# TODO/TRACKING
# - TC-UAT-001: TODO -> RED -> GREEN
# - TC-UAT-002: TODO -> RED -> GREEN
# - TC-UAT-003: TODO -> RED -> GREEN
# - TC-UAT-004: TODO -> RED -> GREEN
# - TC-UAT-005: TODO -> RED -> GREEN
# - TC-UAT-006: TODO -> RED -> GREEN


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


def _write_v2603_record(
    path,
    repo_url,
    revision_id,
    *,
    vcs_type="git",
    repo_branch="main",
    file_name="src/main.py",
    revision_timestamp="2026-01-10T00:00:00Z",
):
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
                "fileName": file_name,
                "codeLines": [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            }
        ],
        "REPOSITORY": {
            "vcsType": vcs_type,
            "repoURL": repo_url,
            "repoBranch": repo_branch,
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
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


def _assert_no_partial_outputs(output_dir):
    assert not (output_dir / "genCodeDescV26.03.json").exists()
    assert not (output_dir / "commitStart2EndTime.patch").exists()


def _clone_bare(source_repo_path, bare_repo_path):
    completed = subprocess.run(
        ["git", "clone", "--bare", str(source_repo_path), str(bare_repo_path)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr


def _clone_shallow(remote_url, branch_name, clone_path):
    completed = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch_name, "--", remote_url, str(clone_path)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr


def _run_svn(path, *args):
    completed = subprocess.run(["svn", *args], cwd=path, check=False, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _commit_svn(working_copy_path, message):
    output = _run_svn(working_copy_path, "commit", "-m", message)
    match = re.search(r"Committed revision (\d+)", output)
    assert match is not None, output
    return match.group(1)


def _svn_revision_timestamp(working_copy_path, revision_id):
    output = _run_svn(working_copy_path, "log", "--xml", "-r", revision_id, str(working_copy_path))
    timestamp = ET.fromstring(output).findtext(".//date")
    assert timestamp is not None
    return timestamp


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


# [@TC-UAT-003]
# @[Name]: verifyAlgARemoteWorkflow_withoutRepoPath_expectAutoCloneMetrics
# @[Steps]: SETUP bare remote and genCodeDesc -> BEHAVIOR run documented remote CLI -> VERIFY aggregate metrics -> CLEANUP tmp_path
def test_alg_a_remote_user_workflow_without_repo_path_auto_clones(tmp_path):
    source_repo_path = tmp_path / "source-repo"
    bare_repo_path = tmp_path / "origin.git"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    source_repo_path.mkdir()
    gen_code_desc_dir.mkdir()
    _run_git(source_repo_path, "init", "-q")
    _run_git(source_repo_path, "checkout", "-b", "main")
    (source_repo_path / "src").mkdir()
    (source_repo_path / "src" / "main.py").write_text("generated = True\n", encoding="utf-8")
    revision_id = _commit_all(source_repo_path, "add generated line", "2026-01-10T00:00:00+0000")
    _run_git(source_repo_path, "rm", "-q", "src/main.py")
    _commit_all(source_repo_path, "delete after measurement window", "2026-02-01T00:00:00+0000")
    _clone_bare(source_repo_path, bare_repo_path)
    remote_url = bare_repo_path.as_uri()
    _write_v2603_record(gen_code_desc_dir / f"{revision_id}.json", remote_url, revision_id)

    completed = _run_root_cli(
        [
            "--repoUrl",
            remote_url,
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
    assert {
        "repoUrl": aggregate["REPOSITORY"]["repoURL"],
        "totalCodeLines": aggregate["SUMMARY"]["totalCodeLines"],
        "weighted": aggregate["AGGREGATE"]["metrics"]["weighted"]["value"],
    } == {"repoUrl": remote_url, "totalCodeLines": 1, "weighted": 1.0}


# [@TC-UAT-004]
# @[Name]: verifyAlgAShallowWorkflow_withShallowClone_expectPartialBlameWarning
# @[Steps]: SETUP shallow clone and genCodeDesc -> BEHAVIOR run AlgA with repoPath -> VERIFY warning diagnostics -> CLEANUP tmp_path
def test_alg_a_shallow_git_workflow_reports_partial_blame_warning(tmp_path):
    source_repo_path = tmp_path / "source-repo"
    bare_repo_path = tmp_path / "origin.git"
    shallow_repo_path = tmp_path / "shallow-repo"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    source_repo_path.mkdir()
    gen_code_desc_dir.mkdir()
    _run_git(source_repo_path, "init", "-q")
    _run_git(source_repo_path, "checkout", "-b", "main")
    (source_repo_path / "src").mkdir()
    (source_repo_path / "src" / "main.py").write_text("generated = True\n", encoding="utf-8")
    revision_id = _commit_all(source_repo_path, "add generated line", "2026-01-10T00:00:00+0000")
    (source_repo_path / "src" / "helper.py").write_text("helper = True\n", encoding="utf-8")
    _commit_all(source_repo_path, "add helper line", "2026-01-20T00:00:00+0000")
    _clone_bare(source_repo_path, bare_repo_path)
    remote_url = bare_repo_path.as_uri()
    _clone_shallow(remote_url, "main", shallow_repo_path)
    _write_v2603_record(gen_code_desc_dir / f"{revision_id}.json", str(shallow_repo_path), revision_id)

    completed = _run_root_cli(
        [
            "--repoUrl",
            str(shallow_repo_path),
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
            "--repoPath",
            str(shallow_repo_path),
            "--outputDir",
            str(output_dir),
        ]
    )

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert "shallow Git history" in completed.stderr
    assert any("shallow Git history" in warning for warning in aggregate["AGGREGATE"]["diagnostics"]["warnings"])


# [@TC-UAT-005]
# @[Name]: verifyAlgASvnWorkflow_withPostWindowDelete_expectEndTimePatchWindow
# @[Steps]: SETUP SVN revisions around window -> BEHAVIOR run documented CLI -> VERIFY metrics and audit patch -> CLEANUP tmp_path
def test_alg_a_svn_workflow_uses_end_time_snapshot_and_patch_window(tmp_path):
    repository_path = tmp_path / "svn-repo"
    working_copy_path = tmp_path / "svn-wc"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()

    subprocess.run(["svnadmin", "create", str(repository_path)], check=True, text=True, capture_output=True)
    _run_svn(tmp_path, "checkout", f"file://{repository_path}", str(working_copy_path))

    (working_copy_path / "src").mkdir()
    (working_copy_path / "src" / "pre.py").write_text("before_window = True\n", encoding="utf-8")
    _run_svn(working_copy_path, "add", "src")
    _commit_svn(working_copy_path, "add pre-window file")

    (working_copy_path / "src" / "window.py").write_text("generated = True\n", encoding="utf-8")
    _run_svn(working_copy_path, "add", "src/window.py")
    window_revision_id = _commit_svn(working_copy_path, "add in-window generated file")
    window_revision_timestamp = _svn_revision_timestamp(working_copy_path, window_revision_id)

    _run_svn(working_copy_path, "delete", "src/window.py")
    (working_copy_path / "src" / "post.py").write_text("after_window = True\n", encoding="utf-8")
    _run_svn(working_copy_path, "add", "src/post.py")
    _commit_svn(working_copy_path, "delete window file and add post-window file")

    _write_v2603_record(
        gen_code_desc_dir / f"r{window_revision_id}.json",
        str(working_copy_path),
        window_revision_id,
        vcs_type="svn",
        repo_branch="trunk",
        file_name="src/window.py",
        revision_timestamp=window_revision_timestamp,
    )

    completed = _run_root_cli(
        [
            "--repoUrl",
            str(working_copy_path),
            "--repoBranch",
            "trunk",
            "--startTime",
            window_revision_timestamp,
            "--endTime",
            window_revision_timestamp,
            "--genCodeDescDir",
            str(gen_code_desc_dir),
            "--algorithm",
            "A",
            "--scope",
            "A",
            "--repoPath",
            str(working_copy_path),
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
        "patchContainsWindowFile": "src/window.py" in patch_text,
        "patchContainsPreFile": "src/pre.py" in patch_text,
        "patchContainsPostFile": "src/post.py" in patch_text,
    } == {
        "totalCodeLines": 1,
        "weighted": 1.0,
        "patchContainsWindowFile": True,
        "patchContainsPreFile": False,
        "patchContainsPostFile": False,
    }


# [@TC-UAT-006]
# @[Name]: verifyAlgARemoteWorkflow_whenCloneFails_expectGuidanceAndNoPartialOutput
# @[Steps]: SETUP missing Git remote and matching genCodeDesc -> BEHAVIOR run documented remote CLI -> VERIFY failure guidance and no outputs -> CLEANUP tmp_path
def test_alg_a_remote_clone_failure_reports_guidance_and_writes_no_output(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    missing_remote_url = (tmp_path / "missing-origin.git").as_uri()
    gen_code_desc_dir.mkdir()
    _write_v2603_record(gen_code_desc_dir / "missing-remote.json", missing_remote_url, "a" * 40)

    completed = _run_root_cli(
        [
            "--repoUrl",
            missing_remote_url,
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

    assert completed.returncode == 1
    assert "Algorithm A VCS access failed" in completed.stderr
    assert "retry" in completed.stderr
    assert "Algorithm C" in completed.stderr
    _assert_no_partial_outputs(output_dir)