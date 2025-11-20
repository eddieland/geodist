"""Typing stub for the compiled geodist Rust extension.

Exports stay intentionally small while Rust-backed geometry wrappers are built.
Keep this stub in sync with `geodist-rs/src/python.rs`.
"""

from typing import Final

EARTH_RADIUS_METERS: Final[float]

__all__ = ["EARTH_RADIUS_METERS"]

# Upcoming Rust-backed geometry handles will mirror the Rust structs once exposed:
# - Point(latitude_degrees: float, longitude_degrees: float)
# - Additional geometry containers will be added incrementally once the kernels are wired.
