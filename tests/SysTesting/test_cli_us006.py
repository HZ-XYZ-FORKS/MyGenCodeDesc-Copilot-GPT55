import json
import os
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
):
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
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": repo_url,
            "repoBranch": repo_branch,
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _run_algorithm_c(gen_code_desc_dir, output_dir, repo_url="https://example.test/repo", repo_branch="main"):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [
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
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _assert_no_partial_outputs(output_dir):
    assert not (output_dir / "genCodeDescV26.03.json").exists()
    assert not (output_dir / "commitStart2EndTime.patch").exists()


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