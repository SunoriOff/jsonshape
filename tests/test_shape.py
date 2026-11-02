from jsonshape.render import render_tree, type_label
from jsonshape.shape import detect_format, infer


def test_scalar_kinds():
    assert type_label(infer(1)) == "integer"
    assert type_label(infer(1.5)) == "number"
    assert type_label(infer(True)) == "boolean"
    assert type_label(infer(None)) == "null"
    assert type_label(infer("x")) == "string"


def test_bool_is_not_integer():
    assert infer(True).kinds == {"boolean"}


def test_int_and_float_merge_to_number():
    shape = infer([1, 2.5])
    assert type_label(shape) == "array<number>"


def test_formats():
    assert detect_format("2026-11-02") == "date"
    assert detect_format("2026-11-02T13:00:00Z") == "date-time"
    assert detect_format("123e4567-e89b-12d3-a456-426614174000") == "uuid"
    assert detect_format("a@b.co") == "email"
    assert detect_format("https://example.com/x") == "uri"
    assert detect_format("hello") is None


def test_mixed_strings_lose_format():
    assert type_label(infer(["a@b.co", "plain"])) == "array<string>"
    assert type_label(infer(["a@b.co", "c@d.org"])) == "array<string (email)>"


def test_optional_and_nullable_properties():
    shape = infer([{"id": 1, "nick": "x"}, {"id": 2, "nick": None}, {"id": 3}])
    tree = render_tree(shape)
    assert "id: integer" in tree
    assert "nick?: string | null" in tree


def test_arrays_of_objects_are_expanded_under_the_array():
    shape = infer({"users": [{"name": "a", "tags": ["x", "y"]}, {"name": "b", "tags": []}]})
    tree = render_tree(shape)
    assert "users: array<object> [2]" in tree
    assert "name: string" in tree
    assert "tags: array<string> [0..2]" in tree


def test_depth_limit():
    shape = infer({"a": {"b": {"c": 1}}})
    tree = render_tree(shape, depth=2)
    assert "a: object" in tree and "b: object" in tree
    assert "c:" not in tree


def test_empty_array_is_unknown():
    assert type_label(infer([])) == "array<unknown>"
