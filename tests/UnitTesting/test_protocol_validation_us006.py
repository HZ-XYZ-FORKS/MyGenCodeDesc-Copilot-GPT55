import json

import pytest

from aggregate_gen_code_desc.protocol import load_gen_code_desc_dir


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _valid_record(protocol_version="26.04"):
    record = {
        "protocolName": "generatedTextDesc",
        "protocolVersion": protocol_version,
        "codeAgent": "UnitTestingFixture",
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
                "fileName": "src/main.py",
                "codeLines": [
                    {
                        "changeType": "add",
                        "lineLocation": 1,
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": "rev1",
                            "originalFilePath": "src/main.py",
                            "originalLine": 1,
                            "timestamp": "2026-01-10T00:00:00Z",
                        },
                    }
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": "rev1",
            "revisionTimestamp": "2026-01-10T00:00:00Z",
        },
    }
    if protocol_version == "26.03":
        record["DETAIL"][0]["codeLines"] = [
            {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}
        ]
    return record


def _load(record, tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "record.json", record)
    return load_gen_code_desc_dir(gen_code_desc_dir, "https://example.test/repo", "main")


@pytest.mark.parametrize("field_name", ["protocolName", "SUMMARY", "DETAIL", "REPOSITORY"])
# US-006 / schema required-field validation / TC-UNIT-047
def test_loader_rejects_missing_required_top_level_fields(tmp_path, field_name):
    record = _valid_record()
    record.pop(field_name)

    with pytest.raises(ValueError, match=rf"{field_name} is required"):
        _load(record, tmp_path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda record: record.__setitem__("DETAIL", {}), "DETAIL must be an array"),
        (lambda record: record["SUMMARY"].__setitem__("totalCodeLines", "one"), "SUMMARY.totalCodeLines must be an integer"),
        (lambda record: record.__setitem__("REPOSITORY", []), "REPOSITORY must be an object"),
    ],
)
# US-006 / schema type validation / TC-UNIT-048
def test_loader_rejects_required_field_type_mismatches(tmp_path, mutate, message):
    record = _valid_record()
    mutate(record)

    with pytest.raises(ValueError, match=message):
        _load(record, tmp_path)


# US-006 / v26.03 DETAIL location validation / TC-UNIT-049
def test_loader_rejects_v2603_detail_entry_without_line_location_or_range(tmp_path):
    record = _valid_record(protocol_version="26.03")
    record["DETAIL"][0]["codeLines"][0].pop("lineLocation")

    with pytest.raises(ValueError, match=r"DETAIL\[0\]\.codeLines\[0\] must include lineLocation or lineRange"):
        _load(record, tmp_path)


# US-006 / BASE v26.03 optional doc SUMMARY fields / TC-UNIT-056
def test_loader_accepts_v2603_record_without_optional_doc_summary_fields(tmp_path):
    record = _valid_record(protocol_version="26.03")
    for field_name in ("totalDocLines", "fullGeneratedDocLines", "partialGeneratedDocLines"):
        record["SUMMARY"].pop(field_name)

    loaded = _load(record, tmp_path)

    assert loaded.protocol_version == "26.03"


# US-006, US-007 / BASE v26.03 optional vcsType default / TC-UNIT-057
def test_loader_accepts_v2603_record_without_optional_vcs_type_as_git(tmp_path, monkeypatch):
    monkeypatch.delenv("AGGREGATE_GCD_ALLOW_SYNTHETIC_REVISION_IDS", raising=False)
    record = _valid_record(protocol_version="26.03")
    record["REPOSITORY"].pop("vcsType")
    record["REPOSITORY"]["revisionId"] = "a" * 40

    loaded = _load(record, tmp_path)

    assert loaded.record_summaries == [{"revisionId": "a" * 40, "entries": 1}]


# US-006 / BASE v26.03 DETAIL code/doc collection presence / TC-UNIT-058
def test_loader_rejects_detail_file_without_code_or_doc_lines(tmp_path):
    record = _valid_record(protocol_version="26.03")
    record["DETAIL"] = [{"fileName": "src/empty.py"}]

    with pytest.raises(ValueError, match=r"DETAIL\[0\] must include codeLines or docLines"):
        _load(record, tmp_path)


