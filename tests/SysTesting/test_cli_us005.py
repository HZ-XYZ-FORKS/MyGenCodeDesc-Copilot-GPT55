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


def _write_add_file_patch(path, file_name):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            f"+++ b/{file_name}",
            "@@ -0,0 +1,1 @@",
            "+value = 1",
        ],
    )


def _write_empty_patch(path):
    path.write_text("", encoding="utf-8")


def _write_submodule_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/libs/crypto b/libs/crypto",
            "new file mode 160000",
            "index 0000000..abcdef1",
        ],
    )


def _record(revision_id, revision_timestamp, file_name, gen_ratio, parent_revision_ids=None):
    repository = {
        "vcsType": "git",
        "repoURL": "https://example.test/repo",
        "repoBranch": "main",
        "revisionId": revision_id,
        "revisionTimestamp": revision_timestamp,
    }
    if parent_revision_ids is not None:
        repository["parentRevisionIds"] = parent_revision_ids

    detail = [] if file_name is None else [{"fileName": file_name, "codeLines": [{"lineLocation": 1, "genRatio": gen_ratio, "genMethod": "codeCompletion"}]}]
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "SysTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 0 if file_name is None else 1,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": detail,
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


# US-005 / AC-005-2, AC-005-5 / root CLI branch/history policy / TC-SYS-026
def test_aggregate_gen_code_desc_py_algorithm_b_counts_merged_lines_once_and_reports_history_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    for revision_id, file_name, gen_ratio in [
        ("branch-a", "src/a.py", 100),
        ("branch-b", "src/b.py", 60),
    ]:
        _write_record(gen_code_desc_dir / f"{revision_id}.json", _record(revision_id, "2026-01-10T00:00:00Z", file_name, gen_ratio))
        _write_add_file_patch(commit_patch_dir / f"{revision_id}.patch", file_name)
    _write_record(
        gen_code_desc_dir / "merge.json",
        _record("merge", "2026-01-11T00:00:00Z", None, 0, parent_revision_ids=["branch-a", "branch-b"]),
    )
    _write_record(gen_code_desc_dir / "submodule.json", _record("submodule", "2026-01-12T00:00:00Z", None, 0))
    _write_empty_patch(commit_patch_dir / "merge.patch")
    _write_submodule_patch(commit_patch_dir / "submodule.patch")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.8
    assert aggregate["AGGREGATE"]["diagnostics"]["historyPolicy"]["multipleMerges"].startswith("Algorithm B")
    assert "independent aggregateGenCodeDesc run" in aggregate["AGGREGATE"]["diagnostics"]["historyPolicy"]["submodules"]
