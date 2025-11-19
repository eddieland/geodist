//! PyO3 module exposing minimal bindings for smoke testing.
//!
//! PyO3 compiles this crate into a CPython extension and wires Rust
//! functions into a Python module via the `#[pymodule]` entrypoint; see
//! https://pyo3.rs/latest/ for patterns and lifecycle details.
//!
//! Keep bindings in sync: any changes here must be mirrored in
//! `pygeodist/src/geodist/_geodist_rs.pyi` in the same commit.
use pyo3::prelude::*;
use pyo3::types::PyModule;

use crate::constants::EARTH_RADIUS_METERS;

#[pymodule]
fn _geodist_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
  m.add("EARTH_RADIUS_METERS", EARTH_RADIUS_METERS)?;
  Ok(())
}
