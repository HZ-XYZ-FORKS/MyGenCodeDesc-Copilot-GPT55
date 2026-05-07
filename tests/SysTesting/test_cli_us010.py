import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _read_aggregate(output_dir):
    return json.loads((output_dir / "aggregatedGenCodeDescV26.03.json").read_text(encoding="utf-8"))


def _assert_timing_summary(timing):
    duration_fields = [
        "totalSeconds",
        "cloneRepoSeconds",
        "checkoutSeconds",
        "loadGenCodeDescSeconds",
        "blameSeconds",
        "diffSeconds",
        "aggregateSeconds",
        "writeOutputSeconds",
    ]
    for field_name in duration_fields:
        assert isinstance(timing[field_name], (int, float))
        assert timing[field_name] >= 0
    for field_name in duration_fields[1:]:
        assert timing["totalSeconds"] >= timing[field_name]
    assert isinstance(timing["notRun"], list)


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


def _v2604_record(summary_total_code_lines=1):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": summary_total_code_lines,
            "fullGeneratedCodeLines": 1,
            "partialGeneratedCodeLines": 0,
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
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": "rev1",
                            "originalFilePath": "src/auth.py",
                            "originalLine": 1,
                            "timestamp": "2026-01-10T00:00:00Z",
                        },
                    }
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": "rev1",
            "revisionTimestamp": "2026-01-10T00:00:00Z",
        },
    }


def _v2603_record(repo_url, revision_id="c1", revision_timestamp="2026-01-10T00:00:00Z"):
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


def _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=None):
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


