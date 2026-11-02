"""Render a Shape as a tree, TypeScript interfaces, or JSON Schema."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .shape import Shape, object_owner


# ---------------------------------------------------------------- tree -----
def type_label(shape: Shape) -> str:
    names: List[str] = []
    for kind in shape.kind_list():
        if kind == "array":
            inner = type_label(shape.items) if shape.items is not None else "unknown"
            names.append(f"array<{inner}>")
        elif kind == "string" and shape.string_format():
            names.append(f"string ({shape.string_format()})")
        else:
            names.append(kind)
    return " | ".join(names) or "unknown"


def _length_suffix(shape: Shape) -> str:
    if "array" not in shape.kinds or shape.min_len is None:
        return ""
    if shape.min_len == shape.max_len:
        return f" [{shape.min_len}]"
    return f" [{shape.min_len}..{shape.max_len}]"


def render_tree(root: Shape, depth: Optional[int] = None, name: str = "$") -> str:
    lines = [f"{name}: {type_label(root)}{_length_suffix(root)}"]
    _walk(root, "", lines, 1, depth)
    return "\n".join(lines)


def _walk(shape: Shape, prefix: str, lines: List[str], level: int, depth: Optional[int]) -> None:
    owner = object_owner(shape)
    if owner is None or (depth is not None and level > depth):
        return
    keys = list(owner.props)
    for index, key in enumerate(keys):
        sub = owner.props[key]
        last = index == len(keys) - 1
        optional = "?" if owner.is_optional(key) else ""
        branch = "└── " if last else "├── "
        lines.append(f"{prefix}{branch}{key}{optional}: {type_label(sub)}{_length_suffix(sub)}")
        _walk(sub, prefix + ("    " if last else "│   "), lines, level + 1, depth)


# ----------------------------------------------------------- typescript ----
IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def pascal(text: str) -> str:
    words = [w for w in re.split(r"[^A-Za-z0-9]+", text) if w]
    name = "".join(w[:1].upper() + w[1:] for w in words) or "Item"
    return name if not name[0].isdigit() else "T" + name


def singular(text: str) -> str:
    if text.endswith("ies") and len(text) > 3:
        return text[:-3] + "y"
    if text.endswith("s") and not text.endswith("ss") and len(text) > 1:
        return text[:-1]
    return text + "Item"


def render_typescript(root: Shape, name: str = "Root") -> str:
    definitions: List[Optional[str]] = []
    used: Dict[str, int] = {}

    def unique(base: str) -> str:
        count = used.get(base, 0)
        used[base] = count + 1
        return base if count == 0 else f"{base}{count + 1}"

    def key_literal(key: str) -> str:
        if IDENT.match(key):
            return key
        escaped = key.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def interface(shape: Shape, hint: str) -> str:
        iface = unique(pascal(hint))
        slot = len(definitions)
        definitions.append(None)
        body = []
        for key, sub in shape.props.items():
            optional = "?" if shape.is_optional(key) else ""
            body.append(f"  {key_literal(key)}{optional}: {ts_type(sub, key)};")
        inner = "\n".join(body)
        definitions[slot] = f"export interface {iface} {{\n{inner}\n}}" if body else f"export interface {iface} {{}}"
        return iface

    def ts_type(shape: Shape, hint: str) -> str:
        parts: List[str] = []
        for kind in shape.kind_list():
            if kind == "object":
                rendered = interface(shape, hint)
            elif kind == "array":
                inner = ts_type(shape.items, singular(hint)) if shape.items is not None else "unknown"
                rendered = f"({inner})[]" if " | " in inner else f"{inner}[]"
            elif kind in ("integer", "number"):
                rendered = "number"
            else:
                rendered = kind
            if rendered not in parts:
                parts.append(rendered)
        return " | ".join(parts) or "unknown"

    top = ts_type(root, name)
    if top != pascal(name):
        definitions.append(f"export type {pascal(name)} = {top};")
    return "\n\n".join(d for d in definitions if d)


# ---------------------------------------------------------- json schema ----
def to_schema(shape: Shape) -> dict:
    kinds = shape.kind_list()
    schema: dict = {}
    if len(kinds) == 1:
        schema["type"] = kinds[0]
    elif kinds:
        schema["type"] = kinds
    if "object" in kinds:
        schema["properties"] = {k: to_schema(v) for k, v in shape.props.items()}
        required = [k for k in shape.props if not shape.is_optional(k)]
        if required:
            schema["required"] = required
    if "array" in kinds:
        schema["items"] = to_schema(shape.items) if shape.items is not None else {}
    if shape.string_format():
        schema["format"] = shape.string_format()
    return schema


def render_schema(shape: Shape) -> dict:
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
    schema.update(to_schema(shape))
    return schema
