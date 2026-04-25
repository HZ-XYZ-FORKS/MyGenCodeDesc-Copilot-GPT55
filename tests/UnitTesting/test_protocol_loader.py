import json

from aggregate_gen_code_desc.protocol import strip_jsonc_comments


# Protocol loader / TC-UNIT-006
def test_jsonc_comment_stripper_preserves_url_strings():
    text = '{"repoURL": "https://example.test/repo", "value": 1 // trailing comment\n}'

    parsed = json.loads(strip_jsonc_comments(text))

    assert parsed["repoURL"] == "https://example.test/repo"
    assert parsed["value"] == 1
