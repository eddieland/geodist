"""Geodesic typing primitives shared across geodist bindings.

Angles are expressed in degrees and distances in meters to match the Rust kernels.
"""

from __future__ import annotations

LatitudeDegrees = float
LongitudeDegrees = float
Meters = float

# Geographic point represented as (latitude_degrees, longitude_degrees).
PointDegrees = tuple[LatitudeDegrees, LongitudeDegrees]

# Bounding box encoded as (min_latitude, max_latitude, min_longitude, max_longitude).
BoundingBoxDegrees = tuple[LatitudeDegrees, LatitudeDegrees, LongitudeDegrees, LongitudeDegrees]

__all__ = (
    "BoundingBoxDegrees",
    "LatitudeDegrees",
    "LongitudeDegrees",
    "Meters",
    "PointDegrees",
)
