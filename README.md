# jsonshape

[![CI](https://github.com/SunoriOff/jsonshape/actions/workflows/ci.yml/badge.svg)](https://github.com/SunoriOff/jsonshape/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/jsonshape.svg)](https://pypi.org/project/jsonshape/)
[![Python](https://img.shields.io/pypi/pyversions/jsonshape.svg)](https://pypi.org/project/jsonshape/)
[![License: WTFPL](https://img.shields.io/badge/license-WTFPL-brightgreen.svg)](LICENSE)
![Dependencies: 0](https://img.shields.io/badge/dependencies-0-brightgreen)

**See the structure of any JSON at a glance.**

Got a 40 MB API response and no idea what's in it? `jsonshape` reads it, merges every record, and prints the *shape*: which keys exist, which are optional, which can be null, and what the strings really are (dates, UUIDs, emails, URLs).

```text
$ jsonshape users.json

$: object
├── total: integer
└── users: array<object> [3]
    ├── id: string (uuid)
    ├── name: string
    ├── email: string (email)
    ├── created: string (date-time)
    ├── tags: array<string> [0..2]
    ├── address: object
    │   ├── city: string
    │   └── zip: string | null
    ├── age?: integer
    └── score?: number
```

`?` marks keys that are missing in some records. `[0..2]` is the min and max array length. Because all items of an array are merged, you see the real contract of your data, not just the first element.

## Install

```bash
pip install jsonshape
# or without installing:
curl -s https://api.example.com/users | pipx run jsonshape
```

Requires Python 3.9+. No dependencies.

## Usage

```bash
jsonshape data.json                 # tree view
cat data.json | jsonshape           # from stdin
curl -s https://api.github.com/repos/python/cpython | jsonshape
jsonshape data.json --depth 2       # limit the tree depth
jsonshape data.json -f ts           # TypeScript interfaces
jsonshape data.json -f ts --name ApiResponse
jsonshape data.json -f schema       # JSON Schema (draft 2020-12)
```

JSON Lines (one document per line, typical for logs) is detected automatically and merged as an array:

```text
$ jsonshape events.jsonl

$: array<object> [2]
├── level: string
├── msg: string
├── ts: string (date-time)
└── err?: object
    └── code: integer
```

### TypeScript

```text
$ jsonshape users.json -f ts

export interface Root {
  total: number;
  users: User[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  created: string;
  tags: string[];
  address: Address;
  age?: number;
  score?: number;
}

export interface Address {
  city: string;
  zip: string | null;
}
```

Interface names come from the keys (`users` becomes `User`). Keys that aren't valid identifiers are quoted, and clashing names are numbered.

### JSON Schema

```text
$ echo '[{"id":1,"email":"a@b.co"},{"id":2}]' | jsonshape -f schema

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
      },
      "email": {
        "type": "string",
        "format": "email"
      }
    },
    "required": [
      "id"
    ]
  }
}
```

Keys present in every record go in `required`; the others stay optional.

## What it detects

| Kind | Notes |
|---|---|
| `object`, `array`, `string`, `integer`, `number`, `boolean`, `null` | unions are shown as `string \| null` |
| string formats | `date-time`, `date`, `uuid`, `email`, `uri`, only reported when **every** string at that position matches |
| optional keys | key missing in at least one record |
| array length | `[min..max]` across all arrays at that position |

Mixed `integer` and `number` values at the same position are merged into `number`.

## Use it as a library

```python
import json
from jsonshape.shape import infer
from jsonshape.render import render_tree, render_typescript

shape = infer(json.load(open("data.json")))
print(render_tree(shape))
print(render_typescript(shape, name="Api"))
```

## Development

```bash
git clone https://github.com/SunoriOff/jsonshape
cd jsonshape
pip install -e ".[dev]"
pytest
```

## Roadmap

- [ ] Python output (`TypedDict` / `dataclass` / Pydantic)
- [ ] Enum detection for low-cardinality strings
- [ ] Numeric ranges and null ratios per key
- [ ] YAML and TOML input

## License

[WTFPL](LICENSE): do what the fuck you want to.
