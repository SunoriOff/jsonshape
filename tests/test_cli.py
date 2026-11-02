import io
import json

from jsonshape.cli import load, main


def test_load_json_and_jsonlines():
    assert load('{"a": 1}') == {"a": 1}
    assert load('{"a": 1}\n{"a": 2}\n') == [{"a": 1}, {"a": 2}]


def test_tree_from_file(tmp_path, capsys):
    f = tmp_path / "d.json"
    f.write_text(json.dumps({"name": "x", "n": [1, 2, 3]}))
    assert main([str(f)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("$: object")
    assert "name: string" in out
    assert "n: array<integer> [3]" in out


def test_jsonlines_merges_records(tmp_path, capsys):
    f = tmp_path / "d.jsonl"
    f.write_text('{"a": 1}\n{"a": 2, "b": "x"}\n')
    main([str(f)])
    out = capsys.readouterr().out
    assert "$: array<object> [2]" in out
    assert "b?: string" in out


def test_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO('[1, 2]'))
    assert main(["-f", "schema"]) == 0
    assert json.loads(capsys.readouterr().out)["items"] == {"type": "integer"}


def test_typescript_format(tmp_path, capsys):
    f = tmp_path / "d.json"
    f.write_text('{"id": 1}')
    main([str(f), "-f", "ts", "--name", "User"])
    assert "export interface User {" in capsys.readouterr().out


def test_invalid_json(tmp_path, capsys):
    f = tmp_path / "bad.json"
    f.write_text("{nope")
    assert main([str(f)]) == 2
    assert "invalid JSON" in capsys.readouterr().err


def test_missing_file(capsys):
    assert main(["/no/such/file.json"]) == 2
