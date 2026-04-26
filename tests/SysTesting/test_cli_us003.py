import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_add_file_patch(path, total_lines=1):
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


def _record(revision_id, revision_timestamp, gen_ratio, gen_method="codeCompletion", parent_revision_ids=None):
    repository = {
        "vcsType": "git",
        "repoURL": "https://example.test/repo",
        "repoBranch": "main",
        "revisionId": revision_id,
        "revisionTimestamp": revision_timestamp,
    }
    if parent_revision_ids is not None:
        repository["parentRevisionIds"] = parent_revision_ids

    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 1,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/auth.py",
                "codeLines": [{"lineLocation": 1, "genRatio": gen_ratio, "genMethod": gen_method}],
            }
        ],
        "REPOSITORY": repository,
    }


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


# US-003 / AC-003-5 / root CLI amend orphan handling / TC-SYS-023
def test_aggregate_gen_code_desc_py_algorithm_b_ignores_amended_revision_absent_from_patch_history(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "aaa.json", _record("aaa", "2026-01-10T00:00:00Z", 100))
    _write_record(gen_code_desc_dir / "bbb.json", _record("bbb", "2026-01-11T00:00:00Z", 40, "vibeCoding"))
    _write_add_file_patch(commit_patch_dir / "bbb.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.4
    assert aggregate["AGGREGATE"]["diagnostics"]["orphanedRevisions"] == ["aaa"]
    assert "aaa.patch" not in (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")


# US-003 / AC-003-6 / root CLI rebase orphan handling / TC-SYS-024
def test_aggregate_gen_code_desc_py_algorithm_b_uses_rebased_revision_ids_from_patch_history(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "old-c1.json", _record("old-c1", "2026-01-09T00:00:00Z", 100))
    _write_record(gen_code_desc_dir / "old-c2.json", _record("old-c2", "2026-01-09T00:00:00Z", 100))
    _write_record(gen_code_desc_dir / "new-c1.json", _record("new-c1", "2026-01-10T00:00:00Z", 70, "vibeCoding"))
    _write_record(
        gen_code_desc_dir / "new-c2.json",
        _record("new-c2", "2026-01-11T00:00:00Z", 100, parent_revision_ids=["new-c1"]),
    )
    _write_add_file_patch(commit_patch_dir / "new-c1.patch")
    _write_single_line_modify_patch(commit_patch_dir / "new-c2.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 1.0
    assert aggregate["AGGREGATE"]["diagnostics"]["orphanedRevisions"] == ["old-c1", "old-c2"]
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert patch_text.index("# --- commit new-c1 ---") < patch_text.index("# --- commit new-c2 ---")
