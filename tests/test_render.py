import json

from jsonshape.render import pascal, render_schema, render_typescript, singular
from jsonshape.shape import infer


def test_helpers():
    assert pascal("user_name") == "UserName"
    assert pascal("123abc") == "T123abc"
    assert singular("users") == "user"
    assert singular("categories") == "category"
    assert singular("data") == "dataItem"


def test_typescript_interfaces():
    data = {"id": 1, "name": "x", "address": {"city": "Paris"}, "tags": ["a"]}
    ts = render_typescript(infer(data))
    assert "export interface Root {" in ts
    assert "  id: number;" in ts
    assert "  address: Address;" in ts
    assert "  tags: string[];" in ts
    assert "export interface Address {" in ts
    assert "  city: string;" in ts


def test_typescript_root_array_and_optional_and_union():
    data = [{"id": 1, "v": 1}, {"id": 2, "v": "x", "extra": None}]
    ts = render_typescript(infer(data), name="Rows")
    assert "export type Rows = Row[];" in ts
    assert "export interface Row {" in ts
    assert "  v: string | number;" in ts or "  v: number | string;" in ts
    assert "  extra?: null;" in ts


def test_typescript_quotes_odd_keys():
    ts = render_typescript(infer({"first-name": "a"}))
    assert '"first-name": string;' in ts


def test_typescript_duplicate_names_are_disambiguated():
    data = {"a": {"item": {"x": 1}}, "b": {"item": {"y": 2}}}
    ts = render_typescript(infer(data))
    assert "export interface Item {" in ts
    assert "export interface Item2 {" in ts


def test_json_schema():
    data = [{"id": 1, "email": "a@b.co"}, {"id": 2}]
    schema = render_schema(infer(data))
    assert schema["$schema"].startswith("https://json-schema.org")
    assert schema["type"] == "array"
    item = schema["items"]
    assert item["required"] == ["id"]
    assert item["properties"]["email"] == {"type": "string", "format": "email"}
    json.dumps(schema)  # serialisable
