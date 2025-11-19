"""Library-specific exceptions raised by the geodist Python layer."""

from __future__ import annotations


class GeodistError(Exception):
    """Base class for geodist errors surfaced from Python shims."""


class GeometryTypeError(GeodistError):
    """Raised when a geometry of an unexpected type is supplied to an operation."""


class InvalidGeometryError(GeodistError):
    """Raised when inputs cannot be coerced into a valid geometry."""


class CRSValidationError(GeodistError):
    """Raised when CRS metadata is missing or fails validation."""


class VectorizationError(GeodistError):
    """Raised when vectorized helpers cannot process the provided inputs."""


class KernelUnavailableError(GeodistError):
    """Raised when the compiled Rust kernels are missing at runtime."""


class KernelExecutionError(GeodistError):
    """Raised when a Rust kernel fails unexpectedly during execution."""


__all__ = (
    "CRSValidationError",
    "GeodistError",
    "GeometryTypeError",
    "InvalidGeometryError",
    "KernelUnavailableError",
    "KernelExecutionError",
    "VectorizationError",
)
