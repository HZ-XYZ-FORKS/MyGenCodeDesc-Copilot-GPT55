import json

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_add_file_patch(path, file_name="src/auth.py", total_lines=1):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        f"+++ b/{file_name}",
        f"@@ -0,0 +1,{total_lines} @@",
        *[f"+value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_empty_patch(path):
    path.write_text("", encoding="utf-8")


def _write_delete_file_patch(path, file_name="src/auth.py", total_lines=2):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "deleted file mode 100644",
        "index 1111111..0000000",
        f"--- a/{file_name}",
        "+++ /dev/null",
        f"@@ -1,{total_lines} +0,0 @@",
        *[f"-value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_single_line_modify_patch(path, file_name="src/auth.py"):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "index 1111111..2222222 100644",
        f"--- a/{file_name}",
        f"+++ b/{file_name}",
        "@@ -1,1 +1,1 @@",
        "-value_1 = 1",
        "+value_1 = 20",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


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


# US-003 / AC-003-1 / merge commit preserves original line origins / TC-UNIT-020
def test_algorithm_b_merge_commit_keeps_feature_origin_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "feature.json",
        _record(
            "feature",
            "2026-01-10T00:00:00Z",
            [_file_detail("src/feature.py", [_line(1, 100), _line(2, 100)])],
            2,
        ),
    )
    _write_record(
        gen_code_desc_dir / "merge.json",
        _record("merge", "2026-01-11T00:00:00Z", [], 0, parent_revision_ids=["feature"]),
    )
    _write_add_file_patch(commit_patch_dir / "feature.patch", file_name="src/feature.py", total_lines=2)
    _write_empty_patch(commit_patch_dir / "merge.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [
        ("src/feature.py", 1, 100, "codeCompletion"),
        ("src/feature.py", 2, 100, "codeCompletion"),
    ]


# US-003 / AC-003-2 / squash merge uses squash commit genCodeDesc / TC-UNIT-021
def test_algorithm_b_squash_merge_uses_squash_commit_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "squash.json",
        _record(
            "squash",
            "2026-01-12T00:00:00Z",
            [_file_detail("src/auth.py", [_line(1, 100), _line(2, 40, "vibeCoding"), _line(3, 0, "Manual")])],
            3,
        ),
    )
    _write_add_file_patch(commit_patch_dir / "squash.patch", total_lines=3)

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [
        ("src/auth.py", 1, 100, "codeCompletion"),
        ("src/auth.py", 2, 40, "vibeCoding"),
        ("src/auth.py", 3, 0, "Manual"),
    ]


# US-003 / AC-003-3 / cherry-pick uses new commit attribution / TC-UNIT-022
def test_algorithm_b_cherry_pick_uses_cherry_picked_revision_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "cherry-picked.json",
        _record(
            "cherry-picked",
            "2026-01-13T00:00:00Z",
            [_file_detail("src/auth.py", [_line(1, 80, "vibeCoding")])],
            1,
        ),
    )
    _write_add_file_patch(commit_patch_dir / "cherry-picked.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/auth.py", 1, 80, "vibeCoding")]
    assert "# --- commit cherry-picked ---" in result.patch_text


# US-003 / AC-003-4 / revert removes reverted lines / TC-UNIT-023
def test_algorithm_b_revert_commit_removes_reverted_ai_lines(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "add-ai.json",
        _record("add-ai", "2026-01-10T00:00:00Z", [_file_detail("src/auth.py", [_line(1, 100), _line(2, 100)])], 2),
    )
    _write_record(
        gen_code_desc_dir / "revert.json",
        _record("revert", "2026-01-14T00:00:00Z", [], 0, parent_revision_ids=["add-ai"]),
    )
    _write_add_file_patch(commit_patch_dir / "add-ai.patch", total_lines=2)
    _write_delete_file_patch(commit_patch_dir / "revert.patch", total_lines=2)

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert result.lines == []


# US-003 / AC-003-5 / amend orphans old genCodeDesc / TC-UNIT-024
def test_algorithm_b_amend_ignores_old_revision_not_present_in_patch_history(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "aaa.json",
        _record("aaa", "2026-01-10T00:00:00Z", [_file_detail("src/auth.py", [_line(1, 100)])], 1),
    )
    _write_record(
        gen_code_desc_dir / "bbb.json",
        _record("bbb", "2026-01-11T00:00:00Z", [_file_detail("src/auth.py", [_line(1, 40, "vibeCoding")])], 1),
    )
    _write_add_file_patch(commit_patch_dir / "bbb.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/auth.py", 1, 40, "vibeCoding")]
    assert result.diagnostics["orphanedRevisions"] == ["aaa"]


# US-003 / AC-003-6 / rebase uses regenerated revisionIds / TC-UNIT-025
def test_algorithm_b_rebase_ignores_old_revision_ids_and_uses_replayed_revision_ids(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    for old_revision_id in ["old-c1", "old-c2"]:
        _write_record(
            gen_code_desc_dir / f"{old_revision_id}.json",
            _record(old_revision_id, "2026-01-09T00:00:00Z", [_file_detail("src/auth.py", [_line(1, 100)])], 1),
        )
    _write_record(
        gen_code_desc_dir / "new-c1.json",
        _record("new-c1", "2026-01-10T00:00:00Z", [_file_detail("src/auth.py", [_line(1, 70, "vibeCoding")])], 1),
    )
    _write_record(
        gen_code_desc_dir / "new-c2.json",
        _record(
            "new-c2",
            "2026-01-11T00:00:00Z",
            [_file_detail("src/auth.py", [_line(1, 100)])],
            1,
            parent_revision_ids=["new-c1"],
        ),
    )
    _write_add_file_patch(commit_patch_dir / "new-c1.patch")
    _write_single_line_modify_patch(commit_patch_dir / "new-c2.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/auth.py", 1, 100, "codeCompletion")]
    assert result.diagnostics["orphanedRevisions"] == ["old-c1", "old-c2"]
