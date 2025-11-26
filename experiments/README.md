# geodist-experiments

Experimentation, benchmarks, notebooks, and visualizations for geodist development.

This workspace is intentionally **not published** to PyPI. It holds exploratory code,
benchmarks, and tools that may eventually be promoted into the main `pygeodist` package.

## Setup

```bash
cd experiments && uv sync --all-extras
```

The `pygeodist` package is installed as an editable dependency, so changes to the core
library are reflected immediately.

## Usage

### Notebooks

```bash
cd experiments && uv run jupyter notebook notebooks/
```

### Benchmarks

```bash
cd experiments && uv run python -m experiments.bench_vectorized --count 100000
```

## Adding Dependencies

Feel free to add arbitrary dependencies here. This workspace is isolated from the
published PyPI package, so experimental or heavy dependencies won't affect users.

Edit `pyproject.toml` and run `uv sync` to install new packages.
