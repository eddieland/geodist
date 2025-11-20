"""Python bindings for the geodist Rust library."""

from __future__ import annotations

from . import _geodist_rs
from .errors import (
    CRSValidationError,
    GeodistError,
    GeometryTypeError,
    InvalidGeometryError,
    KernelUnavailableError,
    VectorizationError,
)

EARTH_RADIUS_METERS = float(_geodist_rs.EARTH_RADIUS_METERS)

__all__ = (
    "CRSValidationError",
    "EARTH_RADIUS_METERS",
    "GeodistError",
    "GeometryTypeError",
    "InvalidGeometryError",
    "KernelUnavailableError",
    "VectorizationError",
)