def _run_algorithm_a(gen_code_desc_dir, repo_path, end_rev, output_dir, extra_args=None):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    args = [
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


def _write_add_patch(path):
    path.write_text(
        "\n".join(
            [
                "diff --git a/src/main.py b/src/main.py",
                "new file mode 100644",
                "index 0000000..1111111",
                "--- /dev/null",
                "+++ b/src/main.py",
                "@@ -0,0 +1,1 @@",
                "+known = True",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _assert_structured_log(stderr, level, component, message_fragment):
    assert re.search(
        rf"\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}Z \[{level}\] \[{component}\] .*{re.escape(message_fragment)}",
        stderr,
    )


# US-010 / AC-010-1, AC-010-6 / default INFO phases / TC-SYS-020
def test_aggregate_gen_code_desc_py_default_info_logs_load_process_and_summary_phases(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    _assert_structured_log(completed.stderr, "INFO", "LOAD", "LOAD [1/1] revisionId=rev1 entries=1")
    _assert_structured_log(completed.stderr, "INFO", "PROCESS", "PROCESS algorithm=C records=1 lines=1")
    _assert_structured_log(completed.stderr, "INFO", "SUMMARY", "SUMMARY aggregate totalLines=1 weighted=100.0%")
    assert "[DEBUG]" not in completed.stderr
    assert (output_dir / "aggregatedGenCodeDescV26.03.json").exists()


# US-010 / AC-010-8 / default timing summary / TC-SYS-050
def test_aggregate_gen_code_desc_py_default_timing_summary_writes_timing_object_and_log(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = _read_aggregate(output_dir)
    _assert_timing_summary(aggregate["TIMING"])
    assert "cloneRepo" in aggregate["TIMING"]["notRun"]
    assert "blame" in aggregate["TIMING"]["notRun"]
    _assert_structured_log(completed.stderr, "INFO", "TIMING", "TIMING totalSeconds=")


# US-010 / AC-010-8 / timing off policy / TC-SYS-051
def test_aggregate_gen_code_desc_py_timing_off_omits_timing_object_and_logs(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--timing", "off"])

    assert completed.returncode == 0, completed.stderr
    aggregate = _read_aggregate(output_dir)
    assert "TIMING" not in aggregate
    assert "[TIMING]" not in completed.stderr


# US-010 / AC-010-8 / detailed timing logs / TC-SYS-052
def test_aggregate_gen_code_desc_py_detailed_timing_logs_stage_records(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--timing", "detailed"])

    assert completed.returncode == 0, completed.stderr
    aggregate = _read_aggregate(output_dir)
    _assert_timing_summary(aggregate["TIMING"])
    _assert_structured_log(completed.stderr, "INFO", "TIMING", "TIMING stage=loadGenCodeDescSeconds seconds=")
    _assert_structured_log(completed.stderr, "INFO", "TIMING", "TIMING stage=aggregateSeconds seconds=")


# US-010 / AC-010-2, AC-010-6 / DEBUG detail / TC-SYS-021
def test_aggregate_gen_code_desc_py_debug_logs_algorithm_file_and_line_detail(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "DEBUG"])

    assert completed.returncode == 0, completed.stderr
    _assert_structured_log(completed.stderr, "DEBUG", "CLI", "algorithm=C")
    _assert_structured_log(completed.stderr, "DEBUG", "PROCESS", "file=src/auth.py lines=1")
    _assert_structured_log(completed.stderr, "DEBUG", "PROCESS", "file=src/auth.py line=1 genRatio=100")


# US-010 / AC-010-3 / recoverable SUMMARY/DETAIL warning / TC-SYS-022
def test_aggregate_gen_code_desc_py_warns_and_continues_on_summary_detail_mismatch(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    record = _v2604_record()
    record["SUMMARY"]["fullGeneratedCodeLines"] = 0
    _write_record(gen_code_desc_dir / "rev1.json", record)

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "WARN"])

    assert completed.returncode == 0, completed.stderr
    _assert_structured_log(completed.stderr, "WARN", "LOAD", "revisionId=rev1 SUMMARY.fullGeneratedCodeLines expected 0 lines, found 1")
    assert "[INFO]" not in completed.stderr
    assert (output_dir / "aggregatedGenCodeDescV26.03.json").exists()


# US-010 / AC-010-5, AC-010-6 / stdout metric result contract / TC-SYS-040
def test_aggregate_gen_code_desc_py_writes_metric_result_to_stdout_without_mixing_logs(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record(summary_total_code_lines=2))

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "ERROR"])

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    metric_result = json.loads(completed.stdout)
    assert metric_result == {
        "totalLines": 1,
        "weighted": {"value": 1.0, "numerator": 1.0},
        "fullyAI": {"value": 1.0, "numerator": 1},
        "mostlyAI": {"value": 1.0, "numerator": 1, "threshold": 60},
    }


# US-010 / AC-010-2, AC-010-6 / Algorithm A blame DEBUG detail / TC-SYS-041
def test_aggregate_gen_code_desc_py_debug_logs_algorithm_a_blame_origin_detail(tmp_path):
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
    revision_id = _commit_all(repo_path, "known record", "2026-01-10T00:00:00+0000")
    _write_record(gen_code_desc_dir / "known.json", _v2603_record(str(repo_path), revision_id=revision_id))

    completed = _run_algorithm_a(gen_code_desc_dir, repo_path, revision_id, output_dir, extra_args=["--logLevel", "DEBUG"])

    assert completed.returncode == 0, completed.stderr
    _assert_structured_log(
        completed.stderr,
        "DEBUG",
        "PROCESS",
        f"algorithm=A file=src/main.py line=1 state=BLAME origin={revision_id} original=src/main.py:1 genRatio=100",
    )


# US-010 / AC-010-2, AC-010-6 / Algorithm B replay DEBUG detail / TC-SYS-042
def test_aggregate_gen_code_desc_py_debug_logs_algorithm_b_replay_origin_detail(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _v2603_record("https://example.test/repo", revision_id="c1"))
    _write_add_patch(commit_patch_dir / "c1.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir, extra_args=["--logLevel", "DEBUG"])

    assert completed.returncode == 0, completed.stderr
    _assert_structured_log(
        completed.stderr,
        "DEBUG",
        "PROCESS",
        "algorithm=B file=src/main.py line=1 state=REPLAYED origin=c1 original=src/main.py:1 genRatio=100",
    )
