import json
import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _run_git(repo_path, *args, env=None):
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _commit_all(repo_path, message, timestamp):
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": timestamp,
        "GIT_COMMITTER_DATE": timestamp,
    }
    _run_git(repo_path, "add", ".")
    _run_git(
        repo_path,
        "-c",
        "user.name=SysTesting",
        "-c",
        "user.email=sys@example.test",
        "commit",
        "-m",
        message,
        env=env,
    )
    return _run_git(repo_path, "rev-parse", "HEAD")


def _v2604_record(
    repo_url="https://example.test/repo",
    repo_branch="main",
    revision_id="rev1",
    revision_timestamp="2026-01-10T00:00:00Z",
    gen_ratio=100,
    parent_revision_ids=None,
):
    repository = {
        "vcsType": "git",
        "repoURL": repo_url,
        "repoBranch": repo_branch,
        "revisionId": revision_id,
        "revisionTimestamp": revision_timestamp,
    }
    if parent_revision_ids is not None:
        repository["parentRevisionIds"] = parent_revision_ids

    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 1,
            "fullGeneratedCodeLines": 1 if gen_ratio == 100 else 0,
            "partialGeneratedCodeLines": 1 if 0 < gen_ratio < 100 else 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/auth.py",
                "codeLines": [
                    {
                        "changeType": "add",
                        "lineLocation": 1,
                        "genRatio": gen_ratio,
                        "genMethod": "codeCompletion" if gen_ratio == 100 else "vibeCoding",
                        "blame": {
                            "revisionId": revision_id,
                            "originalFilePath": "src/auth.py",
                            "originalLine": 1,
                            "timestamp": revision_timestamp,
                        },
                    }
                ],
            }
        ],
        "REPOSITORY": repository,
    }


def _v2603_record(revision_id="c1", revision_timestamp="2026-01-10T00:00:00Z", repo_url="https://example.test/repo"):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "SysTestingFixture",
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
            "revisionTimestamp": revision_timestamp,
        },
    }


def _write_patch(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_add_file_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/main.py b/src/main.py",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            "+++ b/src/main.py",
            "@@ -0,0 +1,1 @@",
            "+known = True",
        ],
    )


def _write_missing_record_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/main.py b/src/main.py",
            "index 1111111..2222222 100644",
            "--- a/src/main.py",
            "+++ b/src/main.py",
            "@@ -1,1 +1,2 @@",
            " known = True",
            "+missing_record_line = True",
        ],
    )


def _run_algorithm_c(gen_code_desc_dir, output_dir, repo_url="https://example.test/repo", repo_branch="main", extra_args=None):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    args = [
        sys.executable,
        str(REPO_ROOT / "aggregateGenCodeDesc.py"),
        "--repoUrl",
        repo_url,
        "--repoBranch",
        repo_branch,
        "--startTime",
        "2026-01-01T00:00:00Z",
        "--endTime",
        "2026-01-31T00:00:00Z",
        "--genCodeDescDir",
        str(gen_code_desc_dir),
        "--algorithm",
        "C",
        "--scope",
        "A",
        "--outputDir",
        str(output_dir),
    ]
    if extra_args is not None:
        args.extend(extra_args)

    return subprocess.run(
        args,
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir, extra_args=None):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    args = [
        sys.executable,
        str(REPO_ROOT / "aggregateGenCodeDesc.py"),
        "--repoUrl",
        "https://example.test/repo",
        "--repoBranch",
        "main",
        "--startTime",
        "2026-01-01T00:00:00Z",
        "--endTime",
        "2026-01-31T00:00:00Z",
        "--genCodeDescDir",
        str(gen_code_desc_dir),
        "--algorithm",
        "B",
        "--scope",
        "A",
        "--commitPatchDir",
        str(commit_patch_dir),
        "--outputDir",
        str(output_dir),
    ]
    if extra_args is not None:
        args.extend(extra_args)

    return subprocess.run(
        args,
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _run_algorithm_a(gen_code_desc_dir, repo_path, end_rev, output_dir):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "aggregateGenCodeDesc.py"),
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
            "--repoPath",
            str(repo_path),
            "--outputDir",
            str(output_dir),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _run_root_cli(args, output_dir):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "aggregateGenCodeDesc.py"), *args, "--outputDir", str(output_dir)],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _assert_no_partial_outputs(output_dir):
    assert not (output_dir / "aggregatedGenCodeDescV26.03.json").exists()
    assert not (output_dir / "commitStart2EndTime.patch").exists()


