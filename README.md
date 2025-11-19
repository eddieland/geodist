# geodist

**High-performance geometric distance algorithms with Rust kernels and Python bindings.**

`geodist` focuses on transparent distance calculations you can audit and explain
rather than treating results as opaque numbers. The Rust crate provides the core
geodesic kernels; Python bindings will layer ergonomic geometry wrappers once
the Rust surface settles.

## Crates & Packages

| Component      | What exists today                                   | Path |
|----------------|-----------------------------------------------------|------|
| **geodist-rs** | Rust crate with geodesic distance + Hausdorff APIs  | `geodist-rs/` |
| **pygeodist**  | Python package with a PyO3 extension smoke test     | `pygeodist/` |

## What works now

- Validated geodesic primitives (`Point`, `Distance`, `Ellipsoid`, `BoundingBox`) with strict input checking.
- Great-circle distance on a spherical Earth (WGS84 mean radius by default) plus custom radius/ellipsoid helpers.
- Batch distance calculation for many point pairs.
- Initial/final bearing output that reuses the distance kernel.
- Directed and symmetric Hausdorff distance over point sets, with bounding-box-clipped variants and an automatic switch between an `rstar` index and an O(n*m) fallback for tiny inputs.
- Feature-gated PyO3 module exposing `EARTH_RADIUS_METERS` for Python wheel smoke tests (future bindings will forward the Rust kernels).

## Roadmap highlights

- Witness point reporting for all metrics.
- Geometry coverage beyond point sets (LineString/Polygon sampling, densification).
- Parallel computation paths and richer distance metrics (Frechét, Chamfer).
- Full Python geometry wrappers and vectorized operations backed by the Rust kernels.

## Rust quickstart

```rust
use geodist_rs::{Point, geodesic_distance, geodesic_with_bearings, hausdorff};

let origin = Point::new(40.7128, -74.0060)?;
let destination = Point::new(51.5074, -0.1278)?;

let meters = geodesic_distance(origin, destination)?.meters();
let bearings = geodesic_with_bearings(origin, destination)?;

let path_a = [origin, Point::new(40.0, -73.5)?];
let path_b = [destination, Point::new(51.0, -0.2)?];
let hausdorff_meters = hausdorff(&path_a, &path_b)?.meters();
```

While the API stabilizes, use the crate from this workspace or add it as a path
dependency.

## Python quickstart (smoke test)

The Python package includes the PyO3 extension stub and a small Typer CLI to
confirm the extension loads. Kernels are not wired into the Python wrapper yet.

```bash
cd pygeodist
uv sync --all-extras --dev
uv run maturin develop  # builds the extension module
uv run geodist info     # prints whether the extension loaded
uv run pytest           # exercises the stub surface
```

## Project Status

The project is in early active development. APIs may evolve until the initial
stable release. Contributions, suggestions, and issue reports are welcome.

## Tooling

- Python uses [uv](https://docs.astral.sh/uv/). Install it via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv` on macOS, then provision a toolchain with `uv python install 3.13`.
- Set up the Python environment with `cd pygeodist && uv sync --all-extras` (or `make install` for the same effect). Run `uv run maturin develop` after Rust changes to rebuild the extension.
- Common Python shortcuts from `pygeodist/Makefile`: `make lint`, `make test`, `make build`, `make clean`.
- Rust work happens under `geodist-rs`; use `cargo fmt`, `cargo clippy`, and `cargo nextest run` (or the root `make fmt|lint|test`) while iterating on kernels.
