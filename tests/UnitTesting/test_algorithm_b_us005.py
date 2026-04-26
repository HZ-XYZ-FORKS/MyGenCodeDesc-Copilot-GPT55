import json

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_patch(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_add_file_patch(path, file_name, total_lines=1):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            f"+++ b/{file_name}",
            f"@@ -0,0 +1,{total_lines} @@",
            *[f"+value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
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


def _record(revision_id, revision_timestamp, file_details, total_code_lines, parent_revision_ids=None):
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
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": total_code_lines,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": file_details,
        "REPOSITORY": repository,
    }


def _file_detail(file_name, code_lines):
    return {"fileName": file_name, "codeLines": code_lines}


def _line(line_number, gen_ratio, gen_method="codeCompletion"):
    return {"lineLocation": line_number, "genRatio": gen_ratio, "genMethod": gen_method}


def _collect(gen_code_desc_dir, commit_patch_dir):
    return collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )


def _line_summary(result):
    return [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines]


# US-005 / AC-005-1 / outside-window origin excluded / TC-UNIT-032
def test_algorithm_b_excludes_surviving_line_with_origin_before_start_time(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "old.json", _record("old", "2025-12-01T00:00:00Z", [_file_detail("src/main.py", [_line(1, 100)])], 1))
    _write_add_file_patch(commit_patch_dir / "old.patch", "src/main.py")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert result.lines == []


# US-005 / AC-005-2 / multiple merges have one origin per line / TC-UNIT-033
def test_algorithm_b_multiple_branch_merges_count_each_distinct_line_once(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    for revision_id, file_name, gen_ratio in [
        ("branch-a", "src/a.py", 100),
        ("branch-b", "src/b.py", 60),
        ("branch-c", "src/c.py", 30),
    ]:
        _write_record(
            gen_code_desc_dir / f"{revision_id}.json",
            _record(revision_id, "2026-01-10T00:00:00Z", [_file_detail(file_name, [_line(1, gen_ratio)])], 1),
        )
        _write_add_file_patch(commit_patch_dir / f"{revision_id}.patch", file_name)
    _write_record(
        gen_code_desc_dir / "merge-all.json",
        _record("merge-all", "2026-01-11T00:00:00Z", [], 0, parent_revision_ids=["branch-a", "branch-b", "branch-c"]),
    )
    _write_empty_patch(commit_patch_dir / "merge-all.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)
    line_identities = {(line.file_name, line.line_number) for line in result.lines}

    assert _line_summary(result) == [
        ("src/a.py", 1, 100, "codeCompletion"),
        ("src/b.py", 1, 60, "codeCompletion"),
        ("src/c.py", 1, 30, "codeCompletion"),
    ]
    assert len(line_identities) == len(result.lines)


# US-005 / AC-005-3 / long-lived branch uses true origin timestamp / TC-UNIT-034
def test_algorithm_b_long_lived_branch_includes_feature_origin_and_excludes_old_base(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "base.json", _record("base", "2025-07-01T00:00:00Z", [_file_detail("src/base.py", [_line(1, 100)])], 1))
    _write_record(
        gen_code_desc_dir / "feature.json",
        _record("feature", "2026-01-10T00:00:00Z", [_file_detail("src/feature.py", [_line(1, 80, "vibeCoding")])], 1, parent_revision_ids=["base"]),
    )
    _write_record(
        gen_code_desc_dir / "merge-feature.json",
        _record("merge-feature", "2026-01-11T00:00:00Z", [], 0, parent_revision_ids=["base", "feature"]),
    )
    _write_add_file_patch(commit_patch_dir / "base.patch", "src/base.py")
    _write_add_file_patch(commit_patch_dir / "feature.patch", "src/feature.py")
    _write_empty_patch(commit_patch_dir / "merge-feature.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/feature.py", 1, 80, "vibeCoding")]


# US-005 / AC-005-4 / shallow history limitation policy / TC-UNIT-035
def test_algorithm_b_reports_shallow_history_limitation_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "rev1.json", _record("rev1", "2026-01-10T00:00:00Z", [_file_detail("src/main.py", [_line(1, 100)])], 1))
    _write_add_file_patch(commit_patch_dir / "rev1.patch", "src/main.py")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert "shallow" in result.diagnostics["historyPolicy"]["shallowHistory"]


# US-005 / AC-005-5 / submodule parent exclusion policy / TC-UNIT-036
def test_algorithm_b_ignores_submodule_gitlink_patches_and_reports_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "submodule.json", _record("submodule", "2026-01-10T00:00:00Z", [], 0))
    _write_submodule_patch(commit_patch_dir / "submodule.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert result.lines == []
    assert "independent aggregateGenCodeDesc run" in result.diagnostics["historyPolicy"]["submodules"]
