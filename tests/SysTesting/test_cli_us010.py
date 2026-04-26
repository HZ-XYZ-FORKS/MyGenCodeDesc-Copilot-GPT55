import json
import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


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
    assert (output_dir / "genCodeDescV26.03.json").exists()


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
    _write_record(gen_code_desc_dir / "rev1.json", _v2604_record(summary_total_code_lines=2))

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir, extra_args=["--logLevel", "WARN"])

    assert completed.returncode == 0, completed.stderr
    _assert_structured_log(completed.stderr, "WARN", "LOAD", "revisionId=rev1 SUMMARY.totalCodeLines expected 2 entries, found 1")
    assert "[INFO]" not in completed.stderr
    assert (output_dir / "genCodeDescV26.03.json").exists()
