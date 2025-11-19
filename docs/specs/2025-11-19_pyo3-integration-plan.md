# PyO3 Integration Plan (Bootstrap)

## Purpose

- Introduce PyO3 as the Rust↔Python bridge.
- Produce a small, buildable binding (e.g., exposing a Rust constant) to verify wheel generation in CI and locally.
- Leave room for a follow-up spec to design full API surface and packaging layout.

## Scope (this pass)

- Keep existing Rust crate (`geodist-rs`) as the single source of truth for kernels and types.
- Add an optional `python` feature that hosts PyO3 bindings and a trivial export.
- Switch Python packaging to maturin so we can publish a wheel that vendors the Rust extension.
- Ensure Python imports work via the `geodist` package namespace.

## Approach

1) **Rust bindings shell**
   - Add PyO3 dependency gated behind a `python` feature.
   - Provide a minimal `#[pymodule]` that exports `EARTH_RADIUS_METERS` (or a stub struct) for smoke testing.
2) **Build system wiring**
   - Use maturin as the PEP 517 backend in `pyproject.toml` with `manifest-path` pointing at `../geodist-rs/Cargo.toml`.
   - Configure module name under `geodist` (e.g., `geodist._geodist_rs`) and enable the `python` feature.
   - Add Make targets/notes for `maturin develop` / `uv build`.
3) **Python surface**
   - Re-export the bound constant from `geodist/__init__.py` so downstream code can `import geodist`.
   - Add a smoke test that asserts the constant matches the Rust value.
4) **Validation**
   - `uv sync --all-extras --dev`
   - `cd pygeodist && uv run maturin develop --features python --manifest-path ../geodist-rs/Cargo.toml`
   - `cd pygeodist && uv run pytest`

## Status

- ✅ (Step 1) Rust bindings shell: Added optional `python` feature, PyO3 dependency, and `_geodist_rs` module exporting `EARTH_RADIUS_METERS`; `cargo check` passes with and without the feature.
- ⬜ (Step 2) Build system wiring: configure maturin/pyproject and build targets.
- ⬜ (Step 3) Python surface: re-export constant and add smoke test.
- ⬜ (Step 4) Validation: run maturin develop and pytest once wiring is in place.

## Lessons Learned

- PyO3 0.22 requires using `Bound<PyModule>` in the module signature for `#[pymodule]`; the older `&PyModule` form no longer exposes `add`.

## Out-of-scope for this pass

- Final API design (function signatures, error mapping, data model).
- Performance tuning or zero-copy array handling.
- Packaging optimizations (manylinux builds, universal2, etc.).

## Risks / Open Questions

- Module naming: prefer `geodist._geodist_rs` to avoid top-level clutter; adjust if we later build multiple extensions.
- Versioning: keep using `uv-dynamic-versioning` unless maturin conflicts; revisit if tags diverge.
- Workspace structure: we may split bindings into a dedicated crate later if the Rust core needs to stay PyO3-free by default.
