"""Library-specific exceptions raised by the geodist Python layer."""

from __future__ import annotations


class GeodistError(Exception):
    """Base class for geodist errors surfaced from Python shims."""


class InvalidGeometryError(GeodistError):
    """Raised when inputs cannot be coerced into a valid geometry."""


__all__ = (
    "GeodistError",
    "InvalidGeometryError",
)
