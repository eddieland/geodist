"""Geometry predicates and measures dispatched to the Rust kernels."""

from __future__ import annotations

from .errors import KernelUnavailableError
from .geometry import Geometry, Point
from .types import CRSLike


def distance(a: Geometry, b: Geometry, *, crs: CRSLike = None) -> float:
    """Compute the geodesic distance between two geometries in meters."""
    raise KernelUnavailableError(
        "Distance computation is unavailable until Rust kernels are wired to the Python layer."
    )


def equals(a: Geometry, b: Geometry) -> bool:
    """Return True when the geometries are topologically equal."""
    raise KernelUnavailableError("Equality testing is unavailable until Rust kernels are wired to the Python layer.")


def intersects(a: Geometry, b: Geometry) -> bool:
    """Return True when geometries have any boundary or interior intersection."""
    raise KernelUnavailableError(
        "Intersection testing is unavailable until Rust kernels are wired to the Python layer."
    )


def within(a: Geometry, b: Geometry) -> bool:
    """Return True when geometry `a` lies within geometry `b`."""
    raise KernelUnavailableError("Within predicate is unavailable until Rust kernels are wired to the Python layer.")


def buffer(geometry: Geometry, distance_meters: float) -> Geometry:
    """Return a buffered geometry generated around the input geometry."""
    raise KernelUnavailableError("Buffering is unavailable until Rust kernels are wired to the Python layer.")


def centroid(geometry: Geometry) -> Point:
    """Return the centroid of the geometry."""
    raise KernelUnavailableError(
        "Centroid computation is unavailable until Rust kernels are wired to the Python layer."
    )


__all__ = (
    "buffer",
    "centroid",
    "distance",
    "equals",
    "intersects",
    "within",
)