# US-006 / AC-006-1 / missing per-revision genCodeDesc for Algorithm B / TC-SYS-027
def test_aggregate_gen_code_desc_py_algorithm_b_replays_missing_gen_code_desc_patch_as_manual(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _v2603_record())
    _write_add_file_patch(commit_patch_dir / "c1.patch")
    _write_missing_record_patch(commit_patch_dir / "c5.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "aggregatedGenCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5
    assert aggregate["AGGREGATE"]["diagnostics"]["missingRevisions"] == ["c5"]


# US-006 / AC-006-1 / missing genCodeDesc abort policy / TC-SYS-043
def test_aggregate_gen_code_desc_py_algorithm_b_aborts_missing_gen_code_desc_when_policy_requires(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _v2603_record())
    _write_add_file_patch(commit_patch_dir / "c1.patch")
    _write_missing_record_patch(commit_patch_dir / "c5.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir, extra_args=["--onMissing", "abort"])

    assert completed.returncode == 2
    assert "missing genCodeDesc records for patch revisions: c5" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-1 / missing per-revision genCodeDesc for Algorithm A / TC-SYS-037
def test_aggregate_gen_code_desc_py_algorithm_a_marks_missing_live_blame_revision_as_manual(tmp_path):
    repo_path = tmp_path / "repo"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    repo_path.mkdir()
    gen_code_desc_dir.mkdir()
    _run_git(repo_path, "init")
    _run_git(repo_path, "checkout", "-b", "main")
    source_dir = repo_path / "src"
    source_dir.mkdir()
    (source_dir / "main.py").write_text("known = True\n", encoding="utf-8")
    known_revision = _commit_all(repo_path, "known record", "2026-01-10T00:00:00+0000")
    (source_dir / "main.py").write_text("known = True\nmissing_record_line = True\n", encoding="utf-8")
    missing_revision = _commit_all(repo_path, "missing record", "2026-01-12T00:00:00+0000")
    _write_record(
        gen_code_desc_dir / "known.json",
        _v2603_record(revision_id=known_revision, repo_url=str(repo_path)),
    )

    completed = _run_algorithm_a(gen_code_desc_dir, repo_path, missing_revision, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "aggregatedGenCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5
    assert aggregate["AGGREGATE"]["diagnostics"]["missingRevisions"] == [missing_revision]
    assert aggregate["DETAIL"] == [
        {"fileName": "src/main.py", "codeLines": [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}]}
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "# algorithm: A" in patch_text
    assert "diff --git" in patch_text


# US-006 / AC-006-1 / missing genCodeDesc input / TC-SYS-013
def test_aggregate_gen_code_desc_py_rejects_empty_gen_code_desc_dir(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "no genCodeDesc JSON files found" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-2 / mismatched repoURL / TC-SYS-014
def test_aggregate_gen_code_desc_py_rejects_mismatched_repo_url(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2604_record(repo_url="https://example.test/other-repo"),
    )

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "REPOSITORY.repoURL does not match requested repoUrl" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-2 / mismatched repoBranch / TC-SYS-015
def test_aggregate_gen_code_desc_py_rejects_mismatched_repo_branch(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2604_record(repo_branch="feature"),
    )

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "REPOSITORY.repoBranch does not match requested repoBranch" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-3 / duplicate revisionId / TC-SYS-016
def test_aggregate_gen_code_desc_py_rejects_duplicate_revision_ids(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "first.json", _v2604_record(revision_id="abc123", gen_ratio=100))
    _write_record(gen_code_desc_dir / "second.json", _v2604_record(revision_id="abc123", gen_ratio=40))

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "duplicate revisionId: abc123" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-3 / duplicate revisionId last-wins policy / TC-SYS-044
def test_aggregate_gen_code_desc_py_accepts_duplicate_revision_ids_with_last_wins_warning(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "first.json", _v2604_record(revision_id="abc123", gen_ratio=100))
    _write_record(gen_code_desc_dir / "second.json", _v2604_record(revision_id="abc123", gen_ratio=40))

    completed = _run_algorithm_c(
        gen_code_desc_dir,
        output_dir,
        extra_args=["--onDuplicate", "last-wins", "--logLevel", "Warning"],
    )

    assert completed.returncode == 0, completed.stderr
    assert "duplicate revisionId abc123 accepted by last-wins policy" in completed.stderr
    aggregate = json.loads((output_dir / "aggregatedGenCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.4


# US-006 / AC-006-5 / invalid genRatio / TC-SYS-017
def test_aggregate_gen_code_desc_py_rejects_gen_ratio_outside_valid_range(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record(gen_ratio=150))

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "genRatio must be 0-100" in completed.stderr
    assert "src/auth.py" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / corrupted JSON validation breadth / TC-SYS-028
def test_aggregate_gen_code_desc_py_rejects_corrupted_json_with_file_context(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    (gen_code_desc_dir / "broken.json").write_text('{"protocolVersion": "26.04", bad}', encoding="utf-8")

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "invalid JSON" in completed.stderr
    assert "broken.json" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / schema required-field validation / TC-SYS-038
def test_aggregate_gen_code_desc_py_rejects_missing_required_summary_with_no_partial_output(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    record = _v2604_record()
    record.pop("SUMMARY")
    _write_record(gen_code_desc_dir / "rev1.json", record)

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "SUMMARY is required" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / schema type validation / TC-SYS-039
def test_aggregate_gen_code_desc_py_rejects_invalid_summary_count_type_with_no_partial_output(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    record = _v2604_record()
    record["SUMMARY"]["totalCodeLines"] = "one"
    _write_record(gen_code_desc_dir / "rev1.json", record)

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "SUMMARY.totalCodeLines must be an integer" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-6 / optional UserGuide policy flags / TC-SYS-045
def test_aggregate_gen_code_desc_py_help_exposes_userguide_policy_flags():
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "aggregateGenCodeDesc.py"), "--help"],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    for flag_name in ["--blameWhitespace", "--renameDetection", "--onMissing", "--onDuplicate", "--onClockSkew"]:
        assert flag_name in completed.stdout


# US-006 / AC-006-1 / Algorithm C missing genCodeDesc chain break / TC-SYS-030
def test_aggregate_gen_code_desc_py_algorithm_c_rejects_missing_parent_chain_break(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2604_record(revision_id="child", revision_timestamp="2026-01-02T00:00:00Z", parent_revision_ids=["missing-parent"]),
    )

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 2
    assert "genCodeDesc chain break" in completed.stderr
    assert "child" in completed.stderr
    assert "missing-parent" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-6 / lower camel mandatory argument names / TC-SYS-029
def test_aggregate_gen_code_desc_py_requires_lower_camel_mandatory_argument_names(tmp_path):
    output_dir = tmp_path / "out"

    completed = _run_root_cli(
        [
            "--repoURL",
            "https://example.test/repo",
            "--repoBranch",
            "main",
            "--startTime",
            "2026-01-01T00:00:00Z",
            "--endTime",
            "2026-01-31T00:00:00Z",
            "--genCodeDescDir",
            str(tmp_path / "genCodeDesc"),
        ],
        output_dir,
    )

    assert completed.returncode == 2
    assert "--repoUrl" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-4, US-010 / AC-010-4, AC-010-6 / clock skew diagnostics / TC-SYS-018
def test_aggregate_gen_code_desc_py_logs_error_and_rejects_algorithm_c_clock_skew(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "parent.json", _v2604_record(revision_id="parent", revision_timestamp="2026-01-03T00:00:00Z"))
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2604_record(
            revision_id="child",
            revision_timestamp="2026-01-02T00:00:00Z",
            parent_revision_ids=["parent"],
        ),
    )

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "ERROR"])

    assert completed.returncode == 2
    assert re.search(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \[ERROR\] \[CLI\] aggregateGenCodeDesc: clock skew detected",
        completed.stderr,
    )
    assert "child" in completed.stderr
    assert "parent" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-006 / AC-006-4 / clock skew ignore policy / TC-SYS-046
def test_aggregate_gen_code_desc_py_warns_and_continues_when_clock_skew_policy_ignores(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "parent.json", _v2604_record(revision_id="parent", revision_timestamp="2026-01-03T00:00:00Z"))
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2604_record(
            revision_id="child",
            revision_timestamp="2026-01-02T00:00:00Z",
            parent_revision_ids=["parent"],
            gen_ratio=40,
        ),
    )

    completed = _run_algorithm_c(
        gen_code_desc_dir,
        output_dir,
        extra_args=["--onClockSkew", "ignore", "--logLevel", "Warning"],
    )

    assert completed.returncode == 0, completed.stderr
    assert "clock skew ignored by policy" in completed.stderr
    aggregate = json.loads((output_dir / "aggregatedGenCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["AGGREGATE"]["diagnostics"]["clockSkewDetected"] is True
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "# algorithm: C" in patch_text
    assert "+src/auth.py:1" in patch_text


# US-010 / AC-010-5 / log-level filtering / TC-SYS-019
def test_aggregate_gen_code_desc_py_log_level_error_suppresses_success_logs(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "ERROR"])

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert (output_dir / "aggregatedGenCodeDescV26.03.json").exists()
