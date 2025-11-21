"""Library-specific exceptions raised by the geodist Python layer."""

from __future__ import annotations

from . import _geodist_rs

GeodistError = _geodist_rs.GeodistError
InvalidLatitudeError = _geodist_rs.InvalidLatitudeError
InvalidLongitudeError = _geodist_rs.InvalidLongitudeError
InvalidAltitudeError = _geodist_rs.InvalidAltitudeError
InvalidDistanceError = _geodist_rs.InvalidDistanceError
InvalidRadiusError = _geodist_rs.InvalidRadiusError
InvalidEllipsoidError = _geodist_rs.InvalidEllipsoidError
InvalidBoundingBoxError = _geodist_rs.InvalidBoundingBoxError
EmptyPointSetError = _geodist_rs.EmptyPointSetError
InvalidGeometryError = _geodist_rs.InvalidGeometryError


__all__ = (
    "GeodistError",
    "InvalidGeometryError",
    "InvalidLatitudeError",
    "InvalidLongitudeError",
    "InvalidAltitudeError",
    "InvalidDistanceError",
    "InvalidRadiusError",
    "InvalidEllipsoidError",
    "InvalidBoundingBoxError",
    "EmptyPointSetError",
)
