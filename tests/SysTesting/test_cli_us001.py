import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _v2604_record():
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 10,
            "fullGeneratedCodeLines": 5,
            "partialGeneratedCodeLines": 4,
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
                        "lineRange": {"from": 1, "to": 5},
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": "abc123",
                            "originalFilePath": "src/auth.py",
                            "originalLine": 1,
                            "timestamp": "2026-01-10T00:00:00Z",
                        },
                    },
                    {
                        "changeType": "add",
                        "lineRange": {"from": 6, "to": 8},
                        "genRatio": 80,
                        "genMethod": "vibeCoding",
                        "blame": {
                            "revisionId": "abc123",
                            "originalFilePath": "src/auth.py",
                            "originalLine": 6,
                            "timestamp": "2026-01-10T00:00:00Z",
                        },
                    },
                    {
                        "changeType": "add",
                        "lineLocation": 9,
                        "genRatio": 30,
                        "genMethod": "vibeCoding",
                        "blame": {
                            "revisionId": "abc123",
                            "originalFilePath": "src/auth.py",
                            "originalLine": 9,
                            "timestamp": "2026-01-10T00:00:00Z",
                        },
                    },
                    {
                        "changeType": "add",
                        "lineLocation": 10,
                        "genRatio": 0,
                        "genMethod": "Manual",
                        "blame": {
                            "revisionId": "abc123",
                            "originalFilePath": "src/auth.py",
                            "originalLine": 10,
                            "timestamp": "2026-01-10T00:00:00Z",
                        },
                    },
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": "abc123",
            "revisionTimestamp": "2026-01-10T00:00:00Z",
        },
    }


def _v2604_outside_window_record():
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 1000,
            "fullGeneratedCodeLines": 1000,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/legacy.py",
                "codeLines": [
                    {
                        "changeType": "add",
                        "lineRange": {"from": 1, "to": 1000},
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": "old123",
                            "originalFilePath": "src/legacy.py",
                            "originalLine": 1,
                            "timestamp": "2025-12-01T00:00:00Z",
                        },
                    }
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": "old123",
            "revisionTimestamp": "2025-12-01T00:00:00Z",
        },
    }


def _v2603_record_with_detail(
    repo_url,
    revision_id,
    revision_timestamp,
    code_lines,
    total_code_lines,
    parent_revision_ids=None,
    vcs_type="git",
    repo_branch="main",
):
    repository = {
        "vcsType": vcs_type,
        "repoURL": repo_url,
        "repoBranch": repo_branch,
        "revisionId": revision_id,
    }
    if revision_timestamp is not None:
        repository["revisionTimestamp"] = revision_timestamp
    if parent_revision_ids is not None:
        repository["parentRevisionIds"] = parent_revision_ids

    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": total_code_lines,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/auth.py",
                "codeLines": code_lines,
            }
        ],
        "REPOSITORY": repository,
    }


def _v2603_record(repo_url, revision_id, revision_timestamp=None):
    return _v2603_record_with_detail(
        repo_url,
        revision_id,
        revision_timestamp,
        [
            {"lineRange": {"from": 1, "to": 5}, "genRatio": 100, "genMethod": "codeCompletion"},
            {"lineRange": {"from": 6, "to": 8}, "genRatio": 80, "genMethod": "vibeCoding"},
            {"lineLocation": 9, "genRatio": 30, "genMethod": "vibeCoding"},
        ],
        10,
    )


