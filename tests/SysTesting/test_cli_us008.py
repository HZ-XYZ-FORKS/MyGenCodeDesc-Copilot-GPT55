import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _v2604_record(revision_id="legacy", revision_timestamp="2025-12-01T00:00:00Z"):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
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
                "fileName": "src/legacy.py",
                "codeLines": [
                    {
                        "changeType": "add",
                        "lineLocation": 1,
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": revision_id,
                            "originalFilePath": "src/legacy.py",
                            "originalLine": 1,
                            "timestamp": revision_timestamp,
                        },
                    }
                ],
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


def _run_algorithm_c(gen_code_desc_dir, output_dir):
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
            "C",
            "--scope",
            "A",
            "--outputDir",
            str(output_dir),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _assert_no_partial_outputs(output_dir):
    assert not (output_dir / "genCodeDescV26.03.json").exists()
    assert not (output_dir / "commitStart2EndTime.patch").exists()


# US-008 / AC-008-1, AC-008-2, AC-008-3 / root CLI empty window scale policy / TC-SYS-033
def test_aggregate_gen_code_desc_py_algorithm_c_empty_window_outputs_zero_metrics_and_scale_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "legacy.json", _v2604_record())

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 0
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.0
    assert aggregate["AGGREGATE"]["metrics"]["fullyAI"]["value"] == 0.0
    assert aggregate["AGGREGATE"]["metrics"]["mostlyAI"]["value"] == 0.0
    assert "correctness over speed" in aggregate["AGGREGATE"]["diagnostics"]["scalePolicy"]["algorithmAReferenceScale"]
    assert "200 GB" in aggregate["AGGREGATE"]["diagnostics"]["scalePolicy"]["algorithmCReferenceScale"]


# US-008 / AC-008-4, US-010 / AC-010-4 / root CLI I/O failure with no partial output / TC-SYS-034
def test_aggregate_gen_code_desc_py_rejects_mid_stream_io_failure_with_context_and_no_partial_output(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "001-good.json", _v2604_record(revision_id="good", revision_timestamp="2026-01-10T00:00:00Z"))
    (gen_code_desc_dir / "500-unreadable.json").mkdir()

    completed = _run_algorithm_c(gen_code_desc_dir, output_dir)

    assert completed.returncode == 1
    assert "unable to read genCodeDesc file" in completed.stderr
    assert "500-unreadable.json" in completed.stderr
    assert "revisionId=500-unreadable" in completed.stderr
    _assert_no_partial_outputs(output_dir)
