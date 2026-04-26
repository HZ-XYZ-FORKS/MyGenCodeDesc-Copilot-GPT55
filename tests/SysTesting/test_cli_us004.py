import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_patch(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_add_file_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/auth.py b/src/auth.py",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            "+++ b/src/auth.py",
            "@@ -0,0 +1,2 @@",
            "+allowed = True",
            "+return value",
        ],
    )


def _write_human_edit_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/auth.py b/src/auth.py",
            "index 1111111..2222222 100644",
            "--- a/src/auth.py",
            "+++ b/src/auth.py",
            "@@ -1,2 +1,2 @@",
            "-allowed = True",
            "+allowed = False",
            " return value",
        ],
    )


def _write_ai_rewrite_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/auth.py b/src/auth.py",
            "index 2222222..3333333 100644",
            "--- a/src/auth.py",
            "+++ b/src/auth.py",
            "@@ -1,2 +1,2 @@",
            " allowed = False",
            "-return value",
            "+return normalize(value)",
        ],
    )


def _record(revision_id, revision_timestamp, code_lines):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": len(code_lines),
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [{"fileName": "src/auth.py", "codeLines": code_lines}],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _line(line_number, gen_ratio, gen_method="codeCompletion"):
    return {"lineLocation": line_number, "genRatio": gen_ratio, "genMethod": gen_method}


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


# US-004 / AC-004-1, AC-004-2, AC-004-3 / root CLI line ownership transfer / TC-SYS-025
def test_aggregate_gen_code_desc_py_algorithm_b_outputs_line_ownership_transfers_and_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", [_line(1, 100), _line(2, 0, "Manual")]))
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", [_line(1, 0, "Manual")]))
    _write_record(gen_code_desc_dir / "c3.json", _record("c3", "2026-01-12T00:00:00Z", [_line(2, 100)]))
    _write_add_file_patch(commit_patch_dir / "c1.patch")
    _write_human_edit_patch(commit_patch_dir / "c2.patch")
    _write_ai_rewrite_patch(commit_patch_dir / "c3.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == 1
    assert aggregate["SUMMARY"]["partialGeneratedCodeLines"] == 0
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.5
    assert aggregate["DETAIL"] == [
        {"fileName": "src/auth.py", "codeLines": [{"lineLocation": 2, "genRatio": 100, "genMethod": "codeCompletion"}]}
    ]
    assert "whitespace-only" in aggregate["AGGREGATE"]["diagnostics"]["lineOwnershipPolicy"]["whitespaceOnlyChanges"]