def _write_add_only_patch(path, total_lines=10):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        "+++ b/src/auth.py",
        f"@@ -0,0 +1,{total_lines} @@",
        *[f"+value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_add_only_patch_for_file(path, file_name, total_lines=3):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        f"+++ b/{file_name}",
        f"@@ -0,0 +1,{total_lines} @@",
        *[f"+value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_modify_delete_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "index 1111111..2222222 100644",
        "--- a/src/auth.py",
        "+++ b/src/auth.py",
        "@@ -1,5 +1,5 @@",
        " value_1 = 1",
        "-value_2 = 2",
        "+value_2 = 20",
        " value_3 = 3",
        "-value_4 = 4",
        " value_5 = 5",
        "+value_6 = 6",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_single_line_modify_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "index 1111111..2222222 100644",
        "--- a/src/auth.py",
        "+++ b/src/auth.py",
        "@@ -1,1 +1,1 @@",
        "-value_1 = 1",
        "+value_1 = 20",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_pure_rename_patch(path):
    _write_pure_rename_patch_for_paths(path, "src/auth.py", "src/account.py")


def _write_pure_rename_patch_for_paths(path, old_file_name, new_file_name):
    patch_lines = [
        f"diff --git a/{old_file_name} b/{new_file_name}",
        "similarity index 100%",
        f"rename from {old_file_name}",
        f"rename to {new_file_name}",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_delete_file_patch(path, file_name="src/auth.py", total_lines=3):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "deleted file mode 100644",
        "index 1111111..0000000",
        f"--- a/{file_name}",
        "+++ /dev/null",
        f"@@ -1,{total_lines} +0,0 @@",
        *[f"-value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_window_diff_add_patch(path):
    patch_lines = [
        "diff --git a/src/window.py b/src/window.py",
        "index 1111111..2222222 100644",
        "--- a/src/window.py",
        "+++ b/src/window.py",
        "@@ -1,1 +1,3 @@",
        " legacy = True",
        "+window_alive = True",
        "+deleted_later = True",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_window_diff_delete_patch(path):
    patch_lines = [
        "diff --git a/src/window.py b/src/window.py",
        "index 2222222..3333333 100644",
        "--- a/src/window.py",
        "+++ b/src/window.py",
        "@@ -1,3 +1,2 @@",
        " legacy = True",
        " window_alive = True",
        "-deleted_later = True",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_pure_copy_patch(path, old_file_name="src/auth.py", new_file_name="src/auth_copy.py"):
    patch_lines = [
        f"diff --git a/{old_file_name} b/{new_file_name}",
        "similarity index 100%",
        f"copy from {old_file_name}",
        f"copy to {new_file_name}",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_rename_modify_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/account.py",
        "similarity index 66%",
        "rename from src/auth.py",
        "rename to src/account.py",
        "index 1111111..2222222 100644",
        "--- a/src/auth.py",
        "+++ b/src/account.py",
        "@@ -1,3 +1,3 @@",
        " value_1 = 1",
        "-value_2 = 2",
        "+value_2 = 20",
        " value_3 = 3",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_initial_multifile_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        "+++ b/src/auth.py",
        "@@ -0,0 +1,4 @@",
        "+auth_1 = 1",
        "+auth_2 = 2",
        "+auth_3 = 3",
        "+auth_4 = 4",
        "diff --git a/src/helper.py b/src/helper.py",
        "new file mode 100644",
        "index 0000000..2222222",
        "--- /dev/null",
        "+++ b/src/helper.py",
        "@@ -0,0 +1,3 @@",
        "+helper_1 = 1",
        "+helper_2 = 2",
        "+helper_3 = 3",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_multifile_multihunk_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "index 1111111..3333333 100644",
        "--- a/src/auth.py",
        "+++ b/src/auth.py",
        "@@ -1,1 +1,1 @@",
        "-auth_1 = 1",
        "+auth_1 = 10",
        "@@ -4,1 +4,2 @@",
        "-auth_4 = 4",
        "+auth_4 = 40",
        "+auth_5 = 5",
        "diff --git a/src/helper.py b/src/helper.py",
        "index 2222222..4444444 100644",
        "--- a/src/helper.py",
        "+++ b/src/helper.py",
        "@@ -2,2 +2,2 @@",
        "-helper_2 = 2",
        "+helper_2 = 20",
        " helper_3 = 3",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


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


def _v2603_multifile_record(repo_url, revision_id, revision_timestamp, file_details, total_code_lines):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": total_code_lines,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": file_details,
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": repo_url,
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _make_git_repo_with_auth_file(repo_path):
    repo_path.mkdir()
    _run_git(repo_path, "init")
    _run_git(repo_path, "checkout", "-b", "main")
    source_dir = repo_path / "src"
    source_dir.mkdir()
    (source_dir / "auth.py").write_text(
        "\n".join(f"value_{line_number} = {line_number}" for line_number in range(1, 11)) + "\n",
        encoding="utf-8",
    )
    _run_git(repo_path, "add", "src/auth.py")
    commit_env = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-01-10T00:00:00+0000",
        "GIT_COMMITTER_DATE": "2026-01-10T00:00:00+0000",
    }
    _run_git(
        repo_path,
        "-c",
        "user.name=SysTesting",
        "-c",
        "user.email=systesting@example.test",
        "commit",
        "-m",
        "add auth fixture",
        env=commit_env,
    )
    return _run_git(repo_path, "rev-parse", "HEAD")


# US-001 / AC-001-1, AC-001-2, AC-001-3 / TC-SYS-001
def test_aggregate_gen_code_desc_py_writes_us001_aggregate_json(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "abc123.json", _v2604_record())
    env = {**os.environ, "PYTHONPATH": os.path.abspath("src")}

    completed = subprocess.run(
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
            "C",
            "--scope",
            "A",
            "--threshold",
            "60",
            "--outputDir",
            str(output_dir),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    aggregate_path = output_dir / "genCodeDescV26.03.json"
    assert aggregate_path.exists()
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))

    assert aggregate["protocolVersion"] == "26.03"
    assert aggregate["SUMMARY"]["totalCodeLines"] == 10
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 5
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 4
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.77
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["numerator"] == 7.7
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.5
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["numerator"] == 5
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.8
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["numerator"] == 8


# US-001 / AC-001-6 / TC-SYS-002
def test_aggregate_gen_code_desc_py_outputs_zero_denominator_when_no_live_lines_are_in_window(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "old123.json", _v2604_outside_window_record())
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "C",
            "--scope",
            "A",
            "--threshold",
            "60",
            "--outputDir",
            str(output_dir),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 0
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.0
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.0
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.0


# US-001 / AC-001-7 / TC-SYS-003
def test_aggregate_gen_code_desc_py_supports_v2603_with_algorithm_a(tmp_path):
    repo_path = tmp_path / "repo"
    revision_id = _make_git_repo_with_auth_file(repo_path)
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / f"{revision_id}.json", _v2603_record(str(repo_path), revision_id))
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["AGGREGATE"]["parameters"]["algorithm"] == "A"
    assert aggregate["AGGREGATE"]["parameters"]["inputProtocolVersion"] == "26.03"
    assert aggregate["SUMMARY"]["totalCodeLines"] == 10
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 5
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 4
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.77
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.5
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.8


# US-001 / Algorithm B / TC-SYS-004
def test_aggregate_gen_code_desc_py_supports_v2603_with_algorithm_b_patch_replay(tmp_path):
    revision_id = "patch123"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / f"{revision_id}.json",
        _v2603_record("https://example.test/repo", revision_id, "2026-01-10T00:00:00Z"),
    )
    _write_add_only_patch(commit_patch_dir / f"{revision_id}.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["AGGREGATE"]["parameters"]["algorithm"] == "B"
    assert aggregate["AGGREGATE"]["parameters"]["inputProtocolVersion"] == "26.03"
    assert aggregate["SUMMARY"]["totalCodeLines"] == 10
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 5
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 4
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.77
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.5
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.8


# US-001, US-009 / Algorithm B / TC-SYS-005
def test_aggregate_gen_code_desc_py_algorithm_b_replays_multiple_patches_to_final_snapshot(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 80, "genMethod": "vibeCoding"},
                {"lineLocation": 4, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
            5,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                {"lineLocation": 5, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
            5,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=5)
    _write_modify_delete_patch(commit_patch_dir / "rev2.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 5
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 2
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.52
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.4
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.6
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/auth.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                {"lineLocation": 5, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
        }
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert patch_text.startswith(
        "# repoURL: https://example.test/repo\n"
        "# repoBranch: main\n"
        "# startTime: 2026-01-01T00:00:00Z\n"
        "# endTime: 2026-01-31T00:00:00Z\n"
        "# algorithm: B\n"
        "# scope: A\n"
    )
    assert patch_text.index("# --- commit rev1 ---") < patch_text.index("# --- commit rev2 ---")
    assert "-value_2 = 2" in patch_text
    assert "+value_2 = 20" in patch_text


# US-001 / AC-001-8 / Algorithm B alive subset of window diff / TC-SYS-046
def test_aggregate_gen_code_desc_py_algorithm_b_counts_only_alive_subset_of_window_diff(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {
                    "fileName": "src/window.py",
                    "codeLines": [
                        {"lineLocation": 2, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 3, "genRatio": 80, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [{"fileName": "src/window.py", "codeLines": []}],
            0,
        ),
    )
    _write_window_diff_add_patch(commit_patch_dir / "rev1.patch")
    _write_window_diff_delete_patch(commit_patch_dir / "rev2.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 1
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 0
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 1.0
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/window.py",
            "codeLines": [{"lineLocation": 2, "genRatio": 100, "genMethod": "codeCompletion"}],
        }
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "+window_alive = True" in patch_text
    assert "+deleted_later = True" in patch_text
    assert "-deleted_later = True" in patch_text


# US-001, US-009 / Algorithm B diagnostics / TC-SYS-006
def test_aggregate_gen_code_desc_py_algorithm_b_reports_missing_patch_dir(tmp_path):
    revision_id = "rev1"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / f"{revision_id}.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            revision_id,
            "2026-01-10T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
        ),
    )
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            str(tmp_path / "missing-patches"),
            "--outputDir",
            str(output_dir),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 2
    assert "commit patch dir not found" in completed.stderr


# US-001, US-009 / Algorithm B Git ordering / TC-SYS-007
def test_aggregate_gen_code_desc_py_algorithm_b_uses_parent_order_over_timestamp_order(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "child",
            "2026-01-10T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"}],
            1,
            parent_revision_ids=["parent"],
        ),
    )
    _write_record(
        gen_code_desc_dir / "parent.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "parent",
            "2026-01-11T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "parent.patch", total_lines=1)
    _write_single_line_modify_patch(commit_patch_dir / "child.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.4
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert patch_text.index("# --- commit parent ---") < patch_text.index("# --- commit child ---")


# US-001, US-007, US-009 / Algorithm B SVN ordering / TC-SYS-008
def test_aggregate_gen_code_desc_py_algorithm_b_uses_svn_revision_order_over_timestamp_order(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "10.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "10",
            "2026-01-10T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"}],
            1,
            vcs_type="svn",
            repo_branch="trunk",
        ),
    )
    _write_record(
        gen_code_desc_dir / "2.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "2",
            "2026-01-11T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
            vcs_type="svn",
            repo_branch="trunk",
        ),
    )
    _write_add_only_patch(commit_patch_dir / "2.patch", total_lines=1)
    _write_single_line_modify_patch(commit_patch_dir / "10.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "aggregateGenCodeDesc.py"),
            "--repoUrl",
            "https://example.test/repo",
            "--repoBranch",
            "trunk",
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["REPOSITORY"]["vcsType"] == "svn"
    assert aggregate["SUMMARY"]["totalCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.4
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert patch_text.index("# --- commit 2 ---") < patch_text.index("# --- commit 10 ---")


# US-009 / AC-009-4 / Algorithm B multi-file multi-hunk replay / TC-SYS-009
def test_aggregate_gen_code_desc_py_algorithm_b_replays_multifile_multihunk_patch(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {
                    "fileName": "src/auth.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 4, "genRatio": 70, "genMethod": "vibeCoding"},
                    ],
                },
                {
                    "fileName": "src/helper.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 80, "genMethod": "vibeCoding"},
                        {"lineLocation": 3, "genRatio": 100, "genMethod": "codeCompletion"},
                    ],
                },
            ],
            7,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {
                    "fileName": "src/auth.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"},
                        {"lineLocation": 4, "genRatio": 90, "genMethod": "vibeCoding"},
                        {"lineLocation": 5, "genRatio": 100, "genMethod": "codeCompletion"},
                    ],
                },
                {
                    "fileName": "src/helper.py",
                    "codeLines": [
                        {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                    ],
                },
            ],
            8,
        ),
    )
    _write_initial_multifile_patch(commit_patch_dir / "rev1.patch")
    _write_multifile_multihunk_patch(commit_patch_dir / "rev2.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 8
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 2
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 4
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5875
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.25
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.625
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/auth.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"},
                {"lineLocation": 4, "genRatio": 90, "genMethod": "vibeCoding"},
                {"lineLocation": 5, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
        },
        {
            "fileName": "src/helper.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 80, "genMethod": "vibeCoding"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                {"lineLocation": 3, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
        },
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "diff --git a/src/auth.py b/src/auth.py" in patch_text
    assert "diff --git a/src/helper.py b/src/helper.py" in patch_text
    assert "@@ -4,1 +4,2 @@" in patch_text


# US-002 / AC-002-1, US-009 / AC-009-5 / Algorithm B pure rename / TC-SYS-010
def test_aggregate_gen_code_desc_py_algorithm_b_replays_pure_rename(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [],
            3,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_pure_rename_patch(commit_patch_dir / "rev2.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 3
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5333333333
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.3333333333
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.6666666667
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/account.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
        }
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "rename from src/auth.py" in patch_text
    assert "rename to src/account.py" in patch_text


# US-002 / AC-002-2, US-009 / AC-009-5 / Algorithm B rename plus modify / TC-SYS-011
def test_aggregate_gen_code_desc_py_algorithm_b_replays_rename_plus_modify(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {
                    "fileName": "src/account.py",
                    "codeLines": [
                        {"lineLocation": 2, "genRatio": 40, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            3,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_rename_modify_patch(commit_patch_dir / "rev2.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 3
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.4666666667
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.3333333333
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.3333333333
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/account.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 40, "genMethod": "vibeCoding"},
            ],
        }
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "rename from src/auth.py" in patch_text
    assert "rename to src/account.py" in patch_text
    assert "+value_2 = 20" in patch_text


# US-009 / AC-009-5 / Algorithm B chained renames / TC-SYS-012
def test_aggregate_gen_code_desc_py_algorithm_b_replays_chained_renames(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {
                    "fileName": "src/v1.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            3,
        ),
    )
    for revision_id, revision_timestamp in [
        ("rev2", "2026-01-11T00:00:00Z"),
        ("rev3", "2026-01-12T00:00:00Z"),
    ]:
        _write_record(
            gen_code_desc_dir / f"{revision_id}.json",
            _v2603_multifile_record(
                "https://example.test/repo",
                revision_id,
                revision_timestamp,
                [],
                3,
            ),
        )
    _write_add_only_patch_for_file(commit_patch_dir / "rev1.patch", "src/v1.py", total_lines=3)
    _write_pure_rename_patch_for_paths(commit_patch_dir / "rev2.patch", "src/v1.py", "src/v2.py")
    _write_pure_rename_patch_for_paths(commit_patch_dir / "rev3.patch", "src/v2.py", "src/v3.py")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 3
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 1
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5333333333
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.3333333333
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.6666666667
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/v3.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
        }
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert patch_text.index("# --- commit rev2 ---") < patch_text.index("# --- commit rev3 ---")
    assert "rename from src/v1.py" in patch_text
    assert "rename to src/v3.py" in patch_text


# US-002 / AC-002-3 / Algorithm B deleted file / TC-SYS-013
def test_aggregate_gen_code_desc_py_algorithm_b_excludes_deleted_file(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [],
            0,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_delete_file_patch(commit_patch_dir / "rev2.patch", total_lines=3)
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 0
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 0
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 0
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.0
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.0
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.0
    assert aggregate["DETAIL"] == []
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "+++ /dev/null" in patch_text


# US-002 / AC-002-4 / Algorithm B copied file / TC-SYS-014
def test_aggregate_gen_code_desc_py_algorithm_b_attributes_copied_file_to_copy_commit(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_with_detail(
            "https://example.test/repo",
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multifile_record(
            "https://example.test/repo",
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {
                    "fileName": "src/auth_copy.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"},
                        {"lineLocation": 2, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 3, "genRatio": 70, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            6,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_pure_copy_patch(commit_patch_dir / "rev2.patch")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    completed = subprocess.run(
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
            "--threshold",
            "60",
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

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 6
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 2
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 3
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.6166666667
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.3333333333
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.6666666667
    assert aggregate["DETAIL"] == [
        {
            "fileName": "src/auth.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
        },
        {
            "fileName": "src/auth_copy.py",
            "codeLines": [
                {"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"},
                {"lineLocation": 2, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 3, "genRatio": 70, "genMethod": "vibeCoding"},
            ],
        },
    ]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert "copy from src/auth.py" in patch_text
    assert "copy to src/auth_copy.py" in patch_text