# US-006 / BASE v26.03 SUMMARY generated-count relationship with ranges / TC-UNIT-059
def test_loader_warns_when_generated_summary_counts_do_not_match_expanded_detail_lines(tmp_path):
    record = _valid_record(protocol_version="26.03")
    record["SUMMARY"] = {
        "totalCodeLines": 8,
        "fullGeneratedCodeLines": 2,
        "partialGeneratedCodeLines": 1,
    }
    record["DETAIL"] = [
        {
            "fileName": "src/ranged.py",
            "codeLines": [
                {"lineRange": {"from": 1, "to": 3}, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineRange": {"from": 4, "to": 5}, "genRatio": 40, "genMethod": "vibeCoding"},
            ],
        }
    ]

    loaded = _load(record, tmp_path)

    assert loaded.warnings == [
        "revisionId=rev1 SUMMARY.fullGeneratedCodeLines expected 2 lines, found 3",
        "revisionId=rev1 SUMMARY.partialGeneratedCodeLines expected 1 lines, found 2",
    ]


# US-006 / BASE v26.03 expanded lineRange summary/detail agreement / TC-UNIT-060
def test_loader_accepts_expanded_line_range_summary_detail_agreement_without_warnings(tmp_path):
    record = _valid_record(protocol_version="26.03")
    record["SUMMARY"] = {
        "totalCodeLines": 5,
        "fullGeneratedCodeLines": 3,
        "partialGeneratedCodeLines": 2,
    }
    record["DETAIL"] = [
        {
            "fileName": "src/ranged.py",
            "codeLines": [
                {"lineRange": {"from": 1, "to": 3}, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineRange": {"from": 4, "to": 5}, "genRatio": 50, "genMethod": "vibeCoding"},
            ],
        }
    ]

    loaded = _load(record, tmp_path)

    assert loaded.warnings == []


# US-006 / BASE v26.03 sparse manual-line omission / TC-UNIT-061
def test_loader_allows_sparse_manual_code_lines_without_total_count_warning(tmp_path):
    record = _valid_record(protocol_version="26.03")
    record["SUMMARY"] = {
        "totalCodeLines": 5,
        "fullGeneratedCodeLines": 1,
        "partialGeneratedCodeLines": 0,
    }
    record["DETAIL"] = [
        {
            "fileName": "src/sparse.py",
            "codeLines": [
                {"lineLocation": 3, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
        }
    ]

    loaded = _load(record, tmp_path)

    assert loaded.warnings == []


# US-006 / v26.04 blame required-field validation / TC-UNIT-050
def test_loader_rejects_v2604_add_entry_without_blame_timestamp(tmp_path):
    record = _valid_record(protocol_version="26.04")
    record["DETAIL"][0]["codeLines"][0]["blame"].pop("timestamp")

    with pytest.raises(ValueError, match=r"DETAIL\[0\]\.codeLines\[0\]\.blame\.timestamp is required"):
        _load(record, tmp_path)


# US-007 / malformed Git revision ID strict validation / TC-UNIT-053
def test_loader_rejects_malformed_git_revision_id_when_strict_policy_is_enabled(tmp_path, monkeypatch):
    monkeypatch.delenv("AGGREGATE_GCD_ALLOW_SYNTHETIC_REVISION_IDS", raising=False)
    record = _valid_record(protocol_version="26.03")
    record["REPOSITORY"]["revisionId"] = "abc123"

    with pytest.raises(ValueError, match=r"REPOSITORY\.revisionId must be a 40-character SHA-1 or 64-character SHA-256 hex string"):
        _load(record, tmp_path)


# US-007 / malformed SVN revision ID strict validation / TC-UNIT-054
def test_loader_rejects_malformed_svn_revision_id_when_strict_policy_is_enabled(tmp_path, monkeypatch):
    monkeypatch.delenv("AGGREGATE_GCD_ALLOW_SYNTHETIC_REVISION_IDS", raising=False)
    record = _valid_record(protocol_version="26.03")
    record["REPOSITORY"]["vcsType"] = "svn"
    record["REPOSITORY"]["revisionId"] = "abc123"

    with pytest.raises(ValueError, match=r"REPOSITORY\.revisionId must be a positive SVN revision number"):
        _load(record, tmp_path)


# US-007 / malformed embedded blame revision ID strict validation / TC-UNIT-055
def test_loader_rejects_malformed_v2604_blame_revision_id_when_strict_policy_is_enabled(tmp_path, monkeypatch):
    monkeypatch.delenv("AGGREGATE_GCD_ALLOW_SYNTHETIC_REVISION_IDS", raising=False)
    record = _valid_record(protocol_version="26.04")
    valid_git_revision = "a" * 40
    record["REPOSITORY"]["revisionId"] = valid_git_revision
    record["DETAIL"][0]["codeLines"][0]["blame"]["revisionId"] = "bad-blame-id"

    with pytest.raises(
        ValueError,
        match=r"DETAIL\[0\]\.codeLines\[0\]\.blame\.revisionId must be a 40-character SHA-1 or 64-character SHA-256 hex string",
    ):
        _load(record, tmp_path)
