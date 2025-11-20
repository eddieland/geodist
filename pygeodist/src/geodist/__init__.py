"""Minimal Python surface for the geodist Rust kernels.

Only the constant and error types are exported while Rust-backed geometry wrappers
are prepared. Keep this module's public API aligned with the compiled extension.
"""

from __future__ import annotations

from typing import Final

from . import _geodist_rs
from .errors import (
    CRSValidationError,
    GeodistError,
    GeometryTypeError,
    InvalidGeometryError,
    KernelExecutionError,
    KernelUnavailableError,
    VectorizationError,
)

EARTH_RADIUS_METERS: Final[float] = float(_geodist_rs.EARTH_RADIUS_METERS)

__all__ = (
    "CRSValidationError",
    "EARTH_RADIUS_METERS",
    "GeodistError",
    "GeometryTypeError",
    "InvalidGeometryError",
    "KernelExecutionError",
    "KernelUnavailableError",
    "VectorizationError",
)
