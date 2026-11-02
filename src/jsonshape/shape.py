"""Infer and merge the structure ("shape") of JSON values."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set

FORMATS = [
    ("date-time", re.compile(
        r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$")),
    ("date", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
    ("uuid", re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")),
    ("email", re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")),
    ("uri", re.compile(r"^https?://\S+$")),
]

ORDER = ["object", "array", "string", "integer", "number", "boolean", "null"]


def detect_format(text: str) -> Optional[str]:
    for name, pattern in FORMATS:
        if pattern.match(text):
            return name
    return None


class Shape:
    """The merged structure of every value seen at one position in the document."""

    def __init__(self) -> None:
        self.kinds: Set[str] = set()
        self.props: Dict[str, "Shape"] = {}
        self.counts: Dict[str, int] = {}
        self.objects = 0
        self.items: Optional["Shape"] = None
        self.formats: Set[Optional[str]] = set()
        self.min_len: Optional[int] = None
        self.max_len: Optional[int] = None

    # -- merging -----------------------------------------------------------
    def merge(self, other: "Shape") -> None:
        self.kinds |= other.kinds
        self.formats |= other.formats
        self.objects += other.objects
        for key, sub in other.props.items():
            if key in self.props:
                self.props[key].merge(sub)
            else:
                self.props[key] = sub
            self.counts[key] = self.counts.get(key, 0) + other.counts[key]
        if other.items is not None:
            if self.items is None:
                self.items = other.items
            else:
                self.items.merge(other.items)
        if other.min_len is not None:
            self.min_len = other.min_len if self.min_len is None else min(self.min_len, other.min_len)
        if other.max_len is not None:
            self.max_len = other.max_len if self.max_len is None else max(self.max_len, other.max_len)

    # -- queries -----------------------------------------------------------
    def is_optional(self, key: str) -> bool:
        return self.counts.get(key, 0) < self.objects

    def string_format(self) -> Optional[str]:
        if "string" in self.kinds and len(self.formats) == 1:
            return next(iter(self.formats))
        return None

    def kind_list(self) -> list:
        """Kinds in a stable display order, with integer folded into number."""
        kinds = [k for k in ORDER if k in self.kinds]
        if "integer" in kinds and "number" in kinds:
            kinds.remove("integer")
        return kinds


def infer(value: Any) -> Shape:
    shape = Shape()
    if value is None:
        shape.kinds.add("null")
    elif isinstance(value, bool):
        shape.kinds.add("boolean")
    elif isinstance(value, int):
        shape.kinds.add("integer")
    elif isinstance(value, float):
        shape.kinds.add("number")
    elif isinstance(value, str):
        shape.kinds.add("string")
        shape.formats.add(detect_format(value))
    elif isinstance(value, list):
        shape.kinds.add("array")
        shape.min_len = shape.max_len = len(value)
        for element in value:
            if shape.items is None:
                shape.items = Shape()
            shape.items.merge(infer(element))
    elif isinstance(value, dict):
        shape.kinds.add("object")
        shape.objects = 1
        for key, sub in value.items():
            shape.props[key] = infer(sub)
            shape.counts[key] = 1
    else:
        shape.kinds.add("string")
        shape.formats.add(None)
    return shape


def object_owner(shape: Shape) -> Optional[Shape]:
    """The shape whose properties should be listed under *shape* (looks through arrays)."""
    if "object" in shape.kinds:
        return shape
    if "array" in shape.kinds and shape.items is not None:
        return object_owner(shape.items)
    return None
