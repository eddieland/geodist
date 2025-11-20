# Python Vectorization for Geometry Batches

## Purpose

- Enable Python users to construct geodist objects (points, polylines, polygons) in bulk and run distance/area/heading computations over large collections with minimal Python overhead.
- Provide ergonomic, well-typed APIs that interoperate with common data containers (NumPy, memoryviews, Arrow arrays) while preserving correctness constraints on lat/lon units and order.

## Guiding Constraints

- Keep imports lightweight: vectorized paths rely on optional extras (e.g., NumPy/pyarrow) and degrade to list/tuple inputs without pulling heavy deps by default.
- Preserve invariants: lat_deg in [-90, 90], lon_deg in [-180, 180]; avoid silent coordinate reordering and validate per-element failures with clear error reporting or masks.
- Favor zero-copy where possible (memoryview/ndarray buffers) and minimize allocations; expose chunking knobs for very large inputs to bound memory.
- API parity with existing scalar constructors and operations; avoid shadow APIs that drift from Rust-backed behavior and keep `_geodist_rs.pyi` in sync.
- Release the GIL for Rust-backed kernels and keep interfaces deterministic (no implicit multithreading unless opt-in).

## Target Capabilities

1. Bulk constructors for core geometry types accepting contiguous buffer inputs (NumPy arrays, array-like lat/lon pairs, Arrow arrays when available) with fast-path validation.
2. Vectorized computation APIs (e.g., distances, bearings, areas) that operate on homogeneous collections and return array outputs aligned with inputs, with optional mask/error reporting.
3. Interop helpers to ingest/export tabular data (pandas/Arrow) without extra copies when shapes and dtypes permit.

## Subagent Execution Plan

The following backlog is prioritized for a single subagent (or small group) to implement iteratively. Update the _Status_ and _Lessons Learned_ sections while working.

### Task Backlog

Use emoji for status (e.g., ✅ done, 🚧 in progress, 📝 planned, ⏸️ deferred).

| Priority | Task | Definition of Done | Notes | Status |
| -------- | ---- | ------------------ | ----- | ------ |
| P0 | Decide API surface for vectorized constructors and outputs | Docstring-level spec for functions/classes (names, args, return types, error handling, optional extras) reviewed and aligned with scalar APIs | Include decisions on mask semantics vs exceptions and table interop naming | 📝 |
| P0 | Implement bulk point/polyline constructors over buffer inputs | Rust/PyO3 entry points accept memoryview/ndarray; validation fast path with lat/lon bounds; optional chunking for large arrays; `_geodist_rs.pyi` updated | Add unit/regression tests covering mixed valid/invalid rows and fallback paths | 📝 |
| P0 | Add vectorized distance/bearing/area kernels for homogeneous batches | Support pairwise and fixed-to-many variants; return ndarray/pyarrow or lists as negotiated; errors surfaced deterministically | Include GIL release and benchmarks for baseline throughput | 📝 |
| P1 | Provide tabular interop adapters (pandas/Arrow) | Helpers to build geometries from DataFrame/Arrow columns with zero-copy where feasible; documented behavior for missing/invalid values | Integration tests across pandas/pyarrow versions in CI matrix | 📝 |
| P1 | Documentation and examples | Add user-facing guide in `pygeodist` docs with realistic examples and performance notes; update README if API is public | Include guidance on coordinate units/order and optional dependencies | 📝 |
| P2 | Performance profiling and tuning | Benchmarks comparing scalar vs vectorized paths; identify bottlenecks and add micro-optimizations or chunk defaults | Could live under `pygeodist/devtools` and inform future tuning | 📝 |
| P3 | Optional multicore/streaming execution | Evaluate opt-in multithreading/streaming for extremely large batches without breaking determinism | Only proceed if P0/P1 performance goals unmet | 📝 |

_Add or remove rows as necessary while keeping priorities sorted (P0 highest)._

### Risks & Mitigations

- **Risk:** Heavy optional deps increase install friction. **Mitigation:** Keep NumPy/pyarrow optional extras; maintain pure-Python fallback with reasonable performance for small batches.
- **Risk:** Silent data corruption from coordinate ordering or invalid values. **Mitigation:** Enforce shape/dtype checks, bounds validation, and explicit mask/exception choices documented in API.
- **Risk:** Memory pressure on huge inputs. **Mitigation:** Provide chunked processing interfaces and document memory expectations; test with large synthetic datasets.
- **Risk:** Divergence between Rust kernels and Python stubs. **Mitigation:** Update `_geodist_rs.pyi` alongside Rust changes; add cross-language parity tests.

### Open Questions

- Should outputs default to NumPy arrays, Arrow arrays, or Python lists when no optional deps are installed?
- How should invalid rows be reported: boolean mask, exceptions with offending indices, or filtered outputs?
- Do we support heterogeneous geometry batches (e.g., mixed points/polylines) or only homogeneous collections?
- What minimum versions of NumPy/pandas/pyarrow do we target for compatibility and wheels?

## Status Tracking (to be updated by subagent)

- **Latest completed task:** _None yet — planned._
- **Next up:** _Decide API surface for vectorized constructors and outputs._

## Lessons Learned (ongoing)

- _TBD._
