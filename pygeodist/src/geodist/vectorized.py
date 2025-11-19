"""Vectorized helpers for batch geometry operations."""

from __future__ import annotations

from typing import Sequence

from .errors import KernelUnavailableError, VectorizationError
from .geometry import Geometry
from .types import CRSLike


def _ensure_lengths_match(left: Sequence[Geometry], right: Sequence[Geometry]) -> None:
    if len(left) != len(right):
        raise VectorizationError("Vectorized operations require sequences of equal length.")


def distance_many(
    left: Sequence[Geometry],
    right: Sequence[Geometry],
    *,
    crs: CRSLike = None,
) -> list[float]:
    """Compute pairwise distances across two geometry sequences."""
    _ensure_lengths_match(left, right)
    raise KernelUnavailableError(
        "Vectorized distances are unavailable until Rust kernels or NumPy fallbacks are wired."
    )


def equals_many(left: Sequence[Geometry], right: Sequence[Geometry]) -> list[bool]:
    """Evaluate equality across two geometry sequences."""
    _ensure_lengths_match(left, right)
    raise KernelUnavailableError("Vectorized equality is unavailable until Rust kernels or NumPy fallbacks are wired.")


def intersects_many(left: Sequence[Geometry], right: Sequence[Geometry]) -> list[bool]:
    """Evaluate intersections across two geometry sequences."""
    _ensure_lengths_match(left, right)
    raise KernelUnavailableError(
        "Vectorized intersections are unavailable until Rust kernels or NumPy fallbacks are wired."
    )


def within_many(left: Sequence[Geometry], right: Sequence[Geometry]) -> list[bool]:
    """Evaluate containment across two geometry sequences."""
    _ensure_lengths_match(left, right)
    raise KernelUnavailableError(
        "Vectorized containment is unavailable until Rust kernels or NumPy fallbacks are wired."
    )


__all__ = (
    "distance_many",
    "equals_many",
    "intersects_many",
    "within_many",
)
