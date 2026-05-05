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


# US-006 / v26.04 blame required-field validation / TC-UNIT-050
def test_loader_rejects_v2604_add_entry_without_blame_timestamp(tmp_path):
    record = _valid_record(protocol_version="26.04")
    record["DETAIL"][0]["codeLines"][0]["blame"].pop("timestamp")

    with pytest.raises(ValueError, match=r"DETAIL\[0\]\.codeLines\[0\]\.blame\.timestamp is required"):
        _load(record, tmp_path)
