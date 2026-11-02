"""Command-line interface for jsonshape."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List, Optional

from . import __version__
from .render import render_schema, render_tree, render_typescript
from .shape import infer


def load(text: str) -> Any:
    """Parse JSON, falling back to JSON Lines (one document per line)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as first_error:
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) > 1:
            try:
                return [json.loads(line) for line in lines]
            except json.JSONDecodeError:
                pass
        raise first_error


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jsonshape",
        description="Show the structure of a JSON file at a glance: a compact tree, "
                    "TypeScript interfaces, or a JSON Schema.",
    )
    p.add_argument("--version", action="version", version=f"jsonshape {__version__}")
    p.add_argument("file", nargs="?", default="-", help="JSON or JSON Lines file (default: stdin)")
    p.add_argument("-f", "--format", choices=["tree", "ts", "typescript", "schema"], default="tree")
    p.add_argument("--name", default="Root", help="root type name for TypeScript output")
    p.add_argument("-d", "--depth", type=int, help="maximum depth of the tree")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
    except OSError as exc:
        print(f"jsonshape: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    try:
        data = load(text)
    except json.JSONDecodeError as exc:
        print(f"jsonshape: invalid JSON: {exc}", file=sys.stderr)
        return 2

    shape = infer(data)
    if args.format == "tree":
        print(render_tree(shape, depth=args.depth))
    elif args.format in ("ts", "typescript"):
        print(render_typescript(shape, name=args.name))
    else:
        print(json.dumps(render_schema(shape), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
