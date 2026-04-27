import json

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines


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
        "codeAgent": "UnitTestingFixture",
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


def _collect(gen_code_desc_dir, commit_patch_dir, repo_branch="main"):
    return collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch=repo_branch,
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )


def _line_summary(result):
    return [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines]


# US-007 / AC-007-1 / Git SHA-1 and SHA-256 revisionIds / TC-UNIT-039
def test_algorithm_b_accepts_git_sha1_and_sha256_revision_ids_and_reports_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "sha1.json", _record(GIT_SHA1, "2026-01-10T00:00:00Z", "src/sha1.py", 100))
    _write_record(gen_code_desc_dir / "sha256.json", _record(GIT_SHA256, "2026-01-11T00:00:00Z", "src/sha256.py", 40))
    _write_add_file_patch(commit_patch_dir / f"{GIT_SHA1}.patch", "src/sha1.py", "sha1_line")
    _write_add_file_patch(commit_patch_dir / f"{GIT_SHA256}.patch", "src/sha256.py", "sha256_line")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [
        ("src/sha1.py", 1, 100, "codeCompletion"),
        ("src/sha256.py", 1, 40, "codeCompletion"),
    ]
    assert "40-character" in result.diagnostics["vcsPolicy"]["gitRevisionIdFormat"]
    assert "64-character" in result.diagnostics["vcsPolicy"]["gitRevisionIdFormat"]


# US-007 / AC-007-2 through AC-007-5 / SVN path and limitation policy / TC-UNIT-040
def test_algorithm_b_normalizes_svn_branch_path_and_reports_svn_policies(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
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

    result = _collect(gen_code_desc_dir, commit_patch_dir, repo_branch="branches/feature-x")

    assert result.vcs_type == "svn"
    assert _line_summary(result) == [
        ("src/feature.py", 1, 100, "codeCompletion"),
        ("src/merge.py", 1, 60, "codeCompletion"),
    ]
    assert "positive integer" in result.diagnostics["vcsPolicy"]["svnRevisionIdFormat"]
    assert "SVN blame may attribute" in result.diagnostics["vcsPolicy"]["svnMergeBlame"]
    assert "skipped for SVN" in result.diagnostics["vcsPolicy"]["gitOnlyHistoryRewrites"]
    assert "normalized" in result.diagnostics["vcsPolicy"]["svnBranchPath"]
