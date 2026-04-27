import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _v2603_record():
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
                "fileName": "src/app.py",
                "codeLines": [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": "abcdef1234567890",
            "revisionTimestamp": "2026-01-10T00:00:00Z",
        },
    }


def _v2604_record(revision_id, revision_timestamp, entries, total_code_lines=None):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": len(entries) if total_code_lines is None else total_code_lines,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [{"fileName": "src/app.py", "codeLines": entries}],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _add_entry(revision_id, timestamp, line_number, gen_ratio, gen_method="codeCompletion"):
    return {
        "changeType": "add",
        "lineLocation": line_number,
        "genRatio": gen_ratio,
        "genMethod": gen_method,
        "blame": {
            "revisionId": revision_id,
            "originalFilePath": "src/app.py",
            "originalLine": line_number,
            "timestamp": timestamp,
        },
    }


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


# US-009 / AC-009-3 / root CLI AlgA VCS access failure / TC-SYS-035
def test_aggregate_gen_code_desc_py_algorithm_a_reports_vcs_access_failure_and_writes_no_output(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev.json", _v2603_record())

    completed = _run_root_cli(
        [
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
            "A",
            "--repoPath",
            str(tmp_path / "missing-repo"),
            "--endRev",
            "HEAD",
        ],
        output_dir,
    )

    assert completed.returncode == 2
    assert "Algorithm A VCS access failed for https://example.test/repo" in completed.stderr
    assert "retry" in completed.stderr
    assert "Algorithm C" in completed.stderr
    _assert_no_partial_outputs(output_dir)


# US-009 / AC-009-8, AC-009-9 / root CLI AlgC duplicate and mismatch diagnostics / TC-SYS-036
def test_aggregate_gen_code_desc_py_algorithm_c_reports_duplicate_add_and_summary_mismatch(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _v2604_record("c1", "2026-01-10T00:00:00Z", [_add_entry("c1", "2026-01-10T00:00:00Z", 42, 100)]))
    _write_record(
        gen_code_desc_dir / "c2.json",
        _v2604_record("c2", "2026-01-11T00:00:00Z", [_add_entry("c2", "2026-01-11T00:00:00Z", 42, 40, "vibeCoding")], total_code_lines=500),
    )

    completed = _run_root_cli(
        [
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
        ],
        output_dir,
    )

    assert completed.returncode == 0, completed.stderr
    assert "duplicate add entry" in completed.stderr
    assert "SUMMARY.totalCodeLines expected 500 entries, found 1" in completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 1
    assert aggregate["AGGREGATE"]["diagnostics"]["duplicateAddEntries"] == ["src/app.py:code:42 overwritten by revision c2"]
    assert aggregate["DETAIL"] == [
        {"fileName": "src/app.py", "codeLines": [{"lineLocation": 42, "genRatio": 40, "genMethod": "vibeCoding"}]}
    ]
