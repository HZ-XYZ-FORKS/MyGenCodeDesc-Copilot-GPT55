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


def _v2603_record(repo_url, revision_id, revision_timestamp=None):
    repository = {
        "vcsType": "git",
        "repoURL": repo_url,
        "repoBranch": "main",
        "revisionId": revision_id,
    }
    if revision_timestamp is not None:
        repository["revisionTimestamp"] = revision_timestamp

    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
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
                    {"lineRange": {"from": 1, "to": 5}, "genRatio": 100, "genMethod": "codeCompletion"},
                    {"lineRange": {"from": 6, "to": 8}, "genRatio": 80, "genMethod": "vibeCoding"},
                    {"lineLocation": 9, "genRatio": 30, "genMethod": "vibeCoding"},
                ],
            }
        ],
        "REPOSITORY": repository,
    }


def _write_add_only_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        "+++ b/src/auth.py",
        "@@ -0,0 +1,10 @@",
        *[f"+value_{line_number} = {line_number}" for line_number in range(1, 11)],
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
            "--endRev",
            revision_id,
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
