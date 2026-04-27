import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GIT_SHA1 = "a" * 40
GIT_SHA256 = "b" * 64


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_patch(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_add_file_patch(path, file_name, value_name):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            f"+++ b/{file_name}",
            "@@ -0,0 +1,1 @@",
            f"+{value_name} = True",
        ],
    )


def _record(revision_id, revision_timestamp, file_name, gen_ratio, vcs_type="git", repo_branch="main"):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
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
                "fileName": file_name,
                "codeLines": [{"lineLocation": 1, "genRatio": gen_ratio, "genMethod": "codeCompletion"}],
            }
        ],
        "REPOSITORY": {
            "vcsType": vcs_type,
            "repoURL": "https://example.test/repo",
            "repoBranch": repo_branch,
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir, repo_branch="main", extra_args=None):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    args = [
        sys.executable,
        str(REPO_ROOT / "aggregateGenCodeDesc.py"),
        "--repoUrl",
        "https://example.test/repo",
        "--repoBranch",
        repo_branch,
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
    return subprocess.run(args, check=False, env=env, text=True, capture_output=True)


# US-007 / AC-007-1 / root CLI accepts Git SHA-1 and SHA-256 / TC-SYS-031
def test_aggregate_gen_code_desc_py_algorithm_b_accepts_git_sha1_and_sha256_revision_ids(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "sha1.json", _record(GIT_SHA1, "2026-01-10T00:00:00Z", "src/sha1.py", 100))
    _write_record(gen_code_desc_dir / "sha256.json", _record(GIT_SHA256, "2026-01-11T00:00:00Z", "src/sha256.py", 40))
    _write_add_file_patch(commit_patch_dir / f"{GIT_SHA1}.patch", "src/sha1.py", "sha1_line")
    _write_add_file_patch(commit_patch_dir / f"{GIT_SHA256}.patch", "src/sha256.py", "sha256_line")

    completed = _run_algorithm_b(gen_code_desc_dir, commit_patch_dir, output_dir)

    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 0.7
    assert "40-character" in aggregate["AGGREGATE"]["diagnostics"]["vcsPolicy"]["gitRevisionIdFormat"]
    assert "64-character" in aggregate["AGGREGATE"]["diagnostics"]["vcsPolicy"]["gitRevisionIdFormat"]


# US-007 / AC-007-2 through AC-007-5 / root CLI SVN policy / TC-SYS-032
def test_aggregate_gen_code_desc_py_algorithm_b_normalizes_svn_branch_and_logs_svn_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    output_dir = tmp_path / "out"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "r4217.json",
        _record("4217", "2026-01-11T00:00:00Z", "src/feature.py", 100, vcs_type="svn", repo_branch="/branches/feature-x"),
    )
    _write_record(
        gen_code_desc_dir / "r4218.json",
        _record("4218", "2026-01-10T00:00:00Z", "src/merge.py", 60, vcs_type="svn", repo_branch="/branches/feature-x"),
    )
    _write_add_file_patch(commit_patch_dir / "4217.patch", "src/feature.py", "feature_line")
    _write_add_file_patch(commit_patch_dir / "4218.patch", "src/merge.py", "merge_line")

    completed = _run_algorithm_b(
        gen_code_desc_dir,
        commit_patch_dir,
        output_dir,
        repo_branch="branches/feature-x",
        extra_args=["--logLevel", "WARN"],
    )

    assert completed.returncode == 0, completed.stderr
    assert "SVN blame may attribute" in completed.stderr
    aggregate = json.loads((output_dir / "genCodeDescV26.03.json").read_text(encoding="utf-8"))
    assert aggregate["REPOSITORY"]["vcsType"] == "svn"
    assert aggregate["SUMMARY"]["totalCodeLines"] == 2
    assert "skipped for SVN" in aggregate["AGGREGATE"]["diagnostics"]["vcsPolicy"]["gitOnlyHistoryRewrites"]
    assert "normalized" in aggregate["AGGREGATE"]["diagnostics"]["vcsPolicy"]["svnBranchPath"]
