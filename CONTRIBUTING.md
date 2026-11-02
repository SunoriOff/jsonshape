# Contributing to jsonshape

Thanks for helping! The project is small on purpose: zero runtime dependencies, fast, easy to read.

## Setup

```bash
git clone https://github.com/SunoriOff/jsonshape
cd jsonshape
pip install -e ".[dev]"
pytest
```

## Where to change things

New output formats go in `src/jsonshape/render.py`; wire them in `src/jsonshape/cli.py` and add tests in `tests/test_render.py`.

## Pull requests

- Keep PRs focused, one change each.
- Add or update tests; CI must pass on Python 3.9 to 3.13.
- Don't add runtime dependencies.

## Reporting bugs

Open an issue with a minimal input and the output you expected. Those reports are very valuable.
