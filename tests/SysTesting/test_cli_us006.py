import json
import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


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


def _v2603_record(revision_id="c1", revision_timestamp="2026-01-10T00:00:00Z"):
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
            "repoURL": "https://example.test/repo",
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


def _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [
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
    assert not (output_dir / "genCodeDescV26.03.json").exists()
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
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5
    assert aggregate["AGGREGATE"]["diagnostics"]["missingRevisions"] == ["c5"]


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


# US-010 / AC-010-5 / log-level filtering / TC-SYS-019
def test_aggregate_gen_code_desc_py_log_level_error_suppresses_success_logs(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "ERROR"])

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert (output_dir / "genCodeDescV26.03.json").exists()
